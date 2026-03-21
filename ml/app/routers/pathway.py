"""Pathway generation endpoint — the core adaptive logic."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.adaptive_engine import generate_pathway

router = APIRouter()


class SkillRequirement(BaseModel):
    level: int
    importance: float
    name: str


class PathwayRequest(BaseModel):
    verified_skills: dict[str, int]  # skill_id -> verified_level
    role_requirements: dict[str, SkillRequirement]
    role_title: str


class ModuleResource(BaseModel):
    pass


class PathwayModule(BaseModel):
    order: int
    skill_id: str
    skill_name: str
    current_level: int
    target_level: int
    gap: int
    priority_score: float
    estimated_hours: int
    reason: str
    resources: list[str]


class PathwayResponse(BaseModel):
    role: str
    total_modules: int
    estimated_hours: int
    modules: list[PathwayModule]
    message: str | None = None
    reasoning_trace: list[dict] | None = None
    summary: dict | None = None


@router.post("/generate-pathway", response_model=PathwayResponse)
async def generate_pathway_endpoint(data: PathwayRequest):
    """
    Generate a personalized learning pathway.

    Adaptive logic (100% original):
    1. Gap calculator — diff between verified and required levels
    2. Priority scorer — gap_size × 0.6 + role_importance × 0.4
    3. Path sequencer — topological sort on skill dependency graph
    """
    role_reqs = {
        sid: {"level": req.level, "importance": req.importance, "name": req.name}
        for sid, req in data.role_requirements.items()
    }

    result = generate_pathway(
        verified_skills=data.verified_skills,
        role_requirements=role_reqs,
        role_title=data.role_title,
    )
    return result
