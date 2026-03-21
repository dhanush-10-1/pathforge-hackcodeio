"""Quiz flow router — start, submit, results."""

import os

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import QuizSession, SkillProfile, Resume
from app.schemas.schemas import (
    QuizStartRequest,
    QuizStartResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    ExternalQuizSubmitRequest,
    ExternalQuizSubmitResponse,
)
from app.services import ml_client

router = APIRouter()


@router.post("/start", response_model=QuizStartResponse)
async def start_quiz(
    data: QuizStartRequest,
    user_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    """
    Start a diagnostic quiz.
    Fetches the user's claimed skills and generates targeted questions.
    """
    # Get role requirements to know which skills to test
    try:
        role_data = await ml_client.map_role(data.target_role)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    effective_user_id = data.user_id or user_id or "demo-user"
    skill_ids = list(role_data["required_skills"].keys())
    claimed_levels: dict[str, int] = data.claimed_levels or {}
    experience_years = data.experience_years

    # If user has claimed skills, prioritize those
    if effective_user_id:
        result = await db.execute(
            select(SkillProfile).where(SkillProfile.user_id == effective_user_id)
        )
        user_skills = result.scalars().all()
        claimed_ids = [s.skill_id for s in user_skills]
        for profile in user_skills:
            claimed_levels.setdefault(profile.skill_id, profile.claimed_level)
        # Test claimed skills + required skills
        skill_ids = list(set(skill_ids + claimed_ids))

        if experience_years is None:
            resume_result = await db.execute(
                select(Resume)
                .where(Resume.user_id == effective_user_id)
                .order_by(Resume.created_at.desc())
            )
            latest_resume = resume_result.scalars().first()
            if latest_resume:
                experience_years = latest_resume.experience_years

    # Generate quiz
    try:
        quiz_data = await ml_client.generate_quiz(
            skill_ids,
            experience_years=experience_years,
            claimed_levels=claimed_levels,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    # Strip correct answers before sending to client
    client_questions = []
    for q in quiz_data["questions"]:
        client_q = {k: v for k, v in q.items() if k != "correct_index"}
        client_questions.append(client_q)

    # Save quiz session
    session = QuizSession(
        user_id=effective_user_id,
        quiz_data=quiz_data,
        target_role=data.target_role,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return QuizStartResponse(
        session_id=session.id,
        quiz_id=quiz_data["quiz_id"],
        questions=client_questions,
        total_questions=quiz_data["total_questions"],
        target_role=data.target_role,
    )


@router.post("/external-submit", response_model=ExternalQuizSubmitResponse)
async def submit_external_quiz(
    data: ExternalQuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept externally graded quiz results (e.g., localhost:8900 quiz app)."""
    expected_secret = os.getenv("QUIZ_CALLBACK_SECRET", "")
    if expected_secret and data.callback_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid callback secret")

    result = await db.execute(
        select(QuizSession).where(QuizSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    session.results = {
        "total_score": data.total_score,
        "max_score": data.max_score,
        "skill_scores": data.skill_scores,
        "source": data.source,
    }
    session.status = "completed"

    for skill_id, scores in data.skill_scores.items():
        profile_result = await db.execute(
            select(SkillProfile).where(
                SkillProfile.user_id == session.user_id,
                SkillProfile.skill_id == skill_id,
            )
        )
        profile = profile_result.scalars().first()
        verified_level = int(scores.get("verified_level", 0))
        if profile:
            profile.verified_level = verified_level
        else:
            db.add(SkillProfile(
                user_id=session.user_id,
                skill_id=skill_id,
                skill_name=skill_id,
                claimed_level=0,
                verified_level=verified_level,
            ))

    await db.commit()

    return ExternalQuizSubmitResponse(session_id=session.id, status=session.status)


@router.get("/{session_id}", response_model=QuizStartResponse)
async def get_quiz_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an existing quiz session and return client-safe questions."""
    result = await db.execute(
        select(QuizSession).where(QuizSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    questions = session.quiz_data.get("questions", []) if session.quiz_data else []
    if not questions:
        raise HTTPException(status_code=400, detail="Quiz data is unavailable for this session")

    client_questions = []
    for q in questions:
        client_q = {k: v for k, v in q.items() if k != "correct_index"}
        client_questions.append(client_q)

    return QuizStartResponse(
        session_id=session.id,
        quiz_id=session.quiz_data.get("quiz_id", ""),
        questions=client_questions,
        total_questions=session.quiz_data.get("total_questions", len(client_questions)),
        target_role=session.target_role,
    )


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz(
    data: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit quiz answers and get graded results."""
    result = await db.execute(
        select(QuizSession).where(QuizSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    # Grade via ML service
    try:
        grade_result = await ml_client.grade_quiz(
            session.quiz_data["questions"],
            data.answers,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service error: {str(e)}")

    # Update session
    session.answers = data.answers
    session.results = grade_result
    session.status = "completed"

    # Update verified skill levels
    for skill_id, scores in grade_result.get("skill_scores", {}).items():
        # Update existing profile or create new
        profile_result = await db.execute(
            select(SkillProfile).where(
                SkillProfile.user_id == session.user_id,
                SkillProfile.skill_id == skill_id,
            )
        )
        profile = profile_result.scalars().first()
        if profile:
            profile.verified_level = scores["verified_level"]
        else:
            db.add(SkillProfile(
                user_id=session.user_id,
                skill_id=skill_id,
                skill_name=skill_id,
                claimed_level=0,
                verified_level=scores["verified_level"],
            ))

    await db.commit()

    return QuizResultResponse(
        session_id=session.id,
        total_score=grade_result["total_score"],
        max_score=grade_result["max_score"],
        skill_scores=grade_result["skill_scores"],
        target_role=session.target_role,
    )


@router.get("/{session_id}/results", response_model=QuizResultResponse)
async def get_quiz_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get results for a completed quiz session."""
    result = await db.execute(
        select(QuizSession).where(QuizSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Quiz not yet completed")

    return QuizResultResponse(
        session_id=session.id,
        total_score=session.results.get("total_score", 0),
        max_score=session.results.get("max_score", 0),
        skill_scores=session.results.get("skill_scores", {}),
        target_role=session.target_role,
    )
