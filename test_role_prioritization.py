from pathlib import Path
import json

from ml.app.models.adaptive_engine import (
    compute_learning_path,
    classify_skill_relevance,
)

ONET_PATH = Path(__file__).parent / "data" / "onet_skills.json"

with open(ONET_PATH, encoding="utf-8") as f:
    onet_data = json.load(f)

# Test 1 — React is irrelevant for data_engineer
relevance = classify_skill_relevance("react", "data_engineer", onet_data)
assert relevance == "irrelevant", "React should be irrelevant for data_engineer"
print("Test 1 PASS - react correctly marked irrelevant")

# Test 2 — SQL is critical for data_engineer
relevance = classify_skill_relevance("sql", "data_engineer", onet_data)
assert relevance == "critical", "SQL should be critical for data_engineer"
print("Test 2 PASS - sql correctly marked critical")

# Test 3 — Irrelevant skills excluded from pathway
skills = {"react": 4, "sql": 1, "python": 2}
path = compute_learning_path(skills, "data_engineer", onet_data)
path_skills = [m["skill"] for m in path]
assert "react" not in path_skills, "React should not appear in data_engineer pathway"
assert "sql" in path_skills, "SQL must appear in data_engineer pathway"
print("Test 3 PASS - irrelevant skills excluded from pathway")

# Test 4 — Critical skills appear before peripheral ones
critical = [m for m in path if m["relevance"] == "critical"]
peripheral = [m for m in path if m["relevance"] == "peripheral"]
if critical and peripheral:
    assert (
        path.index(critical[0]) < path.index(peripheral[0])
    ), "Critical skills should come before peripheral"
    print("Test 4 PASS - critical skills ordered first")

# Test 5 — Every module has a why with relevance mentioned
for module in path:
    assert "why" in module, f"Missing why for {module['skill']}"
    assert module["relevance"] in module["why"], "Relevance not mentioned in why"
print("Test 5 PASS - all modules have relevance in reasoning")

print("All prioritization tests passed!")
