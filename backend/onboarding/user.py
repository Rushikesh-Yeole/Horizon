import os

from pymongo import MongoClient
from dotenv import load_dotenv

from .models import User
from .normalizer.normalizer import normalize_skills

load_dotenv()

collection = MongoClient(os.getenv("MONGODB_URI"))["users_db"]["profiles"]


def insert_user_to_db(user: User):
    skills = user.profile.skills or []
    if skills:
        user.profile.skills = normalize_skills(skills)
    result = collection.insert_one(user.model_dump())
    return str(result.inserted_id)


def get_user_by_email(email: str):
    try:
        return collection.find_one({"email": email})
    except Exception as e:
        print(f"ERROR: get_user_by_email: {e}")
        raise