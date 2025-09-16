
from google.cloud import documentai_v1 as documentai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage

from .user import db

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

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_VERTEX_LOC")
PROCESSOR_ID = os.getenv("GOOGLE_DOC_PROCESSOR_ID")
BUCKET_NAME = os.getenv("GOOGLE_BUCKET_NAME")


MAX_PROJECT_SLOTS = 3
MAX_SKILL_SLOTS = 10

def res_to_json(res_content: str):
    try:
            pattern = r"```json(.*?)```"
            match = re.findall(pattern,res_content)[0]
            json_content = json.loads(match)
            return json_content
    except Exception as e:
        print(f"json parse error {str(e)}")
        raise

name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

def parse_resume(file_path: str):
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

        model = GenerativeModel(model_name="gemini-2.5-flash")

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
        dest_blob_name = f"{user_id}_resume.pdf"

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(dest_blob_name)

        generation_match_precondition = 0
        blob.upload_from_file(file.file,content_type=file.content_type)

        expiration_hours = 2
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=expiration_hours))
        print(f"uploaded to cloud storage successfully {signed_url}")
        return signed_url
    except Exception as e:
        print(f"cloud storage exception: {e}")
        raise 
def merge_resume_with_user(user_id:str,parsed_resume: json,resume_url):
    try:
        batch = db.batch()
        doc_ref = db.collection("users").document(user_id)
        user_data = doc_ref.get().to_dict()

        doc_ref.update({"resume_url":resume_url})
        if not user_data["name"]:
            print("updating user name")
            doc_ref.update({"name":parse_resume["name"]})
        if len(user_data["skills"])<MAX_SKILL_SLOTS:
            print("updating skills...")
            skills_list = user_data["skills"]
            for skill in parsed_resume["skills"]:
                print(f"cur skill : {skill}")
                if(len(skills_list)>=MAX_SKILL_SLOTS):
                    break
                if skill not in skills_list:
                    skills_list.append(skill)
            doc_ref.update({"skills":skills_list})
        if len(user_data["projects"])<MAX_PROJECT_SLOTS:
            print("updating projects...")
            projects = user_data["projects"]
            for project in parsed_resume["projects"]:
                print(f"cur project: {project}")
                if len(projects)>=MAX_PROJECT_SLOTS:
                    break
                if project not in projects:
                    projects.append(project)
            doc_ref.update({"projects":projects})
        batch.commit()
        print("Resume merged with user data")
    except Exception as e:
        print(f"exception during merging of resumes {str(e)}")
        raise
    
if __name__ == "__main__":
    pass