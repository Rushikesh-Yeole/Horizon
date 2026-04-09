import os
import datetime
import jwt
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = "HS256"

_mongo = AsyncIOMotorClient(MONGO_URI)
users_col = _mongo["users_db"]["profiles"]

_PRICING = {
    "gemini-2.5-flash-lite": (0.05, 0.20),
    "gemini-2.5-flash":      (0.30, 2.50),
    "gemini-2.5-pro":        (1.25, 10.00),
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


def log_gemini_cost(op: str, model: str, response):
    try:
        u = response.usage_metadata
        in_rate, out_rate = _PRICING.get(model, (0.30, 2.50))
        cost = ((u.prompt_token_count / 1_000_000) * in_rate +
                (u.candidates_token_count / 1_000_000) * out_rate) * 90
        print(f"[cost] {op} | {model} | in={u.prompt_token_count} out={u.candidates_token_count} | ₹{cost:.4f}")
        return cost
    except Exception as e:
        print(f"[cost] log failed: {e}")
        return 0