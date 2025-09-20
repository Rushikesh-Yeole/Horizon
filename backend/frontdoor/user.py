from pymongo import MongoClient
from bson.objectid import ObjectId



from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["users_db"]  
collection = db["profiles"]  



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


def update_user_personality(user: dict, personality: dict):
    
    try:
        user_data = user
        user_data["personality"] = personality
        print(f"user personality successfully updated")
        return user_data
    
    except Exception as e:
        print(f"mongodb error while updating user personality {e}")
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