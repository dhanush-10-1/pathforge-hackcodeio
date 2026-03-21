"""Resume upload and skill extraction router."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Resume, SkillProfile
from app.schemas.schemas import ResumeUploadResponse
from app.services import ml_client

router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    user_id: str = Form(...),
    file: UploadFile = File(None),
    resume_text: str = Form(None),
    target_role: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume (PDF or raw text) and extract skills.
    Calls the ML service for BERT-based skill extraction.
    """
    text = ""

    if file and file.filename:
        content = await file.read()
        # Try PDF parsing
        filename_lower = file.filename.lower()
        if filename_lower.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader
                import io
                reader = PdfReader(io.BytesIO(content))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                text = content.decode("utf-8", errors="ignore")
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
            try:
                import pytesseract
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image)
            except Exception as e:
                text = f"Error extracting image text: {e}"
        else:
            text = content.decode("utf-8", errors="ignore")
    elif resume_text:
        text = resume_text
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or resume_text")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    # Call ML service
    try:
        extraction = await ml_client.extract_skills(text, role=target_role)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    # Save to database
    resume = Resume(
        user_id=user_id,
        raw_text=text,
        extracted_skills=extraction,
        experience_years=extraction.get("experience_years"),
        domain=extraction.get("domain"),
    )
    db.add(resume)

    # Save individual skill profiles
    for skill in extraction.get("skills", []):
        profile = SkillProfile(
            user_id=user_id,
            skill_id=skill["skill_id"],
            skill_name=skill["name"],
            claimed_level=skill["level"],
            verified_level=0,  # Not verified yet
            category=skill["category"],
        )
        db.add(profile)

    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        resume_id=resume.id,
        skills=extraction.get("skills", []),
        experience_years=extraction.get("experience_years"),
        domain=extraction.get("domain", ""),
        skill_experience=extraction.get("skill_experience", {}),
    )
