import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
import redis.asyncio as aioredis
from neo4j import AsyncGraphDatabase

load_dotenv()

async def ping():
    print("Pinging Redis...")
    try:
        r = aioredis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
        await r.ping()
        print("Redis OK")
        await r.aclose()
    except Exception as e:
        print(f"Redis Failed: {e}")

    print("Pinging MongoDB...")
    try:
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=5000)
        await mongo_client.server_info()
        print("MongoDB OK")
    except Exception as e:
        print(f"MongoDB Failed: {e}")

    print("Pinging Neo4j...")
    try:
        neo = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
        await neo.verify_connectivity()
        print("Neo4j OK")
        await neo.close()
    except Exception as e:
        print(f"Neo4j Failed: {e}")

if __name__ == "__main__":
    asyncio.run(ping())
