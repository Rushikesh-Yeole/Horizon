from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Any,Dict

from .parse_resume import parse_resume,upload_resume_to_cloud,merge_resume_with_user
from .mbti_questionnare import prepare_questions,evaluate_answers
from .user import insert_user_to_db,get_user,mark_user_onboarded,update_user_personality


app = FastAPI()

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

class Answers(BaseModel):
    answers: Dict[str,Any]


@app.post("/user/register")
async def register_user(user: UserForm):
    user_id = insert_user_to_db(user.model_dump(exclude_none=True),confirm_pending=True)
    return JSONResponse({"user_id":user_id,"message":"Form data recieved. Upload resume next"},status_code=200)

@app.post("/user/upload_resume")
async def upload_resume(user_id:str, file: UploadFile = File(...)):
    resume_url = await upload_resume_to_cloud(file,user_id)
    parsed_resume = parse_resume(resume_url)
    merged_profile = merge_resume_with_user(user_id,parsed_resume,resume_url)

    return JSONResponse({"user_id":user_id,"merged_profile":merged_profile},status_code=200)

@app.post("/user/{user_id}/confirm")
async def user_confirm(user_id: str):
    user = get_user(user_id)
    if not user.get("personality_ready"):
        raise HTTPException(status_code=400, detail="Complete MBTI questionnaire first")
    
    mark_user_onboarded(user_id)
    return JSONResponse({"message":"user onboarding complete"},status_code=200)


@app.get("/users/{user_id}/questions")
async def get_questions(user_id:str):
    try:
        questions = prepare_questions()
    except Exception as e:
        return JSONResponse({"err":str(e)},status_code=500)
    return JSONResponse({"questions":questions},status_code=200)

@app.post("users/{user_id}/submit_answers")
async def process_answers(user_id:str, answers: Answers):
    personality,user_pers = evaluate_answers(answers)
    update_user_personality(user_id,personality)
    return JSONResponse({"personality":personality},status_code=200)

