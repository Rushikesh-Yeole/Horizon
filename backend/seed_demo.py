import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def seed():
    client = MongoClient(os.getenv("MONGODB_URI"))
    collection = client["users_db"]["profiles"]

    demo_id = "00000000-0000-0000-0000-000000000000"
    demo_email = "demo@horizon.com"
    hashed_pw = bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode("utf-8")

    import random
    avatar_url = f"/static/avatars/{random.randint(1, 30)}.svg"

    demo_user = {
        "id": demo_id,
        "email": demo_email,
        "password": hashed_pw,
        "avatar_url": avatar_url,
        "profile": {
            "name": "Alex Chen",
            "role": "AI Research Engineer",
            "location": "San Francisco / Remote",
            "skills": ["Python", "PyTorch", "CUDA", "Rust", "LLM Orchestration", "LangChain", "Distributed Systems"],
            "experience": ["Built distributed vector databases, fine-tuned open-source LLMs using QLoRA for healthcare, AI Research Intern at Anthropic."],
        },
        "personality": {}
    }

    result = collection.update_one(
        {"id": demo_id},
        {"$set": demo_user},
        upsert=True
    )
    print("Demo profile seeded successfully.")

if __name__ == "__main__":
    seed()
