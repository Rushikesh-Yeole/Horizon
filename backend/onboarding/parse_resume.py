
import google.generativeai as genai


# from user import db
from pymongo import MongoClient

from fastapi import UploadFile,File

import os
from dotenv import load_dotenv
import pathlib
import re

import pymupdf
import pymupdf4llm

import requests
import json
import tempfile
import datetime
import pprint
import traceback

import uuid

from .normalizer.normalizer import normalize_skills

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.5-flash")

MAX_PROJECT_SLOTS = 3
MAX_SKILL_SLOTS = 10

client = MongoClient(os.getenv("MONGODB_URI"))
db= client["users_db"]
collection = db["profiles"]

def res_to_json(res_content: str):
    try:
        pattern = r"```json(.*?)```"
        matches = re.findall(pattern, res_content, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
            # fallback: assume whole response is JSON
            json_str = res_content.strip()

        json_content = json.loads(json_str)
        
        return json_content
    except Exception as e:
        print(f"json parse error: {str(e)}")
        raise

# name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

def parse_resume(file: UploadFile=File(...)):
    local_path = None
    try:
        print("INFO: Parsing Resume...")
        with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as temp_file:
            temp_file.write(file.file.read())
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

        res = model.generate_content(model_prompt)
        res_content = res.text
        json_res = res_to_json(res_content)
        pprint.pprint(json_res,indent=4)
        print("INFO: Resume parsed")
        return json_res
    
    except Exception as e:
        print("ERROR: Exception during resume parsing",str(e))
        print("ERROR: Exception type: ",type(e).__name__)
        raise
    
    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)


def merge_resume_with_user(user: dict, parsed_resume: dict):
    try:
        print("INFO: Merging with user data.")

        
        updates = {}

        # ----- name -----
        if not user.get("profile", {}).get("name") and parsed_resume.get("name"):
            updates["profile.name"] = parsed_resume["name"]

        # ----- skills -----
        skills = set(user.get("profile", {}).get("skills",[]))
        for skill in parsed_resume.get("skills", []):
            if skill not in skills and len(skills) < MAX_SKILL_SLOTS:
                skills.add(skill)

        skills = normalize_skills(list(skills))
        updates["profile.skills"] = list(set(skills))

        # ----- projects -----
        projects = user.get("profile", {}).get("projects", [])
        for project in parsed_resume.get("projects", []):
            if project not in projects and len(projects) < MAX_PROJECT_SLOTS:
                projects.append(project)

        updates["profile.projects"] = projects

        # ----- resume metadata -----
        updates.update({
            "resume.uploaded": True,
            "resume.parsed_data": parsed_resume,
            "resume.last_updated": datetime.datetime.now()
        })

        return updates
    except Exception as e:
        print(f"exception during merging of resumes {str(e)}")
        traceback.print_exc()
        raise
    
if __name__ == "__main__":
    pass