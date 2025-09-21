import sys
import os
from pprint import pprint

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import requests
import json
import time

import asyncio
import re

from pymongo import MongoClient

from vertexai.generative_models import GenerativeModel

from .personality import detect_company
from common.normalizer.normalizer import normalize_skills,normalize_job_personalities

from dotenv import load_dotenv
load_dotenv()

json_save_path = "/home/shash/projects/google_genai/data/jobs/jobs.json"
final_json_path = "/home/shash/projects/google_genai/data/jobs/final_jobs.json"
model = GenerativeModel(model_name="gemini-2.5-pro")

app = FastAPI(title="JOBS SEEDER")

client = MongoClient(os.getenv("MONGODB_URI"))

def get_google_json_res(pageno: int):
    try:
        jobs_url = f"https://careers.google.com/api/v3/search/?q=&page={pageno}&location=India"

        res = requests.get(jobs_url)
        json_res = res.json()
        # print(res.text)
        return json_res
    except Exception as e:
        print(f"ERROR: during getting job description from google api: {str(e)}")
        raise
   
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



def parse_job(raw_job: dict,cur_id: int):
    try:
        jobs = []
        id = cur_id
        for job in raw_job.get("jobs"):
            title = job["title"]
            apply_link = job["apply_url"]
            qualifications = job["qualifications"]
            responsibilities = job["responsibilities"]
            desc = job["description"]
            created_at = job["created"]
            publish_date = job["publish_date"]
            company = job["company_name"]
            locs = []
            for location_dict in job["locations"]:
                location = location_dict["display"]
                locs.append(location)
            
            job_listing = {
                "id":id,
                "title":title,
                "apply_link":apply_link,
                "company_name":company,
                "qualifications":qualifications,
                "responsibilities":responsibilities,
                "desc":desc ,
                "created_at":created_at,
                "publish_date":publish_date,
                "locations":locs
            }
            jobs.append(job_listing)
            id+=1
        
        return jobs,id
    except Exception as e:
        print(f"ERROR: during parsing jobs: {str(e)}")
        raise

def write_jobs_to_file(data: list, json_save_path: str):
    try:
        with open(json_save_path, 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("saved data")
    except Exception as e:
        print(f"ERROR: during writing jobs to local file {str(e)}")

def create_final_job_dict(entry_data,parsed_data):
    title = entry_data["title"]
    apply_link = entry_data["apply_link"]
    _,shrinked_title,score = detect_company(title,apply_link)

    if score>0.5:
        entry_data["title"] = shrinked_title

    skills = parsed_data["skills"]
    cleaned_skills = normalize_skills(skills)
    parsed_data["skills"] = cleaned_skills

    per_result_dict = normalize_job_personalities([entry_data["title"]])
    mbti_dict = per_result_dict[entry_data["title"]]["mbti"]

    final_dict = {
        "id":entry_data["id"],
        "title":entry_data["title"],
        "company":entry_data["company_name"],
        "apply_link":entry_data["apply_link"],
        "description":entry_data["desc"],
        "created_at":entry_data["created_at"],
        "publish_date":entry_data["publish_date"],
        "locations":entry_data["locations"],
        "skills":parsed_data["skills"],
        "education":parsed_data["education"],
        "personality":mbti_dict
    }
    return final_dict

def llm_condensation(data):
    
    try:
        ptr = 0
        data_size = len(data)
        final_job_data = []

        while(ptr<data_size):
            if ptr<data_size:
                entry = data[ptr]
                id1= entry.get("id",None)
                quals1 = entry.get("qualifications","")
                resp1 = entry.get("responsibilites","")
            if ptr+1<data_size:
                entry = data[ptr+1]
                id2 = entry.get("id",None)
                quals2 = entry.get("qualifications","")
                resp2 = entry.get("responsibilites","")
            if ptr+2<data_size:
                entry = data[ptr+2]
                id3 = entry.get("id",None)
                quals3 = entry.get("qualifications","")
                resp3 = entry.get("responsibilites","")
            

            prompt = f"""
You are an AI assistant that extracts structured info from job requirements.

Input: Here are job requirements for 3 jobs:

Job 1:
id: {id1}
Qualifications: {quals1}
Responsibilities: {resp1}

Job 2:
id: {id2}
Qualifications: {quals2}
Responsibilities: {resp2}

Job 3:
id: {id3}
Qualifications: {quals3}
Responsibilities: {resp3}

Task:
For each job, extract:
- education (degrees required)
- skills (both technical and soft skills)

Return a JSON array:
```json
{{"result":
[
  {{"id": , "education": [...], "skills": [...] }},
  {{ "id": ,"education": [...], "skills": [...] }},
  {{ "id": ,"education": [...], "skills": [...] }}
]
}}
```
"""     
            res = model.generate_content(prompt)
            res_content = res.text
            json_res = res_to_json(res_content)["result"]
            if ptr<data_size:
                f_entry1 = create_final_job_dict(data[ptr],json_res[0])
                final_job_data.append(f_entry1)

            if ptr+1<data_size:
                f_entry2 = create_final_job_dict(data[ptr+1],json_res[1])
                final_job_data.append(f_entry2)

            if ptr+2<data_size:
                f_entry3 = create_final_job_dict(data[ptr+2],json_res[2])
                final_job_data.append(f_entry3)

            ptr+=3
        # print(final_job_data)
        write_jobs_to_file(final_job_data,final_json_path)
        return final_job_data
    except Exception as e:
        print(f"exception while enriching job content {str(e)}")
        raise

def local_parse_pipeline():
    pageno = 1
    retries= 0
    retry_limit = 5
    cur_id = 0
    sleep_time = 3
    data = []
    while(retries<retry_limit and pageno<=10):
        print(f"current page no {pageno}")
        res = get_google_json_res(pageno)
        if("detail" in res.keys() and res["detail"]=="Not Found"):
            if sleep_time>60:
                sleep_time=3 
            print(f"Page not found, waiting for {sleep_time} secs before trying again")
            time.sleep(sleep_time)
            sleep_time=sleep_time**2
            retries+=1
            continue
        else:
            job_list,final_id = parse_job(res,cur_id=cur_id)
            data.extend(job_list)
            cur_id = final_id+1
            pageno+=1
            retries = 0
    print("writing jobs to file...")
    write_jobs_to_file(data,json_save_path)
    return data

@app.post("/seed/jobs")
async def seed_jobs():
    data = local_parse_pipeline()
    final_data = llm_condensation(data)
    db = client["job_listings"]
    collection = db["jobs"]
    collection.insert_many(final_data)
    return JSONResponse({"message":"seeded jobs"},status_code=200)
        
    pass

if __name__ == "__main__":
    data = local_parse_pipeline()
    # print(data)
    final_data = llm_condensation(data)
    pprint(final_data)
