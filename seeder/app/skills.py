# app/main.py
import os
import re
import json
from typing import List, Any
import httpx
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai
from dotenv import load_dotenv

# ------- Load env -------
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # optional for higher rate limits

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not found in environment")

genai.configure(api_key=GEMINI_KEY)
mongo = AsyncIOMotorClient(MONGODB_URI)["kb"]["skills"]

ALLOWED_CATEGORIES = [
    "Programming Language", "Framework", "Tool", "Concept",
    "Database", "DevOps", "ML Framework", "Other", "Platform",
    "Library", "Markup Language", "Data Format", "Cloud Provider"
]


# ------- Ensure DB indexes (startup) -------
async def ensure_indexes():
    try:
        await mongo.create_index("tag_id", unique=True)
        print("[INFO] ensured index: tag_id (unique)")
    except Exception as e:
        print("[WARN] ensure_indexes error:", e)


# ------- Helpers -------
def slugify(name: str) -> str:
    return "skill_" + re.sub(r"[^a-z0-9\+]+", "_", name.lower()).strip("_")


def strip_markdown_and_clean(text: str) -> str:
    if not text:
        return text
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    s = re.sub(r"`{3,}.*?`{3,}", lambda m: m.group(0).strip("`"), s, flags=re.S)
    start = s.find("[")
    end = s.rfind("]") + 1
    if start != -1 and end != -1:
        s = s[start:end]
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s


# ------- Candidate fetchers -------
async def so_tags_paginated(pages: int = 4, pagesize: int = 100) -> List[str]:
    tags = []
    async with httpx.AsyncClient(timeout=20.0) as c:
        for page in range(1, pages + 1):
            url = f"https://api.stackexchange.com/2.3/tags?order=desc&sort=popular&site=stackoverflow&pagesize={pagesize}&page={page}"
            try:
                r = await c.get(url)
                r.raise_for_status()
                items = r.json().get("items", [])
                tags.extend([t["name"] for t in items if t.get("name")])
            except Exception as e:
                print(f"[WARN] SO page {page} failed: {e}")
                continue
    return tags


