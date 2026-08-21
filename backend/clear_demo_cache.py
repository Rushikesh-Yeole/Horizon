import asyncio
import os
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

async def main():
    rc = aioredis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)
    
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client["users_db"]
    demo_user = await db["profiles"].find_one({"email": "demo@horizon.com"})
    
    if demo_user:
        user_id = demo_user["id"]
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await rc.scan(cursor, match=f"*", count=5000)
            target_keys = [k for k in keys if user_id in k]
            if target_keys:
                await rc.delete(*target_keys)
                deleted += len(target_keys)
                
            if cursor == 0:
                break
        print(f"Cleared {deleted} cache keys for demo user {user_id}")
    await rc.aclose()

if __name__ == "__main__":
    asyncio.run(main())
