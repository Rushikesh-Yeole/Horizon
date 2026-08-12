import json
import hashlib
import asyncio
import os
import time
import datetime
import logging
import uuid
import bcrypt
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import random
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

from onboarding.mbti_questionnare import prepare_questions, evaluate_answers
from onboarding.user import insert_user_to_db, get_user_by_email
from onboarding.models import RegisterReq, Answers, User, LoginReq
from onboarding.resume import resume_router

import ops
import neo_graph as graph
from discover import generate_cards
from tree import generate_tree

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
log = logging.getLogger("main")

TAVILY_KEYS = [k.strip() for k in (os.getenv("TAVILY_API_KEYS") or os.getenv("TAVILY_API_KEY", "")).split(",") if k.strip()]
INTEL_CACHE_TTL = 7 * 60

_redis: aioredis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis
    log.info("Starting up...")
    _redis = aioredis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)
    await graph.setup()
    yield
    await graph.close()
    await _redis.aclose()
    log.info("Shutdown complete.")


app = FastAPI(title="Horizon Intelligence Platform", version="2.0.0", lifespan=lifespan)

prod_origin = os.getenv("PROD_FRONTEND_URL")
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if prod_origin:
    origins.append(prod_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-credits-remaining", "x-cost-this-run"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_redis() -> aioredis.Redis:
    return _redis


@app.middleware("http")
async def metering_middleware(request: Request, call_next):
    ops.current_request_cost.set([0.0])
    session_id = request.headers.get("x-demo-session-id")
    if not session_id:
        return await call_next(request)
        
    rc = get_redis()
    if not rc:
        return await call_next(request)
        
    key = f"horizon:metering:{session_id}"
    balance_str = await rc.get(key)
    if balance_str is None:
        await rc.set(key, 100.0)
        balance = 100.0
    else:
        balance = float(balance_str)
        
    if balance <= 0.0:
        return JSONResponse({"detail": "Payment Required"}, status_code=402)
        
    response = await call_next(request)
    
    cost_in_inr = ops.current_request_cost.get()[0]
    # 1 credit = roughly 0.01 INR? Wait, what ratio? 
    # If cost is 0.03 INR, and ratio is 100, then credits_used = 3.0 credits.
    # The previous code used CREDIT_USD_RATIO which is misleading if cost is in INR.
    # Let's fix the env variable name to CREDIT_MULTIPLIER as the user previously used.
    # Let's check what it was in demo_metering_middleware: os.getenv("CREDIT_MULTIPLIER", "1.0")
    # We will stick to CREDIT_MULTIPLIER.
    multiplier = float(os.getenv("CREDIT_MULTIPLIER", "1.0"))
    credits_used = cost_in_inr * multiplier
    
    new_balance = await rc.incrbyfloat(key, -credits_used)
    
    response.headers["x-credits-remaining"] = str(round(new_balance, 2))
    response.headers["x-cost-this-run"] = str(round(credits_used, 2))
    
    return response


async def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization:
        raise HTTPException(401, "Missing auth token.")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Invalid scheme.")
        user_id = await ops.verify_token(token)
        if not user_id:
            raise HTTPException(401, "Token invalid or expired.")
        return user_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Auth failed.")

app.include_router(resume_router, prefix="/auth")

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/auth/register")
async def register(user: RegisterReq):
    try:
        if get_user_by_email(user.email):
            return JSONResponse({"msg": "User already exists."}, status_code=400)
        user_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        avatar_idx = random.randint(1, 30)
        final_user = User(
            id=user_id, 
            email=user.email, 
            password=hashed, 
            avatar_url=f"/static/avatars/{avatar_idx}.svg",
            profile=user.profile, 
            personality=user.personality
        )
        insert_user_to_db(final_user)
        token_data = await ops.issue_token(user_id)
        return JSONResponse({"user_id": user_id, "access_token": token_data["access_token"]})
    except Exception as e:
        log.error(f"Register failed: {e}")
        return JSONResponse({"err": "Registration failed."}, status_code=500)


@app.post("/auth/login")
async def login(user: LoginReq):
    try:
        user_data = get_user_by_email(user.email)
        if not user_data:
            raise HTTPException(404, "User not found.")
        token_data = await ops.issue_token(user_data["id"])
        return JSONResponse({"user_id": user_data["id"], "access_token": token_data["access_token"], "email": user_data["email"]})
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Login failed: {e}")
        raise HTTPException(500, "Login failed.")


# ── Onboarding ────────────────────────────────────────────────────────────────

@app.get("/users/me")
async def get_me(user_id: str = Depends(get_current_user)):
    try:
        user_doc = await ops.users_col.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(404, "User not found.")
        user_doc.pop("_id", None)
        user_doc.pop("password", None)
        return JSONResponse({"user": user_doc})
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get user: {e}")
        raise HTTPException(500, "Internal server error.")

from onboarding.models import Profile

@app.put("/users/me/profile")
async def update_profile(profile: Profile, user_id: str = Depends(get_current_user)):
    try:
        res = await ops.users_col.update_one(
            {"id": user_id},
            {"$set": {"profile": profile.model_dump()}}
        )
        if res.matched_count == 0:
            raise HTTPException(404, "User not found.")
        return JSONResponse({"msg": "Profile updated successfully."})
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to update profile: {e}")
        raise HTTPException(500, "Internal server error.")


@app.get("/personality/questions")
async def get_personality_questions():
    try:
        return JSONResponse({"questions": prepare_questions()})
    except Exception as e:
        return JSONResponse({"err": str(e)}, status_code=500)


@app.post("/users/me/personality")
async def process_personality(user_answers: Answers):
    try:
        scores, persona = evaluate_answers(user_answers=user_answers.answers)
        return JSONResponse({"msg": "Done.", "scores": scores, "persona": persona})
    except Exception as e:
        log.error(f"Personality failed: {e}")
        return JSONResponse({"err": str(e)}, status_code=500)


# ── Market Intel ──────────────────────────────────────────────────────────────

class SearchCriteria(BaseModel):
    role: str = Field(..., example="Senior Backend Engineer")
    target_companies: List[str] = Field(..., example=["Stripe", "Razorpay"])
    location: str = Field(..., example="Bangalore")


class CompanyIntel(BaseModel):
    company_name: str
    role: str
    location: str
    fetched_at: str
    source: str
    search_latency_ms: float
    results: List[Dict[str, str]]


class MarketPacket(BaseModel):
    overall_latency_ms: float
    total_credits_estimated: int
    company_intelligence: List[CompanyIntel]
    search_criteria: Optional[Dict[str, Any]] = None


def _intel_cache_key(role: str, company: str, location: str) -> str:
    h = hashlib.md5(f"{role.lower()}|{company.lower()}|{location.lower()}".encode()).hexdigest()
    return f"horizon:intel:{h}"


async def _fetch_company_intel(role: str, company: str, location: str) -> CompanyIntel:
    start = time.time()
    query = (
        f"recent interview experience {role} at {company} {location} 2024 2025 "
        "hiring bar coding system design skills assessed"
    )
    excluded = ["indeed.com", "glassdoor.com", "simplyhired.com", "ziprecruiter.com", "naukri.com"]
    results, source = [], "No API key"

    for i, key in enumerate(TAVILY_KEYS):
        try:
            client = TavilyClient(api_key=key)
            res = await asyncio.to_thread(
                client.search, query=query, search_depth="advanced",
                max_results=10, exclude_domains=excluded, topic="general",
            )
            results = res.get("results", [])
            source = f"Tavily (key #{i+1})"
            break
        except Exception as e:
            log.warning(f"Tavily key #{i+1} failed [{company}]: {e}")

    return CompanyIntel(
        company_name=company, role=role, location=location,
        fetched_at=datetime.datetime.now().isoformat(),
        source=source,
        search_latency_ms=(time.time() - start) * 1000,
        results=[{"title": r["title"], "url": r["url"], "content": r["content"]} for r in results],
    )


async def _get_market_intel(criteria: SearchCriteria, rc: aioredis.Redis) -> MarketPacket:
    start = time.time()
    credits = 0
    tasks = []

    for company in criteria.target_companies:
        key = _intel_cache_key(criteria.role, company, criteria.location)
        cached = await rc.get(key)
        if cached:
            log.info(f"Intel cache hit: {company}")
            tasks.append(asyncio.sleep(0, result=CompanyIntel(**json.loads(cached))))
        else:
            credits += 2
            async def _fetch_and_cache(c=company, k=key):
                intel = await _fetch_company_intel(criteria.role, c, criteria.location)
                await rc.setex(k, INTEL_CACHE_TTL, intel.model_dump_json())
                return intel
            tasks.append(_fetch_and_cache())

    intel_list = await asyncio.gather(*tasks)
    return MarketPacket(
        overall_latency_ms=(time.time() - start) * 1000,
        total_credits_estimated=credits,
        company_intelligence=list(intel_list),
        search_criteria=criteria.model_dump(),
    )


# Discover

class DiscoverRequest(BaseModel):
    search_criteria: SearchCriteria


@app.post("/discover/search")
async def discover_search(
    request: DiscoverRequest, 
    rc: aioredis.Redis = Depends(get_redis),
    user_id: str = Depends(get_current_user)
):
    user_doc = await ops.users_col.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(404, "User not found.")
    user_doc.pop("_id", None)
    
    market = await _get_market_intel(request.search_criteria, rc)
    cards = await generate_cards(rc, user_doc, market.model_dump())
    return {"guidance_cards": cards}


# Career Tree

@app.get("/career/tree")
async def get_career_tree(
    rc: aioredis.Redis = Depends(get_redis),
    user_id: str = "9f3c7a21-6d44-4a9f-8f1e-2b6c9d3e7a55",
):
    user_doc = await ops.users_col.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(404, "User not found.")
    user_doc.pop("_id", None)

    result = await generate_tree(user_id, user_doc, rc)
    if result.get("status") == "error":
        raise HTTPException(500, result.get("message"))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)