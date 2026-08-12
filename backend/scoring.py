"""
scoring.py — deterministic, pure-Python scoring functions.
No LLM calls. Fully testable, fully reproducible.
"""
import hashlib
import json
from typing import List, Dict, Any


def _normalize(skill: str) -> str:
    return skill.lower().strip()


def compute_coverage_score(
    user_skills: List[str],
    jd_skills: List[str],
) -> Dict[str, Any]:
    """
    Deterministic coverage scoring.

    Returns:
        coverage_pct          - % of JD skills covered by user skills
        missing               - JD skills absent from user stack (normalized)
        evidence_coverage_score - 0-100 int, same as coverage_pct rounded
    """
    if not jd_skills:
        return {"coverage_pct": 100.0, "missing": [], "evidence_coverage_score": 100}

    norm_user = {_normalize(s) for s in user_skills}
    norm_jd   = [_normalize(s) for s in jd_skills]

    matched = [s for s in norm_jd if s in norm_user]
    missing = [s for s in norm_jd if s not in norm_user]

    pct = (len(matched) / len(norm_jd)) * 100.0
    return {
        "coverage_pct": pct,
        "missing": missing,
        "evidence_coverage_score": round(pct),
    }


def profile_hash(profile: Dict[str, Any]) -> str:
    """Stable MD5 of the profile dict (sorted keys). Used for cache invalidation."""
    serialized = json.dumps(profile, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()
