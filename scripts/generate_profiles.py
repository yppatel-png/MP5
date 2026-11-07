"""
Synthetic Student Profile Generator for IIT Bhilai B.Tech CSE.
Generates realistic, diverse student cohorts with varied CGPAs,
completed courses, constraint flags, career aspirations, and weekly capacities.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT_DIR / "data" / "seed_bhilai"
OUTPUT_FILE = SEED_DIR / "synthetic_profiles.json"

FIRST_NAMES = ["Aarav", "Aditi", "Ananya", "Aryan", "Bhavya", "Dev", "Diya", "Ishaan", "Kabir", "Meera", "Neha", "Pranav", "Pooja", "Rahul", "Riya", "Rohan", "Siddharth", "Tanvi", "Utkarsh", "Varun"]
LAST_NAMES = ["Agarwal", "Bansal", "Chopra", "Gupta", "Iyer", "Jain", "Kapoor", "Kumar", "Malhotra", "Mehta", "Nair", "Patel", "Reddy", "Sharma", "Singh", "Verma"]

GOALS = ["goal_software", "goal_research", "goal_upsc", "goal_startup"]
PROGRAMME = "iit_bhilai_btech_cse_2023"

# Foundational courses by semester pool
CSE_CORE_POOL = [
    ("CSL100", "A"), ("ECL101", "A-"), ("MEL101", "B"),
    ("CSL201", "A"), ("CSL202", "A-"), ("MAL403", "B+"),
    ("CSL253", "B"), ("CSL301", "A-"), ("CSL304", "B+")
]

def generate_profiles(count: int = 75, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    profiles = []

    for i in range(1, count + 1):
        student_id = f"BH-SYN-{i:03d}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"

        prog = PROGRAMME
        year = random.choice([2, 3, 4])
        current_sem = year * 2 - random.choice([0, 1])

        # Vary CGPA: normal distribution centered at 8.0, bounded between 6.2 and 9.8
        cgpa = round(min(9.8, max(6.2, random.gauss(8.0, 0.75))), 2)

        goal = GOALS[i % len(GOALS)]
        hours = random.choice([8.0, 10.0, 12.0, 14.0, 16.0])
        slots = random.choice([2, 3, 4, 5])

        # Slice based on current semester
        num_courses = min(len(CSE_CORE_POOL), current_sem * 2)
        completed_pool = CSE_CORE_POOL[:num_courses]

        completed = []
        for c_code, grade in completed_pool:
            g = grade
            if cgpa > 8.8 and g in ["B", "B-"]:
                g = "A-"
            elif cgpa < 7.0 and g in ["A", "A-"]:
                g = "B"
            completed.append({
                "course_code": c_code,
                "grade": g,
                "semester_completed": max(1, current_sem - 1)
            })

        interests = []
        if goal == "goal_software":
            interests = ["Software Engineering", "Systems", "Web Applications"]
        elif goal == "goal_research":
            interests = ["Machine Learning", "Algorithms", "Theoretical Computer Science"]
        elif goal == "goal_upsc":
            interests = ["Public Policy", "Ethics", "Economics"]
        elif goal == "goal_startup":
            interests = ["Product Development", "Cloud Architecture", "Finance"]

        constraints = {}
        if random.random() < 0.25:
            constraints["no_heavy_workload"] = True
        if random.random() < 0.20:
            constraints["prefer_morning_slots"] = True
        if random.random() < 0.15:
            constraints["max_credits_override"] = 20.0

        profiles.append({
            "student_id": student_id,
            "name": name,
            "programme": prog,
            "year": year,
            "current_semester": current_sem,
            "cgpa": cgpa,
            "goal_id": goal,
            "target_role": "Software Engineer" if goal == "goal_software" else ("Research Scholar" if goal == "goal_research" else ("Civil Services" if goal == "goal_upsc" else "Technical Founder")),
            "available_hours_per_week": hours,
            "remaining_elective_slots": slots,
            "completed_courses": completed,
            "interests": interests,
            "constraints": constraints,
            "preferences": {
                "preferred_track": "core_heavy" if cgpa > 8.5 else "balanced"
            }
        })

    return profiles

if __name__ == "__main__":
    profiles = generate_profiles(count=75)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)
    print(f"Generated {len(profiles)} synthetic profiles -> {OUTPUT_FILE}")
