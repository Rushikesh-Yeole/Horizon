from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import UploadFile

from .models import User,Profile,Personality,RegisterReq
from .parse_resume import parse_resume,merge_resume_with_user
from .mbti_questionnare import evaluate_answers
from .normalizer.normalizer import normalize_skills

from uuid import uuid4
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["users_db"]  
collection = db["profiles"]  

def can_complete_onboarding(user: User) -> bool:
    profile = user.get("profile", {})
    resume = user.get("resume", {})
    personality = user.get("personality", {})

    profile_ok = bool(profile.get("name"))
    resume_ok = resume.get("uploaded", False)
    personality_ok = personality.get("completed", False)

    data_requirement = profile_ok or resume_ok

    return data_requirement and personality_ok

def insert_user_to_db(request: User):
    try:
        skills = request.profile.skills
        norm_skills = normalize_skills(skills=skills)
        request.profile.skills = norm_skills
        final_user = request.model_dump()
        collection.insert_one(final_user)
        print(f"INFO: user successfully inserted {id}")
        return str(id)
    except Exception as e:
        print(f"ERROR: mongodb error while inserting user {e}")
        raise 

def get_onboarding_info(user_id:str):
    try:
        doc = collection.find_one({"id":user_id})
        
        if not doc:
            return {'err':'invalid user id'}
        
        profile = doc.get('profile')
        profile = Profile(**profile)

        resume = doc.get('resume')

        personality = doc.get('personality')
        personality = Personality(**personality)

        status = doc.get('status')
        missing  = []
        if not profile.name:
            missing.append('profile')
        if not resume.uploaded:
            missing.append('resume')
        if not personality.completed:
            missing.append('personality')


        return {'status':status,'missing':missing}
    except Exception as e:
        print(str(e))
        return {}

def get_user_by_email(email:str):
    """gets user with a given email"""
    try:
        user = collection.find_one({"email": email})
        if not user:
            return None
        return user
    except Exception as e:
        print("ERROR: getting user failed")
        raise

def get_user_by_id(user_id: str):
    
    try:
        doc = collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            raise ValueError("user does not exist")
        print(f"user successfully extracted {user_id}")
        return doc
    except Exception as e:
        print(f"mongodb error while fetching user {e}")
        raise 

def update_user_profile(user_id:str, profile: Profile):
    """Update profile with new data"""
    try:
        res = collection.update_one(
            {"id":user_id},
            {
                "$set":{
                    "profile": profile.model_dump(exclude_none=True),
                    "status":"PROFILE_COMPLETED"
                }
            }
        )
    except Exception as e:
        print(f"ERROR: during updating profiles: {str(e)}")
        raise

def process_resume(resume: UploadFile):
    """Process user sent resume"""
    try:
        parsed_resume = parse_resume(resume)
        print("INFO: resume processed successfully")
        return parsed_resume
    except Exception as e:
        print(f"ERR:in processing resume {str(e)}")
        raise

        

    

if __name__=="__main__":
    extracted_skills = [
    "pyhton",             # typo
    "C++", 
    "React JS", 
    "Tensor flow",        # alias / spacing
    "ML",                 # short form
    "Natural Lang Processing", 
    "SQL Database", 
    "Excel", 
    "communication skills", 
    "Leadership", 
    "Problem solving", 
    "Docker containerization", 
    "AWS Cloud", 
    "Azure Devops", 
    "git hub",            # messy form
    "pandas library", 
    "statistics", 
    "Linear Regression", 
    "deep learning", 
    "Public speaking"
]
    print(f"no. of extracted skills {len(extracted_skills)}")
    # normalize_skills(extracted_skills=extracted_skills)