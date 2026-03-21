import json
from pathlib import Path

try:
    import pytest
except Exception:  # pragma: no cover
    pytest = None

from app.models.skill_extractor import extract_skills
from app.models.adaptive_engine import classify_skill_relevance

ONET_PATH = Path(__file__).resolve().parents[2] / "data" / "onet_skills.json"
with open(ONET_PATH, encoding="utf-8") as f:
    onet_data = json.load(f)

TEST_CASES = {
    "backend_engineer": {
        "resume": "Python developer with FastAPI, PostgreSQL, Docker, AWS, Git, REST API, agile teams",
        "must_have": ["python", "fastapi", "postgresql", "docker", "git"],
        "critical": ["python", "fastapi", "rest_api"],
        "irrelevant": ["react", "tableau", "figma"],
    },
    "frontend_engineer": {
        "resume": "React developer skilled in TypeScript, Next.js, HTML CSS, Tailwind CSS, Git, Figma",
        "must_have": ["react", "typescript", "html_css", "git"],
        "critical": ["javascript", "react", "html_css"],
        "irrelevant": ["tensorflow", "docker", "spark"],
    },
    "data_analyst": {
        "resume": "Data analyst with SQL, Excel, Python, Tableau, Power BI, statistics, data analysis",
        "must_have": ["sql", "excel", "python", "tableau", "power_bi"],
        "critical": ["sql", "data_analysis", "excel"],
        "irrelevant": ["react", "docker", "kubernetes"],
    },
    "data_engineer": {
        "resume": "Data engineer with Python, SQL, Apache Spark, Kafka, Airflow, Docker, AWS, dbt",
        "must_have": ["python", "sql", "spark", "kafka", "docker"],
        "critical": ["python", "sql", "spark"],
        "irrelevant": ["react", "figma", "angular"],
    },
    "ml_engineer": {
        "resume": "ML engineer with Python, TensorFlow, Keras, Scikit-learn, Pandas, NumPy, PyTorch, Docker",
        "must_have": ["python", "tensorflow", "scikit_learn", "pandas", "numpy"],
        "critical": ["python", "machine_learning", "tensorflow"],
        "irrelevant": ["angular", "react", "figma"],
    },
    "devops_engineer": {
        "resume": "DevOps engineer with Docker, Kubernetes, AWS, Linux, Terraform, Jenkins, CI/CD, Git",
        "must_have": ["docker", "kubernetes", "aws", "linux", "git"],
        "critical": ["docker", "kubernetes", "linux"],
        "irrelevant": ["react", "pandas", "figma"],
    },
    "product_manager": {
        "resume": "Product manager with agile, scrum, communication, leadership, Jira, data analysis, Excel",
        "must_have": ["agile", "scrum", "communication", "leadership", "jira"],
        "critical": ["communication", "project_management", "leadership"],
        "irrelevant": ["tensorflow", "docker", "kubernetes"],
    },
    "fullstack_engineer": {
        "resume": "Fullstack developer with JavaScript, React, Node.js, PostgreSQL, REST API, Docker, Git",
        "must_have": ["javascript", "react", "nodejs", "git", "rest_api"],
        "critical": ["javascript", "react", "nodejs"],
        "irrelevant": ["tensorflow", "spark", "airflow"],
    },
}


def test_extraction_and_relevance(role, case):
    result = extract_skills(case["resume"], role=role)
    extracted = result["skills"]
    extracted_ids = [s["skill_id"] for s in extracted]

    assert len(extracted_ids) <= 10, f"{role}: too many skills ({len(extracted_ids)})"
    assert len(extracted_ids) >= 4, f"{role}: too few skills ({len(extracted_ids)})"

    for skill in case["must_have"]:
        assert skill in extracted_ids, f"{role}: missing must-have skill '{skill}'"

    for skill in case["critical"]:
        tier = classify_skill_relevance(skill, role, onet_data)
        assert tier == "critical", f"{role}: '{skill}' should be critical, got '{tier}'"

    irrelevant_count = sum(
        1
        for s in extracted_ids
        if classify_skill_relevance(s, role, onet_data) == "irrelevant"
    )
    assert irrelevant_count <= 2, f"{role}: too many irrelevant skills in output ({irrelevant_count})"

    assert "skills" in result
    assert "experience_years" in result
    assert "domains" in result


if pytest is not None:
    test_extraction_and_relevance = pytest.mark.parametrize(
        "role,case", TEST_CASES.items()
    )(test_extraction_and_relevance)


if __name__ == "__main__":
    for role, case in TEST_CASES.items():
        test_extraction_and_relevance(role, case)
        print(f"PASS - {role}")
    print("\nAll cross-role tests passed!")
