"""Skills extraction endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.skill_extractor import extract_skills

router = APIRouter()


class ResumeInput(BaseModel):
    resume_text: str
    role: str | None = None


class SkillItem(BaseModel):
    skill_id: str
    name: str
    level: int
    category: str
    relevance: str | None = None


class SkillExtractionResponse(BaseModel):
    skills: list[SkillItem]
    experience_years: int | None
    domain: str
    skill_experience: dict[str, int] | None = None


@router.post("/extract-skills", response_model=SkillExtractionResponse)
async def extract_skills_endpoint(data: ResumeInput):
    """
    Extract skills from resume text using BERT NER model.

    Takes raw resume text, returns structured skill profile with
    proficiency levels, experience years, and primary domain.
    """
    result = extract_skills(data.resume_text, role=data.role)
    return result
