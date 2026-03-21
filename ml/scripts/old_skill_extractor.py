"""
Skill Extractor Model
=====================
Simulates a fine-tuned BERT NER model (Devlin et al., 2018) for extracting
skills from resume text. Uses keyword matching as a lightweight proxy.

In production, this would load a fine-tuned bert-base-uncased model
trained on the Kaggle Resume Dataset for Named Entity Recognition.
"""

import json
import re
from pathlib import Path
from typing import Pattern

from app.models.adaptive_engine import classify_skill_relevance


# Load O*NET skills taxonomy
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ONET_PATH = DATA_DIR / "onet_skills.json"

_taxonomy = None

CHUNK_WORDS = 400
CHUNK_OVERLAP = 80
MIN_BERT_CONFIDENCE = 0.75
FALLBACK_MIN_SKILLS_TRIGGER = 4
MAX_RETURN_SKILLS = 10

# Ambiguous skills that need at least 2 mentions to avoid false positives.
AMBIGUOUS_SKILLS = {
    "java",
    "go",
    "r",
    "c",
    "scala",
    "rust",
    "swift",
    "ruby",
    "perl",
}

# Normalization map for common resume variants.
# Example: ReactJS -> react, NodeJS -> node.js
SKILL_ALIASES: dict[str, str] = {
    "reactjs": "react",
    "react js": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node js": "node.js",
    "node-js": "node.js",
    "nextjs": "next.js",
    "next js": "next.js",
    "ts": "typescript",
    "js": "javascript",
    "py": "python",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "postgres sql": "postgresql",
    "tailwind": "tailwindcss",
    "tailwind css": "tailwindcss",
    "tailwind_css": "tailwindcss",
    "fast api": "fastapi",
    "scikit learn": "scikit-learn",
    "power bi": "power_bi",
    "machine learning": "machine_learning",
    "machine learning basics": "machine_learning",
    "ml basics": "machine_learning",
    "data analysis": "data_analysis",
    "project management": "project_management",
    "rest api design": "rest_api",
    "rest api": "rest_api",
    "restful api": "rest_api",
    "restful": "rest_api",
    "html & css": "html_css",
    "html and css": "html_css",
    "html, css": "html_css",
    "html/css": "html_css",
    "css": "html_css",
    "agile methodologies": "agile",
    "agile teams": "agile",
    "agile methodology": "agile",
    "scrum methodology": "scrum",
    "amazon web services": "aws",
    "aws lambda": "aws",
    "node": "nodejs",
    "node.js": "nodejs",
    "sklearn": "scikit_learn",
    "sci-kit learn": "scikit_learn",
    "tensorflow / keras": "tensorflow",
    "tensorflow/keras": "tensorflow",
    "keras (lstm)": "keras",
    "tensorflow keras": "tensorflow",
    "lstm": "keras",
    "expressjs": "expressjs",
    "express js": "expressjs",
    "angularjs": "angular",
    "angular.js": "angular",
    "vuejs": "vue",
    "vue.js": "vue",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "dynamo db": "dynamodb",
    "elastic search": "elasticsearch",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "ci/cd": "ci_cd",
    "ci cd": "ci_cd",
    "github actions": "github_actions",
    "powerbi": "power_bi",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "git/github": "git",
    "git / github": "git",
    "github": "git",
    "ml": "machine_learning",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "jira software": "jira",
}

