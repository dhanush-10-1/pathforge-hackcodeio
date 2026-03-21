"""
PathForge Backend Service
=========================
API gateway for the PathForge adaptive onboarding engine.
Handles auth, database operations, and orchestrates ML service calls.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, resume, quiz, pathway
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PathForge Backend",
    description="API gateway for adaptive onboarding — resume upload, skill verification, pathway generation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8900",
        "http://127.0.0.1:8900",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(pathway.router, prefix="/api/pathway", tags=["Pathway"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "backend"}

