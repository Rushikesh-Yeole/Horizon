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
from onboarding.models import RegisterReq, Answers, User, LoginReq, SendOtpReq
from onboarding.resume import resume_router

import ops
import neo_graph as graph
import mailer
from scoring import profile_hash as _profile_hash
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
    try:
        await ops.get_latest_pricing(_redis)
    except Exception as e:
        log.warning(f"Failed to fetch initial OpenRouter pricing: {e}")
    await graph.setup()
    yield
    await graph.close()
    await _redis.aclose()
    log.info("Shutdown complete.")


app = FastAPI(title="Horizon Intelligence Platform", version="2.0.0", lifespan=lifespan)

prod_origin = os.getenv("PROD_FRONTEND_URL")
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://horizon-six-beryl.vercel.app"
]
if prod_origin:
    origins.append(prod_origin.rstrip("/"))

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

@app.post("/auth/send-otp")
async def send_otp_endpoint(req: SendOtpReq, rc: aioredis.Redis = Depends(get_redis)):
    try:
        if get_user_by_email(req.email):
            return JSONResponse({"msg": "User already exists."}, status_code=400)
        
        # Generate 6 digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Store in Redis, expire in 5 minutes
        if rc:
            await rc.setex(f"otp:{req.email}", 300, otp_code)
        
        # Send via email
        asyncio.create_task(mailer.send_otp(req.email, otp_code))
        
        return JSONResponse({"msg": "OTP sent successfully."})
    except Exception as e:
        log.error(f"Send OTP failed: {e}")
        return JSONResponse({"err": "Failed to send OTP."}, status_code=500)


@app.post("/auth/register")
async def register(user: RegisterReq, rc: aioredis.Redis = Depends(get_redis)):
    try:
        if get_user_by_email(user.email):
            return JSONResponse({"msg": "User already exists."}, status_code=400)
            
        # Verify OTP
        if not rc:
            return JSONResponse({"msg": "Redis unavailable for OTP check."}, status_code=500)
            
        stored_otp = await rc.get(f"otp:{user.email}")
        if not stored_otp or stored_otp != user.otp:
            return JSONResponse({"msg": "Invalid or expired OTP."}, status_code=400)
            
        # OTP is valid, remove it
        await rc.delete(f"otp:{user.email}")
        
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
        name = (user.profile.name if user.profile and hasattr(user.profile, 'name') and user.profile.name else user.email)
        asyncio.create_task(mailer.send_welcome(user.email, name))
        return JSONResponse({"user_id": user_id, "access_token": token_data["access_token"]})
    except Exception as e:
        log.error(f"Register failed: {e}")
        return JSONResponse({"err": "Registration failed."}, status_code=500)


@app.post("/auth/login")
async def login(user: LoginReq):
    try:
        user_data = await ops.users_col.find_one({"email": user.email})
        if not user_data or not bcrypt.checkpw(user.password.encode(), user_data["password"].encode()):
            raise HTTPException(401, "Invalid credentials.")
        token_data = await ops.issue_token(user_data["id"])
        if user_data["email"] != "demo@horizon.com":
            asyncio.create_task(mailer.send_login_alert(user_data["email"]))
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


@app.delete("/users/me")
async def delete_account(
    rc: aioredis.Redis = Depends(get_redis),
    user_id: str = Depends(get_current_user),
):
    """Permanently delete user account and flush all their cache keys."""
    result = await ops.users_col.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found.")
    # Flush all Redis keys scoped to this user
    if rc:
        cursor = 0
        while True:
            cursor, keys = await rc.scan(cursor, match=f"horizon:*:{user_id}:*", count=100)
            if keys:
                await rc.delete(*keys)
            if cursor == 0:
                break
    log.info(f"Account deleted: {user_id}")
    return JSONResponse({"msg": "Account deleted."})


from onboarding.resume import _validate_upload

@app.post("/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """Authenticated resume upload with PDF type + 5MB size enforcement."""
    await _validate_upload(file)
    return JSONResponse({"msg": "Upload accepted.", "filename": file.filename})


from onboarding.models import Profile

@app.put("/users/me/profile")
async def update_profile(profile: Profile, user_id: str = Depends(get_current_user)):
    try:
        profile_data = profile.model_dump()
        res = await ops.users_col.update_one(
            {"id": user_id},
            {"$set": {"profile": profile_data, "profile_hash": _profile_hash(profile_data)}}
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


@app.post("/personality/evaluate")
async def evaluate_personality_endpoint(user_answers: Answers):
    try:
        scores, persona = evaluate_answers(user_answers=user_answers.answers)
        return JSONResponse({"msg": "Done.", "scores": scores, "persona": persona})
    except Exception as e:
        log.error(f"Personality evaluation failed: {e}")
        return JSONResponse({"err": str(e)}, status_code=500)


@app.post("/users/me/personality")
async def process_personality(user_answers: Answers, user_id: str = Depends(get_current_user)):
    try:
        scores, persona = evaluate_answers(user_answers=user_answers.answers)
        # Persist as optional self-reported preference — never used for scoring
        await ops.users_col.update_one(
            {"id": user_id},
            {"$set": {"personality_preferences": {"scores": scores, "persona": persona}}}
        )
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
    import re
    def clean(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return f"horizon:intel:{clean(company)}:{clean(role)}:{clean(location)}"


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
    user_id: str = Depends(get_current_user),
    force_refresh: bool = False,
):
    import time
    start_time = time.time()
    
    user_doc = await ops.users_col.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(404, "User not found.")
    user_doc.pop("_id", None)
    
    cards = await generate_cards(rc, user_doc, request.search_criteria.model_dump(), force_refresh=force_refresh)
    
    from scoring import profile_hash as _ph
    run_id = _ph({"user": user_id, "criteria": request.search_criteria.model_dump()})
    latency_ms = (time.time() - start_time) * 1000
    log.info(f"[/discover/search] Completed in {latency_ms:.2f}ms run_id={run_id}")
    
    return {"guidance_cards": cards, "latency_ms": latency_ms, "run_id": run_id}


# Career Tree

@app.get("/career/tree")
async def get_career_tree(
    rc: aioredis.Redis = Depends(get_redis),
    user_id: str = Depends(get_current_user),
):
    import time
    start_time = time.time()
    
    user_doc = await ops.users_col.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(404, "User not found.")
    user_doc.pop("_id", None)

    result = await generate_tree(user_id, user_doc, rc)
    if result.get("status") == "error":
        raise HTTPException(500, result.get("message"))
        
    latency_ms = (time.time() - start_time) * 1000
    result["latency_ms"] = latency_ms
    log.info(f"[/career/tree] Completed in {latency_ms:.2f}ms")
    
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)