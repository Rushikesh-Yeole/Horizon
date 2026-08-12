import os
import datetime
import jwt
import contextvars
from typing import Optional

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = "HS256"

_mongo = AsyncIOMotorClient(MONGO_URI)
users_col = _mongo["users_db"]["profiles"]

current_request_cost = contextvars.ContextVar("current_request_cost", default=None)

_PRICING = {
    "google/gemini-3.5-flash-lite": (0.05, 0.20),
    "google/gemini-2.5-flash-lite-preview": (0.05, 0.20),
    "google/gemini-2.5-flash":      (0.30, 2.50),
    "google/gemini-2.5-pro":        (1.25, 10.00),
}


async def issue_token(user_id: str) -> dict:
    payload = {
        "sub": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return {"access_token": token, "user_id": user_id}


async def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


async def get_latest_pricing(redis_client):
    import json
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    key = f"horizon:pricing:{today}"
    if redis_client:
        cached = await redis_client.get(key)
        if cached:
            try:
                _PRICING.update(json.loads(cached))
                return
            except Exception as e:
                print(f"[cost] cache read failed: {e}")
                
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            resp.raise_for_status()
            data = resp.json()
            new_pricing = {}
            for model in data.get("data", []):
                m_id = model.get("id")
                pricing = model.get("pricing", {})
                prompt_price = float(pricing.get("prompt", 0)) * 1_000_000
                completion_price = float(pricing.get("completion", 0)) * 1_000_000
                new_pricing[m_id] = (prompt_price, completion_price)
            
            _PRICING.update(new_pricing)
            if redis_client:
                await redis_client.setex(key, 86400, json.dumps(new_pricing))
    except Exception as e:
        print(f"[cost] failed to fetch pricing: {e}")


def log_llm_cost(op: str, model: str, response):
    try:
        u = getattr(response, "usage", None)
        if not u:
            print(f"[cost] {op} | {model} | in=0 out=0 | ₹0.0000")
            return 0
        in_rate, out_rate = _PRICING.get(model, (0.30, 2.50))
        cost = ((u.prompt_tokens / 1_000_000) * in_rate +
                (u.completion_tokens / 1_000_000) * out_rate) * 90
        print(f"[cost] {op} | {model} | in={u.prompt_tokens} out={u.completion_tokens} | ₹{cost:.4f}")
        ctx_list = current_request_cost.get()
        if ctx_list is not None:
            ctx_list[0] += cost
        return cost
    except Exception as e:
        print(f"[cost] log failed: {e}")
        return 0