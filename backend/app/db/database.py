"""Database connection and session management."""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Load .env from project root (3 levels up from app/db/database.py)
_dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(_dotenv_path)
# Fallback: also try backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://pathforge:pathforge123@localhost:5432/pathforge"
)

# Auto-convert Supabase postgres:// or plain postgresql:// to postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Ensure SSL is required for Supabase connections (asyncpg needs this explicitly)
if "supabase.co" in DATABASE_URL or "supabase.com" in DATABASE_URL:
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?ssl=require"
    elif "ssl=require" not in DATABASE_URL:
        DATABASE_URL += "&ssl=require"

if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables."""
    from app.db.models import User, Resume, SkillProfile, QuizSession, LearningPathway  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Insert demo-user
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == "demo-user"))
        if not result.scalars().first():
            demo_user = User(
                id="demo-user", 
                name="Demo User", 
                email="demo@example.com", 
                password_hash="demo"
            )
            session.add(demo_user)
            await session.commit()
