import os
import json
import logging
import asyncio
import hashlib
from typing import List, Dict, Any, Literal, Tuple

import redis as sync_redis
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

import neo_graph as graph
from ops import log_gemini_cost

load_dotenv()
log = logging.getLogger("advisor")
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash-lite"
JD_TTL = 30 * 60

SYSTEM = (
    "You are a ruthless career analyst. Binary, objective, zero encouragement. "
    "Measure capability gap and proven velocity. Dense output only."
)

_sync_redis_client = None


def _get_sync_redis():
    global _sync_redis_client
    if _sync_redis_client is None:
        url = os.getenv("REDIS_URL")
        if url:
            _sync_redis_client = sync_redis.from_url(url, decode_responses=True)
    return _sync_redis_client


class AdvisoryCard(BaseModel):
    company_name: str
    reasoning_trace: str = Field(..., description="Max 30 words. Step-by-step scoring & tiering logic. (Ex: Base tier C -> Amazon internship modifier applied -> Final tier B)")
    hiring_bar_difficulty: Literal["Forgiving", "Standard", "High", "Elite"]
    core_pillars_required: List[str] = Field(..., description="3-5 non-negotiable hard skills from JD.")
    user_skill_gaps: List[str] = Field(..., description="Top 10 important JD skills strictly absent from user stack.")
    fit_score: int = Field(..., description="0-100 match score.")
    feasibility_timeline_weeks: int
    verdict_headline: str = Field(..., description="Max 10 words. Brutally honest, no spin.")
    actionable_path: List[str] = Field(..., description="3-4 concrete VERB-first steps with named tech/platforms.")
    main_advisory_text: str = Field(..., description="Max 25 words. What actually moves the needle.")


def _jd_cache_key(role: str, company: str, location: str) -> str:
    h = hashlib.md5(f"{role.lower()}|{company.lower()}|{location.lower()}".encode()).hexdigest()
    return f"horizon:jd:{h}"


def _fetch_jd(role: str, company: str, location: str) -> Tuple[str, List[str], bool]:
    """Fetch JD via Gemini + Google Search. Returns (jd_text, skills, from_cache)."""
    rc = _get_sync_redis()
    key = _jd_cache_key(role, company, location)

    if rc:
        cached = rc.get(key)
        if cached:
            log.info(f"JD cache hit: {company}")
            try:
                return cached, json.loads(cached).get("skills", []), True
            except Exception:
                return cached, [], True

    prompt = (
        f"Find the active JD or known engineering bar for '{role}' at '{company}', {location} (2024–2025). "
        f"Search greenhouse.io, lever.co, {company.lower()}.com/careers. "
        "Extract must-have technical skills only — no soft skills, no vague requirements. "
        'Return ONLY valid JSON: {"skills": ["skill1", "skill2"], "resp": "one-line bar summary"}'
    )

    jd_text = json.dumps({"skills": [], "resp": "JD unavailable."})
    skills: List[str] = []

    try:
        resp = _client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0,
            ),
        )
        log_gemini_cost("fetch_jd", MODEL, resp)
        if resp.text:
            jd_text = resp.text.replace("```json", "").replace("```", "").strip()
            skills = json.loads(jd_text).get("skills", [])
            if rc:
                rc.setex(key, JD_TTL, jd_text)
    except Exception as e:
        log.warning(f"JD fetch failed [{company}]: {e}")

    return jd_text, skills, False


def _build_card(
    user_profile: Dict[str, Any],
    company: str,
    role: str,
    location: str,
    signals: str,
) -> Tuple[Dict[str, Any], str, List[str]]:
    jd_text, jd_skills, from_cache = _fetch_jd(role, company, location)
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

    prompt = f"""COMPANY: {company} ({location}) | ROLE: {role}

JD SIGNALS: {jd_text}
INSIDER DATA: {signals or 'none'}
CANDIDATE STACK: {user_skills}
CANDIDATE PROJECTS: {projects}
EXPERIENCE: {experience}

Scoring Tiers:
  A (90-100): >80% stack match + production proof in target ecosystem
  B (75-89): >50% match, bridgeable via sibling tech (React→Vue, Java→Kotlin)
  C (60-74): <50% match, paradigm shift required, 3+ month ramp
  D (<60): core engineering pillars missing
Modifiers: FAANG/unicorn exp → +5pts | level mismatch → hard cap 20 | ecosystem lock-in → hard cap 30

Gap list: Only Top 10 important skills only from JD, that are strictly absent from candidate stack — zero false positives.
Verdict: state the reality in ≤10 words, no spin, no encouragement.
Actionable path: name actual technologies, platforms, or specific project types — no vague steps.
Advisory: what single thing most changes this person's odds at this company right now."""

    try:
        resp = _client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                response_mime_type="application/json",
                response_schema=AdvisoryCard,
                temperature=0.0,
                seed=42,
            ),
        )
        log_gemini_cost("build_card", MODEL, resp)
        return resp.parsed.model_dump(), role, fresh_skills
    except Exception as e:
        log.error(f"Card failed [{company}]: {e}")
        return {"company_name": company, "fit_score": 0, "verdict_headline": "Analysis failed.", "error": str(e)}, role, []


async def generate_cards(
    user_profile: Dict[str, Any],
    market_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Parallel advisory card generation. Evolves graph only on fresh JD fetches."""
    criteria = market_data.get("search_criteria", {})
    role = criteria.get("role", "Software Engineer")
    location = criteria.get("location", "Global")
    raw_intel = market_data.get("company_intelligence", [])

    companies = criteria.get("target_companies") or list({
        c["company_name"] if isinstance(c, dict) else c.company_name
        for c in raw_intel
    })[:3]

    def get_signals(company: str) -> str:
        for item in raw_intel:
            name = item["company_name"] if isinstance(item, dict) else item.company_name
            if name.lower() == company.lower():
                results = item.get("results", []) if isinstance(item, dict) else item.results
                return "\n".join(
                    r.get("content", "") if isinstance(r, dict) else r.content
                    for r in results
                )
        return ""

    results: List[Tuple[Dict, str, List[str]]] = await asyncio.gather(*[
        asyncio.to_thread(_build_card, user_profile, c, role, location, get_signals(c))
        for c in companies
    ])

    cards = [r[0] for r in results]
    evolutions = [(r[1], r[2]) for r in results if r[2]]

    if evolutions:
        await asyncio.gather(*[graph.evolve(r, s) for r, s in evolutions])
        log.info(f"Graph evolved for {len(evolutions)} roles.")

    log.info(f"Advisory batch done: {len(cards)} cards.")
    return cards