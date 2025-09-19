from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Any,Dict

from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
load_dotenv()

from frontdoor.parse_resume import parse_resume,upload_resume_to_cloud,merge_resume_with_user
from frontdoor.mbti_questionnare import prepare_questions,evaluate_answers
from frontdoor.user import insert_user_to_db,update_user_personality

from auth import hash_password, verify_password, create_access_token, decode_access_token

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
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Answers(BaseModel):
    answers: List[Dict[str,Any]]


pendingUsers : Dict[str,Dict[str,any]] = {}



@app.post("/user/register")
async def register_user(user: UserForm):
    user_id = str(ObjectId())
    pendingUsers[user_id] = user.model_dump(exclude_none=True)
    pendingUsers[user_id]["password"] = hash_password(user.password)
    pendingUsers[user_id]["personality_ready"] = False
    return JSONResponse({"user_id":user_id},status_code=200)

@app.post("/user/{user_id}/resume")
async def upload_resume(user_id:str, file: UploadFile = File(...)):
    if user_id not in pendingUsers:
         raise HTTPException(status_code=404, detail="User not found in pending registrations")
    
    user = pendingUsers[user_id]
    resume_url = await upload_resume_to_cloud(file,user_id)
    parsed_resume = parse_resume(resume_url)

    merged_user = merge_resume_with_user(user,parsed_resume,resume_url)
    pendingUsers[user_id] = merged_user

    return JSONResponse({"user_id":user_id},status_code=200)

@app.post("/user/{user_id}/confirm")
async def user_confirm(user_id: str):
    # user = get_user(user_id)
    user = pendingUsers[user_id]

    if not user.get("personality_ready"):
        raise HTTPException(status_code=400, detail="Complete MBTI questionnaire first")
    
    insert_user_to_db(user)

    del pendingUsers[user_id]

    return JSONResponse({"message":"user onboarding complete"},status_code=200)

@app.get("/user/{user_id}/questions")
async def get_questions(user_id:str):
    try:
        questions = prepare_questions()
    except Exception as e:
        return JSONResponse({"err in getting mbti questions":str(e)},status_code=500)
    return JSONResponse({"questions":questions},status_code=200)

@app.post("/user/{user_id}/answers")
async def process_answers(user_id:str, answers: Answers):
    user = pendingUsers[user_id]

    scores,pers = evaluate_answers(answers.answers)
    updated_user = update_user_personality(user,scores)
    pendingUsers[user_id] = updated_user
    return JSONResponse({"personality scores":scores},status_code=200)

@app.post("/auth/login")
async def login(payload: LoginRequest):
    user = user_collection.find_one({"email":payload.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(payload.password,user["password"]):
         raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}



