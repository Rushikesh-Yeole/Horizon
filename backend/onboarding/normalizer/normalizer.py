import os
import numpy as np
import faiss
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

EMBED_DIM = 768
INDEX_PATH = "./data/skills_vectors/index.bin"
MAP_PATH   = "./data/skills_vectors/map.npy"

_model = None
_index = None
_id_map = None

_mongo = MongoClient(os.getenv("MONGO_URI"))
skills_col = _mongo["kb"]["skills"]


def _get_model():
    global _model
    if _model is None:
        print("INFO: Loading SentenceTransformer...")
        _model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _model


def _get_index():
    global _index, _id_map
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
        _id_map = np.load(MAP_PATH, allow_pickle=True)
    return _index, _id_map


def _embed(texts: list) -> np.ndarray:
    model = _get_model()
    vecs = []
    for i in range(0, len(texts), 200):
        vecs.extend(model.encode(texts[i:i + 200]))
    return np.array(vecs, dtype="float32")


def _fuzzy_pick(neighbor_map: dict) -> list:
    results = []
    for original, neighbors in neighbor_map.items():
        best, best_score = None, -1
        for neighbor, _ in neighbors:
            score = fuzz.ratio(original, neighbor)
            if score > best_score:
                best_score = score
                best = neighbor
        if best:
            results.append(best)
    return results


def _query_index(skills: list, k: int = 5) -> dict:
    index, id_map = _get_index()
    vecs = _embed(skills)
    faiss.normalize_L2(vecs)
    distances, indices = index.search(vecs, k)
    return {
        skill: [(str(id_map[idx]), float(distances[i][j])) for j, idx in enumerate(indices[i])]
        for i, skill in enumerate(skills)
    }


def normalize_skills(skills: list) -> list:
    if not skills:
        return []
    if os.getenv("FAST_START") == "True":
        return skills  # skip normalization in dev, return raw
    try:
        return _fuzzy_pick(_query_index(skills))
    except Exception as e:
        print(f"WARN: normalize_skills failed, returning raw: {e}")
        return skills


# ── Run this to rebuild the FAISS index from the skill KB in MongoDB ──────────

def rebuild_index():
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    docs = list(skills_col.find({}))

    def to_text(d):
        aliases = ",".join(d.get("aliases", []))
        related = ",".join(d.get("related_skills", []))
        return f"name: {d.get('name','')} | aliases: {aliases} | related: {related} | category: {d.get('category','')}"

    texts = [to_text(d) for d in docs]
    names = [d["name"] for d in docs]
    vecs = _embed(texts)

    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(vecs)

    faiss.write_index(index, INDEX_PATH)
    np.save(MAP_PATH, np.array(names))
    print(f"Rebuilt index: {len(names)} skills")


if __name__ == "__main__":
    rebuild_index()