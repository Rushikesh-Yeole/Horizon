# app/domains_one_pass.py
import os
import re
import json
import logging
import random
from typing import List, Dict, Any

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import anyio

# Gemini client (same as your SkillsKB)
import google.generativeai as genai

# ---- LOAD ENV ----
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI required in .env")
if not GENAI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY required in .env")

genai.configure(api_key=GENAI_API_KEY)

# ---- LOGGING ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("domains-onepass")

# ---- MONGO (async) ----
mongo = AsyncIOMotorClient(MONGODB_URI)
db = mongo["kb"]
domains = db["domains"]

async def ensure_indexes():
    try:
        await domains.create_index("domain_id", unique=True)
        logger.info("Ensured unique index on domain_id")
    except Exception as e:
        logger.warning("Index creation warning: %s", e)

# ---- HELPERS ----
def slugify_domain(name: str) -> str:
    return "domain_" + re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def strip_markdown_and_clean(text: str) -> str:
    """Trim, remove code fences/backticks, extract first JSON array and fix trailing commas."""
    if not text:
        return text
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    # remove multi-fence segments safely
    s = re.sub(r"`{3,}.*?`{3,}", lambda m: m.group(0).strip("`"), s, flags=re.S)
    start = s.find("[")
    end = s.rfind("]") + 1
    if start != -1 and end != -1:
        s = s[start:end]
    # remove trailing commas before brace/bracket
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s

