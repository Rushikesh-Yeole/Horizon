import json
import hashlib
import asyncio
import os
import time
import datetime
import logging
import uuid
import bcrypt
from typing import List, Optional, Dict, Any

from onboarding.mbti_questionnare import prepare_questions, evaluate_answers
from onboarding.user import (
    insert_user_to_db,
    get_onboarding_info,
    process_resume,
    get_user_by_email,
)
from onboarding.models import RegisterReq, Profile, Answers, User, LoginReq
from onboarding.parse_resume import parse_resume

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from tavily import TavilyClient
from dotenv import load_dotenv

from advisory_generator import AdvisoryGenerator
import tree
import ops

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(" Discovery ")

_raw_keys = os.getenv("TAVILY_API_KEYS") or os.getenv("TAVILY_API_KEY", "")
TAVILY_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

CACHE_TTL_SECONDS = 3600 * 24 * 7

app = FastAPI(title="Horizon Intelligence Platform", version="1.0.0 (Unified)")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

advisory_gen = AdvisoryGenerator()


async def get_redis():
    return redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authentication Scheme")

        user_id = await ops.verify_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token Invalid or Expired")

        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication Failed")


class OnboardRequest(BaseModel):
    name: str
    email: str
    skills: str  # Frontend sends comma-separated string
    experience: str  # Frontend sends raw text/summary
    role: Optional[str] = "Software Engineer"
    location: Optional[str] = "Remote"


class SearchCriteria(BaseModel):
    role: str = Field(..., example="Senior Product Manager")
    target_companies: List[str] = Field(..., example=["Uber", "Lyft"])
    location: str = Field(..., example="Bangalore")


class DiscoverRequest(BaseModel):
    user_profile: Optional[Dict[str, Any]] = None
    search_criteria: SearchCriteria


class CompanyIntel(BaseModel):
    company_name: str
    role: str
    location: str
    fetched_at: str
    source: str
    search_latency_ms: float
    results: List[Dict[str, str]]


class MarketIntelligencePacket(BaseModel):
    overall_latency_ms: float
    total_credits_estimated: int
    company_intelligence: List[CompanyIntel]
    search_criteria: Optional[Dict[str, Any]] = None


class MarketIntelligenceService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def _generate_company_key(self, role: str, company: str, location: str) -> str:
        clean_role = role.strip().lower()
        clean_comp = company.strip().lower()
        clean_loc = location.strip().lower()
        key_hash = hashlib.md5(
            f"{clean_role}|{clean_comp}|{clean_loc}".encode()
        ).hexdigest()
        return f"horizon:intel:{key_hash}"

    async def _fetch_single_company_intel(
        self, role: str, company: str, location: str
    ) -> CompanyIntel:
        start_time = time.time()
        query = (
            f"recent interview experience for {role} at {company} {location} 2024 2025 "
            f"hiring bar skills assessed coding rounds system design "
            f"compensation {location} offer details rejected accepted"
        )
        excluded_domains = [
            "indeed.com",
            "glassdoor.com",
            "simplyhired.com",
            "ziprecruiter.com",
            "naukri.com",
        ]

        results = []
        source = "Mock (No API Key)"

        if TAVILY_KEYS:
            for i, key in enumerate(TAVILY_KEYS):
                try:
                    client = TavilyClient(api_key=key)
                    tavily_response = await asyncio.to_thread(
                        client.search,
                        query=query,
                        search_depth="advanced",
                        max_results=10,
                        exclude_domains=excluded_domains,
                        topic="general",
                    )
                    results = tavily_response.get("results", [])
                    source = f"Tavily AI (Key #{i + 1})"
                    break
                except Exception as e:
                    print(f" ⚠️ API ERROR [{company}] with Key #{i + 1}: {e}")

        latency = (time.time() - start_time) * 1000
        return CompanyIntel(
            company_name=company,
            role=role,
            location=location,
            fetched_at=datetime.datetime.now().isoformat(),
            source=source,
            search_latency_ms=latency,
            results=[
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in results
            ],
        )

    async def _fetch_and_cache(self, criteria, company, cache_key) -> CompanyIntel:
        intel = await self._fetch_single_company_intel(
            criteria.role, company, criteria.location
        )
        await self.redis.setex(cache_key, CACHE_TTL_SECONDS, intel.model_dump_json())
        return intel

    async def get_market_intelligence(
        self, criteria: SearchCriteria
    ) -> MarketIntelligencePacket:
        global_start = time.time()
        tasks = []
        credits_burned = 0
        for company in criteria.target_companies:
            cache_key = self._generate_company_key(
                criteria.role, company, criteria.location
            )
            cached_blob = await self.redis.get(cache_key)
            if cached_blob:
                tasks.append(asyncio.sleep(0, result=json.loads(cached_blob)))
                logger.info(f"♻️  JD Cache Hit: {company} | {criteria.role}")
            else:
                credits_burned += 2
                tasks.append(self._fetch_and_cache(criteria, company, cache_key))

        raw_results = await asyncio.gather(*tasks)
        final_intel_list = [
            CompanyIntel(**r) if isinstance(r, dict) else r for r in raw_results
        ]
        return MarketIntelligencePacket(
            overall_latency_ms=(time.time() - global_start) * 1000,
            total_credits_estimated=credits_burned,
            company_intelligence=final_intel_list,
            search_criteria=criteria.model_dump(),
        )


