# main.py
import os
import math
import json
import asyncio
from typing import List, Dict, Any, Optional, Set
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rapidfuzz import process, fuzz
from datetime import datetime, timezone

# Motor async MongoDB client
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()  # <- this loads variables from .env

# ---------- CONFIG ----------
FUZZY_TITLE_THRESHOLD = float(os.environ.get("FUZZY_TITLE_THRESHOLD", 70.0))
ACTIVE_FUZZY_TITLE_THRESHOLD = float(os.environ.get("ACTIVE_FUZZY_TITLE_THRESHOLD", 60.0))
SKILL_FUZZY_THRESHOLD = float(os.environ.get("SKILL_FUZZY_THRESHOLD", 60.0))
MAX_TITLE_MATCHES = int(os.environ.get("MAX_TITLE_MATCHES", 50))
W_SKILLS = float(os.environ.get("W_SKILLS", 0.60))
W_PERSONALITY = float(os.environ.get("W_PERSONALITY", 0.25))
W_RECENCY = float(os.environ.get("W_RECENCY", 0.15))
SCORING_CONCURRENCY = int(os.environ.get("SCORING_CONCURRENCY", 32))

MONGODB_URI = os.environ.get("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI environment variable must be set to your MongoDB Atlas connection string")

# DB / collection names (as requested)
JOBS_DB = os.environ.get("JOBS_DB", "job_listings")
JOBS_COLLECTION = os.environ.get("JOBS_COLLECTION", "jobs")
USERS_DB = os.environ.get("USERS_DB", "users_db")
USERS_COLLECTION = os.environ.get("USERS_COLLECTION", "profiles")

app = FastAPI(title="Aggregator (MongoDB-backed)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # list of allowed origins
    allow_credentials=True,      # allow cookies, auth headers
    allow_methods=["*"],         # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],         # allow all headers
)

# ---------- In-memory data structures ----------
# JOBS: List[Dict] — canonical jobs loaded from Mongo
JOBS: List[Dict[str, Any]] = []
# USERS: mapping of user id string -> user document
USERS: Dict[str, Dict[str, Any]] = {}

# ---------- Indexes & caches ----------
_PERSONALITY_INDEX: List[tuple[str, Dict[str, float]]] = []
_PERSONALITY_TITLES: List[str] = []
_JOB_TITLES: List[str] = []
_JOB_COUNT = 0
_JOB_SKILLS_LOWER: List[List[str]] = []
_SKILL_INVERT: Dict[str, Set[int]] = {}
_scoring_sema = asyncio.Semaphore(SCORING_CONCURRENCY)

# ---------- Helpers ----------
def safe_mbti_from_doc(doc: Dict[str, Any]) -> Dict[str, float]:
    # Accepts user or job doc with potential fields "mbti" or "personality"
    base = {"E": 0.5, "S": 0.5, "T": 0.5, "J": 0.5}
    if not doc:
        return base
    mb = doc.get("mbti") or doc.get("personality") or {}
    if isinstance(mb, dict):
        for k in base:
            try:
                base[k] = max(0.0, min(1.0, float(mb.get(k, base[k]))))
            except Exception:
                pass
    return base

def cosine_similarity_4d(a: Dict[str,float], b: Dict[str,float]) -> float:
    keys=["E","S","T","J"]
    dot=sum(a.get(k,0.5)*b.get(k,0.5) for k in keys)
    na=math.sqrt(sum(a.get(k,0.5)**2 for k in keys))
    nb=math.sqrt(sum(b.get(k,0.5)**2 for k in keys))
    if na==0 or nb==0: return 0.0
    return dot/(na*nb)

def weighted_avg_mbti(matches: list[tuple[Dict[str,float],float]]) -> Dict[str,float]:
    if not matches: return {"E":0.5,"S":0.5,"T":0.5,"J":0.5}
    total=sum(w for _,w in matches) or 1.0
    agg={"E":0.0,"S":0.0,"T":0.0,"J":0.0}
    for mbti,w in matches:
        for k in agg: agg[k]+=mbti.get(k,0.5)*(w/total)
    return {k:max(0.0,min(1.0,v)) for k,v in agg.items()}

def days_since(dt: Optional[str]) -> float:
    if not dt: return 9999.0
    try:
        # accept ISO format, possibly with Z
        dt_parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        # try parsing if dt is already a datetime
        if isinstance(dt, datetime):
            dt_parsed = dt
        else:
            return 9999.0
    now = datetime.now(timezone.utc)
    if dt_parsed.tzinfo is None:
        dt_parsed = dt_parsed.replace(tzinfo=timezone.utc)
    delta = now - dt_parsed
    return delta.days + delta.seconds/86400.0

