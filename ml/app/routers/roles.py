"""Role mapping endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.role_mapper import map_role, get_all_roles

router = APIRouter()


class RoleInput(BaseModel):
    role_title: str


class RoleSkillRequirement(BaseModel):
    level: int
    importance: float
    name: str


class RoleMappingResponse(BaseModel):
    role_id: str
    title: str
    description: str
    required_skills: dict[str, RoleSkillRequirement]


class RoleListItem(BaseModel):
    role_id: str
    title: str
    description: str


@router.post("/map-role", response_model=RoleMappingResponse)
async def map_role_endpoint(data: RoleInput):
    """
    Map a job role to its required competency profile using
    sentence-transformers matched against O*NET taxonomy.
    """
    result = map_role(data.role_title)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not map role '{data.role_title}' to a known competency profile. "
                   f"Try: Backend Engineer, Frontend Engineer, Full Stack Engineer, "
                   f"Data Engineer, ML Engineer, DevOps Engineer."
        )
    return result


@router.get("/roles", response_model=list[RoleListItem])
async def list_roles():
    """List all available target roles."""
    return get_all_roles()
