import os
import ast
import json
import logging
import asyncio
import datetime
from typing import List, Optional, Dict, Any, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tavily import TavilyClient

import neo_graph as graph

load_dotenv()
log = logging.getLogger("tree")

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", "").split(",")[0])
MODEL = "gemini-2.5-flash-lite"
CACHE_TTL = 86400

BIO_DOMAINS = [
    "reddit.com", "news.ycombinator.com", "teamblind.com", "indiehackers.com",
    "linkedin.com", "medium.com", "substack.com", "github.com",
    "netflixtechblog.com", "engineering.fb.com", "openai.com/research",
]


# Schemas

class Opportunity(BaseModel):
    title: str
    url: Optional[str] = None
    snippet: str = Field(..., description="Why this matches the candidate's trajectory.")


class Stage(BaseModel):
    name: str = Field(..., description="Concrete role or milestone title.")
    description: str
    eta_months: int
    skill_requirements: List[str]
    citations: List[str] = Field(..., description="SOURCE_REF_X tags from evidence.")
    top_opportunities: List[Opportunity]


class PathBranch(BaseModel):
    id: str
    title: str = Field(..., description="Career archetype name.")
    summary: str = Field(..., description="Long-term destination and honest probability assessment.")
    fit_score: float
    stages: List[Stage]


class CareerTree(BaseModel):
    user_id: str
    generated_at: str
    paths: List[PathBranch]
    observed_paths: List[List[str]] = Field(
        default_factory=list,
        description=(
            "Real career progressions extracted ONLY from evidence sources — zero hallucination. "
            "Each inner array is an ordered sequence of role titles from junior to senior "
            "as seen in the injected Tavily content. E.g. ['SWE Intern', 'SWE II', 'Senior SWE', 'Staff SWE']."
        ),
    )


# Pipeline

async def _get_archetypes(skills: List[str]) -> Tuple[List[str], List[List[str]]]:
    """
    Graph-first archetype discovery with trajectory traversal.
    Returns (tavily_queries, known_trajectories).
    known_trajectories are injected into synthesis as prior context.
    Falls back to LLM if graph has insufficient data.
    """
    try:
        records = await graph.find_trajectories(skills, limit=5)
        if len(records) < 5:
            log.warning("Graph returned <5 trajectory matches — falling back to LLM.")
            return await _archetypes_from_llm(skills), []

        queries = [
            f"{rec['terminal']} career path site:reddit.com OR site:teamblind.com"
            for rec in records
        ]
        trajectories = [rec["trajectory"] for rec in records if len(rec["trajectory"]) > 1]
        log.info(f"Graph trajectories: {[r['trajectory'] for r in records]}")
        return queries, trajectories

    except Exception as e:
        log.warning(f"Graph traversal failed: {e}")
        return await _archetypes_from_llm(skills), []


async def _archetypes_from_llm(skills: List[str]) -> List[str]:
    log.info("Generating archetypes via LLM fallback.")
    prompt = f"""Predict 4 distinct long-term career destinations (5-10 year horizon) for someone with these skills: {skills}

Rules:
- Each path must be architecturally different (IC track, founder, domain specialist, etc.)
- Be opinionated — match paths to the actual skill signal, not generic mappings
- No tech stack names in archetype titles

Return ONLY a JSON array of 3 Tavily search queries targeting real career stories and biographies:
["Staff Engineer at fintech career path reddit", "ML infrastructure founder journey indiehackers", "Engineering Manager FAANG teamblind"]"""

    resp = await asyncio.to_thread(
        _client.models.generate_content,
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4),
    )
    text = resp.text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").replace("python", "").strip()
    try:
        return json.loads(text)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception:
            return [f"senior software engineer career path {skills[:2]}"] * 3


async def _fetch_evidence(queries: List[str]) -> Tuple[str, Dict[str, str]]:
    """Fetch real career stories for each archetype in parallel."""
    log.info(f"Fetching evidence for {len(queries)} archetypes...")

    async def fetch(q: str) -> List[Dict]:
        try:
            res = await asyncio.to_thread(
                _tavily.search,
                query=q,
                search_depth="advanced",
                include_domains=BIO_DOMAINS,
                max_results=14,
            )
            return res.get("results", [])
        except Exception as e:
            log.error(f"Tavily error for '{q}': {e}")
            return []

    batches = await asyncio.gather(*[fetch(q) for q in queries])

    evidence = ""
    url_map: Dict[str, str] = {}
    idx = 0

    for i, results in enumerate(batches):
        evidence += f"<ARCHETYPE_SOURCES query='{queries[i]}'>\n"
        for item in results:
            ref = f"SOURCE_REF_{idx}"
            url_map[ref] = item["url"]
            evidence += f"[{ref}]: {item['url']}\nTITLE: {item['title']}\nCONTENT: {item['content'][:3000]}\n\n"
            idx += 1
        evidence += "</ARCHETYPE_SOURCES>\n"

    log.info(f"Evidence gathered: {idx} sources.")
    return evidence, url_map