def recency_score_from_days(days: float) -> float:
    return max(0.0, 1.0 - days/365.0)

# Normalize helper
def _normalize(s: Optional[str]) -> str:
    return s.lower().strip() if s and isinstance(s, str) else ""

# Convert Mongo job document to plain job dict consumed by scoring/index
def _convert_job_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    # doc could contain BSON types; convert to JSON-friendly
    job = {}
    # id: prefer explicit 'id' field, else use string of _id
    if "id" in doc and doc["id"] is not None:
        job_id = doc["id"]
    else:
        job_id = str(doc.get("_id", ""))
    # normalize job_id to string for certain uses but keep original where needed
    job["id"] = job_id
    job["title"] = doc.get("title", "") or ""
    job["apply_link"] = doc.get("apply_link", "") or ""
    job["description"] = doc.get("description", "") or ""
    # publish_date: store ISO string if possible
    pd = doc.get("publish_date") or doc.get("created_at") or doc.get("posted_at")
    if isinstance(pd, datetime):
        job["publish_date"] = pd.astimezone(timezone.utc).isoformat()
    else:
        job["publish_date"] = str(pd) if pd is not None else None
    job["locations"] = doc.get("locations") or doc.get("location") or []
    job["skills"] = doc.get("skills") or []
    job["education"] = doc.get("education") or []
    job["company"] = doc.get("company") or ""
    # optionally include raw personality/mbti fields as they might exist
    if "personality" in doc or "mbti" in doc:
        job["personality"] = doc.get("personality") or doc.get("mbti")
    # relevance may exist; ignore — we'll compute our own relevance
    return job

# ---------- Personality index ----------
async def build_personality_index():
    global _PERSONALITY_INDEX, _PERSONALITY_TITLES
    idx = []
    for job in JOBS:
        t = job.get("title")
        if t:
            idx.append((t.lower().strip(), safe_mbti_from_doc(job)))
    _PERSONALITY_INDEX = idx
    _PERSONALITY_TITLES = [t for t,_ in idx]
    _compute_job_mbti_by_title_cached.cache_clear()

@lru_cache(maxsize=4096)
def _compute_job_mbti_by_title_cached(job_title: str, max_matches: int = MAX_TITLE_MATCHES, threshold: float = FUZZY_TITLE_THRESHOLD) -> Dict[str,float]:
    if not _PERSONALITY_TITLES: return {"E":0.5,"S":0.5,"T":0.5,"J":0.5}
    raw = process.extract(job_title, _PERSONALITY_TITLES, scorer=fuzz.token_sort_ratio, limit=max_matches)
    matches = []
    for _, score, idx in raw:
        if score >= threshold:
            matches.append((_PERSONALITY_INDEX[idx][1], float(score)))
    return weighted_avg_mbti(matches)

async def _compute_job_mbti_by_title(job_title: str) -> Dict[str,float]:
    return _compute_job_mbti_by_title_cached(job_title.lower().strip())

def compute_skill_score(job_skills: List[str], user_skills: List[str]) -> float:
    if not job_skills or not user_skills: return 0.0
    matched = 0
    for js in job_skills:
        if not js: continue
        best = process.extractOne(js, user_skills, scorer=fuzz.token_sort_ratio)
        if best and best[1] >= SKILL_FUZZY_THRESHOLD:
            matched += 1
    return matched / len(job_skills)

async def _enhance_and_score_job(job: Dict[str,Any], user_mbti: Dict[str,float], user_skills: List[str]) -> Dict[str,Any]:
    async with _scoring_sema:
        job_mbti = await _compute_job_mbti_by_title(job.get("title",""))
        skill_score = compute_skill_score(job.get("skills",[]), user_skills)
        person_sim = cosine_similarity_4d(job_mbti, user_mbti)
        recency = recency_score_from_days(days_since(job.get("publish_date")))
        final = W_SKILLS*skill_score + W_PERSONALITY*person_sim + W_RECENCY*recency
        final_100 = int(round(final*100))
        return {
            "id": job.get("id"),
            "title": job.get("title",""),
            "company": job.get("company",""),
            "apply_link": job.get("apply_link",""),
            "description": job.get("description",""),
            "publish_date": job.get("publish_date"),
            "locations": job.get("locations", []),
            "skills": job.get("skills", []),
            "education": job.get("education", []),
            "relevance": final_100
        }