async def gh_candidates(queries: List[str], per_query: int = 50, token: str | None = None) -> List[str]:
    headers = {"Accept": "application/vnd.github.mercy-preview+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    candidates = []
    async with httpx.AsyncClient(timeout=30.0) as c:
        for q in queries:
            url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page={min(per_query,100)}"
            try:
                r = await c.get(url, headers=headers)
                r.raise_for_status()
                items = r.json().get("items", [])
                for it in items:
                    if it.get("language"):
                        candidates.append(it["language"])
                    if it.get("name"):
                        candidates.append(it["name"])
                    topics = it.get("topics") or []
                    for t in topics:
                        candidates.append(t)
            except Exception as e:
                print(f"[WARN] GH query {q} failed: {e}")
                continue
    return candidates


def combine_and_clean(raw: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in raw:
        if not s:
            continue
        token = s.strip()
        token = re.sub(r"[_/\\]+", " ", token)
        token = re.sub(r"\s+", " ", token).strip()
        if len(token) < 2 or re.match(r'^\d+$', token):
            continue
        if len(token) > 60:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(token)
    return out


# ------- Robust tolerant JSON array parsing -------
def tolerant_parse_json_array(s: str) -> List[Any]:
    """
    Attempt to parse a JSON array robustly even when malformed:
    - Extracts first [...] slice
    - Splits top-level items by scanning and tracking nested braces/brackets and string boundaries
    - For each item: try json.loads(item), else wrap as JSON string
    """
    if not s:
        return []
    start = s.find("[")
    end = s.rfind("]") + 1
    if start == -1 or end == -1:
        raise ValueError("No JSON array found")

    arr = s[start+1:end-1]  # content between brackets
    items = []
    buf = []
    depth = 0
    in_str = False
    esc = False
    quote_char = None

    for ch in arr:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote_char:
                in_str = False
                quote_char = None
            continue

        # not in string
        if ch == '"' or ch == "'":
            in_str = True
            quote_char = ch
            buf.append(ch)
            continue

        if ch in "{[":
            depth += 1
            buf.append(ch)
            continue
        if ch in "}]":
            depth -= 1 if depth > 0 else 0
            buf.append(ch)
            continue

        if ch == "," and depth == 0:
            item = "".join(buf).strip()
            if item:
                items.append(item)
            buf = []
            continue

        buf.append(ch)

    # last buffer
    last = "".join(buf).strip()
    if last:
        items.append(last)

    parsed = []
    for it in items:
        it = it.strip()
        if not it:
            continue
        try:
            parsed_item = json.loads(it)
            parsed.append(parsed_item)
            continue
        except Exception:
            # try wrap bare token as string (e.g., Python)
            # but first strip surrounding quotes if weird
            bare = it
            # if it looks like key:value (not expected) - skip
            if re.match(r'^[\w\-\+]+$', bare):
                parsed.append(bare)
                continue
            # try to coerce to string safely
            try:
                coerced = json.loads(f'"{bare.replace("\"", "\\\"")}"')
                parsed.append(coerced)
                continue
            except Exception:
                # last resort: append raw text
                parsed.append(bare)
                continue

    return parsed


# ------- LLM normalization (expanded) -------
def norm_prompt_expanded(cands: List[str], target: int = 150) -> str:
    sample = cands[:200] if len(cands) > 200 else cands
    return f"""
You are a precise skill normalizer. Given a large noisy candidate list of tokens, produce a JSON array
of approximately {target} programming / computer-science skills (target ±30).

For each skill object include:
- name: canonical, Title Case string (e.g., "Python")
- aliases: up to 4 common aliases/abbreviations (short strings)
- category: one of {ALLOWED_CATEGORIES} (or "Other")
- related_skills: up to 2 canonical related skill names

Rules:
- You MAY include popular skills NOT present in the input candidates.
- Aim for diversity across languages, frameworks, libraries, tools, databases, ML, concepts.
- Output ONLY a valid JSON array. Do NOT include markdown fences, backticks, explanation text, or trailing commas.
- If you cannot reach the target in a single response, output as many valid items as possible; we'll ask you to continue.

Example:
[{{"name":"Python","aliases":["py","python3"],"category":"Programming Language","related_skills":["C++","Java"]}}, ... ]

Input candidates (sample): {sample}
"""


async def llm_normalize_expanded(cands: List[str], target: int = 150, retry_continue: bool = True):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = norm_prompt_expanded(cands, target)

    try:
        resp = model.generate_content(prompt)
        raw = resp.text or ""
    except Exception as e:
        print("[ERROR] Gemini call failed:", e)
        raise HTTPException(status_code=500, detail=f"Gemini call failed: {e}")

    cleaned = strip_markdown_and_clean(raw)
    if not cleaned:
        print("[ERROR] LLM returned empty response")
        raise HTTPException(500, "LLM returned empty response")

    # First attempt: normal json.loads
    parsed = None
    try:
        parsed_candidate = json.loads(cleaned)
        if isinstance(parsed_candidate, list):
            parsed = parsed_candidate
        else:
            parsed = [parsed_candidate]
    except Exception as e:
        # fallback: tolerant parsing
        try:
            parsed = tolerant_parse_json_array(cleaned)
        except Exception as e2:
            print("[ERROR] primary parse failed:", e2)
            print("LLM raw (first 1500):", raw[:1500])
            raise HTTPException(500, f"LLM parse error: {e2}")

    # parsed is now a list (maybe mixture of dicts and strings)
    if not isinstance(parsed, list):
        parsed = [parsed]

    # if parsed is too small, attempt one continuation
    if retry_continue:
        minimal = max(50, target - 50)
        if len(parsed) < minimal:
            print(f"[WARN] LLM returned {len(parsed)} items, below minimal {minimal}. Asking for continuation.")
            follow_prompt = "Please continue: provide additional skills in the same JSON array format until the total list is about {} items. Output only a JSON array.".format(target)
            try:
                resp2 = model.generate_content(follow_prompt)
                raw2 = resp2.text or ""
                cleaned2 = strip_markdown_and_clean(raw2)
                parsed2 = []
                if cleaned2:
                    try:
                        parsed2_candidate = json.loads(cleaned2)
                        if isinstance(parsed2_candidate, list):
                            parsed2 = parsed2_candidate
                        else:
                            parsed2 = [parsed2_candidate]
                    except Exception:
                        try:
                            parsed2 = tolerant_parse_json_array(cleaned2)
                        except Exception as e3:
                            print("[WARN] continuation parse failed:", e3)
                            parsed2 = []
                # normalize parsed2 to list
                if not isinstance(parsed2, list):
                    parsed2 = [parsed2]
                # merge without duplicates by name
                def item_name(it: Any) -> str | None:
                    if isinstance(it, str):
                        return it.strip().lower()
                    if isinstance(it, dict):
                        return (it.get("name") or "").strip().lower()
                    return None

                seen_names = set()
                for it in parsed:
                    nm = item_name(it)
                    if nm:
                        seen_names.add(nm)

                for it in parsed2:
                    nm = item_name(it)
                    if not nm or nm in seen_names:
                        continue
                    # promote plain string to {"name": ...}
                    if isinstance(it, str):
                        it = {"name": it.strip()}
                    parsed.append(it)
                    seen_names.add(nm)
            except Exception as e:
                print("[WARN] continuation Gemini call failed:", e)

    # final normalization & dedupe
    seen = set()
    out = []
    for it in parsed:
        if isinstance(it, str):
            it = {"name": it}
        if not isinstance(it, dict):
            continue
        name = (it.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        aliases = it.get("aliases") or []
        aliases_clean = [a.strip() for a in aliases if a and isinstance(a, str)]
        related = it.get("related_skills") or []
        related_clean = [r.strip() for r in related if r and isinstance(r, str)]
        category = it.get("category") or "Other"
        if category not in ALLOWED_CATEGORIES:
            category = "Other"
        out.append({
            "name": name,
            "aliases": aliases_clean[:4],
            "category": category,
            "related_skills": related_clean[:2]
        })

    return out


# ------- Mongo upsert helper -------
async def upsert_skill(collection, skill_obj: dict):
    tag = slugify(skill_obj["name"])
    aliases = [a.lower() for a in skill_obj.get("aliases", []) if a]
    related = [slugify(r) for r in skill_obj.get("related_skills", []) if r]
    base = {
        "tag_id": tag,
        "name": skill_obj["name"],
        "category": skill_obj.get("category", "Other"),
        "vector_id": ""
    }

    await collection.update_one(
        {"tag_id": tag},
        {
            "$setOnInsert": base,
            "$addToSet": {
                "aliases": {"$each": aliases},
                "related_skills": {"$each": related}
            }
        },
        upsert=True
    )


# ------- API models -------
class Skill(BaseModel):
    tag_id: str
    name: str
    aliases: List[str]
    category: str
    related_skills: List[str]
    vector_id: str


app = FastAPI(title="Horizon Skills Seeder")


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()


# ------- Endpoints -------
@app.post("/seed/skills", response_model=List[Skill])
async def seed(
    domain: str = Query(..., description="Seed domain keyword, e.g., 'Computer Science'"),
    target: int = Query(300, description="Target number of normalized skills (±30)"),
    so_pages: int = Query(4, description="StackOverflow pages to fetch (100 tags per page)"),
):
    raw = []
    print("[INFO] fetching StackOverflow tags...")
    so = await so_tags_paginated(pages=so_pages, pagesize=100)
    print(f"[INFO] so_tags fetched: {len(so)}")
    raw.extend(so)

    cleaned = combine_and_clean(raw)
    print(f"[INFO] raw combined tokens: {len(raw)}, cleaned unique tokens: {len(cleaned)}")

    if len(cleaned) < 100:
        print("[WARN] cleaned candidate pool small; consider increasing pages/queries or adding more sources")

    print(f"[INFO] requesting LLM normalize (target={target})...")
    normalized = await llm_normalize_expanded(cleaned, target=target, retry_continue=True)
    print(f"[INFO] normalized count from LLM: {len(normalized)}")

    results = []
    for s in normalized:
        await upsert_skill(mongo, s)
        results.append({
            "tag_id": slugify(s["name"]),
            "name": s["name"],
            "aliases": [a.lower() for a in s.get("aliases", [])],
            "category": s.get("category", "Other"),
            "related_skills": [slugify(r) for r in s.get("related_skills", [])],
            "vector_id": ""
        })

    print(f"[INFO] inserted/merged {len(results)} skills (requested target={target})")
    return results


@app.get("/skills", response_model=List[Skill])
async def list_skills(limit: int = 500):
    return [doc async for doc in mongo.find().limit(limit)]


@app.get("/skills/count")
async def skills_count():
    count = await mongo.count_documents({})
    return {"total_skills": count}

@app.get("/domains", response_model=List[Skill])
async def all_skills(limit: int = 1000):
    docs = await mongo.find({}, {"_id": 0}).to_list(length=limit)
    return docs