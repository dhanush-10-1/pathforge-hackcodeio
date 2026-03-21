"""HTTP client for communicating with the ML service."""

import os
import httpx

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")


async def extract_skills(resume_text: str, role: str | None = None) -> dict:
    """Call ML service to extract skills from resume text."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload: dict = {"resume_text": resume_text}
        if role:
            payload["role"] = role
        response = await client.post(
            f"{ML_SERVICE_URL}/api/ml/extract-skills",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def map_role(role_title: str) -> dict:
    """Call ML service to map a role to its competency profile."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/ml/map-role",
            json={"role_title": role_title},
        )
        response.raise_for_status()
        return response.json()


async def get_roles() -> list[dict]:
    """Get all available roles from ML service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{ML_SERVICE_URL}/api/ml/roles")
        response.raise_for_status()
        return response.json()


async def generate_quiz(
    skill_ids: list[str],
    max_questions: int = 10,
    experience_years: int | None = None,
    claimed_levels: dict[str, int] | None = None,
) -> dict:
    """Call ML service to generate a diagnostic quiz."""
    payload: dict = {
        "skill_ids": skill_ids,
        "max_questions": max_questions,
    }
    if experience_years is not None:
        payload["experience_years"] = experience_years
    if claimed_levels:
        payload["claimed_levels"] = claimed_levels

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/ml/generate-quiz",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def grade_quiz(questions: list[dict], answers: dict[str, int]) -> dict:
    """Call ML service to grade quiz responses."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/ml/grade-quiz",
            json={"questions": questions, "answers": answers},
        )
        response.raise_for_status()
        return response.json()


async def generate_pathway(
    verified_skills: dict[str, int],
    role_requirements: dict[str, dict],
    role_title: str,
) -> dict:
    """Call ML service to generate a personalized learning pathway."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/api/ml/generate-pathway",
            json={
                "verified_skills": verified_skills,
                "role_requirements": role_requirements,
                "role_title": role_title,
            },
        )
        response.raise_for_status()
        return response.json()