SKILL_KEYWORDS: dict[str, list[str]] = {
    "python": ["python", "py", "python3"],
    "javascript": ["javascript", "js", "es6", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java", "jdk", "jvm"],
    "sql": ["sql", "mysql", "sqlite", "postgres", "postgresql"],
    "html_css": ["html", "css", "html5", "css3", "scss", "sass"],
    "react": ["react", "reactjs", "react.js"],
    "nextjs": ["next.js", "nextjs", "next"],
    "nodejs": ["node.js", "nodejs", "node", "express", "express.js"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mongodb": ["mongodb", "mongo", "mongoose"],
    "docker": ["docker", "dockerfile", "docker-compose"],
    "kubernetes": ["kubernetes", "k8s", "kubectl"],
    "git": ["git", "github", "gitlab", "bitbucket"],
    "ci_cd": ["ci/cd", "jenkins", "github actions", "gitlab ci", "circleci"],
    "machine_learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
    "deep_learning": ["deep learning", "neural network", "tensorflow", "pytorch", "keras"],
    "nlp": ["nlp", "natural language", "bert", "gpt", "transformers", "hugging face"],
    "data_analysis": ["data analysis", "pandas", "numpy", "matplotlib", "data science"],
    "rest_api": ["rest", "restful", "api", "rest api"],
    "graphql": ["graphql"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "testing": ["testing", "unit test", "pytest", "jest", "selenium", "cypress"],
    "agile": ["agile", "scrum", "kanban", "sprint"],
    "system_design": ["system design", "architecture", "microservices"],
    "redis": ["redis"],
    "tailwindcss": ["tailwind", "tailwindcss", "tailwind css"],
    "linux": ["linux", "ubuntu", "debian", "centos"],
    "excel": ["excel", "microsoft excel", "spreadsheets"],
    "tableau": ["tableau"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "statistics": ["statistics", "statistical analysis"],
    "power_bi": ["power bi", "powerbi"],
    "r": ["r", "r language", "r programming"],
    "communication": ["communication", "stakeholder communication", "presentation"],
    "scrum": ["scrum", "scrum master"],
    "project_management": ["project management", "project planning", "roadmap"],
    "leadership": ["leadership", "team leadership", "mentoring"],
    "jira": ["jira", "atlassian jira"],
    "figma": ["figma"],
    "vue": ["vue", "vue.js", "vuejs"],
    "webpack": ["webpack"],
    "expressjs": ["express.js", "expressjs", "express js", "express"],
    "spring": ["spring", "spring boot"],
    "laravel": ["laravel"],
    "rails": ["rails", "ruby on rails"],
    "grpc": ["grpc", "g-rpc"],
    "angular": ["angular", "angularjs", "angular.js"],
    "svelte": ["svelte"],
    "babel": ["babel"],
    "scikit_learn": ["scikit-learn", "scikit learn", "sklearn"],
    "tensorflow": ["tensorflow", "tf"],
    "keras": ["keras", "lstm"],
    "pytorch": ["pytorch", "torch"],
    "matplotlib": ["matplotlib"],
    "seaborn": ["seaborn"],
    "scipy": ["scipy"],
    "xgboost": ["xgboost"],
    "lightgbm": ["lightgbm"],
    "nltk": ["nltk"],
    "spacy": ["spacy"],
    "opencv": ["opencv", "cv2"],
    "huggingface": ["huggingface", "hugging face"],
    "transformers": ["transformers"],
    "jupyter": ["jupyter", "jupyter notebook"],
    "colab": ["colab", "google colab"],
    "mlflow": ["mlflow"],
    "airflow": ["airflow", "apache airflow"],
    "spark": ["spark", "apache spark", "pyspark"],
    "hadoop": ["hadoop"],
    "kafka": ["kafka", "apache kafka"],
    "dbt": ["dbt", "data build tool"],
    "snowflake": ["snowflake"],
    "bigquery": ["bigquery", "big query"],
    "redshift": ["redshift"],
    "hive": ["hive", "apache hive"],
    "flink": ["flink", "apache flink"],
    "mysql": ["mysql"],
    "firebase": ["firebase"],
    "dynamodb": ["dynamodb", "dynamo db"],
    "cassandra": ["cassandra", "apache cassandra"],
    "neo4j": ["neo4j"],
    "elasticsearch": ["elasticsearch", "elastic search"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "terraform": ["terraform"],
    "ansible": ["ansible"],
    "jenkins": ["jenkins"],
    "github_actions": ["github actions"],
    "nginx": ["nginx"],
    "prometheus": ["prometheus"],
    "grafana": ["grafana"],
    "looker": ["looker"],
    "google_analytics": ["google analytics"],
    "confluence": ["confluence"],
    "postman": ["postman"],
    "swagger": ["swagger", "openapi"],
    "pytest": ["pytest"],
    "jest": ["jest"],
    "selenium": ["selenium"],
    "cypress": ["cypress"],
    "problem_solving": ["problem solving", "problem-solving"],
    "vscode": ["vscode", "vs code", "visual studio code"],
    "bash": ["bash", "shell scripting"],
}

KNOWN_SKILLS: set[str] = set(SKILL_KEYWORDS.keys()) | {
    "node.js",
    "next.js",
    "tailwind_css",
    "express.js",
    "scikit-learn",
}


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
    """
    Detect domain dynamically from role-skill overlap scoring.

    Scoring priority:
    1) Highest weighted overlap with role profiles
    2) Selected role as tie-breaker and zero-overlap fallback
    3) Category-based fallback
    """
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

        # Blend weighted overlap and breadth of overlap.
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

    # Selected role fallback when overlap is weak or tied at zero.
    if selected_role_key and selected_role_key in roles:
        return roles[selected_role_key].get("title", selected_role_key)

    # Last fallback: infer from extracted categories.
    category_counts: dict[str, int] = {}
    for s in extracted:
        cat = s.get("category", "")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    return max(category_counts, key=category_counts.get) if category_counts else "General"


def _load_taxonomy() -> dict:
    global _taxonomy
    if _taxonomy is None:
        # Try local data dir first, then mounted volume
        for path in [ONET_PATH, Path("/app/data/onet_skills.json")]:
            if path.exists():
                with open(path) as f:
                    _taxonomy = json.load(f)
                return _taxonomy
        raise FileNotFoundError("onet_skills.json not found")
    return _taxonomy


def _normalize_phrase(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9+.#/\-\s]", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return SKILL_ALIASES.get(normalized, normalized)


def _split_into_chunks(text: str, chunk_words: int = CHUNK_WORDS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []

    if len(words) <= chunk_words:
        return [text]

    step = max(1, chunk_words - overlap)
    chunks = []
    for i in range(0, len(words), step):
        part = words[i:i + chunk_words]
        if not part:
            continue
        chunks.append(" ".join(part))
        if i + chunk_words >= len(words):
            break
    return chunks


def _alias_pattern(alias: str) -> Pattern[str]:
    # Allow lightweight punctuation/spacing variations while keeping whole-word matching.
    tokens = [re.escape(tok) for tok in re.split(r"\s+", alias.strip()) if tok]
    joined = r"[\s\-._/]*".join(tokens) if tokens else re.escape(alias)
    return re.compile(rf"(?<![a-z0-9]){joined}(?![a-z0-9])", re.IGNORECASE)


def _build_skill_patterns() -> dict[str, list[Pattern[str]]]:
    patterns: dict[str, list[Pattern[str]]] = {}

    normalized_base: dict[str, set[str]] = {}
    for skill_id, aliases in SKILL_KEYWORDS.items():
        normalized_base[skill_id] = {_normalize_phrase(a) for a in aliases}

    for skill_id, aliases in SKILL_KEYWORDS.items():
        expanded = {a.lower().strip() for a in aliases}
        for variant, canonical in SKILL_ALIASES.items():
            if _normalize_phrase(canonical) in normalized_base[skill_id]:
                # Keep the raw variant for explicit matching (e.g., reactjs, nodejs)
                expanded.add(variant.lower().strip())
                # Also keep normalized form for canonical matching.
                expanded.add(_normalize_phrase(variant))

        patterns[skill_id] = [_alias_pattern(a) for a in sorted(expanded) if a]

    return patterns


def _extract_years_near_text(text: str) -> int | None:
    match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _estimate_confidence(mentions: int, context_text: str) -> float:
    """Estimate extraction confidence in a BERT-like range [0, 1]."""
    lowered = context_text.lower()
    confidence = 0.5 + min(0.36, mentions * 0.12)

    confidence_terms = [
        "expert",
        "senior",
        "advanced",
        "proficient",
        "developed",
        "implemented",
        "built",
    ]
    if any(term in lowered for term in confidence_terms):
        confidence += 0.06

    return max(0.0, min(0.99, round(confidence, 3)))


def _fallback_min_mentions(skill_id: str) -> int:
    return 2 if skill_id in AMBIGUOUS_SKILLS else 1


LEVEL_PATTERNS = {
    5: ["expert", "lead", "architect", "principal", "10+ years", "9+ years", "8+ years"],
    4: ["advanced", "senior", "proficient", "7+ years", "6+ years", "5+ years"],
    3: ["intermediate", "3+ years", "4+ years", "experienced"],
    2: ["familiar", "basic", "fundamental", "1+ year", "2+ years", "exposure", "basics"],
    1: ["beginner", "learning", "studying", "intern", "fresher"],
}


def _estimate_experience(resume_text: str) -> int | str:
    text_lower = resume_text.lower()
    years = _extract_overall_experience_years(text_lower)
    if years is None:
        return "Not detected"
    return years


def estimate_level(skill: str, resume_text: str) -> int:
    text_lower = resume_text.lower()

    # Step 1: Global experience years from resume.
    global_exp = _estimate_experience(resume_text)
    try:
        exp_years = int(str(global_exp).replace("+", "").strip())
    except Exception:
        exp_years = 0

    # Step 2: Base level from global experience.
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

    # Step 3: Find skill mention in resume.
    skill_pos = text_lower.find(skill.lower())
    if skill_pos == -1:
        return max(1, min(5, base_level))

    # Step 4: Check sentence-scoped context around skill mention.
    left = text_lower.rfind(".", 0, skill_pos)
    right = text_lower.find(".", skill_pos)
    if left == -1:
        left = 0
    else:
        left += 1
    if right == -1:
        right = len(text_lower)
    context = text_lower[left:right]

    # Step 5: Explicit level keywords in context.
    for level, keywords in sorted(LEVEL_PATTERNS.items(), reverse=True):
        for keyword in keywords:
            if keyword in context:
                return int(max(1, min(5, level)))

    # Step 6: "familiar with X" -> level 2.
    familiar_pattern = rf"familiar with[^.]*{re.escape(skill.lower())}"
    if re.search(familiar_pattern, text_lower):
        return 2

    # Step 7: "proficient in X" -> level 4.
    proficient_pattern = rf"proficient in[^.]*{re.escape(skill.lower())}"
    if re.search(proficient_pattern, text_lower):
        return 4

    # Step 8: Fall back to base level.
    return int(max(1, min(5, base_level)))


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


def extract_skills(resume_text: str, role: str | None = None) -> dict:
    """
    Extract skills from resume text.

    Returns:
        {
            "skills": [{"skill_id": str, "name": str, "level": int, "category": str}],
            "experience_years": int | None,
            "domain": str
        }
    """
    taxonomy = _load_taxonomy()
    text_lower = resume_text.lower()
    skill_patterns = _build_skill_patterns()
    role_required_ids = _get_role_required_skill_ids(role, taxonomy)
    role_importance = _get_role_importance_map(role, taxonomy)

    # Fix 1: Chunking (400 words with overlap) to mimic BERT window processing.
    chunks = _split_into_chunks(resume_text)

    bert_aggregated: dict[str, dict] = {}

    # Pass 1 (BERT-like chunked extraction).
    for chunk in chunks:
        chunk_lower = chunk.lower()
        for skill_id, patterns in skill_patterns.items():
            if skill_id not in taxonomy["skills"]:
                continue
            mentions = 0
            snippets = []
            for pattern in patterns:
                for match in pattern.finditer(chunk_lower):
                    mentions += 1
                    start = max(0, match.start() - 80)
                    end = min(len(chunk_lower), match.end() + 80)
                    snippets.append(chunk_lower[start:end])

            if mentions == 0:
                continue

            info = bert_aggregated.setdefault(skill_id, {"mentions": 0, "contexts": []})
            info["mentions"] += mentions
            info["contexts"].extend(snippets)

    aggregated: dict[str, dict] = {}
    raw_bert_ids: set[str] = set()

    for skill_id, info in bert_aggregated.items():
        contexts = info.get("contexts", [])
        context_text = " ".join(contexts)
        confidence = _estimate_confidence(info.get("mentions", 0), context_text)
        if confidence >= MIN_BERT_CONFIDENCE:
            aggregated[skill_id] = {
                "mentions": info.get("mentions", 0),
                "contexts": contexts,
                "confidence": confidence,
            }
            raw_bert_ids.add(skill_id)

    # Run fallback when BERT found few skills OR when role-required skills are missing.
    missing_role_skills = role_required_ids.difference(aggregated.keys())
    if len(aggregated) < FALLBACK_MIN_SKILLS_TRIGGER or missing_role_skills:
        for skill_id, patterns in skill_patterns.items():
            if skill_id not in taxonomy["skills"]:
                continue
            mentions = 0
            snippets = []
            for pattern in patterns:
                for match in pattern.finditer(text_lower):
                    mentions += 1
                    start = max(0, match.start() - 80)
                    end = min(len(text_lower), match.end() + 80)
                    snippets.append(text_lower[start:end])

            if mentions < _fallback_min_mentions(skill_id):
                continue

            context_text = " ".join(snippets)
            fallback_confidence = _estimate_confidence(mentions, context_text)

            if skill_id not in aggregated:
                aggregated[skill_id] = {
                    "mentions": mentions,
                    "contexts": snippets,
                    "confidence": fallback_confidence,
                }
                continue

            existing = aggregated[skill_id]
            existing["mentions"] = max(existing.get("mentions", 0), mentions)
            existing_contexts = existing.get("contexts", [])
            existing["contexts"] = existing_contexts + snippets
            existing["confidence"] = max(existing.get("confidence", 0.0), fallback_confidence)

    aggregated = _apply_role_aware_cap(aggregated, role, taxonomy, cap=MAX_RETURN_SKILLS)

    exp_years = _extract_overall_experience_years(text_lower)

    # Fix 4: Estimate skill levels from context keywords + local years around mentions.
    skill_experience: dict[str, int] = {}
    extracted = []
    for skill_id, info in aggregated.items():
        contexts = info.get("contexts", [])
        joined_context = " ".join(contexts)

        local_years: list[int] = []
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

    # Fix 3: Validate against O*NET skill IDs loaded once at module import time.
    if ONET_SKILL_IDS:
        validated = [s for s in extracted if s["skill_id"] in ONET_SKILL_IDS]
        if validated:
            extracted = validated
        elif raw_bert_ids:
            raw_bert = [s for s in extracted if s["skill_id"] in raw_bert_ids]
            if raw_bert:
                extracted = raw_bert[:MAX_RETURN_SKILLS]

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
