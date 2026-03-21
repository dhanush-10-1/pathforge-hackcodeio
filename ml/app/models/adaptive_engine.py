"""
Adaptive Engine — Core Innovation
==================================
100% original implementation. Three-step adaptive logic:
1. Gap Calculator — difference between verified skills and role targets
2. Priority Scorer — gap_size × 0.6 + role_importance × 0.4
3. Path Sequencer — topological sort on skill dependency graph
"""

import json
from collections import deque
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DEPS_PATH = DATA_DIR / "skill_dependencies.json"
ONET_PATH = DATA_DIR / "onet_skills.json"

_deps = None
_taxonomy = None

# Three tiers of relevance plus hard exclusion for unrelated skills.
RELEVANCE_TIERS = {
    "critical": 1.0,
    "important": 0.6,
    "peripheral": 0.2,
    "irrelevant": 0.0,
}


def _load_deps() -> dict:
    global _deps
    if _deps is None:
        for path in [DEPS_PATH, Path("/app/data/skill_dependencies.json")]:
            if path.exists():
                with open(path) as f:
                    _deps = json.load(f)
                return _deps
        raise FileNotFoundError("skill_dependencies.json not found")
    return _deps


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


def _normalize_role_key(role: str, onet_data: dict) -> str | None:
    if not role:
        return None

    roles = onet_data.get("roles", {})
    role_lower = role.lower().strip()
    if role_lower in roles:
        return role_lower

    role_compact = role_lower.replace("-", " ").replace("_", " ")
    for role_id, role_data in roles.items():
        if role_compact == role_id.replace("_", " "):
            return role_id
        title = str(role_data.get("title", "")).lower().strip()
        if title and title == role_compact:
            return role_id

    return None


def _extract_role_skill_maps(role: str, onet_data: dict) -> tuple[dict[str, int], dict[str, float]]:
    role_key = _normalize_role_key(role, onet_data)
    if role_key is None:
        return {}, {}

    role_data = onet_data.get("roles", {}).get(role_key, {})
    role_skills_raw = role_data.get("required_skills", role_data.get("skills", {}))
    importance_weights = dict(role_data.get("importance_weights", {}))

    role_skills: dict[str, int] = {}
    for skill_id, value in role_skills_raw.items():
        if isinstance(value, dict):
            role_skills[skill_id] = int(value.get("level", 0))
            importance_weights.setdefault(skill_id, float(value.get("importance", 0.0)))
        else:
            role_skills[skill_id] = int(value)
            importance_weights.setdefault(skill_id, 0.5)

    return role_skills, importance_weights


def classify_skill_relevance(skill: str, role: str, onet_data: dict) -> str:
    """Classify how relevant a skill is to the selected role."""
    role_skills, importance_weights = _extract_role_skill_maps(role, onet_data)

    if skill not in role_skills:
        return "irrelevant"

    weight = float(importance_weights.get(skill, 0.0))

    if weight >= 0.85:
        return "critical"
    if weight >= 0.65:
        return "important"
    if weight >= 0.4:
        return "peripheral"
    return "irrelevant"


def compute_priority_score(skill: str, gap: float, role: str, onet_data: dict) -> float:
    """
    Updated formula:
    priority = gap * 0.5 + importance * 0.3 + relevance * 0.2

    Irrelevant skills get 0.0 and are excluded from pathway.
    """
    relevance_tier = classify_skill_relevance(skill, role, onet_data)
    relevance_score = RELEVANCE_TIERS[relevance_tier]

    if relevance_tier == "irrelevant":
        return 0.0

    _, importance_weights = _extract_role_skill_maps(role, onet_data)
    importance = float(importance_weights.get(skill, 0.5))

    priority = (gap * 0.5) + (importance * 0.3) + (relevance_score * 0.2)
    return round(priority, 4)


def fetch_module(skill: str) -> dict:
    taxonomy = _load_taxonomy()
    skill_info = taxonomy.get("skills", {}).get(skill, {})
    return {
        "skill_id": skill,
        "skill_name": skill_info.get("name", skill),
        "resources": _suggest_resources(skill, skill_info, current_level=0),
    }


