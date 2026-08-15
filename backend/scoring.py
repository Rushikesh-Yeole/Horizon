"""
scoring.py — Agnostic, LLM-driven semantic scoring engine.
Zero hardcoded heuristics. Infinitely scalable across all tech professions.
"""
import json
import os
import logging
import hashlib
from typing import List, Dict, Any
from openai import AsyncOpenAI

log = logging.getLogger(__name__)

MODEL = os.getenv("MODEL_SCORING", os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"))
_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

async def compute_coverage_score(
    user_skills: List[str],
    jd_skills: List[str],
) -> Dict[str, Any]:
    """
    LLM-driven semantic coverage scoring.
    
    Returns:
        coverage_pct          - % of JD skills covered by user skills
        missing               - JD skills absent from user stack
        evidence_coverage_score - 0-100 int, same as coverage_pct rounded
    """
    if not jd_skills:
        # No JD extracted — indeterminate, not a perfect score
        return {"coverage_pct": 0.0, "missing": [], "evidence_coverage_score": 0, "no_jd": True}

    if not user_skills:
        return {"coverage_pct": 0.0, "missing": jd_skills, "evidence_coverage_score": 0}

    prompt = (
        f"You are an expert technical evaluator.\n"
        f"Given a candidate's actual extracted skills and a job description's required skills, determine EXACTLY which JD skills the candidate is completely missing.\n\n"
        f"CANDIDATE SKILLS:\n{json.dumps(user_skills)}\n\n"
        f"REQUIRED JD SKILLS:\n{json.dumps(jd_skills)}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. A candidate 'has' a JD skill if they possess it directly OR if they possess a skill that semantically covers it (e.g., 'React' covers 'Frontend', 'LangChain' covers 'RAG', 'C++' covers 'Systems Programming').\n"
        f"2. Return ONLY the JD skills that are definitively MISSING from the candidate's profile.\n"
        f"3. Return the exact string names of the missing skills as they appeared in the REQUIRED JD SKILLS list.\n"
        f"4. If no skills are missing, return an empty array.\n\n"
        'Return ONLY valid JSON: {"missing": ["skill1", "skill2"]}'
    )

    missing = jd_skills.copy()  # Fallback to 0% coverage if LLM fails
    try:
        resp = await _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        if resp and getattr(resp, "choices", None) and len(resp.choices) > 0 and resp.choices[0].message.content:
            content = resp.choices[0].message.content.strip()
            if "```" in content:
                parts = content.split("```")
                content = parts[1] if len(parts) >= 3 else parts[-1]
                if content.startswith("json"): content = content[4:]
                content = content.strip()
            
            parsed = json.loads(content)
            missing = parsed.get("missing", [])
            # Ensure exact matches to jd_skills array
            missing = [s for s in jd_skills if any(m.lower() == s.lower() for m in missing)]
    except Exception as e:
        log.warning(f"LLM scoring failed: {e}")

    matched_count = len(jd_skills) - len(missing)
    pct = (matched_count / len(jd_skills)) * 100.0 if jd_skills else 0.0

    print(f"\n[SCORING DEBUG] User Base: {user_skills}\n[SCORING DEBUG] JD Base: {jd_skills}\n[SCORING DEBUG] Missing Evaluated: {missing}\n")

    return {
        "coverage_pct": pct,
        "missing": missing,
        "evidence_coverage_score": int(round(pct)),
    }

def profile_hash(profile: Dict[str, Any]) -> str:
    """Stable hash of a user profile dict."""
    s = json.dumps(profile, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
