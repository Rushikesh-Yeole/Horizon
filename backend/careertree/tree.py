# tree.py - FastAPI Career Tree Generator (MongoDB-backed, career-stage focused)
# Version: 2.1 - full end-to-end, advisory-driven provenance + concrete opportunities
# Minimal fixes: increased default retries and store failed raw outputs to ctree_failures for debugging.

import os
import json
import asyncio
import datetime
import logging
import json5
import re
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, HttpUrl, validator
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# load env
load_dotenv(dotenv_path='../../.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career-generator")

# -----------------------------
# Config (env)
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY","AIzaSyAxnpSVprS68cBVHcOFq1WXdhIzAI0tPxg")
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-2.5-flash-lite")
GENAI_TIMEOUT = float(os.getenv("GENAI_TIMEOUT", "20"))
GENAI_MAX_TOKENS = int(os.getenv("GENAI_MAX_TOKENS", "10000"))

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB","users_db")

if not GEMINI_API_KEY:
    raise RuntimeError("GENAI_API_KEY environment variable is required. Set it before starting the app.")
if not MONGODB_URI or not MONGODB_DB:
    raise RuntimeError("MONGODB_URI and MONGODB_DB environment variables are required.")

# -----------------------------
# MongoDB client
# -----------------------------
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]
users_collection = db["profiles"]
ctrees_collection = db["ctrees"]  # store generated career trees
ctree_failures = db["ctree_failures"]  # debug store for failed/invalid LLM output

# -----------------------------
# Pydantic models (canonical career tree)
# -----------------------------
class Opportunity(BaseModel):
    title: str
    url: Optional[HttpUrl] = None
    snippet: Optional[str] = None   # 1-2 sentence reason or context
    source_type: Optional[str] = None  # exploratory free-form
    provenance: List[HttpUrl] = Field(default_factory=list)  # top 3 source URLs for this opportunity (company/university/jobboard)
    confidence: float = Field(..., ge=0.0, le=1.0)