def calculate_gaps(
    verified_skills: dict[str, int],
    role_requirements: dict[str, dict],
) -> list[dict]:
    """
    Step 1: Gap Calculator
    Computes gap = required_level - verified_level for each skill.

    Args:
        verified_skills: {skill_id: verified_level}
        role_requirements: {skill_id: {"level": int, "importance": float, "name": str}}

    Returns:
        List of gap objects sorted by priority score.
    """
    gaps = []
    for skill_id, req in role_requirements.items():
        verified = verified_skills.get(skill_id, 0)
        required = req["level"]
        gap = max(0, required - verified)

        if gap > 0:
            gaps.append({
                "skill_id": skill_id,
                "skill_name": req.get("name", skill_id),
                "verified_level": verified,
                "required_level": required,
                "gap": gap,
                "importance": req["importance"],
            })

    return gaps


def score_priorities(gaps: list[dict]) -> list[dict]:
    """
    Step 2: Priority Scorer
    priority = gap_size × 0.6 + role_importance × 0.4

    Normalizes gap (max 5) and importance (max 1.0) to [0,1] before scoring.
    """
    for g in gaps:
        role_for_scoring = g.get("role_key") or g.get("role_title") or ""
        onet_data = _load_taxonomy()
        normalized_gap = g["gap"] / 5.0  # max gap is 5
        g["relevance"] = classify_skill_relevance(g["skill_id"], role_for_scoring, onet_data)
        g["priority_score"] = compute_priority_score(
            skill=g["skill_id"],
            gap=normalized_gap,
            role=role_for_scoring,
            onet_data=onet_data,
        )

    filtered = [g for g in gaps if g.get("priority_score", 0.0) > 0.0]
    return sorted(filtered, key=lambda x: (x["priority_score"], x.get("importance", 0.0)), reverse=True)


def compute_learning_path_with_trace(
    verified_skills: dict,
    role: str,
    onet_data: dict,
) -> dict:
    """
    FEATURE 2: Compute learning path WITH reasoning trace.
    
    Returns dict with both pathway and reasoning_trace for frontend visualization.
    
    Returns:
        {
            "pathway": [...],
            "reasoning_trace": [...],
            "summary": {...}
        }
    """
    role_skills, importance_weights = _extract_role_skill_maps(role, onet_data)
    if not role_skills:
        return {"pathway": [], "reasoning_trace": [], "summary": {}}
    
    gaps: dict[str, dict] = {}
    reasoning_trace = []
    
    # Evaluate all skills in the role — this is the trace
    for skill, required_level in role_skills.items():
        current_level = int(verified_skills.get(skill, 0))
        gap = int(required_level) - current_level
        importance = float(importance_weights.get(skill, 0.5))
        relevance = classify_skill_relevance(skill, role, onet_data)
        relevance_score = RELEVANCE_TIERS.get(relevance, 0)
        
        # Calculate priority with new formula: gap×0.5 + importance×0.3 + relevance×0.2
        priority = round(
            (gap / 5.0) * 0.5 + importance * 0.3 + relevance_score * 0.2, 4
        )
        
        # Determine if skill is included in pathway
        included = gap > 0 and relevance != "irrelevant"
        
        # Add trace entry for EVERY skill evaluated
        reasoning_trace.append({
            "skill": skill,
            "current_level": current_level,
            "required_level": required_level,
            "gap": gap,
            "importance_weight": importance,
            "relevance_tier": relevance,
            "priority_score": priority,
            "included_in_path": included,
            "decision": (
                f"Included — {relevance} skill with gap of {gap}"
                if included
                else (
                    "Excluded — already at required level"
                    if gap <= 0
                    else f"Excluded — {relevance} skill not needed for role"
                )
            )
        })
        
        if included:
            gaps[skill] = {
                "gap": gap,
                "priority": priority,
                "relevance": relevance,
                "required_level": int(required_level),
                "current_level": current_level,
                "importance": importance,
            }
    
    if not gaps:
        return {
            "pathway": [],
            "reasoning_trace": reasoning_trace,
            "summary": {
                "total_evaluated": len(reasoning_trace),
                "in_pathway": 0,
                "excluded": len(reasoning_trace),
                "role": role,
                "formula": "priority = gap×0.5 + importance×0.3 + relevance×0.2"
            }
        }
    
    # Generate pathway
    preordered = sorted(gaps.keys(), key=lambda s: gaps[s]["priority"], reverse=True)
    ordered = topological_sort(preordered)
    
    role_label = role.replace("_", " ").title()
    pathway = []
    for position, skill in enumerate(ordered):
        data = gaps[skill]
        pathway.append({
            "skill": skill,
            "position": position + 1,
            "relevance": data["relevance"],
            "priority_score": data["priority"],
            "why": (
                f"You scored {data['current_level']}/5 in {skill} "
                f"but {role_label} requires {data['required_level']}/5 — "
                f"this is a {data['relevance']} skill for your role."
            ),
            "module": fetch_module(skill),
        })
    
    return {
        "pathway": pathway,
        "reasoning_trace": reasoning_trace,
        "summary": {
            "total_evaluated": len(reasoning_trace),
            "in_pathway": len(pathway),
            "excluded": len(reasoning_trace) - len(pathway),
            "role": role,
            "formula": "priority = gap×0.5 + importance×0.3 + relevance×0.2"
        }
    }


