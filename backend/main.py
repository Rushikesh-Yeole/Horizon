from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Any,Dict,Optional

import asyncio
import datetime
import json
import tempfile
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
# Set Google credentials for local dev or relative path deploys
google_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Parse it to make sure it’s valid JSON
try:
    creds_dict = json.loads(google_creds_json)
except json.JSONDecodeError:
    raise Exception("GOOGLE_APPLICATION_CREDENTIALS env var is not valid JSON!")

# Write the JSON to a temporary file
with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
    json.dump(creds_dict, f)
    temp_path = f.name

# Set the env var to point to this temporary file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path

from frontdoor.parse_resume import parse_resume,upload_resume_to_cloud,get_resume_url
from frontdoor.mbti_questionnare import prepare_questions,evaluate_answers
from frontdoor.user import insert_user_to_db
from careertree.tree import users_collection,generate_for_user, generate_one, ctrees_collection,ctree_failures,logger

from normalizer.normalizer import normalize_skills

from auth import hash_password, verify_password, create_access_token

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # list of allowed origins
    allow_credentials=True,      # allow cookies, auth headers
    allow_methods=["*"],         # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],         # allow all headers
)

client = MongoClient(os.getenv("MONGODB_URI"))
user_db = client["user_db"]
user_collection = user_db["users"]

class Education(BaseModel):
    degree: str
    branch: str
    college: str

class Project(BaseModel):
    title: str
    desc: str

class UserForm(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    preferences: dict   # {"location": "...", "role": "..."}
    education: List[Education]
    skills: List[str]
    projects: List[Project]
    personality: Dict[str,float] #calculated by backend, cant be modified
    bucket: Optional[str]=None #not visible
    destination_blob: Optional[str]=None #not visible 
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Answers(BaseModel):
    answers: List[Dict[str,Any]]


# ---- USER INGESTION ----
@app.post("/user/register")
async def register_user(user: UserForm):
    user_data = user.model_dump(exclude_none=True)
    user_data["password"] = hash_password(user.password)
    
    user_skills = user_data.get("skills",[])
    if user_skills != []:
        cleaned_skills = normalize_skills(user_skills)
        user_data["skills"] = cleaned_skills
    
    if(user_data["personality"]=={}):
        return JSONResponse({"message":"user must complete MBTI questionnare first"},status_code=400)
    
    user_id = insert_user_to_db(user_data)

    return JSONResponse({"user_id":user_id},status_code=200)

@app.post("/user/resume")
async def upload_resume(file: UploadFile = File(...)):
    """stores the resume in GCS, parses it and returns 
    bucket name
    destination blob
    parsed resume dict
    """
    bucket_name,dest_blob_name = await upload_resume_to_cloud(file)
    resume_url = get_resume_url(bucket_name,dest_blob_name)
    parsed_resume = parse_resume(resume_url)

    return JSONResponse({"bucket":bucket_name,"dest_blob":dest_blob_name,"parsed_resume":parsed_resume},status_code=200)

@app.get("/user/questions")
async def get_questions():
    try:
        questions = prepare_questions()
    except Exception as e:
        return JSONResponse({"err in getting mbti questions":str(e)},status_code=500)
    return JSONResponse({"questions":questions},status_code=200)

@app.post("/user/answers")
async def process_answers(answers: Answers):
    try:
        scores,pers = evaluate_answers(answers.answers)
        return JSONResponse({"personality scores":scores},status_code=200)
    except Exception as e:
        return JSONResponse({"err":f"{str(e)}"},status_code=400)

@app.post("/auth/login")
async def login(payload: LoginRequest):
    user = user_collection.find_one({"email":payload.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(payload.password,user["password"]):
         raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}


# ---- CAREER TREE ----
@app.post("/careertree/generate/{name}")
async def genTree(name: str):
    return await generate_one(name)

@app.get("/careertree/health")
def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat() + "Z"}

# @app.on_event("startup")
# async def startup_tasks():
#     try:
#         await users_collection.create_index("id", unique=True)
#         await ctrees_collection.create_index("id", unique=False)
#         await ctree_failures.create_index("id", unique=False)
#         logger.info("Ensured index on users.id, ctrees.id and ctree_failures.id")
#     except Exception as e:
#         logger.warning("Index creation failed or already exists: %s", e)
