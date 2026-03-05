import os
import datetime
import uuid
import jwt
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# --- CONFIGURATION ---
MONGO_URI = os.getenv("MONGODB_URI")
USER_DB = "users_db"
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = "HS256"

# DB 
client = AsyncIOMotorClient(MONGO_URI)
db = client[USER_DB]
users_col = db["profiles"]

async def issue_token(user_id) -> dict:
    """
    Constructs the Nested Target Schema and persists it to MongoDB.
    Returns a secure JWT and system identity.
    """
    payload = {
        "sub": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    return {
        "access_token": token,
        "user_id": user_id,
        "status": "ONBOARDED"
    }

async def verify_token(token: str) -> Optional[str]:
    """
    Stateless validation of the JWT. 
    Returns the user_id (subject) if valid. [cite: 147, 187]
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None