def compute_learning_path(
    verified_skills: dict,
    role: str,
    onet_data: dict,
) -> list[dict]:
    """
    Role-prioritized path builder used for explainability and testing.

    Return structure intentionally preserves keys expected by frontend/tests:
    skill, why, module
    """
    role_skills, _ = _extract_role_skill_maps(role, onet_data)
    if not role_skills:
        return []

    gaps: dict[str, dict] = {}
    for skill, required_level in role_skills.items():
        current_level = int(verified_skills.get(skill, 0))
        gap = int(required_level) - current_level
        if gap <= 0:
            continue

        relevance = classify_skill_relevance(skill, role, onet_data)
        priority = compute_priority_score(skill, gap / 5.0, role, onet_data)
        if priority <= 0.0:
            continue

        gaps[skill] = {
            "gap": gap,
            "priority": priority,
            "relevance": relevance,
            "required_level": int(required_level),
            "current_level": current_level,
        }

    if not gaps:
        return []

    # Relevance filtering happens before topological sort.
    preordered = sorted(gaps.keys(), key=lambda s: gaps[s]["priority"], reverse=True)
    ordered = topological_sort(preordered)

    role_label = role.replace("_", " ").title()
    path: list[dict] = []
    for skill in ordered:
        data = gaps[skill]
        path.append({
            "skill": skill,
            "relevance": data["relevance"],
            "priority_score": data["priority"],
            "why": (
                f"You scored {data['current_level']}/5 in {skill} "
                f"but {role_label} requires {data['required_level']}/5. "
                f"Gap: {data['gap']} level(s) to bridge. "
                f"This is a {data['relevance']} skill for your role."
            ),
            "module": fetch_module(skill),
        })

    return path


def topological_sort(skill_ids: list[str]) -> list[str]:
    """
    Step 3: Path Sequencer — Topological Sort
    Ensures prerequisites come before dependent skills.
    Uses Kahn's algorithm (BFS-based).
    """
    deps_data = _load_deps()
    dep_graph = deps_data.get("dependencies", {})

    # Build adjacency and in-degree for only the skills we care about
    skill_set = set(skill_ids)

    # Add prerequisites that are also in the gap set
    relevant_deps: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {s: 0 for s in skill_ids}

    for skill in skill_ids:
        prereqs = dep_graph.get(skill, [])
        relevant_prereqs = [p for p in prereqs if p in skill_set]
        relevant_deps[skill] = relevant_prereqs
        in_degree[skill] = len(relevant_prereqs)

    # Kahn's algorithm
    queue = deque([s for s in skill_ids if in_degree[s] == 0])
    sorted_skills = []

    while queue:
        current = queue.popleft()
        sorted_skills.append(current)

        for skill in skill_ids:
            if current in relevant_deps.get(skill, []):
                in_degree[skill] -= 1
                if in_degree[skill] == 0:
                    queue.append(skill)

    # If there are remaining skills (cycle), append them
    remaining = [s for s in skill_ids if s not in sorted_skills]
    sorted_skills.extend(remaining)

    return sorted_skills