def combine_and_clean_tokens(raw: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in raw:
        if not s:
            continue
        t = s.strip()
        # unify separators and collapse multiple spaces
        t = re.sub(r"[_/\\]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 2 or re.match(r'^\d+$', t):
            continue
        if len(t) > 80:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out

# ---- SCRAPERS ----
async def so_tags_paginated(pages: int = 4, pagesize: int = 100) -> List[str]:
    """Fetch top StackOverflow tags (async, pages*pagesize total)."""
    tags = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for page in range(1, pages + 1):
            url = f"https://api.stackexchange.com/2.3/tags?order=desc&sort=popular&site=stackoverflow&pagesize={pagesize}&page={page}"
            try:
                r = await client.get(url)
                r.raise_for_status()
                items = r.json().get("items", [])
                tags.extend([t["name"] for t in items if t.get("name")])
            except Exception as e:
                logger.warning("SO page %d fetch failed: %s", page, e)
                # continue and try other pages
                continue
    return tags

async def fetch_coursera_categories() -> List[str]:
    url = "https://www.coursera.org/browse/computer-science"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        cat_texts = set()
        for tag in soup.find_all(["h1", "h2", "h3", "a", "span"]):
            t = (tag.text or "").strip()
            if not t:
                continue
            if len(t) < 120 and re.search(r"[A-Za-z]", t):
                cat_texts.add(t)
        logger.info("Scraped %d Coursera strings", len(cat_texts))
        return list(cat_texts)
    except Exception as e:
        logger.warning("Coursera scrape failed: %s", e)
        return []

import json
import re

def safe_json_parse(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # attempt quick fixes
        fixed = s

        # remove trailing commas
        fixed = re.sub(r",\s*([\]}])", r"\1", fixed)

        # add missing commas between string items
        fixed = re.sub(r'"\s+"', '", "', fixed)

        # ensure proper quotes for keys
        fixed = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', fixed)

        try:
            return json.loads(fixed)
        except Exception as e:
            raise ValueError(f"Could not repair JSON. Sample:\n{fixed[:500]}") from e


# ---- SINGLE PASS LLM CALL (genai client in thread) ----
async def gemini_single_call(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """
    Call Gemini via google.generativeai (synchronous client) inside a thread pool.
    Returns raw text resp.text (not cleaned).
    """
    def _call():
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(prompt)
        return resp.text or ""
    try:
        raw = await anyio.to_thread.run_sync(_call)
        return raw
    except Exception as e:
        logger.exception("Gemini call failed")
        raise RuntimeError(f"LLM generation failed: {e}")

# ---- PROMPT (one-pass) ----
ONEPASS_PROMPT = """
You are a strict, factual enumerator and normalizer for Computer Science domains.
Input: a noisy list of short tokens/phrases (GitHub/StackOverflow/Coursera candidates).

Task:
- Produce a JSON array of approximately {target} domain objects (target ±20), prioritizing **top-level and widely used CS domains**.
- Each domain object MUST include:
  - name: canonical domain name (Title Case)
  - aliases: up to 3 short aliases
  - skills: 7 to 10 most important skills for this domain
  - jobs: exactly 3–5 typical industry job titles for this domain (MUST NOT be empty)
  - brief: one short sentence describing the domain (<=25 words)
  - vector_id: ""   (leave empty)

Rules:
- Output STRICT valid JSON array ONLY. No markdown, commentary, or extra text.
- Deduplicate near-synonyms (merge AI / Artificial Intelligence etc.).
- Keep skills as tokens (not sentences), 7–10 each.
- Keep job titles realistic and aligned to industry standards for this domain.
- If you are uncertain, pick the most common, widely recognized jobs.

Input candidates (sample): {items}
"""


async def llm_onepass_normalize_and_enrich(candidates: List[str]) -> List[Dict[str, Any]]:
    # Chunk into smaller sets for stability
    CHUNK_SIZE = 25
    out = []
    for i in range(0, len(candidates), CHUNK_SIZE):
        chunk = candidates[i:i+CHUNK_SIZE]
        prompt = f"""
You are a strict JSON generator. From this list of Computer Science tags:
{json.dumps(chunk)}

Output a JSON array where each object has:
- name
- aliases (1-4)
- jobs (5)
- skills (7–10)
- brief (1 sentence)
- vector_id: ""

Rules:
- Output STRICT valid JSON array ONLY. No markdown, commentary, or extra text.
- Deduplicate near-synonyms (merge AI / Artificial Intelligence etc.).
- Keep skills as tokens (not sentences), 7–10 each.
- Keep job titles realistic and aligned to industry standards for this domain.
- If you are uncertain, pick the most common, widely recognized jobs.
"""
        def _call():
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            resp = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}  # <== Force JSON
            )
            return resp.text or ""

        raw = await anyio.to_thread.run_sync(_call)
        cleaned = strip_markdown_and_clean(raw)

        try:
            parsed = safe_json_parse(cleaned)
        except json.JSONDecodeError:
            # attempt a repair
            fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
            parsed = json.loads(fixed)

        for it in parsed:
            jobs = it.get("jobs")
            if not isinstance(jobs, list):
                jobs = []  # fallback if LLM returned int or string
            aliases = it.get("aliases")
            if not isinstance(aliases, list):
                aliases = []
            skills = it.get("skills")
            if not isinstance(skills, list):
                skills = []

            out.append({
                "name": it.get("name", "").strip(),
                "aliases": aliases[:4],
                "jobs": jobs[:5],
                "skills": skills[:10],
                "brief": it.get("brief", ""),
                "vector_id": it.get("vector_id", "") or ""
            })
    logger.info("LLM produced %d enriched domain objects", len(out))
    return out


# ---- UPsert ----
async def upsert_domain_doc(doc: Dict[str, Any]) -> None:
    domain_id = slugify_domain(doc["name"])
    doc_to_store = {
        "domain_id": domain_id,
        "name": doc["name"],
        "aliases": doc.get("aliases", []),
        "skills": doc.get("skills", []),
        "jobs": doc.get("jobs", []),
        "brief": doc.get("brief",""),
        "vector_id": doc.get("vector_id","") or ""
    }
    await domains.replace_one({"domain_id": domain_id}, doc_to_store, upsert=True)

# ---- API models ----
class DomainDoc(BaseModel):
    domain_id: str
    name: str
    aliases: List[str]
    skills: List[str]
    jobs: List[str]
    brief: str
    vector_id: str

# ---- FASTAPI ----
app = FastAPI(title="DomainsKB One-Pass Seeder")

@app.on_event("startup")
async def startup():
    await ensure_indexes()

@app.post("/seed/domains", response_model=List[DomainDoc])
async def seed_domains(
    domain: str = Query("Computer Science", description="Top-level domain to seed"),
    target: int = Query(100, description="Target number of domain objects (±20)"),
    so_pages: int = Query(4, description="StackOverflow pages to fetch (100 tags per page)"),
    coursera_limit: int = Query(200, description="How many Coursera tokens to consider"),
    model_name: str = Query("gemini-2.5-flash-lite", description="Gemini model to use")
):
    """
    One-pass seeder:
    1) fetch StackOverflow tags and Coursera categories
    2) combine & clean candidate tokens
    3) single LLM call to produce ~target domain objects, each with jobs & 7-10 skills
    4) upsert into MongoDB
    """
    # 1) fetch sources (async)
    so = await so_tags_paginated(pages=so_pages, pagesize=100)
    coursera = await fetch_coursera_categories()
    coursera = coursera[:coursera_limit]

    raw = list(set(so + coursera))
    logger.info("Raw candidate tokens fetched: %d (SO=%d, Coursera=%d)", len(raw), len(so), len(coursera))

    cleaned_tokens = combine_and_clean_tokens(raw)
    logger.info("Cleaned candidate pool: %d tokens", len(cleaned_tokens))

    if len(cleaned_tokens) < 50:
        logger.warning("Candidate pool small (%d). Consider increasing sources/pages.", len(cleaned_tokens))

    # 2) single LLM call to get domains enriched
    normalized = await llm_onepass_normalize_and_enrich(cleaned_tokens)
    # optionally cap to requested target + small margin
    if len(normalized) > target + 20:
        normalized = normalized[: target + 20]

    # 3) upsert into MongoDB
    created = []
    for d in normalized:
        await upsert_domain_doc(d)
        created.append({
            "domain_id": slugify_domain(d["name"]),
            "name": d["name"],
            "aliases": d.get("aliases", []),
            "skills": d.get("skills", []),
            "jobs": d.get("jobs", []),
            "brief": d.get("brief",""),
            "vector_id": d.get("vector_id","") or ""
        })

    logger.info("One-pass inserted/merged %d domain docs (requested target=%d)", len(created), target)
    return created

@app.get("/domains", response_model=List[DomainDoc])
async def list_domains(limit: int = 1000):
    docs = await domains.find({}, {"_id": 0}).to_list(length=limit)
    return docs

@app.get("/domains/count")
async def domains_count():
    cnt = await domains.count_documents({})
    return {"total_domains": cnt}

@app.post("/test/llm")
async def test_llm(prompt: str = Query("Hello Gemini, respond briefly"), model_name: str = Query("gemini-2.5-flash-lite")):
    raw = await gemini_single_call(prompt, model_name=model_name)
    cleaned = strip_markdown_and_clean(raw)
    return {"raw": raw, "cleaned": cleaned}

@app.post("/domains/del")
def delete_domains_without_jobs():
    result = domains.delete_many({
        "$or": [
            {"jobs": {"$exists": False}},
            {"jobs": {"$size": 0}}
        ]
    })
    return {result}