# ---- USER INGESTION ----
@app.post("/auth/register")
async def register_user(user: RegisterReq):
    """Asks to ser username, password, Resume, preferred skills ,preferred jobs, preferred location"""
    try:
        user_data = get_user_by_email(user.email)
        if user_data:
            return JSONResponse({"msg": "user already exists!"}, status_code=400)

        print("INFO: registering user")
        user_id = str(uuid.uuid4())
        password_bytes = user.password.encode("utf-8")

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)

        final_user = User(
            id=user_id,
            email=user.email,
            password=hashed.decode("utf-8"),
            profile=user.profile,
            personality=user.personality,
        )
        print("INFO: insert user to db")
        insert_user_to_db(final_user)
        token_data = await ops.issue_token(user_id)

        return JSONResponse(
            {"user_id": user_id, "access_token": token_data.get("access_token")},
            status_code=200,
        )
    except Exception as e:
        print(f"ERROR: user onboarding failed {str(e)}")
        return JSONResponse({"err": "user onboarding failed"}, status_code=500)


@app.post("/auth/login")
async def login(user: LoginReq):
    try:
        userData = get_user_by_email(user.email)
        if not userData:
            raise HTTPException(status_code=404, detail="user not found")
        storedPass = userData.get("password")
        print(storedPass, user.password)
        if not storedPass==user.password:
            raise HTTPException(status_code=401, detail="Invalid Password")
        tokenData = await ops.issue_token(userData["id"])

        return JSONResponse(
            {"user_id": userData["id"], "access_token": tokenData["access_token"]},
            status_code=200,
        )
    except Exception as e:
        print(f"ERROR: login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="login failed")


@app.post("/users/me/resume")
async def handle_resume(resume: UploadFile = File(...)):
    """Parse resume and add to user's profile"""
    try:
        print("🔥 ENDPOINT HIT 🔥", flush=True)
        parsed_resume = parse_resume(file=resume)
        return JSONResponse(
            {"msg": "resume processed", "resume": parsed_resume}, status_code=200
        )
    except Exception as e:
        print(f"ERROR: resume processing failed {str(e)}")
        return JSONResponse({"err": str(e)}, status_code=500)


@app.get("/personality/questions")
async def get_personality_questions():
    "Get a set of MBTI questions"
    try:
        questions = prepare_questions()
        return JSONResponse({"questions": questions}, status_code=200)
    except Exception as e:
        return JSONResponse({"err": str(e)}, status_code=500)


@app.post("/users/me/personality")
async def process_personality(user_answers: Answers):
    "Process user given answers , calculate personality and assign it to the user"
    try:
        scores, persona = evaluate_answers(user_answers=user_answers.answers)
        return JSONResponse(
            {"msg": "onboarding complete", "scores": scores, "persona": persona},
            status_code=200,
        )
    except Exception as e:
        print(f"ERROR: processing personality failed: {str(e)}")
        return JSONResponse({"err": str(e)}, status_code=500)


# ---- DISCOVERY MODULE ----
@app.post("/discover/search")
async def initiate_discover_search(
    request: DiscoverRequest,
    redis_client=Depends(get_redis),
    user_id: str = Depends(get_current_user),
):
    if not request.user_profile:
        # Schema change: Search by "id", return the nested doc
        user_doc = await ops.users_col.find_one({"id": user_id})
        if user_doc:
            user_doc.pop("_id", None)
            request.user_profile = user_doc
        else:
            raise HTTPException(status_code=404, detail="User profile not found")

    service = MarketIntelligenceService(redis_client)
    market_packet = await service.get_market_intelligence(request.search_criteria)
    advisory_cards = await asyncio.to_thread(
        advisory_gen.generate_batch_cards,
        request.user_profile,
        market_packet.model_dump(),
    )
    return {"guidance_cards": advisory_cards}


# 3. CAREER TREE (New Integration)
@app.get("/career/tree")
async def get_user_career_tree(
    redis_client=Depends(get_redis), user_id: str = Depends(get_current_user)
):
    """
    Fetches the Cached Career Tree or Generates a new one.
    Zero arguments needed - infers everything from JWT + DB.
    """
    try:
        # 1. Fetch Profile (Needed for generation)
        # Note: We query by "id" (UUID) which is what 'user_id' from JWT maps to
        print("TOKEN USER ID:", user_id)

        user_doc = await ops.users_col.find_one({"id": user_id})

        print("DB RESULT:", user_doc)

        if not user_doc:
            raise HTTPException(status_code=404, detail="User profile not found")

        # 2. Call the Engine
        # The engine handles the Redis check, the LLM call, and the caching.
        result = await tree.engine.generate_for_user(user_id, user_doc, redis_client)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))

        return result

    except Exception as e:
        logger.error(f"Tree Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
