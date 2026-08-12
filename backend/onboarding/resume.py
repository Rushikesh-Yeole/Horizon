import pdfplumber
from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import AsyncOpenAI
from onboarding.models import Profile
import os

resume_router = APIRouter()
client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

@resume_router.post("/parse_resume")
async def parse_resume(file: UploadFile = File(...)):
    try:
        text = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        
        response = await client.beta.chat.completions.parse(
            model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
            messages=[
                {"role": "system", "content": "Extract resume data into the exact schema provided. If a field is missing, leave it empty."},
                {"role": "user", "content": text}
            ],
            response_format=Profile
        )
        
        return response.choices[0].message.parsed.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
