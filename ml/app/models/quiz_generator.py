"""
Quiz Generator
==============
Rule-based MCQ generator using TF-IDF on O*NET skill descriptions.
Generates diagnostic quiz questions to verify claimed skill levels.
"""

import json
import random
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


# Question templates per skill — curated diagnostic questions
QUESTION_BANK: dict[str, list[dict]] = {
    "python": [
        {
            "question": "What is the output of `print(type([]) is list)`?",
            "options": ["True", "False", "Error", "None"],
            "correct": 0, "difficulty": 1,
        },
        {
            "question": "Which keyword is used to create a generator function in Python?",
            "options": ["generate", "yield", "return", "iter"],
            "correct": 1, "difficulty": 2,
        },
        {
            "question": "What does the `@staticmethod` decorator do?",
            "options": [
                "Makes a method that doesn't receive the class or instance as first argument",
                "Makes a method that runs at compile time",
                "Makes a method that cannot be overridden",
                "Makes a method that is called only once"
            ],
            "correct": 0, "difficulty": 3,
        },
        {
            "question": "What is the time complexity of lookup in a Python dictionary?",
            "options": ["O(n)", "O(log n)", "O(1) amortized", "O(n log n)"],
            "correct": 2, "difficulty": 3,
        },
        {
            "question": "Which of the following correctly implements a context manager?",
            "options": [
                "Define __enter__ and __exit__ methods",
                "Define __init__ and __del__ methods",
                "Define __start__ and __stop__ methods",
                "Define __open__ and __close__ methods"
            ],
            "correct": 0, "difficulty": 4,
        },
    ],
    "javascript": [
        {
            "question": "What is the output of `typeof null`?",
            "options": ["'null'", "'undefined'", "'object'", "'boolean'"],
            "correct": 2, "difficulty": 2,
        },
        {
            "question": "What does `===` do differently from `==`?",
            "options": [
                "No difference",
                "Checks type and value without coercion",
                "Only checks type",
                "Checks reference equality"
            ],
            "correct": 1, "difficulty": 1,
        },
        {
            "question": "What is a closure in JavaScript?",
            "options": [
                "A function that has access to variables from its outer scope",
                "A way to close a browser window",
                "A method to end a loop",
                "A type of error handling"
            ],
            "correct": 0, "difficulty": 3,
        },
        {
            "question": "What does `Promise.all()` return if one promise rejects?",
            "options": [
                "All resolved values",
                "Only the rejected promise",
                "It rejects with the first rejection reason",
                "An array of mixed results"
            ],
            "correct": 2, "difficulty": 3,
        },
    ],
    "typescript": [
        {
            "question": "What is the purpose of TypeScript's `interface`?",
            "options": [
                "To define the shape of an object",
                "To create a new class",
                "To handle errors",
                "To import modules"
            ],
            "correct": 0, "difficulty": 1,
        },
        {
            "question": "What does `keyof` operator do in TypeScript?",
            "options": [
                "Creates a new object key",
                "Returns a union of all property names of a type",
                "Deletes a key from an object",
                "Checks if a key exists"
            ],
            "correct": 1, "difficulty": 3,
        },
    ],
    "react": [
        {
            "question": "What hook is used for side effects in React?",
            "options": ["useState", "useEffect", "useContext", "useMemo"],
            "correct": 1, "difficulty": 1,
        },
        {
            "question": "What is the virtual DOM?",
            "options": [
                "A lightweight copy of the real DOM for efficient updates",
                "A hidden DOM element",
                "A server-side rendering technique",
                "A CSS optimization"
            ],
            "correct": 0, "difficulty": 2,
        },
        {
            "question": "When should you use `useMemo`?",
            "options": [
                "To memoize expensive computations and avoid re-calculation",
                "To create mutable state",
                "To replace useEffect",
                "To handle form submissions"
            ],
            "correct": 0, "difficulty": 3,
        },
    ],
    "sql": [
        {
            "question": "What SQL clause is used to filter grouped results?",
            "options": ["WHERE", "HAVING", "FILTER", "GROUP BY"],
            "correct": 1, "difficulty": 2,
        },
        {
            "question": "What is a LEFT JOIN?",
            "options": [
                "Returns all rows from the left table and matching rows from the right",
                "Returns only matching rows from both tables",
                "Returns all rows from the right table",
                "Returns rows not in the right table"
            ],
            "correct": 0, "difficulty": 2,
        },
        {
            "question": "What does ACID stand for in database transactions?",
            "options": [
                "Atomicity, Consistency, Isolation, Durability",
                "Authentication, Control, Identity, Data",
                "Access, Cache, Index, Deploy",
                "Aggregate, Count, Insert, Delete"
            ],
            "correct": 0, "difficulty": 3,
        },
    ],
    "fastapi": [
        {
            "question": "How do you define a path parameter in FastAPI?",
            "options": [
                "Using curly braces in the path: /items/{item_id}",
                "Using query string: /items?id=1",
                "Using headers",
                "Using cookies"
            ],
            "correct": 0, "difficulty": 1,
        },
        {
            "question": "What does `Depends()` do in FastAPI?",
            "options": [
                "Implements dependency injection",
                "Creates a database connection",
                "Handles errors",
                "Validates input"
            ],
            "correct": 0, "difficulty": 2,
        },
    ],
    "docker": [
        {
            "question": "What is the difference between `CMD` and `ENTRYPOINT` in a Dockerfile?",
            "options": [
                "CMD provides defaults that can be overridden; ENTRYPOINT always runs",
                "No difference",
                "CMD runs at build time; ENTRYPOINT at runtime",
                "ENTRYPOINT is deprecated"
            ],
            "correct": 0, "difficulty": 3,
        },
        {
            "question": "What does `docker-compose up -d` do?",
            "options": [
                "Starts services in detached (background) mode",
                "Deletes all containers",
                "Downloads images",
                "Debugs containers"
            ],
            "correct": 0, "difficulty": 1,
        },
    ],
    "git": [
        {
            "question": "What does `git rebase` do?",
            "options": [
                "Re-applies commits on top of another base tip",
                "Deletes a branch",
                "Creates a new repository",
                "Merges two branches with a merge commit"
            ],
            "correct": 0, "difficulty": 3,
        },
    ],
    "machine_learning": [
        {
            "question": "What is overfitting?",
            "options": [
                "Model performs well on training data but poorly on unseen data",
                "Model performs poorly on all data",
                "Model takes too long to train",
                "Model uses too much memory"
            ],
            "correct": 0, "difficulty": 2,
        },
        {
            "question": "What is the purpose of a validation set?",
            "options": [
                "To tune hyperparameters and evaluate model during training",
                "To train the model",
                "To deploy the model",
                "To collect more data"
            ],
            "correct": 0, "difficulty": 2,
        },
    ],
    "rest_api": [
        {
            "question": "Which HTTP method is idempotent?",
            "options": ["POST", "PUT", "PATCH", "None of the above"],
            "correct": 1, "difficulty": 2,
        },
        {
            "question": "What status code indicates a resource was created?",
            "options": ["200", "201", "204", "301"],
            "correct": 1, "difficulty": 1,
        },
    ],
    "html_css": [
        {
            "question": "What does `display: flex` do?",
            "options": [
                "Creates a flex container for 1D layout",
                "Hides the element",
                "Makes element fixed position",
                "Adds animation"
            ],
            "correct": 0, "difficulty": 1,
        },
    ],
    "postgresql": [
        {
            "question": "What is a CTE (Common Table Expression)?",
            "options": [
                "A named temporary result set defined with WITH clause",
                "A type of index",
                "A stored procedure",
                "A database trigger"
            ],
            "correct": 0, "difficulty": 3,
        },
    ],
    "testing": [
        {
            "question": "What is the purpose of mocking in unit tests?",
            "options": [
                "To simulate dependencies so you test units in isolation",
                "To make tests run faster",
                "To skip certain tests",
                "To generate test data"
            ],
            "correct": 0, "difficulty": 2,
        },
    ],
    "data_analysis": [
        {
            "question": "What pandas method combines DataFrames on a common column?",
            "options": ["concat()", "merge()", "append()", "stack()"],
            "correct": 1, "difficulty": 2,
        },
    ],
    "deep_learning": [
        {
            "question": "What activation function is commonly used in hidden layers of deep networks?",
            "options": ["Sigmoid", "ReLU", "Softmax", "Linear"],
            "correct": 1, "difficulty": 2,
        },
    ],
    "aws": [
        {
            "question": "What AWS service provides serverless compute?",
            "options": ["EC2", "Lambda", "S3", "RDS"],
            "correct": 1, "difficulty": 1,
        },
    ],
    "nextjs": [
        {
            "question": "What rendering method does Next.js use by default for pages?",
            "options": [
                "Server-side rendering",
                "Static site generation",
                "Client-side rendering",
                "Incremental static regeneration"
            ],
            "correct": 0, "difficulty": 2,
        },
    ],
    "nodejs": [
        {
            "question": "What is the event loop in Node.js?",
            "options": [
                "A mechanism that handles async operations by queuing callbacks",
                "A type of for-loop",
                "A debugging tool",
                "A package manager feature"
            ],
            "correct": 0, "difficulty": 2,
        },
    ],
    "redis": [
        {
            "question": "What data structure does Redis primarily use?",
            "options": [
                "Key-value pairs (in-memory)",
                "Relational tables",
                "Document collections",
                "Graph nodes"
            ],
            "correct": 0, "difficulty": 1,
        },
    ],
}


