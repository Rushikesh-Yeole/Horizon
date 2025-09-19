from vertexai.generative_models import GenerativeModel
from google.cloud import storage

# from user import db
from pymongo import MongoClient
from bson.objectid import ObjectId

from fastapi import UploadFile

import os
from dotenv import load_dotenv
import pathlib
import re

import pymupdf
import pymupdf4llm

import requests
import json
import tempfile
from datetime import timedelta

from user import normalize_skills

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_VERTEX_LOC")
PROCESSOR_ID = os.getenv("GOOGLE_DOC_PROCESSOR_ID")
BUCKET_NAME = os.getenv("GOOGLE_BUCKET_NAME")


MAX_PROJECT_SLOTS = 3
MAX_SKILL_SLOTS = 10

client = MongoClient(os.getenv("MONGODB_URI"))
db= client["users_db"]
collection = db["users"]

def res_to_json(res_content: str):
    try:
        pattern = r"```json(.*?)```"
        matches = re.findall(pattern, res_content, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
            # fallback: assume whole response is JSON
            json_str = res_content.strip()

        return json.loads(json_str)
    except Exception as e:
        print(f"json parse error: {str(e)}")
        raise

name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

def parse_resume(file_path: str):
    local_path = None
    try:
        res = requests.get(file_path)
        res.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as temp_file:
            temp_file.write(res.content)
            local_path = temp_file.name

        document = pymupdf.open(filename=local_path)
        text = pymupdf4llm.to_markdown(document)

        model_prompt = f"""
        You are given an resume, you have to parse the below text and return in JSON format with correct entities in correct fields.
        1.name , 2.education , 3.skills ,4.projects
        RESUME TEXT: {text}
        ONLY RESPOND IN VALID JSON, DO NOT include any extra abbrivations,salutations,or extra text.
        Follow the below format:
        ```json
        {{
        
          "name":
          "education":[{{"degree":, "branch":, "college":}}],
          "skills":[...],
          "projects":[{{"title":"","desc":"..."}}]
        }}
        ```
        """

        model = GenerativeModel(model_name="gemini-2.5-pro")

        res = model.generate_content(model_prompt)
        res_content = res.text
        json_res = res_to_json(res_content)
        return json_res
    
    except Exception as e:
        print("Exception during resume parsing",str(e))
        print("Exception type: ",type(e).__name__)
        return ""
    
    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)

async def upload_resume_to_cloud(file :UploadFile,user_id:str):
    try:
        print("uploading resume to cloud storage...")
        dest_blob_name = f"{user_id}_resume.pdf"

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(dest_blob_name)

        # generation_match_precondition = 0
        blob.upload_from_file(file.file,content_type=file.content_type)

        expiration_hours = 2
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=expiration_hours))
        print(f"uploaded to cloud storage successfully {signed_url}")
        return signed_url
    except Exception as e:
        print(f"cloud storage exception: {e}")
        raise 


def merge_resume_with_user(user: dict, parsed_resume: dict, resume_url: str):
    try:
        print("merging with user data")

        
        user_data = user 
        if not user_data:
            raise ValueError("user does not exist")

        # update_data = {"resume_url": resume_url}
        user_data["resume_url"] = resume_url
        print("updated resume url")

        
        if not user_data.get("name"):
            print("updating user name")
            user_data["name"] = parsed_resume.get("name", "")

        
        skills_list = user_data.get("skills", [])
        if len(skills_list) < MAX_SKILL_SLOTS:
            print("updating skills...")
            for skill in parsed_resume.get("skills", []):
                if len(skills_list) >= MAX_SKILL_SLOTS:
                    break
                if skill not in skills_list:
                    skills_list.append(skill)
            

        skills_list = normalize_skills(skills_list)
        user_data["skills"] = skills_list
        
        projects = user_data.get("projects", [])
        if len(projects) < MAX_PROJECT_SLOTS:
            print("updating projects...")
            for project in parsed_resume.get("projects", []):
                if len(projects) >= MAX_PROJECT_SLOTS:
                    break
                if project not in projects:
                    projects.append(project)
            user_data["projects"] = projects

        print("Resume merged with user data")
        return user_data
    except Exception as e:
        print(f"exception during merging of resumes {str(e)}")
        raise
    
if __name__ == "__main__":
    pass