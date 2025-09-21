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

model = TextEmbeddingModel.from_pretrained("text-embedding-004")




client = MongoClient(os.getenv("MONGODB_URI"))
# kb = client["kb"]
# skills_collection = kb["skills"]


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

def fuzzy_finder_personality(extracted_pers: dict):
    db = client["kb"]
    collection = db["personality"]

    final_results = {}

    for original_job, neighbors in extracted_pers.items():
        best_match = None
        best_score = -1

        for neighbor_id, distance in neighbors:
            doc = collection.find_one({"job_id": neighbor_id})
            if not doc:
                continue

            for job in doc.get("job_titles", []):
                title = job.get("title")
                score = fuzz.token_sort_ratio(original_job, title)

                if score > best_score:
                    best_score = score
                    best_match = {
                        "matched_title": title,
                        "score": score,
                        "mbti": job.get("mbti"),
                        "distance": distance
                    }

        if best_match:
            final_results[original_job] = best_match

    return final_results
    


def doc_to_text(doc):
    parts = []
    parts.append(f"name: {doc.get('name','')}")
    aliases = ','.join(doc.get("aliases",[]))
    parts.append(f"aliases: {aliases}" if aliases else "aliases: None")
    related = ','.join(doc.get("related_skills",[]))
    parts.append(f"related_skills: {related}" if related else "related_skills: None")
    parts.append(f"category: {doc.get("category","")}")
    return " | ".join(parts)


def get_personality_embedding(personalities):
    LIMIT =200
    embeddings = []
    idx = 0
    while(idx<len(personalities)):
        chunk = []
        if idx+LIMIT >= len(personalities):
            chunk = personalities[idx:len(personalities)]
        else:
            chunk = personalities[idx:idx+LIMIT]

        res = model.get_embeddings(chunk)
        for emb in res:
            embeddings.append(emb.values)

        idx+=LIMIT
    
    return embeddings

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
    csv_path = f"/home/shash/projects/google_genai/data/vectors/skills.csv"
    with open(csv_path,'w',newline='') as csv_file:
        writer = csv.writer(csv_file)
    
        for idx, (doc, vector) in enumerate(zip(docs, vectors), 1):
            print(f"{idx}/{len(docs)} - {doc['name']} -> dims: {len(vector)}")
            writer.writerow([doc["name"]]+vector)

def export_personality_vectors_to_csv():
    db = client["kb"]
    coll = db["personality"]
    docs= list(coll.find({}))
    pers = [doc["job_id"] for doc in docs]

    vectors = get_embedding(pers)
    csv_path = f"/home/shash/projects/google_genai/data/vectors/personality.csv"
    with open(csv_path,'w',newline='') as csv_file:
        writer = csv.writer(csv_file)
    
        for idx, (doc, vector) in enumerate(zip(docs, vectors), 1):
            print(f"{idx}/{len(docs)} - {doc['job_id']} -> dims: {len(vector)}")
            writer.writerow([doc["job_id"]]+vector)

def query_personality_index(text_query:list,num_neighbors=3):
    API_ENDPOINT=os.getenv("PERSONALITY_API_ENDPOINT")
    INDEX_ENDPOINT=os.getenv("PERSONALITY_INDEX_ENDPOINT")
    DEPLOYED_INDEX_ID=os.getenv("PERSONALITY_DEPLOYED_INDEX_ID")
    # Configure Vector Search client
    client_options = {
      "api_endpoint": API_ENDPOINT
    }
    vector_search_client = aiplatform_v1.MatchServiceClient(
      client_options=client_options,
    )

    vectors = get_personality_embedding(text_query)
    queries = []
    for vec in vectors:
        datapoint = aiplatform_v1.IndexDatapoint(feature_vector=vec)
        query = aiplatform_v1.FindNeighborsRequest.Query(datapoint=datapoint,neighbor_count=num_neighbors)
        queries.append(query)
    request = aiplatform_v1.FindNeighborsRequest(index_endpoint=INDEX_ENDPOINT,deployed_index_id=DEPLOYED_INDEX_ID,queries=queries,return_full_datapoint=False,)

    # Execute the request
    response_top_k = vector_search_client.find_neighbors(request)
    return response_top_k

def query_index(text_query:list, num_neighbors=3):
    """Query a deployed Matching Engine index with text input."""

    API_ENDPOINT=os.getenv("SKILLS_API_ENDPOINT")
    INDEX_ENDPOINT=os.getenv("SKILLS_INDEX_ENDPOINT")
    DEPLOYED_INDEX_ID=os.getenv("SKILLS_DEPLOYED_INDEX_ID")

    client_options = {
  "api_endpoint": API_ENDPOINT
    }
    vector_search_client = aiplatform_v1.MatchServiceClient(
    client_options=client_options,
    )

    # pass_text = list(text_query)
    vecs = get_embedding(text_query)
    queries = []
    for vec in vecs:
        datapoint = aiplatform_v1.IndexDatapoint(feature_vector=vec)
        query = aiplatform_v1.FindNeighborsRequest.Query(datapoint=datapoint,neighbor_count=num_neighbors)
        queries.append(query)

    request = aiplatform_v1.FindNeighborsRequest(index_endpoint=INDEX_ENDPOINT,deployed_index_id=DEPLOYED_INDEX_ID,queries=queries,return_full_datapoint=False,)
    response_top_k = vector_search_client.find_neighbors(request)

    return response_top_k

def extract_jobs(response, input_jobs):
    """
    Returns dict:
    {
      "original_job": [(neighbor1, distance1), (neighbor2, distance2), ...],
      ...
    }
    """
    results = {}

    for i, nn in enumerate(response.nearest_neighbors):
        original_job = input_jobs[i] if i < len(input_jobs) else f"job_{i}"
        neighbors_list = []
        for neighbor in nn.neighbors:
            datapoint_id = neighbor.datapoint.datapoint_id
            distance = neighbor.distance
            neighbors_list.append((datapoint_id, distance))
        results[original_job] = neighbors_list

    return results


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
        print(f"exception during normalization of skills{str(e)}")
        raise

def normalize_job_personalities(jobs: list):
    try:
        results = query_personality_index(jobs)
        extracted = extract_jobs(results,jobs)
        final = fuzzy_finder_personality(extracted)
        return final
    except Exception as e:
        print(f"exception during normalization of personas {str(e)}")
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
    
    # export_vectors_to_csv()
    # export_personality_vectors_to_csv()