def generate_quiz(
    skill_ids: list[str],
    questions_per_skill: int = 2,
    max_questions: int = 10,
    experience_years: int | None = None,
    claimed_levels: dict[str, int] | None = None,
) -> dict:
    """
    Generate a diagnostic quiz for the given skills.

    Returns:
        {
            "quiz_id": str,
            "questions": [{
                "id": str,
                "skill_id": str,
                "skill_name": str,
                "question": str,
                "options": [str],
                "correct_index": int,
                "difficulty": int
            }],
            "total_questions": int
        }
    """
    taxonomy = _load_taxonomy()
    questions = []
    q_id = 0
    claimed_levels = claimed_levels or {}

    if experience_years is None:
        min_diff, max_diff = 1, 4
        target_diff = 2
    elif experience_years <= 1:
        min_diff, max_diff = 1, 2
        target_diff = 2
    elif experience_years <= 4:
        min_diff, max_diff = 2, 3
        target_diff = 3
    else:
        min_diff, max_diff = 3, 5
        target_diff = 4

    for skill_id in skill_ids:
        bank = QUESTION_BANK.get(skill_id, [])
        if not bank:
            continue

        # Adapt difficulty by both overall experience and claimed skill level.
        skill_target = claimed_levels.get(skill_id)
        if isinstance(skill_target, int):
            target = max(1, min(5, round((target_diff + skill_target) / 2)))
        else:
            target = target_diff

        in_band = [q for q in bank if min_diff <= q["difficulty"] <= max_diff]
        candidate_pool = in_band if in_band else list(bank)
        random.shuffle(candidate_pool)
        candidate_pool.sort(key=lambda q: abs(q["difficulty"] - target))
        selected = candidate_pool[: min(questions_per_skill, len(candidate_pool))]

        for q in selected:
            skill_name = taxonomy["skills"].get(skill_id, {}).get("name", skill_id)
            questions.append({
                "id": f"q_{q_id}",
                "skill_id": skill_id,
                "skill_name": skill_name,
                "question": q["question"],
                "options": q["options"],
                "correct_index": q["correct"],
                "difficulty": q["difficulty"],
            })
            q_id += 1

    # Cap at max_questions, preferring diversity across skills.
    if len(questions) > max_questions:
        random.shuffle(questions)
        questions = questions[:max_questions]

    quiz_id = f"quiz_{''.join(random.choices('abcdef0123456789', k=8))}"

    return {
        "quiz_id": quiz_id,
        "questions": questions,
        "total_questions": len(questions),
    }


