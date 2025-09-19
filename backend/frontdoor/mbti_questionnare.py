# from google.cloud import firestore
from pymongo import MongoClient

from typing import Dict,List

import pandas as pd
import numpy as np
import random


import json
from dotenv import load_dotenv
import os

load_dotenv()
# db = firestore.Client(database="hackathonfirestore")
# batch = db.batch()
# collection_ref = db.collection("questions")

LOCAL_MBTI_JSON = "/home/shash/projects/google_genai/data/MBTI_questions/MBTI_subtopic_wise.json"

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["mbti_questions"]

def insert_questions():
    try:
        with open(LOCAL_MBTI_JSON,'r') as f:
            json_data = json.load(f)
        questions_list = json_data.get("MBTI_Questions",[])
        if(questions_list==[]):
            raise RuntimeError("Got empty MBTI questions list during insertion to DB")
        print("quetions loaded")
        final_dict = {}
        for subtopic in questions_list:
            id = 1
            final_entry_list = []
            for question in questions_list.get(subtopic):
                q_id = f"{subtopic}_{id}"
                entry = {"id":q_id,"question":question}
                final_entry_list.append(entry)
                id+=1
            final_dict[subtopic] = final_entry_list
        print("final data parsed, inserting in database")
        collection = db["questions"]
        res = collection.insert_one(final_dict)
        print(f"inserted one document with id {res.inserted_id}")
        print("inserting of MBTI questions done!")

    except Exception as e:
        print(f"ERROR: during inserting MBTI questions in DB {str(e)}")
        raise

def prepare_questions():
    #return type: [{"type":,"id":,"question":}]
    try:
        collection = db["questions"]
        doc = collection.find_one()
        if not doc:
            raise RuntimeError("No MBTI questions found in DB")
        ques_list = []
        for subtopic,questions in doc.items():
            if subtopic=="_id":
                continue
            chosen = random.sample(questions,2)
            for q_entry in chosen:
                q_id = q_entry["id"]
                ques = q_entry["question"]
                prepared_ques = {"type":subtopic,"id":q_id,"question":ques}
                ques_list.append(prepared_ques)
        # print(ques_list)
        return ques_list
    except Exception as e:
        print(f"error in preparing MBTI questions {str(e)}")
   
def get_persona(scores):
    persona = ""
    if(scores["E"]<0.5):
        persona+='I'
    else:
        persona+='E'

    if(scores["N"]<0.5):
        persona+='S'
    else: 
        persona+='N'
    
    if(scores["F"]<0.5):
        persona+='T'
    else:
        persona+='F'

    if(scores["P"]<0.5):
        persona+='J'
    else:
        persona+='P'
    return persona

def evaluate_answers(user_answers: List[Dict[str,int]]):
    #input data : [{"type":score(int)}]
    
    # strongly agree: 5 , strongly disagree: 1

    pairs = [("I","E"), ("S","N"), ("T","F"), ("J","P")]
    scores = {}

    
    grouped = {}
    for r in user_answers:
        grouped.setdefault(r["type"], []).append(r["score"])

    for a, b in pairs:
        values = []

        # normalize first category (I/S/T/J)
        for s in grouped.get(a, []):
            values.append((s - 1) / 4)

        # normalize second category (E/N/F/P)
        for s in grouped.get(b, []):
            values.append(1 - ((s - 1) / 4))

        final_score = np.mean(values) if values else 0.5
        scores[f"{b}"] = final_score
    persona = get_persona(scores)
    # print(scores)
    # print(persona)
    return scores,persona
    

if __name__ == "__main__":

    # insert_questions()
    # prepare_questions()
    responses = [
  {"type": "I", "score": 4},
  {"type": "I", "score": 2},
  {"type": "E", "score": 5},
  {"type": "E", "score": 3},
  {"type": "S", "score": 1},
  {"type": "S", "score": 4},
  {"type": "N", "score": 2},
  {"type": "N", "score": 5},
  {"type": "T", "score": 3},
  {"type": "T", "score": 4},
  {"type": "F", "score": 2},
  {"type": "F", "score": 5},
  {"type": "J", "score": 1},
  {"type": "J", "score": 4},
  {"type": "P", "score": 3},
  {"type": "P", "score": 5}
]

    evaluate_answers(responses)
