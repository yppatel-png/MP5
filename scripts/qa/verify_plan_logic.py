import json
from pathlib import Path
from collections import defaultdict

SEED_DIR = Path("data/seed_bhilai")

courses = {c["code"]: c for c in json.load(open(SEED_DIR / "courses.json", encoding="utf-8"))}
prereqs = json.load(open(SEED_DIR / "prerequisites.json", encoding="utf-8"))
prereq_map = defaultdict(list)
for p in prereqs:
    prereq_map[p["course_code"]].append(p["requires_code"])

curricula = json.load(open(SEED_DIR / "iit_bhilai_cse_curricula.json", encoding="utf-8"))
btech = next(p for p in curricula["programmes"] if p["id"] == "iit_bhilai_btech_cse_2023")
sem_templates = {s["semester"]: s for s in btech["semesters"]}

from backend.student.model import StudentStore
from backend.planner.validator import independent_validator
from tests.test_plan_validity_independent import validate_plan_independently

print("Ready to test.")
