import os
import json
import logging
import asyncio
import datetime
from typing import List, Optional, Dict, Any, Tuple

from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tavily import TavilyClient

# --- SETUP ---
load_dotenv()
logger = logging.getLogger(" Serendipty Engine ")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEYS = [k.strip() for k in (os.getenv("TAVILY_API_KEY") or "").split(",") if k.strip()]
REDIS_URL = os.getenv("REDIS_URL")

if not API_KEY or not TAVILY_KEYS:
    raise ValueError("Missing API Keys")

# --- 1. THE DATA SCHEMA ---
class Opportunity(BaseModel):
    title: str = Field(..., description="Concrete next step")
    url: Optional[str] = Field(None, description="Direct link if found")
    snippet: str = Field(..., description="Why this fits")

class Stage(BaseModel):
    name: str = Field(..., description="CONCRETE Role/Checkpoint")
    description: str = Field(..., description="Context")
    eta_months: int = Field(..., description="Timeline")
    skill_requirements: List[str] = Field(..., description="Hard skills")
    citations: List[str] = Field(..., description="List of 'SOURCE_REF_X' tags that prove this step.")
    top_opportunities: List[Opportunity] = Field(..., description="Gateway opportunities")

class PathBranch(BaseModel):
    id: str
    title: str = Field(..., description="The Archetype Name")
    summary: str = Field(..., description="Philosophy")
    fit_score: float = Field(..., description="Match Score")
    stages: List[Stage]

class CareerTree(BaseModel):
    user_id: str
    generated_at: str
    paths: List[PathBranch]

