# aggregator.py
import os
import math
import json
import asyncio
from typing import List, Dict, Any, Optional, Set
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from rapidfuzz import process, fuzz
from datetime import datetime, timezone

# ---------- CONFIG ----------
FUZZY_TITLE_THRESHOLD = float(os.environ.get("FUZZY_TITLE_THRESHOLD", 70.0))
ACTIVE_FUZZY_TITLE_THRESHOLD = float(os.environ.get("ACTIVE_FUZZY_TITLE_THRESHOLD", 65.0))
SKILL_FUZZY_THRESHOLD = float(os.environ.get("SKILL_FUZZY_THRESHOLD", 78.0))
MAX_TITLE_MATCHES = int(os.environ.get("MAX_TITLE_MATCHES", 50))
W_SKILLS = float(os.environ.get("W_SKILLS", 0.60))
W_PERSONALITY = float(os.environ.get("W_PERSONALITY", 0.25))
W_RECENCY = float(os.environ.get("W_RECENCY", 0.15))
SCORING_CONCURRENCY = int(os.environ.get("SCORING_CONCURRENCY", 32))

# ---------- Dummy “DB” from env ----------
DUMMY_USERS = {u["id"]: u for u in json.loads(os.environ.get("DUMMY_USERS", "[]"))}
DUMMY_JOBS = json.loads(os.environ.get("DUMMY_JOBS", "[]"))

if not DUMMY_USERS or not DUMMY_JOBS:
    raise RuntimeError("Environment must provide DUMMY_USERS and DUMMY_JOBS arrays!")

app = FastAPI(title="Aggregator (Dummy Users/Jobs)")

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
    base = {"E":0.5,"S":0.5,"T":0.5,"J":0.5}
    mb = doc.get("mbti") or doc.get("personality") or {}
    if isinstance(mb, dict):
        for k in base:
            try:
                base[k] = max(0.0, min(1.0, float(mb.get(k, base[k]))))
            except:
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
    total=sum(w for _,w in matches)
    agg={"E":0.0,"S":0.0,"T":0.0,"J":0.0}
    for mbti,w in matches:
        for k in agg: agg[k]+=mbti.get(k,0.5)*(w/total)
    return {k:max(0.0,min(1.0,v)) for k,v in agg.items()}

def days_since(dt: Optional[str]) -> float:
    if not dt: return 9999.0
    try: dt=datetime.fromisoformat(dt.replace("Z","+00:00"))
    except: return 9999.0
    now=datetime.now(timezone.utc)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    delta=now-dt
    return delta.days + delta.seconds/86400.0

def recency_score_from_days(days: float) -> float:
    return max(0.0, 1.0 - days/365.0)

# ---------- Personality index ----------
async def build_personality_index():
    global _PERSONALITY_INDEX,_PERSONALITY_TITLES
    idx=[]
    for job in DUMMY_JOBS:
        t=job.get("title")
        if t: idx.append((t.lower().strip(), safe_mbti_from_doc(job)))
    _PERSONALITY_INDEX=idx
    _PERSONALITY_TITLES=[t for t,_ in idx]
    _compute_job_mbti_by_title_cached.cache_clear()

@lru_cache(maxsize=4096)
def _compute_job_mbti_by_title_cached(job_title: str, max_matches: int = MAX_TITLE_MATCHES, threshold: float = FUZZY_TITLE_THRESHOLD) -> Dict[str,float]:
    if not _PERSONALITY_TITLES: return {"E":0.5,"S":0.5,"T":0.5,"J":0.5}
    raw=process.extract(job_title, _PERSONALITY_TITLES, scorer=fuzz.token_sort_ratio, limit=max_matches)
    matches=[]
    for _,score,idx in raw:
        if score>=threshold: matches.append((_PERSONALITY_INDEX[idx][1], float(score)))
    return weighted_avg_mbti(matches)

async def _compute_job_mbti_by_title(job_title: str) -> Dict[str,float]:
    return _compute_job_mbti_by_title_cached(job_title.lower().strip())

def compute_skill_score(job_skills: List[str], user_skills: List[str]) -> float:
    if not job_skills or not user_skills: return 0.0
    matched=0
    for js in job_skills:
        best=process.extractOne(js,user_skills,scorer=fuzz.token_sort_ratio)
        if best and best[1]>=SKILL_FUZZY_THRESHOLD: matched+=1
    return matched/len(job_skills)