def generate_pathway(
    verified_skills: dict[str, int],
    role_requirements: dict[str, dict],
    role_title: str,
) -> dict:
    """
    Full adaptive pathway generation pipeline:
    1. Calculate gaps
    2. Score priorities
    3. Topological sort for sequencing
    4. Generate modules with human-readable reasons

    Returns:
        {
            "role": str,
            "total_modules": int,
            "estimated_hours": int,
            "modules": [{
                "order": int,
                "skill_id": str,
                "skill_name": str,
                "current_level": int,
                "target_level": int,
                "gap": int,
                "priority_score": float,
                "estimated_hours": int,
                "reason": str,
                "resources": [str]
            }]
        }
    """
    taxonomy = _load_taxonomy()

    # Step 0: resolve role key for relevance-aware scoring
    role_key = _normalize_role_key(role_title, taxonomy) or role_title

    # Step 1: Calculate gaps
    gaps = calculate_gaps(verified_skills, role_requirements)
    for g in gaps:
        g["role_key"] = role_key
        g["role_title"] = role_title

    if not gaps:
        return {
            "role": role_title,
            "total_modules": 0,
            "estimated_hours": 0,
            "modules": [],
            "message": "Congratulations! You already meet all competency requirements for this role.",
        }

    # Step 2: Score priorities
    scored_gaps = score_priorities(gaps)

    # Step 3: Topological sort (after relevance filtering)
    skill_order = topological_sort([g["skill_id"] for g in scored_gaps])

    # Build module list in topological order, preserving priority info
    gap_map = {g["skill_id"]: g for g in scored_gaps}
    modules = []

    for order, skill_id in enumerate(skill_order, 1):
        g = gap_map[skill_id]
        skill_info = taxonomy["skills"].get(skill_id, {})

        # Estimate hours: gap × 4 hours per level
        est_hours = g["gap"] * 4

        # Human-readable reason
        reason = (
            f"You scored {g['verified_level']}/5 in {g['skill_name']} "
            f"but {role_title} requires {g['required_level']}/5. "
            f"Gap: {g['gap']} level(s) to bridge."
        )

        # Suggest resources based on skill category
        resources = _suggest_resources(skill_id, skill_info, g["verified_level"])

        modules.append({
            "order": order,
            "skill_id": skill_id,
            "skill_name": g["skill_name"],
            "current_level": g["verified_level"],
            "target_level": g["required_level"],
            "gap": g["gap"],
            "priority_score": g["priority_score"],
            "relevance": g.get("relevance", "important"),
            "estimated_hours": est_hours,
            "reason": reason + f" Relevance: {g.get('relevance', 'important')}.",
            "resources": resources,
        })

    total_hours = sum(m["estimated_hours"] for m in modules)

    return {
        "role": role_title,
        "total_modules": len(modules),
        "estimated_hours": total_hours,
        "modules": modules,
    }


def _suggest_resources(
    skill_id: str, skill_info: dict, current_level: int
) -> list[str]:
    """Generate suggested learning resources based on skill and level."""
    name = skill_info.get("name", skill_id)
    resources = []

    if current_level <= 1:
        resources.append(f"📖 Official {name} documentation — Getting Started guide")
        resources.append(f"🎥 {name} crash course for beginners (YouTube)")
        resources.append(f"💻 Interactive {name} tutorial on freeCodeCamp")
    elif current_level <= 3:
        resources.append(f"📖 {name} intermediate concepts & best practices")
        resources.append(f"🛠️ Build a project using {name}")
        resources.append(f"📝 {name} practice exercises on LeetCode/HackerRank")
    else:
        resources.append(f"📖 Advanced {name} patterns & architecture")
        resources.append(f"🏗️ Contribute to open-source {name} projects")
        resources.append(f"📊 {name} performance optimization techniques")

    return resources