# --- 2. THE ENGINE ---
class CareerTreeEngine:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.5-flash" 
        self.tavily = TavilyClient(api_key=TAVILY_KEYS[0]) 
        self.cache_ttl = 86400

        self.target_domains = [
            "reddit.com", "news.ycombinator.com", "teamblind.com", "lobste.rs", 
            "indiehackers.com", "linkedin.com", "read.cv", "polywork.com",
            "uber.com/blog", "netflixtechblog.com", "engineering.fb.com", 
            "openai.com/research", "research.google", "blogs.microsoft.com",
            "medium.com", "substack.com", "github.com"
        ]

    def _generate_custom_archetypes(self, profile_summary: str) -> List[str]:
        logger.info("🔮 Generating Custom Archetypes (North Stars)...")
        prompt = f"""
        **OBJECTIVE:** Predict 3 distinct "Career North Stars" for this User.
        **USER DNA:** {profile_summary}
        
        **CRITICAL RULES for TITLES:**
        1. DO NOT include tech-stack keywords (e.g., No "Python", "Node.js", "Redis").
        2. Each title must represent a long-term career destination, not just a current job.
        3. Get best-case future scenarios for user, Be Opinionated.
        4. The future career options may be in Corporate, Entrepreneurship, Management, Deep Tech, Academia, etc. Be Open to Best possible Futures suited & aligned to user.

        **OUTPUT:** Return ONLY a Python list of 3 specific Search Queries for Tavily.
        Example: ["Infrastructure Lead career path reddit", "Staff Systems Engineer biography", "CTO roadmap for backend developers"]
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            text = response.text.strip()
            if text.startswith("```python"): text = text.split("```python")[1].split("```")[0]
            result = eval(text)
            logger.info(f"✅ Generated Archetypes: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Archetype Generation Failed: {e}")
            return [f"Career path for {profile_summary[:20]} reddit"] * 3

    # --- CHANGED: Returns (Evidence Text, URL Map) ---
    async def _fetch_biographies(self, queries: List[str]) -> Tuple[str, Dict[str, str]]:
        logger.info(f"🕵️  Fetching Biographies for {len(queries)} queries...")
        combined_evidence = ""
        url_map = {} # Maps 'SOURCE_REF_0' -> '[https://reddit.com/](https://reddit.com/)...'
        
        async def fetch(q):
            try:
                res = await asyncio.to_thread(
                    self.tavily.search,
                    query=q,
                    search_depth="advanced",
                    include_domains=self.target_domains,
                    max_results=14
                )
                return res.get("results", [])
            except Exception as e:
                logger.error(f"⚠️ Search Error for '{q}': {e}")
                return []

        results = await asyncio.gather(*[fetch(q) for q in queries])
        
        global_idx = 0
        total_items = 0
        for i, result_batch in enumerate(results):
            combined_evidence += f"<ARCHETYPE_SOURCES query='{queries[i]}'>\n"
            for item in result_batch:
                ref_tag = f"SOURCE_REF_{global_idx}"
                url_map[ref_tag] = item['url'] # Store the real URL
                
                combined_evidence += f"[{ref_tag}]: {item['url']}\nTITLE: {item['title']}\nCONTENT: {item['content'][:3000]}...\n\n"
                combined_evidence += "</ARCHETYPE_SOURCES>\n"
                global_idx += 1
                total_items += 1
        
        logger.info(f"📚 Evidence Gathered: {total_items} items.")
        return combined_evidence, url_map

    async def _synthesize_tree(self, user_id: str, profile_summary: str, evidence_text: str) -> Dict[str, Any]:
        logger.info("🧬 Synthesizing Career Tree Structure...")
        prompt = f"""
        ### 🧠 SYSTEM: THE CAREER META-ANALYST
        **USER PROFILE:** {profile_summary}
        **EVIDENCE LOCKER:**
        {evidence_text}

        ### ⚡ MISSION
        Construct 3 Distinct Career Paths based on **OVERLAPPING PATTERNS**.

        ### 💎 CITATION RULES (CRITICAL)
        1. **USE TAGS:** In the `citations` list, use the exact tags found in evidence: `["SOURCE_REF_0", "SOURCE_REF_5"]`.
        2. Include at least 4-5 diverse relevant citations for every stage to maximize evidence.
        3. **TRIANGULATE:** Do not invent stages. 
        4. Do not make stage contents/advice very abstracted or generic, make it as precise, personlaized, citations grounded and Oponionated as possible. Mention few exact Company/Institution/Universty names too in each stage wherein the opportunity lies best, for that stage respectively, grounded in citations.

        ### OUTPUT
        Return valid JSON matching the `CareerTree` schema.
        """

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CareerTree,
                    temperature=0.1
                )
            )
            logger.info("✅ Tree Synthesis Complete.")
            return response.parsed.model_dump()
        except Exception as e:
            logger.error(f"❌ Synthesis Failed: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_for_user(self, user_id: str, user_doc: Dict[str, Any], redis_client) -> Dict[str, Any]:
        logger.info(f"🚀 [Start] Career Tree for User: {user_id}")
        cache_key = f"horizon:tree_bio_v5:{user_id}" # Bumped Version
        
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info("♻️  Returning Cached Tree")
                return json.loads(cached)

        # 1. Adapt Profile
        profile = user_doc.get("profile", {})
        parsed_resume = user_doc.get("resume", {}).get("parsed_data", {})
        skills = list(set((profile.get("skills", []) or []) + (parsed_resume.get("skills", []) or [])))
        projects = (profile.get("projects", []) or []) + (parsed_resume.get("projects", []) or [])
        project_titles = [p.get("title") for p in projects if isinstance(p, dict)]
        
        profile_summary = f"""
        Role: {profile.get('preferences', {}).get('role', 'AI Engineer')}
        Interests: {profile.get('preferences', {}).get('interests', ['AI', 'ML', 'Data Science', 'Social Networks', 'Metaverse'])}
        Skills: {skills[:15]}
        Project History: {project_titles}
        """
        logger.info(f"📝 Profile Summary Built (Length: {len(profile_summary)})")

        # 2. Run Pipeline
        archetypes = self._generate_custom_archetypes(profile_summary)
        
        # Get Evidence AND the Map
        evidence, url_map = await self._fetch_biographies(archetypes)
        
        tree_data = await self._synthesize_tree(user_id, profile_summary, evidence)
        
        if "status" in tree_data and tree_data["status"] == "error":
            logger.error("🛑 Pipeline Aborted due to Synthesis Error")
            return tree_data

        # 3. RESOLVE REFERENCES (The Fix)
        # Swap 'SOURCE_REF_0' with 'https://...'
        logger.info("🔗 Resolving Citations...")
        try:
            resolved_count = 0
            for path in tree_data.get('paths', []):
                for stage in path.get('stages', []):
                    resolved_citations = []
                    for cit in stage.get('citations', []):
                        # Clean up potential brackets from LLM (e.g., "[SOURCE_REF_0]")
                        clean_ref = cit.replace("[", "").replace("]", "").strip()
                        
                        if clean_ref in url_map:
                            resolved_citations.append(url_map[clean_ref])
                            resolved_count += 1
                        elif cit.startswith("http"):
                            resolved_citations.append(cit)
                    
                    stage['citations'] = resolved_citations
            logger.info(f"✅ Resolved {resolved_count} citations.")
        except Exception as e:
            logger.error(f"Citation Resolution Failed: {e}")

        # 4. Cache & Return
        tree_data["generated_at"] = datetime.datetime.utcnow().isoformat()
        if redis_client:
            await redis_client.setex(cache_key, self.cache_ttl, json.dumps(tree_data))
            logger.info("💾 Tree Cached to Redis")
            
        return tree_data

# Singleton
engine = CareerTreeEngine()