# seeder_minimal.py
import os
import logging
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from rapidfuzz import process, fuzz
from dotenv import load_dotenv
from typing import Dict, Any, List, Tuple, Optional

load_dotenv()
logging.basicConfig(level=logging.INFO)

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "kb"
ONET_CSV_PATH = os.environ.get("ONET_WORKSTYLES_CSV", "./app/data/WorkStyles.csv")
FUZZY_THRESHOLD = float(os.environ.get("FUZZY_THRESHOLD", 80.0))

mongo = AsyncIOMotorClient(MONGODB_URI)
db = mongo[DB_NAME]
domains_col = db["domains"]
personality_col = db["personality"]

app = FastAPI(title="Minimal O*NET Personality Seeder (fixed)")

# -------- Mapping WorkStyles -> Big Five (trimmed version) --------
WORKSTYLE_TO_BIG5: Dict[str, Dict[str, float]] = {
    "Achievement/Effort": {"Openness": 0.0, "Conscientiousness": 1.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Persistence": {"Openness": 0.0, "Conscientiousness": 1.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Initiative": {"Openness": 0.0, "Conscientiousness": 1.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Leadership": {"Openness": 0.2, "Conscientiousness": 0.3, "Extraversion": 0.5, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Cooperation": {"Openness": 0.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 1.0, "Neuroticism": 0.5},
    "Concern for Others": {"Openness": 0.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 1.0, "Neuroticism": 0.5},
    "Social Orientation": {"Openness": 0.0, "Conscientiousness": 0.0, "Extraversion": 0.6, "Agreeableness": 0.4, "Neuroticism": 0.5},
    "Self-Control": {"Openness": 0.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.0},
    "Stress Tolerance": {"Openness": 0.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.0},
    "Adaptability/Flexibility": {"Openness": 0.33, "Conscientiousness": 0.0, "Extraversion": 0.33, "Agreeableness": 0.0, "Neuroticism": 0.34},
    "Dependability": {"Openness": 0.0, "Conscientiousness": 1.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Attention to Detail": {"Openness": 0.0, "Conscientiousness": 1.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Integrity": {"Openness": 0.0, "Conscientiousness": 0.3, "Extraversion": 0.0, "Agreeableness": 0.4, "Neuroticism": 0.3},
    "Independence": {"Openness": 0.5, "Conscientiousness": 0.5, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Innovation": {"Openness": 1.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5},
    "Analytical Thinking": {"Openness": 1.0, "Conscientiousness": 0.0, "Extraversion": 0.0, "Agreeableness": 0.0, "Neuroticism": 0.5}
}

BIG5_AXES = ["Extraversion", "Agreeableness", "Conscientiousness", "Openness", "Neuroticism"]

# In-memory mappings built from CSV
ONET_TITLES: List[str] = []
ONET_TITLE_TO_WORKSTYLES: Dict[str, Dict[str, float]] = {}
ONET_TITLE_TO_ROW: Dict[str, Dict[str, Any]] = {}


def load_onet_csv(path: str = ONET_CSV_PATH) -> None:
    """
    Loads the long-form O*NET WorkStyles CSV and builds:
      - ONET_TITLES: list of titles
      - ONET_TITLE_TO_WORKSTYLES: mapping title -> {Element Name: Data Value}
      - ONET_TITLE_TO_ROW: first raw row dict (metadata) per title
    """
    global ONET_TITLES, ONET_TITLE_TO_WORKSTYLES, ONET_TITLE_TO_ROW

    df = pd.read_csv(path, dtype=str).fillna("")
    cols = df.columns.tolist()

    title_col = next((c for c in cols if "Title" in c), None)
    element_name_col = next((c for c in cols if "Element Name" in c), None)
    data_value_col = next((c for c in cols if "Data Value" in c or "DataValue" in c or "Data_Value" in c), None)
    scale_col = next((c for c in cols if "Scale ID" in c or "Scale" in c), None)

    if not title_col or not element_name_col or not data_value_col:
        raise RuntimeError(f"Could not find expected columns in CSV. Columns found: {cols}")

    # keep only Importance (IM) scale entries when present
    if scale_col and df[scale_col].str.contains("IM").any():
        df = df[df[scale_col].str.contains("IM")]

    grouped: Dict[str, Dict[str, float]] = {}
    first_row: Dict[str, Dict[str, Any]] = {}
    for _, row in df.iterrows():
        title = str(row[title_col]).strip()
        el_name = str(row[element_name_col]).strip()
        raw_val = row[data_value_col]
        try:
            val = float(raw_val)
        except Exception:
            try:
                val = float(str(raw_val).replace(",", "."))
            except Exception:
                continue
        if not title or not el_name:
            continue
        grouped.setdefault(title, {})[el_name] = val
        if title not in first_row:
            first_row[title] = row.to_dict()

    ONET_TITLES = sorted(grouped.keys())
    ONET_TITLE_TO_WORKSTYLES = grouped
    ONET_TITLE_TO_ROW = first_row

    logging.info("Loaded %d O*NET titles (workstyles grouped)", len(ONET_TITLES))


def extract_workstyles_from_title(title: str) -> Dict[str, float]:
    ws_all = ONET_TITLE_TO_WORKSTYLES.get(title, {})
    # include only workstyles we have mapping for
    return {k: float(v) for k, v in ws_all.items() if k in WORKSTYLE_TO_BIG5}


def compute_big5(ws_row: Dict[str, float]) -> Dict[str, float]:
    raw = {b: 0.0 for b in BIG5_AXES}
    weight_sums = {b: 0.0 for b in BIG5_AXES}
    for ws, imp in ws_row.items():
        try:
            imp = float(imp)
        except Exception:
            imp = 0.0
        imp = max(0.0, imp - 1.0)  # scale 1–5 → 0–4
        for axis, w in WORKSTYLE_TO_BIG5[ws].items():
            raw[axis] += imp * w
            weight_sums[axis] += abs(w)
    norm: Dict[str, float] = {}
    for axis in BIG5_AXES:
        denom = 4.0 * weight_sums.get(axis, 0.0)
        norm[axis] = (raw[axis] / denom) if denom else 0.5
    return norm


def big5_to_mbti(big5: Dict[str, float]) -> Dict[str, float]:
    return {
        "E": round(big5.get("Extraversion", 0.5), 3),
        "S": round(1 - big5.get("Openness", 0.5), 3),
        "T": round(1 - big5.get("Agreeableness", 0.5), 3),
        "J": round(big5.get("Conscientiousness", 0.5), 3),
    }


def fuzzy_matches_for_job(domain_job: str, limit: Optional[int] = 5) -> List[Tuple[str, float]]:
    matches = process.extract(
        domain_job,
        ONET_TITLES,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=FUZZY_THRESHOLD,
        limit=limit
    )
    seen = set()
    unique: List[Tuple[str, float]] = []
    for title, score, _ in matches:
        if title in seen:
            continue
        seen.add(title)
        unique.append((title, float(score)))
    return unique


async def seed_job(domain_job: str) -> Optional[Dict[str, Any]]:
    matches = process.extract(
        domain_job,
        ONET_TITLES,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=FUZZY_THRESHOLD,
        limit=None
    )
    seen = set()
    matches_array: List[Dict[str, Any]] = []
    for match_title, score, _ in matches:
        if match_title in seen:
            continue
        seen.add(match_title)
        ws = extract_workstyles_from_title(match_title)
        if not ws:
            # no workstyles available → skip this match
            continue
        big5 = compute_big5(ws)
        mbti = big5_to_mbti(big5)
        matches_array.append({
            "title": match_title,
            "mbti": mbti,
            "score": round(float(score), 1)
        })

    if not matches_array:
        return None

    doc = {
        "job_id": domain_job,
        "job_titles": matches_array
    }
    await personality_col.replace_one({"job_id": domain_job}, doc, upsert=True)
    return doc


async def do_seed_all() -> Dict[str, int]:
    cursor = domains_col.find({}, {"jobs": 1})
    jobs: List[str] = []
    async for doc in cursor:
        jobs.extend(doc.get("jobs", []))
    # dedupe and normalize whitespace
    seen_set = set()
    seen_jobs: List[str] = []
    for j in jobs:
        if not j:
            continue
        j = j.strip()
        if j and j not in seen_set:
            seen_set.add(j)
            seen_jobs.append(j)

    inserted = 0
    for job in seen_jobs:
        res = await seed_job(job)
        if res:
            inserted += 1
    return {"domain_jobs_processed": len(seen_jobs), "inserted_docs": inserted}


@app.on_event("startup")
async def startup():
    load_onet_csv()


@app.post("/seed/all")
async def seed_all_endpoint():
    """
    Run seeding inline (await) to avoid running into 'no running event loop'
    when using background thread pools. This returns counts once finished.
    """
    result = await do_seed_all()
    return {"status": "ok", **result}


@app.post("/seed/single")
async def seed_single(job_title: str):
    doc = await seed_job(job_title)
    return doc or {"error": "no match"}


@app.get("/fuzzy_matches")
async def fuzzy_matches(limit_per_job: int = 5):
    matches_dict: Dict[str, List[str]] = {}
    cursor = domains_col.find({}, {"jobs": 1})
    async for doc in cursor:
        jobs = doc.get("jobs", [])
        for job in jobs:
            job = job.strip()
            if not job or job in matches_dict:
                continue
            matched = fuzzy_matches_for_job(job, limit=limit_per_job)
            matches_dict[job] = [t for t, s in matched]
    total_matches = sum(len(v) for v in matches_dict.values())
    return {"total_jobs": len(matches_dict), "total_matches_found": total_matches, "matches": matches_dict}


@app.get("/personalities")
async def all_personalities(limit: int = 1000):
    docs = await personality_col.find({}, {"_id": 0}).to_list(length=limit)
    return docs


@app.get("/count")
async def skills_count():
    skills_count = await db["skills"].count_documents({})
    domain_count = await domains_col.count_documents({})
    jobs_count = await personality_col.count_documents({})
    return {"total skills": skills_count, "total domains": domain_count, "total jobs": jobs_count}
