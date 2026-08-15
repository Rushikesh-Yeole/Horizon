import os
import json
import logging
import asyncio
import datetime
import hashlib
import re
from typing import List, Dict, Any, Literal, Tuple, Optional

import redis as sync_redis
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tavily import TavilyClient

import neo_graph as graph
from ops import log_llm_cost
from scoring import compute_coverage_score, profile_hash as _profile_hash

load_dotenv()
log = logging.getLogger("advisor")
try:
    _tavily_key = os.getenv("TAVILY_API_KEYS") or os.getenv("TAVILY_API_KEY", "")
    _tavily_key = _tavily_key.split(",")[0].strip() if _tavily_key else ""
    tavily_client = TavilyClient(api_key=_tavily_key) if _tavily_key else None
except Exception as e:
    tavily_client = None
    log.warning(f"Failed to init Tavily: {e}")
logging.getLogger("httpx").setLevel(logging.WARNING)

_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
MODEL_JD_EXTRACTOR = os.getenv("MODEL_JD_EXTRACTOR", os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"))
MODEL_DISCOVER_ADVISOR = os.getenv("MODEL_DISCOVER_ADVISOR", os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"))
JD_TTL = 30 * 60

SYSTEM = (
    "You are a ruthless career analyst. Binary, objective, zero encouragement. "
    "Measure capability gap and proven velocity. Dense output only."
)





class AdvisoryCard(BaseModel):
    company_name: str
    reasoning_trace: str = Field(..., description="Max 30 words. Explain the fit tier given the pre-computed score and candidate background. (Ex: Score 83 -> Tier B: strong AI stack, TypeScript gap bridgeable.)")
    hiring_bar_difficulty: Literal["Forgiving", "Standard", "High", "Elite"]
    feasibility_timeline_weeks: int = Field(..., description="Realistic weeks to close the stated skill gaps, based on their complexity and the candidate's existing foundation. 0 if no gaps.")
    verdict_headline: str = Field(..., description="Max 10 words. Brutally honest, no spin.")
    actionable_path: List[str] = Field(..., description="3-4 concrete VERB-first steps targeting the stated gaps with named tech/platforms.")
    main_advisory_text: str = Field(..., description="Max 25 words. What actually moves the needle at this specific company.")
    jd_source_url: Optional[str] = Field(None, description="The exact URL where the JD was sourced from.")


async def _spell_check(role: str, company: str, location: str) -> Dict[str, str]:
    import re
    def clean(s: str) -> str:
        return re.sub(r'\s+', ' ', s.strip()).title()
    
    return {
        "role": clean(role),
        "company": clean(company),
        "location": clean(location)
    }


def _jd_cache_key(role: str, company: str, location: str) -> str:
    def clean(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return f"horizon:jd:{clean(company)}:{clean(role)}:{clean(location)}"


def _card_cache_key(user_id: str, profile: Dict[str, Any], company: str, role: str, location: str) -> str:
    phash = _profile_hash(profile)
    jd_sig = _jd_cache_key(role, company, location)
    return f"horizon:card:{user_id}:{phash}:{jd_sig}"


async def _fetch_jd(rc, role: str, company: str, location: str) -> Tuple[str, List[str], bool]:
    """Fetch JD via Gemini + Tavily Search. Returns (jd_text, skills, from_cache)."""
    key = _jd_cache_key(role, company, location)

    if rc:
        cached = await rc.get(key)
        if cached:
            log.info(f"JD cache hit: {company}")
            try:
                return cached, json.loads(cached).get("skills", []), True
            except Exception:
                return cached, [], True

    prompt = (
        f"Search the web for the canonical tech stack and job requirements for a '{role}' at '{company}'.\n"
        f"Synthesize the results to extract an exhaustive, deduplicated list of their core, non-negotiable technical requirements.\n"
        f"IMPORTANT: Extract atomic skill names only (e.g. 'PyTorch', 'React', 'Kubernetes', 'Go') — no vague terms like 'software engineering' or 'problem solving'.\n\n"
        'Return ONLY valid JSON: {"skills": ["skill1", "skill2"], "resp": "one-line bar summary", "source_url": "url_found"}'
    )

    jd_text = json.dumps({"skills": [], "resp": "JD unavailable.", "source_url": ""})
    skills: List[str] = []

    try:
        resp = await _client.chat.completions.create(
            model=MODEL_JD_EXTRACTOR,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            extra_body={"plugins": [{"id": "web"}]}
        )
        log_llm_cost("fetch_jd", MODEL_JD_EXTRACTOR, resp)
        if resp and getattr(resp, "choices", None) and len(resp.choices) > 0 and resp.choices[0].message.content:
            jd_text = resp.choices[0].message.content.strip()
            clean_text = jd_text
            if "```" in clean_text:
                parts = clean_text.split("```")
                clean_text = parts[1] if len(parts) >= 3 else parts[-1]
                if clean_text.startswith("json"): clean_text = clean_text[4:]
                if clean_text.startswith("python"): clean_text = clean_text[6:]
                clean_text = clean_text.strip()
            skills = json.loads(clean_text).get("skills", [])
            if rc:
                await rc.setex(key, JD_TTL, clean_text)
    except Exception as e:
        log.warning(f"JD fetch failed [{company}]: {e}")

    return jd_text, skills, False


async def _build_card(
    user_profile: Dict[str, Any],
    company: str,
    role: str,
    location: str,
    signals: str,
    jd_text: str,
    jd_skills: List[str],
    from_cache: bool
) -> Tuple[Dict[str, Any], str, List[str]]:
    fresh_skills = [] if from_cache else jd_skills

    p = user_profile.get("profile", {})
    r = user_profile.get("resume", {}).get("parsed_data", {})
    user_skills = list(set((p.get("skills") or []) + (r.get("skills") or [])))
    raw_projects = (p.get("projects") or []) + (r.get("projects") or [])
    projects = [
        f"{x['title']}: {x.get('desc', '')}" if isinstance(x, dict) else str(x)
        for x in raw_projects
    ]
    experience = list(set(
        (p.get("experience") or []) +
        (r.get("experience") or [])
    ))
    if not experience:
        experience = ["None"]

    # ─ Deterministic scoring ─ runs before the LLM call ──────────────────────
    coverage = await compute_coverage_score(user_skills, jd_skills)
    fit_score = coverage["evidence_coverage_score"]
    skill_gaps = coverage["missing"]        # taxonomy-aware, not string match
    core_pillars = jd_skills[:5]            # top skills extracted from JD
    tier = (
        "A" if fit_score >= 90 else
        "B" if fit_score >= 75 else
        "C" if fit_score >= 60 else "D"
    )

    prompt = f"""COMPANY: {company} ({location}) | ROLE: {role}

PRE-COMPUTED FACTS (ground truth — do not re-derive):
  Fit Score : {fit_score}/100  →  Tier {tier}
  Skill Gaps: {skill_gaps if skill_gaps else 'None — candidate covers all core pillars'}
  Core Pillars Required: {core_pillars}

Scoring tiers for context:
  A (90-100): >80% stack match + production proof in ecosystem
  B (75-89):  >50% match, bridgeable via sibling tech
  C (60-74):  <50% match, 3+ month paradigm shift
  D (<60):    core engineering pillars missing
Modifiers: FAANG/unicorn exp → +5pts | level mismatch → cap 20 | ecosystem lock-in → cap 30

CANDIDATE CONTEXT:
  Stack: {user_skills}
  Projects: {projects or ['None']}
  Experience: {experience}

INSIDER DATA (Blind/HN/Reddit signals):
  {signals or 'none'}

JD SUMMARY: {jd_text}

Generate the qualitative advisory only. Do NOT re-compute the score or gaps.
- reasoning_trace: explain WHY Tier {tier} / score {fit_score} given this candidate's background vs the role bar.
- hiring_bar_difficulty: infer from insider signals how selective this company is.
- feasibility_timeline_weeks: realistic weeks to close {len(skill_gaps)} gap(s) given the candidate's existing foundation.
- verdict_headline: ≤10 words, brutal, no spin.
- actionable_path: 3-4 VERB-first steps to close the gaps. Name exact tech.
- main_advisory_text: ≤25 words. Highest-signal thing for THIS company."""

    try:
        resp = await _client.chat.completions.create(
            model=MODEL_DISCOVER_ADVISOR,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "AdvisoryCard",
                    "strict": True,
                    "schema": AdvisoryCard.model_json_schema()
                }
            },
            temperature=0.0,
            seed=42,
        )
        log_llm_cost("build_card", MODEL_DISCOVER_ADVISOR, resp)
        card = json.loads(resp.choices[0].message.content)
        # Overwrite with deterministic values — LLM must not alter these
        card["fit_score"] = fit_score
        card["coverage_pct"] = coverage["coverage_pct"]
        card["user_skill_gaps"] = skill_gaps
        card["core_pillars_required"] = core_pillars
        return card, role, fresh_skills
    except Exception as e:
        log.error(f"Card failed [{company}]: {e}")
        return {"company_name": company, "fit_score": fit_score, "coverage_pct": coverage["coverage_pct"], "user_skill_gaps": skill_gaps, "core_pillars_required": core_pillars, "verdict_headline": "Analysis failed.", "error": str(e), "reasoning_trace": "", "hiring_bar_difficulty": "High", "feasibility_timeline_weeks": 0, "actionable_path": [], "main_advisory_text": ""}, role, []


async def generate_cards(
    rc,
    user_profile: Dict[str, Any],
    criteria: Dict[str, Any],
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """Parallel advisory card generation. Evolves graph only on fresh JD fetches."""
    role = criteria.get("role", "Software Engineer")
    location = criteria.get("location", "Global")
    companies = criteria.get("target_companies", [])[:4]

    clean_data = await asyncio.gather(*[_spell_check(role, c, location) for c in companies])
    if clean_data:
        role = clean_data[0].get("role", role)
        location = clean_data[0].get("location", location)

    async def process_company(original_c, clean_c):
        from main import _fetch_company_intel, _intel_cache_key
        
        user_id = user_profile.get("id") or user_profile.get("email") or "demo"
        profile = user_profile.get("profile", {})
        card_key = _card_cache_key(user_id, profile, clean_c, role, location)
        if rc and not force_refresh:
            cached_card = await rc.get(card_key)
            if cached_card:
                log.info(f"Card cache hit: {clean_c}")
                card = json.loads(cached_card)
                card.setdefault("retrieved_at", datetime.datetime.utcnow().isoformat())
                card["from_cache"] = True
                return card, role, []

        async def get_intel():
            key = _intel_cache_key(role, original_c, location)
            if rc:
                cached = await rc.get(key)
                if cached: 
                    log.info(f"Intel cache hit: {original_c}")
                    return json.loads(cached)
            intel = await _fetch_company_intel(role, original_c, location)
            if rc:
                await rc.setex(key, 3600, intel.model_dump_json())
            return intel.model_dump()
            
        intel, (jd_text, jd_skills, from_cache) = await asyncio.gather(
            get_intel(),
            _fetch_jd(rc, role, clean_c, location)
        )
        
        signals = "\n".join(r.get("content", "") for r in intel.get("results", []))
        card_tuple = await _build_card(user_profile, clean_c, role, location, signals, jd_text, jd_skills, from_cache)
        card = card_tuple[0]
        # Stamp provenance on every freshly-built card
        card["retrieved_at"] = datetime.datetime.utcnow().isoformat()
        card["from_cache"] = False
        if rc and card:
            await rc.setex(card_key, 3600, json.dumps(card))
        return (card,) + card_tuple[1:]

    tasks = []
    for i, original_c in enumerate(companies):
        clean_c = clean_data[i].get("company", original_c) if clean_data else original_c
        tasks.append(process_company(original_c, clean_c))

    results: List[Tuple[Dict, str, List[str]]] = await asyncio.gather(*tasks) if tasks else []

    cards = [r[0] for r in results]
    evolutions = [(r[1], r[2]) for r in results if r[2]]

    if evolutions:
        await asyncio.gather(*[graph.evolve(r, s) for r, s in evolutions])
        log.info(f"Graph evolved for {len(evolutions)} roles.")

    run_id = _profile_hash({"cards": [c.get("company_name") for c in cards], "role": role})
    log.info(f"Advisory batch done: {len(cards)} cards. run_id={run_id}")
    return cards