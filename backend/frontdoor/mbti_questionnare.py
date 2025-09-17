from google.cloud import firestore

from typing import Dict

import pandas as pd
import numpy as np
import random


db = firestore.Client(database="hackathonfirestore")
batch = db.batch()
collection_ref = db.collection("questions")

def insert_questions(mbti_questions_path):
    df = pd.read_csv(mbti_questions_path)
    df.drop(df.columns[1],axis=1)
    df.head()

    for index,row in df.iterrows():
        ques = row["Sentence"]
        cat = row["Type"]
        dat = {"question": ques,"type":cat}
        # if index>10:
        #     break
        try:
            doc_ref = collection_ref.document()
            batch.set(doc_ref,{
                "question":row["Sentence"],
                "type":row["Type"]
            })
            print(f"inserted records {index}",end='\r')

        except Exception as e:
            print(f"error in storing data in firestore {str(e)}")
            print(f"type: {type(e)}")
        continue

    batch.commit()
    print("Batch insert done")

def prepare_questions():
    docs= db.collection("questions").stream()
    data = []
    for doc in docs:
        data.append(doc.to_dict())

    ques_df = pd.DataFrame(data)

    ques_list = {}
    for category in ques_df['type'].unique():
        questions = ques_df.loc[ques_df['type']==category,'question'].tolist()
        ques = random.choice(questions)
        ques_list[category] = [ques]

    print(ques_list)
    return ques_list
    
def evaluate_answers(user_answers: Dict[str,int]):
    #input data : {"type":score(int)}

    # strongly agree: 5 , strongly disagree: 1

    personality = {}
    for key,value in user_answers.items():
        if key not in personality:
            personality[key] = value
        else:
            personality[key] += value

    user_pers = []
    max_val = 0
    for key,value in personality.items():
        if value>= max_val:
            max_val = value
    for key,value in personality.items():
        if value==max_val:
            user_pers.append(key)
    
    print(personality)
    print(user_pers)
    return personality,user_pers

