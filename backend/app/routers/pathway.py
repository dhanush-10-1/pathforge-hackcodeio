"""Pathway generation router."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import QuizSession, LearningPathway, User
from app.schemas.schemas import PathwayGenerateRequest, PathwayResponse
from app.services import ml_client
from app.routers.auth import get_current_user

router = APIRouter()


@router.post("/generate", response_model=PathwayResponse)
async def generate_pathway(
    data: PathwayGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a personalized learning pathway based on quiz results.
    Requires authentication. Uses the adaptive engine: gap calculator → priority scorer → topological sort.
    """
    # Get quiz session and verify user ownership
    result = await db.execute(
        select(QuizSession).where(QuizSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized: You can only access your own pathways")

    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Quiz not yet completed. Submit answers first.")

    # Get role requirements
    try:
        role_data = await ml_client.map_role(session.target_role)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    # Build verified skills map from quiz results
    verified_skills = {}
    for skill_id, scores in session.results.get("skill_scores", {}).items():
        verified_skills[skill_id] = scores["verified_level"]

    # Generate pathway via ML service
    try:
        pathway_data = await ml_client.generate_pathway(
            verified_skills=verified_skills,
            role_requirements=role_data["required_skills"],
            role_title=role_data["title"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    # Save to database
    pathway = LearningPathway(
        user_id=session.user_id,
        role_title=role_data["title"],
        pathway_data=pathway_data,
        total_modules=pathway_data.get("total_modules", 0),
        estimated_hours=pathway_data.get("estimated_hours", 0),
    )
    db.add(pathway)
    await db.commit()
    await db.refresh(pathway)

    return PathwayResponse(
        pathway_id=pathway.id,
        role=pathway_data["role"],
        total_modules=pathway_data["total_modules"],
        estimated_hours=pathway_data["estimated_hours"],
        modules=pathway_data.get("modules", []),
        message=pathway_data.get("message"),
        reasoning_trace=pathway_data.get("reasoning_trace"),
        summary=pathway_data.get("summary"),
    )


@router.get("/{pathway_id}", response_model=PathwayResponse)
async def get_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a previously generated learning pathway."""
    result = await db.execute(
        select(LearningPathway).where(LearningPathway.id == pathway_id)
    )
    pathway = result.scalar_one_or_none()
    if not pathway:
        raise HTTPException(status_code=404, detail="Pathway not found")

    pd = pathway.pathway_data
    return PathwayResponse(
        pathway_id=pathway.id,
        role=pd.get("role", ""),
        total_modules=pd.get("total_modules", 0),
        estimated_hours=pd.get("estimated_hours", 0),
        modules=pd.get("modules", []),
        message=pd.get("message"),
        reasoning_trace=pd.get("reasoning_trace"),
        summary=pd.get("summary"),
    )
