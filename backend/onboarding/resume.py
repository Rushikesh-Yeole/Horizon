import pdfplumber
from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import AsyncOpenAI
from onboarding.models import Profile
import os
from dotenv import load_dotenv

load_dotenv()

resume_router = APIRouter()
client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))

MODEL = os.getenv("MODEL_RESUME_PARSER", os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite"))
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


async def _validate_upload(file: UploadFile) -> bytes:
    """Read, size-cap, and type-check an uploaded file. Returns raw bytes."""
    if file.content_type != "application/pdf":
        raise HTTPException(422, detail="Only PDF files are accepted.")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(422, detail="File exceeds 5 MB limit.")
    return content


@resume_router.post("/parse_resume")
async def parse_resume(file: UploadFile = File(...)):
    try:
        content = await _validate_upload(file)
        import io
        text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        
        response = await client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Extract resume data into the exact schema provided. If a field is missing, leave it empty."},
                {"role": "user", "content": text}
            ],
            response_format=Profile
        )
        
        return response.choices[0].message.parsed.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
