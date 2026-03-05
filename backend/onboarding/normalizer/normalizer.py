from pymongo import MongoClient


import csv
import json
from huggingface_hub import login
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import faiss
import numpy as np
import pprint

load_dotenv()
# login(os.getenv("HF_TOKEN"))

EMBED_DIM = 768

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


dir_path = "./data/skills_vectors"
if not os.path.exists(dir_path):
    os.makedirs(dir_path, exist_ok=True)


csv_path = "./data/skills_vectors/skills.csv"
map_path = "./data/skills_vectors/map.npy"
index_path = "./data/skills_vectors/index.bin"


client = MongoClient(os.getenv("MONGO_URI"))
kb = client["kb"]
skills_collection = kb["skills"]

normalized_skills = [
    doc["name"] for doc in skills_collection.find({}, {"name": 1, "_id": 0})
]

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
            print(
                f"\nOriginal: {original} | Neighbor: {neighbor} | Distance: {dist:.4f} | Fuzzy score: {score}"
            )

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
    aliases = ",".join(doc.get("aliases", []))
    parts.append(f"aliases: {aliases}" if aliases else "aliases: None")
    related = ",".join(doc.get("related_skills", []))
    parts.append(f"related_skills: {related}" if related else "related_skills: None")
    parts.append(f"category: {doc.get("category","")}")

    return " | ".join(parts)


def get_embedding(texts):

    LIMIT = 200
    embeddings = []
    idx = 0
    while idx < len(texts):
        chunk = []
        if idx + LIMIT >= len(texts):
            chunk = texts[idx : len(texts)]
        else:
            chunk = texts[idx : idx + LIMIT]

        res = model.encode(chunk)
        for emb in res:
            embeddings.append(emb)

        idx += LIMIT

    return embeddings


def export_vectors_to_csv():
    db = client["kb"]
    coll = db["skills"]
    docs = list(coll.find({}))
    texts = [doc_to_text(doc) for doc in docs]

    vectors = get_embedding(texts)

    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        for idx, (doc, vector) in enumerate(zip(docs, vectors), 1):
            print(f"{idx}/{len(docs)} - {doc['name']} -> dims: {len(vector)}")
            writer.writerow([doc["name"]] + vector.tolist())


def build_faiss_index(vectors):
    """Build the index"""

    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(vectors)
    return index


def load_vectors_from_csv(csv_path):
    names = []
    vectors = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            # print(row)
            name = row[0]
            vector = list(map(float, row[1:]))

            names.append(name)
            vectors.append(vector)
        vectors = np.array(vectors, dtype="float32")
    print("Shape of vectors", vectors.shape)
    return names, vectors


def add_vectors_to_index():
    """Adds vectors to FAISS index"""

    export_vectors_to_csv()

    names, vectors = load_vectors_from_csv(csv_path)
    index = build_faiss_index(vectors)

    faiss.write_index(index, index_path)
    np.save(map_path, np.array(names))


def query_index(text_query: list, num_neighbors=5):
    """Query a saved FAISS Index index with text input."""

    index = faiss.read_index(index_path)
    id_map = np.load(map_path, allow_pickle=True)

    query_embeddings = get_embedding(text_query)

    query_embeddings = np.array(query_embeddings, dtype="float32")
    faiss.normalize_L2(query_embeddings)

    distances, indices = index.search(query_embeddings, num_neighbors)

    skill_norm_skill_map = (
        {}
    )  # mapping of the user entered skills and the skills in KB which were extracted by the vector db
    idx = 0
    for skill in text_query:
        # print("Current skill: ",skill)
        skill_indices = indices[idx]
        dists = distances[idx]
        norm_skills = []
        for i, index in enumerate(skill_indices):
            norm_skill = id_map[index]
            dist = dists[i]
            norm_skills.append((str(norm_skill), float(dist)))

        # print(norm_skills)
        skill_norm_skill_map[str(skill)] = norm_skills
        idx += 1

    # pprint.pprint(skill_norm_skill_map,indent=4)
    return skill_norm_skill_map


def normalize_skills(skills: list):
    print("INFO: Running Normalize")
    try:
        print(f"INFO: Found skills {skills}")
        query_res = query_index(skills)

        fuzzy_skills = fuzzy_finder_skills(query_res)
        return fuzzy_skills
    except Exception as e:
        print(f"exception during normalization {str(e)}")
        raise


if __name__ == "__main__":
    skills = [
        "Product Management",
        "SaaS",
        "Strategic Marketing",
        "Business Operations",
        "Consulting",
        "Technical Presentations",
        "Cross-functional Collaboration",
        "Software Development",
        "Engineering",
    ]
    # query = "data struc"
    # fuzzy = normalize_skills(skills)

    # print(fuzzy)
    print("ADDING VECTORS")
    add_vectors_to_index()
    print("FUZZY")
    # query_index(skills)
    fuzzy = normalize_skills(skills)
    print(fuzzy)
