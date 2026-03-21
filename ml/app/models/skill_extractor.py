"""
Skill Extractor Model
=====================
Extracts skills from resume text using a fine-tuned BERT NER model.
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    
from app.models.adaptive_engine import classify_skill_relevance


logger = logging.getLogger(__name__)

# Load O*NET skills taxonomy
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
ONET_PATH = DATA_DIR / "onet_skills.json"

_taxonomy = None
_hf_pipeline = None
_pipeline_load_attempted = False
MAX_RETURN_SKILLS = 10

LEVEL_PATTERNS = {
    5: ["expert", "lead", "architect", "principal", "10+ years", "9+ years", "8+ years"],
    4: ["advanced", "senior", "proficient", "7+ years", "6+ years", "5+ years"],
    3: ["intermediate", "3+ years", "4+ years", "experienced"],
    2: ["familiar", "basic", "fundamental", "1+ year", "2+ years", "exposure", "basics"],
    1: ["beginner", "learning", "studying", "intern", "fresher"],
}


def _get_hf_pipeline():
    global _hf_pipeline, _pipeline_load_attempted
    if not _pipeline_load_attempted:
        _pipeline_load_attempted = True
        if not _TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers library is not installed. Falling back to semantic heuristics.")
            _hf_pipeline = None
            return _hf_pipeline
        try:
            model_path = Path(__file__).parent.parent / "models" / "checkpoints" / "skill_extractor"
            # Attempt to safely load the full NER pipeline
            # aggregation_strategy="simple" merges WordPiece sub-tokens back together (B-SKILL, I-SKILL)
            _hf_pipeline = pipeline(
                "token-classification", 
                model=str(model_path), 
                aggregation_strategy="simple"
            )
            logger.info(f"Loaded HuggingFace NER pipeline from {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load fine-tuned BERT NER model: {e}")
            _hf_pipeline = None
    return _hf_pipeline


def _load_onet_skill_ids_once() -> set[str]:
    for path in [ONET_PATH, Path("/app/data/onet_skills.json")]:
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            skills = payload.get("skills", {})
            if isinstance(skills, dict):
                return set(skills.keys())
        except Exception:
            continue
    return set()


ONET_SKILL_IDS = _load_onet_skill_ids_once()


def _resolve_role_key(role: str | None, taxonomy: dict) -> str | None:
    if not role:
        return None
    role_key = role.lower().strip()
    roles = taxonomy.get("roles", {})
    if role_key in roles:
        return role_key

    compact = role_key.replace("-", " ").replace("_", " ")
    for rid, data in roles.items():
        if compact == rid.replace("_", " "):
            return rid
        title = str(data.get("title", "")).lower().strip()
        if title and title == compact:
            return rid
    return None


def _get_role_required_skill_ids(role: str | None, taxonomy: dict) -> set[str]:
    role_key = _resolve_role_key(role, taxonomy)
    if not role_key:
        return set()

    role_data = taxonomy.get("roles", {}).get(role_key, {})
    required = role_data.get("required_skills", role_data.get("skills", {}))
    if not isinstance(required, dict):
        return set()
    return set(required.keys())


def _get_role_importance_map(role: str | None, taxonomy: dict) -> dict[str, float]:
    role_key = _resolve_role_key(role, taxonomy)
    if not role_key:
        return {}

    role_data = taxonomy.get("roles", {}).get(role_key, {})
    importance = role_data.get("importance_weights", {})
    if isinstance(importance, dict) and importance:
        return {k: float(v) for k, v in importance.items()}

    required = role_data.get("required_skills", {})
    if isinstance(required, dict):
        return {
            sid: float(req.get("importance", 0.0))
            for sid, req in required.items()
            if isinstance(req, dict)
        }
    return {}


def _apply_role_aware_cap(
    all_skills: dict[str, dict],
    role: str | None,
    onet_data: dict,
    cap: int = MAX_RETURN_SKILLS,
) -> dict[str, dict]:
    if len(all_skills) <= cap:
        return all_skills

    role_weights = _get_role_importance_map(role, onet_data)

    def score(item: tuple[str, dict]) -> float:
        skill, data = item
        bert_confidence = float(data.get("confidence", 0.5))
        role_importance = float(role_weights.get(skill, 0.1))
        return (role_importance * 0.6) + (bert_confidence * 0.4)

    ranked = sorted(all_skills.items(), key=score, reverse=True)
    return dict(ranked[:cap])


def _detect_domain(
    extracted_skill_ids: set[str],
    role: str | None,
    taxonomy: dict,
    extracted: list[dict],
) -> str:
    """Detect domain dynamically from role-skill overlap scoring."""
    roles = taxonomy.get("roles", {})
    if not extracted_skill_ids or not roles:
        return "General"

    selected_role_key = _resolve_role_key(role, taxonomy)
    role_scores: dict[str, float] = {}

    for role_id, role_data in roles.items():
        importance = role_data.get("importance_weights", {})
        required = role_data.get("skills", role_data.get("required_skills", {}))

        role_skill_ids: set[str] = set()
        if isinstance(required, dict):
            role_skill_ids = set(required.keys())

        if not role_skill_ids:
            role_scores[role_id] = 0.0
            continue

        overlap = extracted_skill_ids.intersection(role_skill_ids)
        if not overlap:
            role_scores[role_id] = 0.0
            continue

        weighted_overlap = 0.0
        for sid in overlap:
            weighted_overlap += float(importance.get(sid, 0.5))

        overlap_ratio = len(overlap) / max(1, len(role_skill_ids))
        role_scores[role_id] = weighted_overlap + (overlap_ratio * 2.0)

    if role_scores:
        best_score = max(role_scores.values())
        if best_score > 0:
            contenders = [rid for rid, score in role_scores.items() if score == best_score]
            if selected_role_key and selected_role_key in contenders:
                return roles[selected_role_key].get("title", selected_role_key)
            winner = sorted(contenders)[0]
            return roles[winner].get("title", winner)

    if selected_role_key and selected_role_key in roles:
        return roles[selected_role_key].get("title", selected_role_key)

    category_counts: dict[str, int] = {}
    for s in extracted:
        cat = s.get("category", "")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return max(category_counts, key=category_counts.get) if category_counts else "General"


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


def _extract_years_near_text(text: str) -> int | None:
    match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _extract_overall_experience_years(text_lower: str) -> int | None:
    year_patterns = [
        r"(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)",
        r"(\d+)\+?\s*yrs?\s*(?:of\s+)?(?:experience|exp)",
        r"experience.*?(\d+)\+?\s*years?",
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    return None


def _estimate_experience(resume_text: str) -> int | str:
    text_lower = resume_text.lower()
    years = _extract_overall_experience_years(text_lower)
    if years is None:
        return "Not detected"
    return years


def estimate_level(skill: str, resume_text: str) -> int:
    text_lower = resume_text.lower()

    global_exp = _estimate_experience(resume_text)
    try:
        exp_years = int(str(global_exp).replace("+", "").strip())
    except Exception:
        exp_years = 0

    if exp_years >= 7:
        base_level = 4
    elif exp_years >= 4:
        base_level = 3
    elif exp_years >= 2:
        base_level = 3
    elif exp_years >= 1:
        base_level = 2
    else:
        base_level = 1

    skill_pos = text_lower.find(skill.lower())
    if skill_pos == -1:
        return max(1, min(5, base_level))

    left = text_lower.rfind(".", 0, skill_pos)
    right = text_lower.find(".", skill_pos)
    if left == -1:
        left = 0
    else:
        left += 1
    if right == -1:
        right = len(text_lower)
    context = text_lower[left:right]

    for level, keywords in sorted(LEVEL_PATTERNS.items(), reverse=True):
        for keyword in keywords:
            if keyword in context:
                return int(max(1, min(5, level)))

    familiar_pattern = rf"familiar with[^.]*{re.escape(skill.lower())}"
    if re.search(familiar_pattern, text_lower):
        return 2

    proficient_pattern = rf"proficient in[^.]*{re.escape(skill.lower())}"
    if re.search(proficient_pattern, text_lower):
        return 4

    return int(max(1, min(5, base_level)))


def extract_skills(resume_text: str, role: str | None = None) -> dict:
    """
    Extract skills from resume text. Uses HF token classification pipeline.
    """
    taxonomy = _load_taxonomy()
    text_lower = resume_text.lower()
    role_importance = _get_role_importance_map(role, taxonomy)

    aggregated: dict[str, dict] = {}
    
    hf_pipeline = _get_hf_pipeline()
    if hf_pipeline:
        # Pass resume_text to pipeline which will output entities. 
        # With aggregation_strategy="simple", WordPiece sub-tokens are automatically stitched.
        entities = hf_pipeline(resume_text)
        
        for entity in entities:
            # Look for SKILL entities (from B-SKILL/I-SKILL aggregated)
            if entity.get("entity_group") == "SKILL":
                skill_phrase = entity.get("word", "").lower().strip()
                
                # Replace spaces and special characters with underscore to match taxonomy keys
                normalized_id = re.sub(r"[^a-z0-9]", "_", skill_phrase).strip("_")
                
                # Try to resolve to taxonomy ID
                best_skill_id = None
                if normalized_id in taxonomy["skills"]:
                    best_skill_id = normalized_id
                else:
                    # check known aliases or just match by name
                    for sid, sinfo in taxonomy["skills"].items():
                        if sinfo.get("name", "").lower() == skill_phrase:
                            best_skill_id = sid
                            break
                            
                if not best_skill_id and skill_phrase in taxonomy["skills"]:
                    best_skill_id = skill_phrase

                if best_skill_id:
                    confidence = float(entity.get("score", 0.5))
                    start_idx = max(0, entity.get("start", 0) - 80)
                    end_idx = min(len(resume_text), entity.get("end", 0) + 80)
                    snippet = resume_text[start_idx:end_idx].lower()
                    
                    if best_skill_id not in aggregated:
                        aggregated[best_skill_id] = {
                            "mentions": 1,
                            "contexts": [snippet],
                            "confidence": confidence
                        }
                    else:
                        aggregated[best_skill_id]["mentions"] += 1
                        aggregated[best_skill_id]["contexts"].append(snippet)
                        aggregated[best_skill_id]["confidence"] = max(aggregated[best_skill_id]["confidence"], confidence)
    else:
        logger.warning("Falling back to empty extraction as pipeline is not loaded.")
        
    aggregated = _apply_role_aware_cap(aggregated, role, taxonomy, cap=MAX_RETURN_SKILLS)

    exp_years = _extract_overall_experience_years(text_lower)

    skill_experience: dict[str, int] = {}
    extracted = []
    
    for skill_id, info in aggregated.items():
        # Fallback year extraction using surrounding context
        contexts = info.get("contexts", [])
        local_years = []
        for snippet in contexts:
            years = _extract_years_near_text(snippet)
            if years is not None:
                local_years.append(years)

        skill_years = max(local_years) if local_years else None
        if skill_years is not None:
            skill_experience[skill_id] = skill_years
            
        level = estimate_level(skill_id, resume_text)
        skill_info = taxonomy["skills"][skill_id]
        extracted.append({
            "skill_id": skill_id,
            "name": skill_info["name"],
            "level": level,
            "category": skill_info["category"],
            "confidence": info.get("confidence", 0.0),
        })

    extracted.sort(
        key=lambda x: (
            role_importance.get(x["skill_id"], 0.0),
            x["confidence"],
            x["level"],
        ),
        reverse=True,
    )

    if ONET_SKILL_IDS:
        validated = [s for s in extracted if s["skill_id"] in ONET_SKILL_IDS]
        if validated:
            extracted = validated

    extracted_ids = {s["skill_id"] for s in extracted}
    skill_experience = {k: v for k, v in skill_experience.items() if k in extracted_ids}
    
    domain = _detect_domain(extracted_ids, role, taxonomy, extracted)

    return {
        "skills": [
            {
                "skill_id": s["skill_id"],
                "name": s["name"],
                "level": s["level"],
                "category": s["category"],
                "relevance": classify_skill_relevance(s["skill_id"], role, taxonomy) if role else "unknown",
            }
            for s in extracted
        ],
        "experience_years": exp_years,
        "domains": [domain],
        "domain": domain,
        "skill_experience": skill_experience,
    }
