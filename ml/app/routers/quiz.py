"""Quiz generation and grading endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.quiz_generator import generate_quiz, grade_quiz, generate_dynamic_quiz

router = APIRouter()


class QuizRequest(BaseModel):
    skill_ids: list[str]
    questions_per_skill: int = 2
    max_questions: int = 10
    experience_years: int | None = None
    claimed_levels: dict[str, int] | None = None


# FEATURE 3: New request/response models for dynamic quiz
class DynamicQuizRequest(BaseModel):
    verified_skills: dict  # {skill: level} or {skill: {level: int}}
    role: str
    experience_years: str = "Not detected"
    max_questions: int = 10


class QuizQuestionWithWhy(BaseModel):
    skill: str
    difficulty: int
    question: str
    options: list[str]
    answer: int
    explanation: str
    why: str


class DynamicQuizResponse(BaseModel):
    questions: list[QuizQuestionWithWhy]
    total: int
    role: str
    adaptive: bool = True
    message: str


class QuizQuestion(BaseModel):
    id: str
    skill_id: str
    skill_name: str
    question: str
    options: list[str]
    correct_index: int
    difficulty: int


class QuizResponse(BaseModel):
    quiz_id: str
    questions: list[QuizQuestion]
    total_questions: int
    difficulty_profile: str | None = None
    experience_years: int | None = None


class GradeRequest(BaseModel):
    questions: list[QuizQuestion]
    answers: dict[str, int]  # question_id -> selected_index


class SkillScore(BaseModel):
    correct: int
    total: int
    verified_level: int


class GradeResponse(BaseModel):
    total_score: int
    max_score: int
    skill_scores: dict[str, SkillScore]


# FEATURE 3: New endpoint for dynamic quiz generation
@router.post("/generate-dynamic-quiz", response_model=DynamicQuizResponse)
async def generate_dynamic_quiz_endpoint(data: DynamicQuizRequest):
    """
    FEATURE 3: Generate adaptive quiz dynamically based on skill gaps and experience.
    
    Questions include "why" explaining which gap they address.
    Hard cap at 10 questions — never exceeds.
    """
    questions = generate_dynamic_quiz(
        verified_skills=data.verified_skills,
        role=data.role,
        experience=data.experience_years,
        max_questions=data.max_questions
    )
    
    return {
        "questions": questions,
        "total": len(questions),
        "role": data.role,
        "adaptive": True,
        "message": f"Quiz generated for {data.role} — {len(questions)} targeted questions based on your skill gaps"
    }


@router.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz_endpoint(data: QuizRequest):
    """Generate a diagnostic MCQ quiz for the given skills."""
    result = generate_quiz(
        data.skill_ids,
        data.questions_per_skill,
        data.max_questions,
        data.experience_years,
        data.claimed_levels,
    )
    if data.experience_years is None:
        difficulty_profile = "balanced"
    elif data.experience_years <= 1:
        difficulty_profile = "foundational"
    elif data.experience_years <= 4:
        difficulty_profile = "intermediate"
    else:
        difficulty_profile = "advanced"

    result["difficulty_profile"] = difficulty_profile
    result["experience_years"] = data.experience_years
    return result


@router.post("/grade-quiz", response_model=GradeResponse)
async def grade_quiz_endpoint(data: GradeRequest):
    """Grade quiz responses and return verified skill levels."""
    questions = [q.model_dump() for q in data.questions]
    result = grade_quiz(questions, data.answers)
    return result
