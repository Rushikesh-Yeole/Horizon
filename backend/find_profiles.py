import os
import asyncio
from dotenv import load_dotenv
import motor.motor_asyncio
import json

load_dotenv()

async def find_demo_profile():
    client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client["users_db"]
    profiles = db["profiles"]
    
    docs = await profiles.find({}).to_list(length=10)
    for doc in docs:
        doc.pop("_id", None)
        print(json.dumps(doc, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(find_demo_profile())
