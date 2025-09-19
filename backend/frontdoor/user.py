from pymongo import MongoClient
from bson.objectid import ObjectId

from rapidfuzz import process,fuzz

from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["users_db"]  
collection = db["profiles"]  


kb = client["kb"]
skills_collection = kb["skills"]

normalized_skills = [doc["name"] for doc in skills_collection.find({}, {"name": 1, "_id": 0})]

normalized_aliases = {
    doc["name"]: doc.get("aliases", [])
    for doc in skills_collection.find({}, {"name": 1, "aliases": 1, "_id": 0})
}

normalized_rel_skills = {
    doc["name"]: doc.get("related_skills", [])
    for doc in skills_collection.find({}, {"name": 1, "related_skills": 1, "_id": 0})
}


def insert_user_to_db(user_data: dict):
    try:

        result = collection.insert_one(user_data)
        print(f"user successfully inserted {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"mongodb error while inserting user {e}")
        raise 

def get_user(user_id: str):
    
    try:
        doc = collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            raise ValueError("user does not exist")
        print(f"user successfully extracted {user_id}")
        return doc
    except Exception as e:
        print(f"mongodb error while fetching user {e}")
        raise 

# def mark_user_onboarded(user_id: str):
    
#     try:
#         result = collection.update_one(
#             {"_id": ObjectId(user_id)},
#             {"$set": {"confirm_pending": False}}
#         )
#         if result.matched_count == 0:
#             raise ValueError("user does not exist")
#         print(f"user successfully updated {user_id}")
#     except Exception as e:
#         print(f"mongodb error while onboarding user {e}")
#         raise 

def update_user_personality(user: dict, personality: dict):
    
    try:
        user_data = user
        user_data["personality"] = personality
        print(f"user personality successfully updated")
        return user_data
    
    except Exception as e:
        print(f"mongodb error while updating user personality {e}")
        raise 

def normalize_skills(extracted_skills,threshold=60):
   
    
    cleaned_skills = []
    for skill in extracted_skills:
        print(f"current skill : {skill}")
        match, score, _ = process.extractOne(skill, normalized_skills, scorer=fuzz.ratio)
        if score >= threshold:
            print(f"found! match: {match}, score: {score}")
            cleaned_skills.append(match)
            continue  

        print("checking in aliases")
        found = False
        for n_skill, aliases in normalized_aliases.items():
            if not aliases:
                continue
            match, score, _ = process.extractOne(skill, aliases, scorer=fuzz.ratio)
            if score >= threshold:
                print(f"found! match: {match}, score: {score}")
                cleaned_skills.append(n_skill)  
                found = True
                break
        if found:
            continue  

        print("checking in related skills")
        for n_skill, related in normalized_rel_skills.items():
            if not related:
                continue
            match, score, _ = process.extractOne(skill, related, scorer=fuzz.ratio)
            if score >= threshold:
                print(f"found! match: {match}, score: {score}")
                cleaned_skills.append(n_skill)  
                found=True
                break  
        if not found:
            print(f"skill: {skill} not found in KB")

    print(len(cleaned_skills))
    return cleaned_skills
    

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
    normalize_skills(extracted_skills=extracted_skills)