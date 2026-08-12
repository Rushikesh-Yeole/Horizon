import os
import json
import logging
import asyncio
import hashlib
import re
from typing import List, Dict, Any, Literal, Tuple

import redis as sync_redis
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

import neo_graph as graph
from ops import log_llm_cost

load_dotenv()
log = logging.getLogger("advisor")
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
JD_TTL = 30 * 60

SYSTEM = (
    "You are a ruthless career analyst. Binary, objective, zero encouragement. "
    "Measure capability gap and proven velocity. Dense output only."
)




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


async def _spell_check(role: str, company: str, location: str) -> Dict[str, str]:
    prompt = f"Spell check and normalize: role, company, location. Return JSON: {{'role': '{role}', 'company': '{company}', 'location': '{location}'}}"
    try:
        resp = await _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        log_llm_cost("spell_check", MODEL, resp)
        if resp.choices[0].message.content:
            parsed = json.loads(resp.choices[0].message.content)
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]
            if isinstance(parsed, dict):
                return parsed
    except Exception as e:
        log.warning(f"Spell check failed: {e}")
    return {"role": role, "company": company, "location": location}


def _jd_cache_key(role: str, company: str, location: str) -> str:
    def clean(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return f"horizon:jd:{clean(company)}:{clean(role)}:{clean(location)}"


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
        f"Find the active JD or known engineering bar for '{role}' at '{company}', {location} (2024–2025). "
        f"Search greenhouse.io, lever.co, {company.lower()}.com/careers. "
        "Extract must-have technical skills only — no soft skills, no vague requirements. "
        'Return ONLY valid JSON: {"skills": ["skill1", "skill2"], "resp": "one-line bar summary"}'
    )

    jd_text = json.dumps({"skills": [], "resp": "JD unavailable."})
    skills: List[str] = []

    try:
        resp = await _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            extra_body={
                "plugins": [{"id": "web"}]
            }
        )
        log_llm_cost("fetch_jd", MODEL, resp)
        if resp and getattr(resp, "choices", None) and len(resp.choices) > 0 and resp.choices[0].message.content:
            jd_text = resp.choices[0].message.content.strip()
            skills = json.loads(jd_text).get("skills", [])
            if rc:
                await rc.setex(key, JD_TTL, jd_text)
    except Exception as e:
        log.warning(f"JD fetch failed [{company}]: {e}")

    return jd_text, skills, False


async def _build_card(
    rc,
    user_profile: Dict[str, Any],
    company: str,
    role: str,
    location: str,
    signals: str,
) -> Tuple[Dict[str, Any], str, List[str]]:
    jd_text, jd_skills, from_cache = await _fetch_jd(rc, role, company, location)
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
        resp = await _client.chat.completions.create(
            model=MODEL,
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
        log_llm_cost("build_card", MODEL, resp)
        return json.loads(resp.choices[0].message.content), role, fresh_skills
    except Exception as e:
        log.error(f"Card failed [{company}]: {e}")
        return {"company_name": company, "fit_score": 0, "verdict_headline": "Analysis failed.", "error": str(e), "reasoning_trace": "", "hiring_bar_difficulty": "Standard", "core_pillars_required": [], "user_skill_gaps": [], "feasibility_timeline_weeks": 0, "actionable_path": [], "main_advisory_text": ""}, role, []


async def generate_cards(
    rc,
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

    clean_data = await asyncio.gather(*[_spell_check(role, c, location) for c in companies])
    if clean_data:
        role = clean_data[0].get("role", role)
        location = clean_data[0].get("location", location)

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

    tasks = []
    for i, original_c in enumerate(companies):
        clean_c = clean_data[i].get("company", original_c) if clean_data else original_c
        tasks.append(_build_card(rc, user_profile, clean_c, role, location, get_signals(original_c)))

    results: List[Tuple[Dict, str, List[str]]] = await asyncio.gather(*tasks) if tasks else []

    cards = [r[0] for r in results]
    evolutions = [(r[1], r[2]) for r in results if r[2]]

    if evolutions:
        await asyncio.gather(*[graph.evolve(r, s) for r, s in evolutions])
        log.info(f"Graph evolved for {len(evolutions)} roles.")

    log.info(f"Advisory batch done: {len(cards)} cards.")
    return cards