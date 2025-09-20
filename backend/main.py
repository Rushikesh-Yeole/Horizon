from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Any,Dict,Optional

from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
load_dotenv()

from frontdoor.parse_resume import parse_resume,upload_resume_to_cloud,get_resume_url
from frontdoor.mbti_questionnare import prepare_questions,evaluate_answers
from frontdoor.user import insert_user_to_db

from normalizer.normalizer import normalize_skills

from auth import hash_password, verify_password, create_access_token

app = FastAPI()

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