def grade_quiz(questions: list[dict], answers: dict[str, int]) -> dict:
    """
    Grade quiz responses and return verified skill levels.

    Args:
        questions: The generated quiz questions
        answers: Map of question_id -> selected_option_index

    Returns:
        {
            "total_score": int,
            "max_score": int,
            "skill_scores": {
                "skill_id": {"correct": int, "total": int, "verified_level": int}
            }
        }
    """
    skill_results: dict[str, dict] = {}

    for q in questions:
        sid = q["skill_id"]
        if sid not in skill_results:
            skill_results[sid] = {"correct": 0, "total": 0, "difficulty_sum": 0}

        skill_results[sid]["total"] += 1
        user_answer = answers.get(q["id"])
        if user_answer == q["correct_index"]:
            skill_results[sid]["correct"] += 1
            skill_results[sid]["difficulty_sum"] += q["difficulty"]

    total_correct = sum(r["correct"] for r in skill_results.values())
    total_questions = sum(r["total"] for r in skill_results.values())

    skill_scores = {}
    for sid, result in skill_results.items():
        if result["total"] == 0:
            verified_level = 1
        else:
            accuracy = result["correct"] / result["total"]
            avg_difficulty = (
                result["difficulty_sum"] / result["correct"]
                if result["correct"] > 0
                else 1
            )
            # Level = accuracy × avg_difficulty, capped at 5
            verified_level = min(5, max(1, round(accuracy * avg_difficulty)))

        skill_scores[sid] = {
            "correct": result["correct"],
            "total": result["total"],
            "verified_level": verified_level,
        }

    return {
        "total_score": total_correct,
        "max_score": total_questions,
        "skill_scores": skill_scores,
    }