async def _enhance_and_score_job(job: Dict[str,Any], user_mbti: Dict[str,float], user_skills: List[str]) -> Dict[str,Any]:
    async with _scoring_sema:
        job_mbti=await _compute_job_mbti_by_title(job.get("title",""))
        skill_score=compute_skill_score(job.get("skills",[]), user_skills)
        person_sim=cosine_similarity_4d(job_mbti, user_mbti)
        recency=recency_score_from_days(days_since(job.get("publish_date")))
        final=W_SKILLS*skill_score + W_PERSONALITY*person_sim + W_RECENCY*recency
        final_100=int(round(final*100))
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
def _normalize(s: str) -> str: return s.lower().strip() if s else ""

async def build_job_indexes():
    global _JOB_TITLES, _JOB_COUNT, _JOB_SKILLS_LOWER, _SKILL_INVERT
    _JOB_TITLES=[]
    _JOB_SKILLS_LOWER=[]
    _SKILL_INVERT={}
    for idx,job in enumerate(DUMMY_JOBS):
        _JOB_TITLES.append(_normalize(job.get("title","")))
        skills_lower=[_normalize(s) for s in job.get("skills",[])]
        _JOB_SKILLS_LOWER.append(skills_lower)
        for s in skills_lower:
            if s: _SKILL_INVERT.setdefault(s,set()).add(idx)
    _JOB_COUNT=len(DUMMY_JOBS)
    _compute_job_mbti_by_title_cached.cache_clear()

def _candidate_jobs_from_user_skills(user_skills: List[str]) -> Set[int]:
    if not user_skills: return set(range(_JOB_COUNT))
    candidate=set()
    for us in user_skills:
        usn=_normalize(us)
        if usn in _SKILL_INVERT: candidate.update(_SKILL_INVERT[usn])
    return candidate if candidate else set(range(_JOB_COUNT))

def _candidate_jobs_from_titles(titles: List[str]) -> Set[int]:
    candidate=set()
    for t in titles:
        raw=process.extract(t, _JOB_TITLES, scorer=fuzz.token_sort_ratio, limit=MAX_TITLE_MATCHES)
        for _,score,idx in raw:
            if score>=ACTIVE_FUZZY_TITLE_THRESHOLD: candidate.add(idx)
    return candidate

# ---------- Startup ----------
@app.on_event("startup")
async def startup():
    await build_personality_index()
    await build_job_indexes()

# ---------- Endpoints ----------
@app.get("/recommend/{user_id}")
async def recommend(user_id: str, top_k: Optional[int]=None, min_relevance: Optional[int]=None):
    user=DUMMY_USERS.get(user_id)
    if not user: raise HTTPException(404,"user not found")
    user_mbti=safe_mbti_from_doc(user)
    user_skills=user.get("skills",[])

    candidates=_candidate_jobs_from_user_skills(user_skills)
    coros=[_enhance_and_score_job(DUMMY_JOBS[idx], user_mbti, user_skills) for idx in candidates]
    scored=await asyncio.gather(*coros)

    if min_relevance is not None: scored=[s for s in scored if s["relevance"]>=min_relevance]
    scored_sorted=sorted(scored, key=lambda x:x["relevance"], reverse=True)
    if top_k: scored_sorted=scored_sorted[:top_k]
    return {"user_id": user_id, "count": len(scored_sorted), "results": scored_sorted}


class SearchTitlesRequest(BaseModel):
    titles: List[str]
    top_k: Optional[int] = None
    min_relevance: Optional[int] = None

@app.post("/search/{user_id}")
async def search_titles(user_id: str, req: SearchTitlesRequest):
    user = DUMMY_USERS.get(user_id)
    if not user:
        raise HTTPException(404, "user not found")

    user_mbti = safe_mbti_from_doc(user)
    user_skills = user.get("skills", [])

    candidates = _candidate_jobs_from_titles(req.titles)
    scored = await asyncio.gather(*[_enhance_and_score_job(DUMMY_JOBS[idx], user_mbti, user_skills) for idx in candidates])

    if req.min_relevance is not None:
        scored = [s for s in scored if s["relevance"] >= req.min_relevance]

    scored_sorted = sorted(scored, key=lambda x: x["relevance"], reverse=True)
    if req.top_k:
        scored_sorted = scored_sorted[:req.top_k]

    return {"user_id": user_id, "query_titles": req.titles, "count": len(scored_sorted), "results": scored_sorted}