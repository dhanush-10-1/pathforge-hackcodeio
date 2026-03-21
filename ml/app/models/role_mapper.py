"""
Role Mapper Model
=================
Simulates sentence-transformers/all-MiniLM-L6-v2 (Reimers & Gurevych, 2019)
for mapping a job role title to a required competency profile using the
O*NET skills taxonomy (onetonline.org).

In production, this would use cosine similarity between role title embeddings
and O*NET occupation embeddings.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
ONET_PATH = DATA_DIR / "onet_skills.json"

_taxonomy = None


def _load_taxonomy() -> dict:
    global _taxonomy
    if _taxonomy is None:
        for path in [ONET_PATH, Path("/app/data/onet_skills.json")]:
            if path.exists():
                with open(path) as f:
                    _taxonomy = json.load(f)
                return _taxonomy
        raise FileNotFoundError("onet_skills.json not found")
    return _taxonomy


def _fuzzy_match_role(role_title: str) -> str | None:
    """Match a free-text role title to a known role ID."""
    taxonomy = _load_taxonomy()
    role_lower = role_title.lower().strip()

    alias_map = {
        "backend_engineer": [
            "backend", "back-end", "back end", "server", "api developer",
            "python developer", "django developer", "fastapi"
        ],
        "frontend_engineer": [
            "frontend", "front-end", "front end", "ui developer",
            "react developer", "web developer"
        ],
        "fullstack_engineer": [
            "fullstack", "full-stack", "full stack", "software engineer",
            "software developer", "web developer", "sde", "swe"
        ],
        "data_engineer": [
            "data engineer", "data pipeline", "etl", "data infrastructure",
            "big data", "data platform"
        ],
        "ml_engineer": [
            "machine learning", "ml engineer", "ai engineer", "deep learning",
            "data scientist", "nlp engineer", "ai/ml"
        ],
        "devops_engineer": [
            "devops", "dev ops", "sre", "site reliability", "infrastructure",
            "cloud engineer", "platform engineer"
        ],
    }

    # Direct match
    if role_lower in taxonomy["roles"]:
        return role_lower

    # Alias matching
    for role_id, aliases in alias_map.items():
        for alias in aliases:
            if alias in role_lower:
                return role_id

    return None


def map_role(role_title: str) -> dict | None:
    """
    Map a job role to its required competency profile.

    Returns:
        {
            "role_id": str,
            "title": str,
            "description": str,
            "required_skills": {
                "skill_id": {"level": int, "importance": float, "name": str}
            }
        }
    """
    taxonomy = _load_taxonomy()
    role_id = _fuzzy_match_role(role_title)

    if role_id is None:
        return None

    role = taxonomy["roles"][role_id]
    skills_data = taxonomy["skills"]

    required = {}
    for skill_id, req in role["required_skills"].items():
        skill_name = skills_data.get(skill_id, {}).get("name", skill_id)
        required[skill_id] = {
            "level": req["level"],
            "importance": req["importance"],
            "name": skill_name,
        }

    return {
        "role_id": role_id,
        "title": role["title"],
        "description": role["description"],
        "required_skills": required,
    }


def get_all_roles() -> list[dict]:
    """Return all available roles."""
    taxonomy = _load_taxonomy()
    return [
        {"role_id": rid, "title": r["title"], "description": r["description"]}
        for rid, r in taxonomy["roles"].items()
    ]