class Stage(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    eta_months: Optional[int] = None
    nsqf_level: Optional[int] = None
    skill_requirements: List[str] = Field(default_factory=list)
    top_opportunities: List[Opportunity] = Field(default_factory=list)
    provenance: List[HttpUrl] = Field(default_factory=list)  # advisory/article/forum URLs that informed this stage

    @validator("top_opportunities")
    def limit_opps(cls, v):
        if len(v) > 10:
            raise ValueError("max 10 opportunities per stage")
        return v

class PathBranch(BaseModel):
    id: str
    title: str
    summary: str
    fit_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    stages: List[Stage] = Field(default_factory=list)

    @validator("stages")
    def limit_stages(cls, v):
        if len(v) > 7:
            raise ValueError("max 7 stages per path")
        return v

class CareerTree(BaseModel):
    user_id: str
    generated_at: str  # ISO timestamp
    domain_focus: List[str]  # supports multiple domains
    paths: List[PathBranch]
    provenance: List[HttpUrl] = Field(default_factory=list)  # aggregated advisory URLs that informed the whole tree
    confidence: float = Field(..., ge=0.0, le=1.0)

    @validator("paths")
    def require_three_paths(cls, v):
        if len(v) < 3:
            raise ValueError("atleast 3 career paths required")
        return v

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Career Path Generator", version="2.1-mongodb-advisory")

# -----------------------------
# Helpers
# -----------------------------
def personality_to_mbti(weights: dict) -> str:
    pairs = [("E","I"), ("S","N"), ("T","F"), ("J","P")]
    mbti = ""
    for a,b in pairs:
        wa = float(weights.get(a, 0.5))
        wb = float(weights.get(b, 0.5))
        mbti += a if wa >= wb else b
    return mbti

def slugify(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:64]

def is_likely_url(u: str) -> bool:
    try:
        if not isinstance(u, str):
            return False
        parts = urlparse(u.strip())
        return parts.scheme in ("http", "https") and parts.netloc != ""
    except Exception:
        return False

def ensure_number_in_0_1(val, default=0.7):
    try:
        v = float(val)
        if v != v:
            return default
        if v < 0: return 0.0
        if v > 1: return 1.0
        return v
    except Exception:
        return default

def normalize_career_tree(parsed: dict) -> dict:
    """
    Normalize structure returned by LLM:
    - Ensure domain_focus is list
    - Filter provenance lists to valid URLs (provenance fields at tree, stage, opportunity)
    - Fill missing ids, confidence defaults, convert eta strings -> ints where possible
    - Ensure source_type present (or set 'unknown')
    """
    if not isinstance(parsed, dict):
        return parsed

    if "domain_focus" in parsed and isinstance(parsed["domain_focus"], str):
        parsed["domain_focus"] = [parsed["domain_focus"]]

    # top-level provenance (string -> list of urls)
    prov = parsed.get("provenance")
    if isinstance(prov, str):
        candidates = [u.strip() for u in re.split(r"[,\n]+", prov) if u.strip()]
        parsed["provenance"] = [u for u in candidates if is_likely_url(u)]
    elif isinstance(prov, list):
        parsed["provenance"] = [u for u in prov if isinstance(u, str) and is_likely_url(u)]
    else:
        parsed["provenance"] = []

    # paths
    paths = parsed.get("paths", [])
    if paths is None:
        parsed["paths"] = []
        paths = parsed["paths"]

    for pi, p in enumerate(paths):
        if not isinstance(p, dict):
            continue
        if "title" not in p and "name" in p:
            p["title"] = p.pop("name")
        p["summary"] = p.get("summary", p.get("description", ""))
        if "id" not in p:
            p["id"] = slugify(p.get("title", f"path_{pi+1}"))
        p["fit_score"] = ensure_number_in_0_1(p.get("fit_score", p.get("score", 0.75)), default=0.75)
        p["confidence"] = ensure_number_in_0_1(p.get("confidence", 0.8), default=0.8)

        stages = p.get("stages", [])
        if stages is None:
            p["stages"] = []
            stages = p["stages"]

        for si, s in enumerate(stages):
            if not isinstance(s, dict):
                continue
            if "name" not in s and "title" in s:
                s["name"] = s.get("title")
            if "id" not in s:
                s["id"] = slugify(s.get("name", s.get("title", f"stage_{si+1}")))
            # parse eta_months if string
            eta = s.get("eta_months")
            if isinstance(eta, str):
                m = re.search(r"(\d+)", eta)
                if m:
                    try:
                        s["eta_months"] = int(m.group(1))
                    except:
                        s["eta_months"] = None

            # normalize stage provenance (advisory article/forum urls)
            st_prov = s.get("provenance")
            if isinstance(st_prov, str):
                cand = [u.strip() for u in re.split(r"[,\n]+", st_prov) if u.strip()]
                s["provenance"] = [u for u in cand if is_likely_url(u)]
            elif isinstance(st_prov, list):
                s["provenance"] = [u for u in st_prov if isinstance(u, str) and is_likely_url(u)]
            else:
                s["provenance"] = []

            opps = s.get("top_opportunities", [])
            if opps is None:
                s["top_opportunities"] = []
                opps = s["top_opportunities"]

            for o in opps:
                if not isinstance(o, dict):
                    continue
                # opportunity provenance -> keep only valid URLs
                if "provenance" in o and isinstance(o["provenance"], str):
                    prov_list = [u.strip() for u in re.split(r"[,\n]+", o["provenance"]) if u.strip()]
                    o["provenance"] = [u for u in prov_list if is_likely_url(u)]
                elif "provenance" in o and isinstance(o["provenance"], list):
                    o["provenance"] = [u for u in o["provenance"] if isinstance(u, str) and is_likely_url(u)]
                else:
                    o["provenance"] = []

                # fallback: if 'source' is a url, use it as provenance
                if not o["provenance"] and "source" in o and isinstance(o["source"], str) and is_likely_url(o["source"]):
                    o["provenance"] = [o["source"]]

                o["confidence"] = ensure_number_in_0_1(o.get("confidence", 0.75), default=0.75)
                if "source_type" not in o:
                    o["source_type"] = "unknown"

    parsed["confidence"] = ensure_number_in_0_1(parsed.get("confidence", 0.8), default=0.8)
    return parsed

# -----------------------------
# New helper: unwrap nested/wrapped career-tree dicts (minimal, safe)
# -----------------------------
def extract_career_tree_dict(parsed):
    """
    If `parsed` is a dict that wraps the real career-tree under keys like
    'career_tree', 'careerTree', 'career', or 'tree', extract and return that inner dict.
    Otherwise, search shallowly (depth <= 3) for a nested dict that looks like a CareerTree
    (contains keys such as 'paths', 'user_id', 'generated_at', 'domain_focus') and return it.
    If nothing found, return original parsed.
    """
    if not isinstance(parsed, dict):
        return parsed

    wrapper_keys = ("career_tree", "careerTree", "career", "tree", "result", "data")
    for k in wrapper_keys:
        if k in parsed and isinstance(parsed[k], dict):
            inner = parsed[k]
            if any(key in inner for key in ("paths", "user_id", "generated_at", "domain_focus")):
                logger.info("Unwrapped career tree from key '%s'", k)
                return inner

    # shallow breadth-first search
    queue = [(parsed, 0)]
    seen = set()
    while queue:
        node, depth = queue.pop(0)
        if depth > 3:
            continue
        if isinstance(node, dict):
            if any(k in node for k in ("paths", "user_id", "generated_at", "domain_focus")):
                logger.info("Found career tree-like dict at depth %d", depth)
                return node
            for v in node.values():
                if isinstance(v, dict) and id(v) not in seen:
                    seen.add(id(v))
                    queue.append((v, depth + 1))
                elif isinstance(v, list) and depth < 3:
                    for item in v:
                        if isinstance(item, dict) and id(item) not in seen:
                            seen.add(id(item))
                            queue.append((item, depth + 1))
    return parsed

# -----------------------------
# Prompt builder (advice-driven + opportunity split)
# -----------------------------
def build_prompt(payload: dict) -> str:
    requirements = [
        "OUTPUT: JSON only. Return exactly one JSON object conforming to the CareerTree schema below. No extra text.",
        "Return exactly 3 distinct career paths. Each path: 4-7 stages. Each stage: 4-10 opportunities.",
        "Design career PATHS & STAGES STRICTLY based on authoritative ADVICE NOT ONLY GENERIC paths and stages: use career articles, blog posts by senior professionals, LinkedIn long-reads, high-signal forum discussions (e.g., relevant subreddits, Hacker News), and published career guides to inform structure (place these advisory URLs in 'tree.provenance' and/or 'stage.provenance').",
        "Provide EXTREMELY CURATED (according to suited jobs, education level, etc...) stages in chronological order aplicable ahead of user's education stage (internships, masters, jobs, mba, career pivot, etc...)",
        "For each stage, provide TOP OPPORTUNITIES (internships, jobs, programs, etc.). Source these from company career pages, university program pages, or reputable job boards. Put these URLs in top_opportunities.provenance.",
        "Do NOT put free-form text into any 'provenance' list — only valid URLs. Free-text advice or summaries belong in 'description' or 'snippet'.",
        "Do NOT invent placeholder names like [Company Name] or 'example' URLs. Use real existing companies, programs, or article links when referencing provenance. If unsure, cite high-signal sources you know exist (e.g., recognized publications, university pages).",
        "Include up to top-3 provenance URLs per opportunity and up to 10 total advisory URLs at the tree level.",
        "Include confidence values [0..1] for tree, each path, stage, and opportunity.",
        "Do not restrict source_type; it can be any descriptive string (e.g., 'company', 'university', 'forum', 'article', 'program', 'jobboard').",
        "If you cannot produce valid JSON, return {\"error\":\"<message>\"}."
    ]

    header = "You are a deterministic career-path generator for a product. FOLLOW REQUIREMENTS strictly.\n\nREQUIREMENTS:\n"
    for i, r in enumerate(requirements, 1):
        header += f"{i}. {r}\n"

    example = {
        "user_id": payload.get("user_id", "u123"),
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "domain_focus": payload.get("domain_focus", ["frontend engineering"]),
        "paths": [
            {
                "id": "path_software_engineer",
                "title": "Software Engineer",
                "summary": "Typical SWE growth path informed by industry advice",
                "fit_score": 0.85,
                "confidence": 0.9,
                "stages": [
                    {
                        "id": "stage_internship",
                        "name": "SWE Internship",
                        "description": "Internship at a tech company to gain practical experience (advice from career blogs and senior engineers).",
                        "eta_months": 3,
                        "skill_requirements": ["python", "javascript", "git"],
                        "provenance": [  # advisory URLs that informed this stage
                            "https://www.freecodecamp.org/news/how-to-get-software-engineer-internship/",
                            "https://lethain.com/how-to-get-an-internship/"
                        ],
                        "top_opportunities": [
                            {
                                "title": "SWE Intern at Microsoft",
                                "url": "https://careers.microsoft.com/students/us/en",
                                "snippet": "Microsoft student internships (official careers page).",
                                "source_type": "company",
                                "provenance": ["https://careers.microsoft.com/"],  # opportunity urls
                                "confidence": 0.95
                            }
                        ]
                    }
                ]
            },
            {
                "id": "path_uiux",
                "title": "UI/UX Designer",
                "summary": "Design career path informed by senior designers and articles",
                "fit_score": 0.70,
                "confidence": 0.80,
                "stages": []
            },
            {
                "id": "path_research",
                "title": "Frontend Research & Scaling",
                "summary": "Research and advanced frontend roles informed by academic and industry articles",
                "fit_score": 0.65,
                "confidence": 0.75,
                "stages": []
            }
        ],
        "provenance": [  # top advisory URLs for the whole tree
            "https://www.freecodecamp.org/news/",
            "https://acm.org",
            "https://news.ycombinator.com"
        ],
        "confidence": 0.85
    }

    body = json.dumps(payload, ensure_ascii=False)
    prompt = header + "\n\nINPUT (user payload):\n" + body + "\n\nEXAMPLE_JSON:\n" + json.dumps(example, ensure_ascii=False, indent=2) + "\n\nOUTPUT: CareerTree JSON only."
    return prompt

# -----------------------------
# Gemini adapter (google.generativeai)
# -----------------------------
try:
    import google.generativeai as genai
except Exception as e:
    raise RuntimeError("google.generativeai package is required. pip install google-generativeai") from e

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    try:
        genai.api_key = GEMINI_API_KEY
    except Exception:
        logger.warning("Unable to call genai.configure(); continuing - client may still work via attribute.")

def gemini_sync_generate(prompt: str, max_output_tokens: int = GENAI_MAX_TOKENS, temperature: float = 0.0) -> str:
    try:
        model = genai.GenerativeModel(GENAI_MODEL)
        resp = model.generate_content(
            [{"role": "user", "parts": [prompt]}],
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        return getattr(resp, "text", str(resp))
    except Exception as e:
        raise RuntimeError(f"gemini.generate_content failed: {e}") from e

# -----------------------------
# Helpers: JSON extraction, repair, finish prompts
# -----------------------------
def extract_json_from_text(text: str) -> str:
    if text is None:
        return ""
    t = text.strip()
    if not t:
        return ""
    if t[0] in ("{", "["):
        return t
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start:end+1]
    start_a = t.find("[")
    end_a = t.rfind("]")
    if start_a != -1 and end_a != -1 and end_a > start_a:
        return t[start_a:end_a+1]
    return t

def remove_trailing_commas(s: str) -> str:
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    return s

def attempt_autorepair_json(candidate: str, max_closers: int = 8) -> Optional[str]:
    if not candidate or not isinstance(candidate, str):
        return None
    s = remove_trailing_commas(candidate.strip())
    try:
        json5.loads(s)
        return s
    except Exception:
        pass
    open_brace = s.count("{")
    close_brace = s.count("}")
    open_sq = s.count("[")
    close_sq = s.count("]")
    missing_braces = open_brace - close_brace
    missing_sq = open_sq - close_sq
    to_append = ""
    if missing_sq > 0:
        to_append += "]" * min(missing_sq, max_closers)
    if missing_braces > 0:
        to_append += "}" * min(missing_braces, max_closers)
    candidate_try = remove_trailing_commas(s + to_append)
    try:
        json5.loads(candidate_try)
        return candidate_try
    except Exception:
        lines = s.splitlines()
        if len(lines) > 1:
            trimmed = "\n".join(lines[:-1])
            trimmed = remove_trailing_commas(trimmed)
            try:
                json5.loads(trimmed)
                return trimmed
            except Exception:
                pass
    return None

def build_repair_prompt(original_prompt: str, raw_output: str, error_msg: str) -> str:
    rp = (
        "You previously returned invalid JSON. Repair ONLY the JSON and return corrected JSON matching the CareerTree schema.\n"
        f"JSON parse/validation error: {error_msg}\n\n"
        f"RAW output: {raw_output}\n\nReturn ONLY corrected JSON. No extra text.\nOriginal instructions:\n{original_prompt}"
    )
    return rp

def build_finish_truncated_prompt(partial_json: str) -> str:
    prompt = (
        "The JSON output below was truncated/cut-off. DO NOT change keys or invent extra top-level fields.\n"
        "Finish the JSON so it becomes a valid CareerTree JSON object that conforms to the previously provided schema.\n"
        "Return ONLY the corrected, completed JSON object — no explanation or extra text.\n\n"
        f"Partial JSON:\n{partial_json}\n\n"
        "If information is missing for required fields, fill with reasonable defaults but keep the schema exact."
    )
    return prompt

# -----------------------------
# Generation flow (validation + normalization + retries + repair)
# -----------------------------
async def generate_for_user(user_id: str, max_retries: int = 4) -> dict:
    """
    Generates a career tree for the user with given user_id.
    - fetches user doc from users_collection (db['profiles'])
    - runs LLM generation + repair + validation
    - stores resulting tree into db['ctrees'] with field "id" == user_id (upsert)
    - on final failure stores debug doc into db['ctree_failures'] for inspection
    - returns dict with status and tree (or error info)
    """
    # fetch user document
    user = await users_collection.find_one({"id": user_id})
    if not user:
        return {"user_id": user_id, "status": "error", "error": f"user with id {user_id} not found"}

    raw_domain = user.get("domain_focus") or user.get("suited_jobs") or ["general"]
    domain_focus = raw_domain if isinstance(raw_domain, list) else [raw_domain]

    payload = {
        "user_id": user.get("id", user.get("user_id", "unknown")),
        "skills": user.get("skills", []),
        "education": user.get("education", []),
        "experience": user.get("experience", []),
        "age": user.get("age"),
        "mbti": personality_to_mbti(user.get("personality", {})),
        "domain_focus": domain_focus
    }

    base_prompt = build_prompt(payload)
    logger.info("Generating career tree for %s (domains=%s)", payload["user_id"], domain_focus)

    attempt = 0
    last_error = None
    raw_last = ""
    while attempt <= max_retries:
        attempt += 1
        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(gemini_sync_generate, base_prompt, GENAI_MAX_TOKENS, 0.0),
                timeout=GENAI_TIMEOUT
            )
            raw_last = raw_text or ""
            logger.debug("Raw Gemini output (first 2000 chars): %s", (raw_last[:2000] if raw_last else "<empty>"))

            candidate = extract_json_from_text(raw_last)
            repaired = attempt_autorepair_json(candidate)
            candidate_to_parse = repaired or candidate

            try:
                parsed = json5.loads(candidate_to_parse)
            except Exception as e_json:
                # if parse failed, try finish-truncated repair
                logger.warning("Initial parse failed: %s. Trying finish-truncated repair.", e_json)
                finish_prompt = build_finish_truncated_prompt(candidate)
                try:
                    finish_raw = await asyncio.wait_for(
                        asyncio.to_thread(gemini_sync_generate, finish_prompt, GENAI_MAX_TOKENS // 2, 0.0),
                        timeout=GENAI_TIMEOUT
                    )
                    raw_last = finish_raw or raw_last
                    finish_candidate = extract_json_from_text(raw_last)
                    finish_repaired = attempt_autorepair_json(finish_candidate)
                    parse_target = finish_repaired or finish_candidate
                    parsed = json5.loads(parse_target)
                except Exception as finish_e:
                    raise ValueError(f"JSON parse error after finish-repair attempt: {finish_e}") from finish_e

            # unwrap mounted/wrapped responses if necessary (keeps behaviour stable)
            parsed = extract_career_tree_dict(parsed)

            if isinstance(parsed, dict) and "error" in parsed:
                raise ValueError(f"LLM signalled error: {parsed['error']}")

            parsed_norm = normalize_career_tree(parsed)
            tree = CareerTree(**parsed_norm)
            logger.info("Validation success for user %s", payload["user_id"])

            # prepare dict to store
            tree_dict = tree.dict()
            # ensure we have both user_id (as per schema) and id (user doc id requested)
            tree_dict["id"] = payload["user_id"]
            tree_dict["stored_at"] = datetime.datetime.utcnow().isoformat() + "Z"

            # make BSON/JSON-safe (converts HttpUrl -> str, BaseModel -> dict, etc.)
            tree_doc = jsonable_encoder(tree_dict)

            # upsert into ctrees collection (so repeated generation replaces previous tree)
            try:
                await ctrees_collection.replace_one(
                    {"id": payload["user_id"]},
                    tree_doc,
                    upsert=True
                )
                logger.info("Stored career tree for user %s into ctrees collection", payload["user_id"])
            except Exception as e_store:
                logger.warning("Failed to store tree for %s: %s", payload["user_id"], e_store)
                # proceed — we still return the tree even if storing failed
                return {"user_id": payload["user_id"], "status": "ok", "tree": tree_dict, "warning": f"store_failed: {e_store}"}

            return {"user_id": payload["user_id"], "status": "ok", "tree": tree_dict}

        except Exception as e:
            last_error = str(e)
            logger.warning("Attempt %d failed for %s: %s", attempt, payload["user_id"], last_error)

            # if retries remain, request a focused repair (existing logic retained)
            if attempt <= max_retries:
                repair_prompt = build_repair_prompt(base_prompt, raw_last, last_error)
                try:
                    raw_text = await asyncio.wait_for(
                        asyncio.to_thread(gemini_sync_generate, repair_prompt, GENAI_MAX_TOKENS, 0.0),
                        timeout=GENAI_TIMEOUT
                    )
                    raw_last = raw_text or raw_last
                    candidate = extract_json_from_text(raw_last)
                    repaired = attempt_autorepair_json(candidate)
                    parsed = json5.loads(repaired or candidate)

                    # unwrap again
                    parsed = extract_career_tree_dict(parsed)

                    if "error" in parsed:
                        raise ValueError(f"LLM signalled error after repair: {parsed['error']}")
                    parsed_norm = normalize_career_tree(parsed)
                    tree = CareerTree(**parsed_norm)

                    # prepare dict to store
                    tree_dict = tree.dict()
                    tree_dict["id"] = payload["user_id"]
                    tree_dict["stored_at"] = datetime.datetime.utcnow().isoformat() + "Z"

                    tree_doc = jsonable_encoder(tree_dict)

                    try:
                        await ctrees_collection.replace_one(
                            {"id": payload["user_id"]},
                            tree_doc,
                            upsert=True
                        )
                        logger.info("Stored career tree (after repair) for user %s into ctrees collection", payload["user_id"])
                    except Exception as e_store:
                        logger.warning("Failed to store repaired tree for %s: %s", payload["user_id"], e_store)
                        return {"user_id": payload["user_id"], "status": "ok", "tree": tree_dict, "warning": f"store_failed: {e_store}"}

                    logger.info("Repair succeeded for user %s", payload["user_id"])
                    return {"user_id": payload["user_id"], "status": "ok", "tree": tree_dict}
                except Exception as repair_e:
                    last_error = f"repair attempt failed: {repair_e}"
                    logger.warning("Repair attempt failed for %s: %s", payload["user_id"], repair_e)
                    await asyncio.sleep(0.6 * attempt)
                    continue

            # no retries left -> persist debug info for inspection and return error
            logger.error("All attempts failed for %s: %s", payload["user_id"], last_error)
            try:
                debug_doc = {
                    "id": payload["user_id"],
                    "error": last_error,
                    "raw_output": raw_last,
                    "prompt": base_prompt,
                    "ts": datetime.datetime.utcnow().isoformat() + "Z"
                }
                await ctree_failures.insert_one(jsonable_encoder(debug_doc))
                logger.info("Stored debug output for failed generation of %s into ctree_failures", payload["user_id"])
            except Exception as dbg_e:
                logger.warning("Failed to store debug doc for %s: %s", payload["user_id"], dbg_e)

            return {"user_id": payload["user_id"], "status": "error", "error": last_error, "raw_output": raw_last}

# -----------------------------
# Endpoints
# -----------------------------
@app.post("/batch-generate")
async def batch_generate():
    # fetch users from MongoDB; change filter as needed
    users = await users_collection.find().to_list(length=1000)
    if not users:
        return {"count": 0, "results": []}
    # call generate_for_user by id for each user
    tasks = [generate_for_user(u.get("id") or u.get("user_id")) for u in users]
    results = await asyncio.gather(*tasks)
    return {"count": len(results), "results": results}

@app.post("/generate/{user_id}")
async def generate_one(user_id: str):
    # --- Minimal change start ---
    existing_tree = await ctrees_collection.find_one({"id": user_id})
    if existing_tree:
        existing_tree.pop("_id", None)  # Remove MongoDB ObjectId for JSON serialization
        return {"user_id": user_id, "status": "ok", "tree": existing_tree}
    # --- Minimal change end ---
    
    result = await generate_for_user(user_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "generation failed"))
    return result


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat() + "Z"}

# -----------------------------

# -----------------------------
# Startup tasks (ensure index on users.id for fast lookups)
# -----------------------------

# -----------------------------
# Notes:
# - Minimal changes: default retries increased to 4 and a debug collection ctree_failures added.
# - If failures persist frequently, the best next steps are:
#   1) Inspect `ctree_failures` entries to see raw LLM outputs (they will be stored there).
#   2) Consider increasing retries further or adjusting repair prompts.
#   3) Optionally add an endpoint to fetch raw failure entries for easier debugging.
# -----------------------------
