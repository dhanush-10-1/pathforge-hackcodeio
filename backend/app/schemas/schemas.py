"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, EmailStr
from datetime import datetime


# ─── Auth ───
class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Resume ───
class ResumeUploadResponse(BaseModel):
    resume_id: str
    skills: list[dict]
    experience_years: int | None
    domain: str
    skill_experience: dict[str, int] | None = None


# ─── Quiz ───
class QuizStartRequest(BaseModel):
    target_role: str
    user_id: str | None = None
    experience_years: int | None = None
    claimed_levels: dict[str, int] | None = None


class QuizStartResponse(BaseModel):
    session_id: str
    quiz_id: str
    questions: list[dict]
    total_questions: int
    target_role: str


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: dict[str, int]  # question_id -> selected_index


class QuizResultResponse(BaseModel):
    session_id: str
    total_score: int
    max_score: int
    skill_scores: dict[str, dict]
    target_role: str


class ExternalQuizSubmitRequest(BaseModel):
    session_id: str
    total_score: int
    max_score: int
    skill_scores: dict[str, dict]
    source: str = "external-quiz"
    callback_secret: str | None = None


class ExternalQuizSubmitResponse(BaseModel):
    session_id: str
    status: str


# ─── Pathway ───
class PathwayGenerateRequest(BaseModel):
    session_id: str  # Quiz session to use for verified skills


class PathwayResponse(BaseModel):
    pathway_id: str
    role: str
    total_modules: int
    estimated_hours: int
    modules: list[dict]
    message: str | None = None
