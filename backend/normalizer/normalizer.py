from pymongo import MongoClient

from google.cloud import aiplatform
import csv

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOC = os.getenv("GOOGLE_VEC_LOC")
ENDPOINT_ID = os.getenv("GOOGLE_VEC_ENDPOINT_ID")
INDEX_ID = os.getenv("GOOGLE_VEC_INDEX_ID")

aiplatform.init(project=PROJECT_ID,location=LOC)

index_endpoint_name = f"projects/{PROJECT_ID}/locations/{LOC}/indexEndpoints/{ENDPOINT_ID}"
deployed_index_id = {INDEX_ID}

csv_path = "/home/shash/projects/google_genai/data/skills_vectots/skills.csv"

def doc_to_text(doc):
    parts = []
    parts.append(f"name: {doc.get('name','')}")
    aliases = ','.join(doc.get("aliases",[]))
    parts.append(f"aliases: {aliases}" if aliases else "aliases: None")
    related = ','.join(doc.get("related_skills",[]))
    parts.append(f"related_skills: {related}" if related else "related_skills: None")
    parts.append(f"category: {doc.get("category","")}")
    return " | ".join(parts)

def get_embedding(text: str):

    from vertexai.language_models import TextEmbeddingModel
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embedding = model.get_embeddings([text])[0].values
    return embedding

def export_vectors_to_csv():
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["kb"]
    coll = db["skills"]
    idx = 0
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["id", "embedding"])  # header
        for doc in coll.find({}):
            text = doc_to_text(doc)
            vector = get_embedding(text)
            writer.writerow([doc["name"], vector])
            idx+=1
            print(f"Processed docs: {idx}",end='\r')

def query_index(text_query, num_neighbors=5):
    """Query a deployed Matching Engine index with text input."""
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=index_endpoint_name
    )
    vector = get_embedding(text_query)
    response = index_endpoint.match(
        deployed_index_id=deployed_index_id,
        queries=[vector],
        num_neighbors=num_neighbors,
    )
    return response

if __name__=="__main__":
    # export_vectors_to_csv()
    query_skill = "AWS"
    res = query_index(query_skill)
    print(res)