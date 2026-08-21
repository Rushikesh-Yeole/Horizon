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

_PRICING: dict = {}


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


async def get_latest_pricing(redis_client=None):
    """Fetch live pricing from Redis or OpenRouter and maintain in-memory index."""
    import json
    key = "horizon:pricing:latest"

    if redis_client:
        try:
            cached = await redis_client.get(key)
            if cached:
                raw_dict = json.loads(cached)
                _PRICING.update({k: tuple(v) for k, v in raw_dict.items()})
                return
        except Exception as e:
            print(f"[cost] redis cache read failed: {e}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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

            # Store in Redis (24-hour TTL)
            pricing_ttl = int(os.getenv("CACHE_TTL_PRICING", "86400"))  # Default: 24 hours
            if redis_client:
                await redis_client.setex(key, pricing_ttl, json.dumps({k: list(v) for k, v in new_pricing.items()}))
    except Exception as e:
        print(f"[cost] live pricing fetch failed: {e}")


def log_llm_cost(op: str, model: str, response):
    try:
        u = getattr(response, "usage", None)
        if not u:
            print(f"[cost] {op} | {model} | in=0 out=0 | INR 0.0000")
            return 0

        rates = _PRICING.get(model)
        if rates is None:
            # Check without provider prefix or exact match
            rates = next((v for k, v in _PRICING.items() if k.endswith(model) or model.endswith(k)), None)

        if rates is None:
            print(f"[cost] {op} | {model} (unindexed model) | in={u.prompt_tokens} out={u.completion_tokens} | INR 0.0000")
            return 0

        in_rate, out_rate = rates
        cost = ((u.prompt_tokens / 1_000_000) * in_rate +
                (u.completion_tokens / 1_000_000) * out_rate) * 90
                
        ctx_list = current_request_cost.get()
        if ctx_list is not None:
            ctx_list[0] += cost
            
        print(f"[cost] {op} | {model} | in={u.prompt_tokens} out={u.completion_tokens} | INR {cost:.4f}")
        
        return cost
    except Exception as e:
        print(f"[cost] log failed: {e}")
        return 0