async def _synthesize(
    user_id: str,
    profile: str,
    evidence: str,
    known_trajectories: List[List[str]],
) -> Dict[str, Any]:
    """
    Generate career tree grounded in evidence.
    known_trajectories from the graph are injected as validated prior paths.
    Also extracts observed_paths from evidence to feed back into the graph.
    """
    log.info("Synthesizing career tree...")

    prior_ctx = ""
    if known_trajectories:
        formatted = "\n".join(f"  {i+1}. {' → '.join(t)}" for i, t in enumerate(known_trajectories))
        prior_ctx = f"""
GRAPH PRIOR — validated career progressions from historical data (use as reference, not constraint):
{formatted}
Search evidence for better/alternative paths if they exist.
"""

    prompt = f"""You are a career intelligence analyst. Build a 5-path roadmap grounded strictly in the evidence below.

CANDIDATE:
{profile}
{prior_ctx}
EVIDENCE:
{evidence}

Rules for paths:
- Minimum 4 stages per path. Every stage must be triangulated from ≥3 evidence sources — cite with exact SOURCE_REF tags
- Name specific companies, programs, or platforms per stage — no generic advice
- skill_requirements: concrete technologies and tools only
- eta_months: realistic based on evidence patterns
- top_opportunities: real roles or programs matching this stage right now
- fit_score: (Range 0-100%) cold probability accounting for skill gaps and market reality — not encouragement
- summary: destination + why this candidate might realistically reach it + the single biggest obstacle

Rules for observed_paths:
- Extract ONLY career progressions that are explicitly described in the evidence sources
- Each array = one person's or one archetype's role sequence in chronological order
- Minimum 3 roles per sequence, maximum 8
- Role titles must be as they appear in the evidence — no paraphrasing or invention
- If evidence has no clear sequences, return an empty array — do not hallucinate

Return valid JSON matching the CareerTree schema exactly."""

    resp = await asyncio.to_thread(
        _client.models.generate_content,
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CareerTree,
            temperature=0.1,
        ),
    )
    log.info("Synthesis done.")
    return resp.parsed.model_dump()


def _resolve_citations(tree: Dict[str, Any], url_map: Dict[str, str]) -> int:
    count = 0
    for path in tree.get("paths", []):
        for stage in path.get("stages", []):
            resolved = []
            for ref in stage.get("citations", []):
                clean = ref.strip("[] ")
                if clean in url_map:
                    resolved.append(url_map[clean])
                    count += 1
                elif ref.startswith("http"):
                    resolved.append(ref)
            stage["citations"] = resolved
    return count


# ── Entry Point ───────────────────────────────────────────────────────────────

async def generate_tree(user_id: str, user_doc: Dict[str, Any], redis_client) -> Dict[str, Any]:
    """
    Full pipeline: graph trajectories → evidence → synthesis → citation resolution → graph learning.
    Each run feeds observed career paths back into the graph, making future traversals smarter.
    """
    cache_key = f"horizon:tree:v7:{user_id}"

    if redis_client:
        cached = await redis_client.get(cache_key)
        if cached:
            log.info("Returning cached tree.")
            return json.loads(cached)

    p = user_doc.get("profile", {})
    parsed = user_doc.get("resume", {}).get("parsed_data", {})
    skills = list(set((p.get("skills") or []) + (parsed.get("skills") or [])))
    projects = (p.get("projects") or []) + (parsed.get("projects") or [])
    project_titles = [x.get("title") for x in projects if isinstance(x, dict)]

    profile = (
        f"Target role: {p.get('preferences', {}).get('role', 'Software Engineer')}\n"
        f"Interests: {p.get('preferences', {})}\n"
        f"Skills: {skills[:15]}\n"
        f"Projects: {project_titles}"
    )

    queries, known_trajectories = await _get_archetypes(skills)
    evidence, url_map = await _fetch_evidence(queries)
    tree = await _synthesize(user_id, profile, evidence, known_trajectories)

    resolved = _resolve_citations(tree, url_map)
    log.info(f"Citations resolved: {resolved}")

    # Feed extracted paths back into the graph — learning loop
    observed = tree.pop("observed_paths", [])
    if observed:
        await graph.evolve_paths(observed)
        log.info(f"Graph learned {len(observed)} new career tracks from this synthesis.")

    tree["generated_at"] = datetime.datetime.utcnow().isoformat()

    if redis_client:
        await redis_client.setex(cache_key, CACHE_TTL, json.dumps(tree))
        log.info("Tree cached.")

    return tree