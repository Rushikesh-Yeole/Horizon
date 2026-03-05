import os
import json
import logging
import concurrent.futures
import hashlib
import redis
from typing import List, Literal, Dict, Any
from dotenv import load_dotenv

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(" Advisor ")

# ENV
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")

if not API_KEY:
    logger.critical("❌ FATAL: GEMINI_API_KEY is missing.")
    raise ValueError("GEMINI_API_KEY is missing.")

class CompanyAdvisoryVerdict(BaseModel):
    company_name: str = Field(..., description="The specific company analyzed.")
    
    # 1. REASONING
    reasoning_trace: str = Field(
        ..., description="The Career Physics Calculation. E.g. 'Base Tier C (Java Gap) + Momentum Bump (Uber) = Final Tier B'."
    )
    
    # 2. MARKET REALITY
    hiring_bar_difficulty: Literal["Forgiving", "Standard", "High", "Elite"] = Field(
        ..., description="Difficulty based on company tier and location."
    )
    core_pillars_required: List[str] = Field(
        ..., description="The 3-5 non-negotiable hard skills found in the JD (e.g., 'Rust', 'Kubernetes')."
    )
    
    # 3. THE GAP ANALYSIS
    user_skill_gaps: List[str] = Field(
        ..., description="STRICT DIFF: List exactly 3-5 important skills in JD, but missing in User Profile."
    )
    
    # 4. THE VERDICT
    fit_score: int = Field(
        ..., description="STABLE SCORE (0-100) based on the Universal Capability Rubric."
    )
    feasibility_timeline_weeks: int = Field(
        ..., description="Accurate Weeks required to close the semantic distance, based on skill gaps and their difficulty."
    )
    verdict_headline: str = Field(
        ..., description="Max 10 words. Brutally honest summary."
    )
    actionable_path: List[str] = Field(
        ..., description="3-4 strict imperatives. Max 20 words each. Start with a VERB. (e.g. 'Build a Raft consensus module in Go.')"
    )
    main_advisory_text: str = Field(
        ..., description="Max 25 words. Strategic advice. Focus on the 'Why', not just the 'What'."
    )

class AdvisoryGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = "gemini-2.5-flash" 
        
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.jd_ttl = 604800
            logger.info("✅ Advisory Redis Connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis Connection Failed: {e}. Caching disabled.")
            self.redis = None

        # Universal Persona
        self.auditor_instruction = (
            "You are the Horizon Engine. You are BINARY, OBJECTIVE, and RUTHLESS. "
            "You measure 'Semantic Distance' (Capability Gap) and 'Momentum' (Proven Velocity). "
            "Output must be TELEGRAPHIC (high information density, zero filler words)."
            "You are BINARY and OBJECTIVE. You rely strictly on the provided evidence."
        )

    def _generate_jd_cache_key(self, role: str, company: str, location: str) -> str:
        """
        Generates a deterministic hash for the JD.
        Matches the caching strategy used in the main module.
        """
        clean_role = role.strip().lower()
        clean_comp = company.strip().lower()
        clean_loc = location.strip().lower()
        key_hash = hashlib.md5(f"{clean_role}|{clean_comp}|{clean_loc}".encode()).hexdigest()
        return f"horizon:jd:{key_hash}"

    def _fetch_official_jd(self, role: str, company: str, location: str) -> str:
        """
        STEP 1: The Researcher (Google Search) with Caching.
        """
        if self.redis:
            cache_key = self._generate_jd_cache_key(role, company, location)
            cached_jd = self.redis.get(cache_key)
            if cached_jd:
                logger.info(f"♻️  JD Cache Hit: {company} | {role}")
                return cached_jd

        logger.info(f"🕵️ [{company}] Searching for Official JD DNA (Live)...")
        
        prompt = f"""
        **OBJECTIVE:**
        Find the **Official Job Description** or **Engineering Standards** for the role of '{role}' at '{company}' in '{location}' (Target Year: 2024-2025).
        
        **CRITICAL EXTRACTION PROTOCOL:**
        1. **Search & Verify:** Use Google Search to find the most recent possible actual JD, team engineering blog, or hiring posts.
        2. **Distinguish 'Must-Haves' vs 'Nice-to-Haves':**
           - Extract the **Non-Negotiable Technical Stack** (e.g., "Must have 3+ years in Rust", "Proficiency in Go").
           - Extract the **Core Engineering Pillars** (e.g., "High-frequency low-latency systems", "Distributed Consensus", "Pixel-perfect UI").
        3. **Generalization Fallback:** If the exact JD is missing, find the *closest technical standard* for this specific team/company (e.g., "Uber Backend Standard Stack").
        
        **OUTPUT:**
        Provide a concise, bulleted summary of:
        - **Tech Stack:** [List hard skills]
        - **Key Responsibilities:** [List core challenges]
        """
        
        jd_text = "JD Unavailable. Using generic role standards."
        try:
            google_search_tool = types.Tool(google_search=types.GoogleSearch())
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    temperature=0.0
                )
            )
            if response.text:
                jd_text = response.text
                
                if self.redis:
                    self.redis.setex(cache_key, self.jd_ttl, jd_text)
                    
        except Exception as e:
            logger.warning(f"⚠️ JD Search Failed: {e}")
            
        return jd_text

    def _generate_single_company_card(self, user_profile: Dict[str, Any], company_name: str, role: str, location: str, advisory_signals: str) -> Dict[str, Any]:
        """
        STEP 2: The Physics Engine (Universal Audit).
        """
        # A. Get the Hard Truth
        official_jd_summary = self._fetch_official_jd(role, company_name, location)
        
        # B. Flatten user data
        profile_data = user_profile.get("profile", {})
        resume_data = user_profile.get("resume", {}).get("parsed_data", {})
        
        # Skills Extraction
        skills = profile_data.get("skills", []) or resume_data.get("skills", []) or user_profile.get("technical_skills", [])
        
        # Experience/Projects Extraction
        raw_projects = profile_data.get("projects", []) or resume_data.get("projects", []) or user_profile.get("key_projects_one_liners", [])
        project_descriptions = []
        for p in raw_projects:
            if isinstance(p, dict):
                project_descriptions.append(f"{p.get('title', 'Project')}: {p.get('desc', '')}")
            else:
                project_descriptions.append(str(p))
        
        # Experience Text
        experience_summary = user_profile.get("experience", [])
        if not experience_summary and project_descriptions:
             experience_summary = project_descriptions

        logger.info(f"🧮 [{company_name}] Running Engine...")
        
        # THE CAREER PHYSICS PROMPT
        prompt = f"""
        ### 🧪 THE LABORATORY (CONTEXT)
        TARGET: {company_name} ({location}) | ROLE: {role}
        
        ### 📜 SOURCE 1: OFFICIAL JD (THE HARD TRUTH)
        *Extracted Requirements:*
        {official_jd_summary}
        
        ### 🗣️ SOURCE 2: ADVISORY SIGNALS (INSIDER INTEL)
        *Real-world interview difficulty, culture, and bar:*
        {advisory_signals}
        
        ### 👤 CANDIDATE DNA (THE INPUT)
        STACK: {skills}
        PROOF: {project_descriptions}
        EXPERIENCE: {experience_summary}

        ### 🧠 THE UNIVERSAL CAREER PHYSICS ENGINE (EXECUTE LOGIC GATES)

        **GATE 1: CALCULATE 'SEMANTIC DISTANCE' (The Base Score)**
        *Compare CANDIDATE STACK vs OFFICIAL JD STACK strictly.*
        * **Tier A (Zero Distance | 90-100):** >80% Match. Candidate has production experience in the specific target ecosystem.
        * **Tier B (Syntactic Distance | 75-89):** >50% Match. Candidate knows Sibling Tech (e.g., React -> Vue, Java -> C#). Concepts transfer, syntax differs.
        * **Tier C (Paradigm Distance | 60-74):** <50% Match. Requires a Paradigm Shift (e.g., Web -> Systems, SQL -> NoSQL). Ramp-up > 3 months.
        * **Tier D (Domain Void | <60):** <20% Match. Fundamental engineering pillars are missing.

        **GATE 2: APPLY 'MOMENTUM MULTIPLIERS' (Velocity Check)**
        *Check 'CANDIDATE PROOF' for High-Velocity Environments.*
        * **High Momentum (+1 Tier Bump):** Does the user have a confirmed internship/role at a FAANG, Unicorn, or Fortune 500 Tech Co?
          * *ACTION:* If YES, upgrade Tier (e.g., Tier C -> Tier B). Proven engineering velocity overrides stack mismatch.
        * **Standard Momentum (+0 Tier):** Startups, Freelance, Personal Projects only.

        **GATE 3: CHECK 'GRAVITY WELLS' (Hard Blockers)**
        * **Level Mismatch:** Intern applying for Senior/Staff/Principal? -> **FORCE SCORE 20.**
        * **Ecosystem Lock:** Embedded/HFT role + Scripting-only skills (JS/Python)? -> **FORCE SCORE 30.**

        ### 🛡️ OUTPUT INSTRUCTIONS (STRICT NO-HALLUCINATION POLICY)
        1. **Strict Diff:** In `user_skill_gaps`, list ONLY the items present in `OFFICIAL JD STACK` that are completely missing from `CANDIDATE DNA`.
        2. **Advisory Synthesis:** Use `ADVISORY SIGNALS` to set the `hiring_bar_difficulty` and craft the `main_advisory_text`. (e.g., If signals say "LeetCode Hard", mention it).
        3. **Action Plan:** Provide 3 dense concrete, first-principles steps to close the specific gaps identified.
        4. **Honesty:** Do not be polite. Be an Engineer. If the gap is large, state it clearly.
        
        **Output strict JSON.**
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.auditor_instruction,
                    response_mime_type="application/json",
                    response_schema=CompanyAdvisoryVerdict,
                    temperature=0.0,
                    seed=42
                )
            )
            if response.parsed:
                return response.parsed.model_dump()
            raise ValueError("Empty response")
            
        except Exception as e:
            logger.error(f"🔥 [{company_name}] Physics Engine Failed: {e}")
            return {
                "company_name": company_name,
                "reasoning_trace": f"Error: {str(e)}",
                "hiring_bar_difficulty": "Standard",
                "core_pillars_required": [],
                "user_skill_gaps": [],
                "fit_score": 0,
                "feasibility_timeline_weeks": 0,
                "verdict_headline": "Analysis Unavailable",
                "actionable_path": [],
                "main_advisory_text": "Could not calculate physics for this role."
            }

    def generate_batch_cards(self, user_profile: Dict[str, Any], market_data_packet: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parallel Entry Point
        """
        logger.info("🚀 Starting Universal Advisory Batch...")
        
        criteria = market_data_packet.get('search_criteria', {})
        target_role = criteria.get('role', 'Software Engineer')
        target_location = criteria.get('location', 'Global')
        target_companies = criteria.get('target_companies', [])
        
        if not target_companies:
            raw_intel = market_data_packet.get('company_intelligence', [])
            target_companies = list(set([c.get('company_name') if isinstance(c, dict) else c.company_name for c in raw_intel]))[:3]

        raw_intel_list = market_data_packet.get('company_intelligence', [])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for company in target_companies:
                specific_intel = [
                    i for i in raw_intel_list 
                    if (i.get('company_name') if isinstance(i, dict) else i.company_name).lower() == company.lower()
                ]
                
                advisory_signals = ""
                for item in specific_intel:
                    results = item.get('results', []) if isinstance(item, dict) else item.results
                    for res in results:
                        content = res.get('content', '') if isinstance(res, dict) else res.content
                        advisory_signals += f"- {content}\n"
                
                if not advisory_signals:
                    advisory_signals = "No specific insider signals available. Relying on JD."

                futures.append(
                    executor.submit(
                        self._generate_single_company_card,
                        user_profile,
                        company,
                        target_role,
                        target_location,
                        advisory_signals
                    )
                )
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                
        logger.info(f"✅ Batch Complete. Generated {len(results)} cards.")
        return results