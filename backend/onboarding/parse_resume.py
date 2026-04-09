import os
import re
import json
import tempfile

from google import genai
from fastapi import UploadFile, File
import pymupdf
import pymupdf4llm
from dotenv import load_dotenv

from .normalizer.normalizer import normalize_skills

load_dotenv()

ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _extract_json(text: str) -> dict:
    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    raw = match.group(1).strip() if match else text.strip()
    return json.loads(raw)


def parse_resume(file: UploadFile = File(...)) -> dict:
    local_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(file.file.read())
            local_path = f.name

        doc = pymupdf.open(filename=local_path)
        text = pymupdf4llm.to_markdown(doc)

        prompt = f"""You are parsing a resume. Extract only these four fields: name, education, skills, projects.

RESUME:
{text}

Return ONLY valid JSON in this exact format — no extra text:
{{
  "name": "Full Name",
  "education": [{{"degree": "", "branch": "", "college": ""}}],
  "skills": ["skill1", "skill2"],
  "projects": [{{"title": "", "desc": "one line"}}]
}}

Skills: technical skills only, no soft skills. Projects: max 3, include only meaningful ones."""

        res = ai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        parsed = _extract_json(res.text)

        if parsed.get("skills"):
            parsed["skills"] = normalize_skills(parsed["skills"])

        return parsed

    except Exception as e:
        print(f"ERROR: resume parse failed: {e}")
        raise
    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)