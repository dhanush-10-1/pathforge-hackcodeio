"""
PathForge ML Service
====================
AI-driven adaptive onboarding engine.

Models used (citations required):
- BERT (Devlin et al., 2018) — fine-tuned for skill NER
- Sentence-Transformers (Reimers & Gurevych, 2019) — role-to-skill mapping
- O*NET Database (onetonline.org) — skills taxonomy
- Kaggle Resume Dataset — training data for skill extraction
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import skills, roles, quiz, pathway

app = FastAPI(
    title="PathForge ML Service",
    description="AI-driven skill extraction, role mapping, quiz generation, and adaptive pathway engine.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(skills.router, prefix="/api/ml", tags=["Skills"])
app.include_router(roles.router, prefix="/api/ml", tags=["Roles"])
app.include_router(quiz.router, prefix="/api/ml", tags=["Quiz"])
app.include_router(pathway.router, prefix="/api/ml", tags=["Pathway"])


@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml"}
