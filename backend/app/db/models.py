"""SQLAlchemy ORM models for PathForge."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "pathforge_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    pathways: Mapped[list["LearningPathway"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "pathforge_resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("pathforge_users.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    extracted_skills: Mapped[dict] = mapped_column(JSON, default=dict)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="resumes")


class SkillProfile(Base):
    __tablename__ = "pathforge_skill_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("pathforge_users.id"))
    skill_id: Mapped[str] = mapped_column(String(50))
    skill_name: Mapped[str] = mapped_column(String(100))
    claimed_level: Mapped[int] = mapped_column(Integer, default=0)
    verified_level: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(100), default="")


class QuizSession(Base):
    __tablename__ = "pathforge_quiz_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("pathforge_users.id"))
    quiz_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Questions
    answers: Mapped[dict] = mapped_column(JSON, default=dict)  # User answers
    results: Mapped[dict] = mapped_column(JSON, default=dict)  # Graded results
    target_role: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | completed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="quiz_sessions")


class LearningPathway(Base):
    __tablename__ = "pathforge_learning_pathways"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("pathforge_users.id"))
    role_title: Mapped[str] = mapped_column(String(100))
    pathway_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Full pathway JSON
    total_modules: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="pathways")