# ---------- Job indexing ----------
async def build_job_indexes():
    global _JOB_TITLES, _JOB_COUNT, _JOB_SKILLS_LOWER, _SKILL_INVERT
    _JOB_TITLES = []
    _JOB_SKILLS_LOWER = []
    _SKILL_INVERT = {}
    for idx,job in enumerate(JOBS):
        _JOB_TITLES.append(_normalize(job.get("title","")))
        skills_lower = [_normalize(s) for s in job.get("skills",[])]
        _JOB_SKILLS_LOWER.append(skills_lower)
        for s in skills_lower:
            if s:
                _SKILL_INVERT.setdefault(s,set()).add(idx)
    _JOB_COUNT = len(JOBS)
    _compute_job_mbti_by_title_cached.cache_clear()

def _candidate_jobs_from_user_skills(user_skills: List[str]) -> Set[int]:
    if not user_skills: return set(range(_JOB_COUNT))
    candidate=set()
    for us in user_skills:
        usn=_normalize(us)
        if usn in _SKILL_INVERT:
            candidate.update(_SKILL_INVERT[usn])
    return candidate if candidate else set(range(_JOB_COUNT))

def _candidate_jobs_from_titles(titles: List[str]) -> Set[int]:
    candidate=set()
    for t in titles:
        raw = process.extract(t, _JOB_TITLES, scorer=fuzz.token_sort_ratio, limit=MAX_TITLE_MATCHES)
        for _, score, idx in raw:
            if score >= ACTIVE_FUZZY_TITLE_THRESHOLD:
                candidate.add(idx)
    return candidate

# ---------- Mongo connection & load ----------
mongo_client: Optional[AsyncIOMotorClient] = None

async def _load_from_db():
    global mongo_client, JOBS, USERS
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    # optional: test connection by ping
    try:
        await mongo_client.admin.command("ping")
    except Exception as e:
        raise RuntimeError(f"Cannot connect to MongoDB: {e}")

    # Load jobs
    jobs_coll = mongo_client[JOBS_DB][JOBS_COLLECTION]
    users_coll = mongo_client[USERS_DB][USERS_COLLECTION]

    JOBS = []
    cursor = jobs_coll.find({})
    async for doc in cursor:
        JOBS.append(_convert_job_doc(doc))

    # Load users and build USERS mapping keyed by both 'id' and '_id' (string)
    USERS = {}
    cursor = users_coll.find({})
    async for doc in cursor:
        # Prepare canonical user dict (leave fields as-is)
        user_doc = dict(doc)
        # map by 'id' field if present
        if "id" in user_doc and user_doc["id"] is not None:
            USERS[str(user_doc["id"])] = user_doc
        # always map by string(_id)
        if "_id" in user_doc:
            USERS[str(user_doc["_id"])] = user_doc

# ---------- Startup ----------
@app.on_event("startup")
async def startup():
    await _load_from_db()
    await build_personality_index()
    await build_job_indexes()

# ---------- Endpoints ----------
@app.get("/recommend/{user_id}")
async def recommend(user_id: str, top_k: Optional[int]=None, min_relevance: Optional[int]=None):
    user = USERS.get(user_id)
    if not user:
        # try numeric id string fallback
        user = USERS.get(str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    user_mbti = safe_mbti_from_doc(user)
    user_skills = user.get("skills", []) or []

    candidates = _candidate_jobs_from_user_skills(user_skills)
    coros = [_enhance_and_score_job(JOBS[idx], user_mbti, user_skills) for idx in candidates]
    scored = await asyncio.gather(*coros)

    if min_relevance is not None:
        scored = [s for s in scored if s["relevance"] >= min_relevance]
    scored_sorted = sorted(scored, key=lambda x: x["relevance"], reverse=True)
    if top_k:
        scored_sorted = scored_sorted[:top_k]
    return {"user_id": user_id, "count": len(scored_sorted), "results": scored_sorted}


class SearchTitlesRequest(BaseModel):
    titles: List[str]
    top_k: Optional[int] = None
    min_relevance: Optional[int] = None

@app.post("/search/{user_id}")
async def search_titles(user_id: str, req: SearchTitlesRequest):
    user = USERS.get(user_id) or USERS.get(str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    user_mbti = safe_mbti_from_doc(user)
    user_skills = user.get("skills", []) or []

    candidates = _candidate_jobs_from_titles(req.titles)
    coros = [_enhance_and_score_job(JOBS[idx], user_mbti, user_skills) for idx in candidates]
    scored = await asyncio.gather(*coros)

    if req.min_relevance is not None:
        scored = [s for s in scored if s["relevance"] >= req.min_relevance]

    scored_sorted = sorted(scored, key=lambda x: x["relevance"], reverse=True)
    if req.top_k:
        scored_sorted = scored_sorted[:req.top_k]

    return {"user_id": user_id, "query_titles": req.titles, "count": len(scored_sorted), "results": scored_sorted}
