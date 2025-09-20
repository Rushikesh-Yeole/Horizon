from pymongo import MongoClient

from vertexai.language_models import TextEmbeddingModel
from google.cloud import aiplatform_v1
import csv
import json

from rapidfuzz import process,fuzz

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOC = os.getenv("GOOGLE_VEC_LOC")
# ENDPOINT_ID = os.getenv("GOOGLE_VEC_ENDPOINT_ID")  # numeric endpoint ID
# INDEX_ID = os.getenv("GOOGLE_VEC_INDEX_ID")
# DEPLOYED_ID = os.getenv("GOOGLE_DEPLOYED_ID")

API_ENDPOINT="841157309.us-central1-588858008843.vdb.vertexai.goog"
INDEX_ENDPOINT="projects/588858008843/locations/us-central1/indexEndpoints/9049510661201068032"
DEPLOYED_INDEX_ID="skills_index_1758357368778"

client_options = {
  "api_endpoint": API_ENDPOINT
}
vector_search_client = aiplatform_v1.MatchServiceClient(
  client_options=client_options,
)

model = TextEmbeddingModel.from_pretrained("text-embedding-004")

csv_path = "/home/shash/projects/google_genai/data/skills_vectots/skills.csv"


client = MongoClient(os.getenv("MONGODB_URI"))
kb = client["kb"]
skills_collection = kb["skills"]

normalized_skills = [doc["name"] for doc in skills_collection.find({}, {"name": 1, "_id": 0})]

normalized_aliases = {
    doc["name"]: doc.get("aliases", [])
    for doc in skills_collection.find({}, {"name": 1, "aliases": 1, "_id": 0})
}

normalized_rel_skills = {
    doc["name"]: doc.get("related_skills", [])
    for doc in skills_collection.find({}, {"name": 1, "related_skills": 1, "_id": 0})
}


def fuzzy_finder_skills(extracted_skills: dict):
    """
    extracted_skills: {
        "original_skill": [(neighbor1, dist1), (neighbor2, dist2), ...],
        ...
    }
    Returns: {"original_skill": "best_matching_neighbor"}
    """
    results = []

    for original, neighbors in extracted_skills.items():
        best_match = None
        best_score = -1

        for neighbor, dist in neighbors:
            score = fuzz.ratio(original, neighbor)
            print(f"\nOriginal: {original} | Neighbor: {neighbor} | Distance: {dist:.4f} | Fuzzy score: {score}")

            if score > best_score:
                best_score = score
                best_match = neighbor

        if best_match:
            print(f"Final match for {original}: {best_match} (score={best_score})")
            results.append(best_match)
        else:
            print(f"No match found for {original}")

    return results

def doc_to_text(doc):
    parts = []
    parts.append(f"name: {doc.get('name','')}")
    aliases = ','.join(doc.get("aliases",[]))
    parts.append(f"aliases: {aliases}" if aliases else "aliases: None")
    related = ','.join(doc.get("related_skills",[]))
    parts.append(f"related_skills: {related}" if related else "related_skills: None")
    parts.append(f"category: {doc.get("category","")}")
    return " | ".join(parts)

def get_embedding(texts):
    
    LIMIT = 200
    embeddings = []
    idx = 0
    while idx<len(texts):
        chunk = []
        if idx+LIMIT >= len(texts):
            chunk = texts[idx:len(texts)]
        else:
            chunk = texts[idx:idx+LIMIT]

        res = model.get_embeddings(chunk)
        for emb in res:
            embeddings.append(emb.values)

        idx+=LIMIT
    
    return embeddings

def export_vectors_to_csv():
    db = client["kb"]
    coll = db["skills"]
    docs= list(coll.find({}))
    texts = [doc_to_text(doc) for doc in docs]

    vectors = get_embedding(texts)

    with open(csv_path,'w',newline='') as csv_file:
        writer = csv.writer(csv_file)
    
        for idx, (doc, vector) in enumerate(zip(docs, vectors), 1):
            print(f"{idx}/{len(docs)} - {doc['name']} -> dims: {len(vector)}")
            writer.writerow([doc["name"]]+vector)

def query_index(text_query:list, num_neighbors=5):
    """Query a deployed Matching Engine index with text input."""

    # pass_text = list(text_query)
    vecs = get_embedding(text_query)
    queries = []
    for vec in vecs:
        datapoint = aiplatform_v1.IndexDatapoint(feature_vector=vec)
        query = aiplatform_v1.FindNeighborsRequest.Query(datapoint=datapoint,neighbor_count=3)
        queries.append(query)

    request = aiplatform_v1.FindNeighborsRequest(index_endpoint=INDEX_ENDPOINT,deployed_index_id=DEPLOYED_INDEX_ID,queries=queries,return_full_datapoint=False,)
    response_top_k = vector_search_client.find_neighbors(request)

    return response_top_k

def extract_skills(response, input_skills):
    """
    Returns dict:
    {
      "original_skill": [(neighbor1, distance1), (neighbor2, distance2), ...],
      ...
    }
    """
    results = {}

    for i, nn in enumerate(response.nearest_neighbors):
        original_skill = input_skills[i] if i < len(input_skills) else f"skill_{i}"
        neighbors_list = []
        for neighbor in nn.neighbors:
            datapoint_id = neighbor.datapoint.datapoint_id
            distance = neighbor.distance
            neighbors_list.append((datapoint_id, distance))
        results[original_skill] = neighbors_list

    return results

def normalize_skills(skills: list):
    try:
        query_res = query_index(skills)
        extracted = extract_skills(query_res,skills)
        
        fuzzy_skills = fuzzy_finder_skills(extracted)
        return fuzzy_skills
    except Exception as e:
        print(f"exception during normalization {str(e)}")
        raise

if __name__=="__main__":
    skills = [
      "Product Management",
      "SaaS",
      "Strategic Marketing",
      "Business Operations",
      "Consulting",
      "Technical Presentations",
      "Cross-functional Collaboration",
      "Software Development",
      "Engineering"
    ]
    query = "data struc"
    fuzzy = normalize_skills(skills)
    
    print(fuzzy)