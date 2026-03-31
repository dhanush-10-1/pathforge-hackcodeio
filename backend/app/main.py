"""
PathForge Backend Service
=========================
API gateway for the PathForge adaptive onboarding engine.
Handles auth, database operations, and orchestrates ML service calls.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

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

# Security: Trust only specified hosts in production
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# CORS configuration - production ready
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(pathway.router, prefix="/api/pathway", tags=["Pathway"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "backend"}

