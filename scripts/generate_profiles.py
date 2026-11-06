"""
Synthetic Student Profile Generator.
Generates 75 diverse, reproducible student profiles covering all 4 goals,
varying programmes, years, CGPA, constraints, and edge cases (backlogs,
interest-evidence mismatch, borderline eligibility, time constraints).
Saves to data/seed/synthetic_profiles.json.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT_DIR / "data" / "seed"
OUTPUT_FILE = SEED_DIR / "synthetic_profiles.json"

FIRST_NAMES = ["Aarav", "Aditi", "Ananya", "Aryan", "Bhavya", "Dev", "Diya", "Ishaan", "Kabir", "Meera", "Neha", "Pranav", "Pooja", "Rahul", "Riya", "Rohan", "Siddharth", "Tanvi", "Utkarsh", "Varun"]
LAST_NAMES = ["Agarwal", "Bansal", "Chopra", "Gupta", "Iyer", "Jain", "Kapoor", "Kumar", "Malhotra", "Mehta", "Nair", "Patel", "Reddy", "Sharma", "Singh", "Verma"]

GOALS = ["goal_software", "goal_research", "goal_upsc", "goal_startup"]
PROGRAMMES = ["CS1", "CH1"]

# Foundational courses by programme
CS1_CORE_SEM1_4 = [
    ("COL100", "A"), ("MTL100", "A-"), ("PYL100", "B"),
    ("MTL101", "A"), ("ELL100", "B+"), ("COL106", "A-"),
    ("COL215", "B"), ("COL226", "A-"), ("COL216", "B+")
]

CH1_CORE_SEM1_4 = [
    ("COL100", "B"), ("MTL100", "B+"), ("PYL100", "B"),
    ("MTL101", "B-"), ("ELL100", "B"), ("CLL110", "B"),
    ("CLL121", "B+"), ("CLL122", "B"), ("CLL251", "B-")
]

def generate_profiles(count: int = 75, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    profiles = []

    for i in range(1, count + 1):
        student_id = f"S{2000 + i}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"

        prog = "CH1" if i % 2 == 0 else "CS1"
        year = random.choice([2, 3, 4])
        current_sem = year * 2 - random.choice([0, 1])
        
        # Vary CGPA: normal distribution centered at 8.0, bounded between 6.2 and 9.8
        cgpa = round(min(9.8, max(6.2, random.gauss(8.0, 0.75))), 2)

        goal = GOALS[i % len(GOALS)]
        hours = random.choice([8.0, 10.0, 12.0, 14.0, 16.0])
        slots = random.choice([2, 3, 4, 5])

        # Completed courses pool
        base_core = CS1_CORE_SEM1_4 if prog == "CS1" else CH1_CORE_SEM1_4
        # Slice based on current semester
        num_courses = min(len(base_core), current_sem * 2 + 1)
        completed_pool = base_core[:num_courses]

        completed = []
        for c_code, grade in completed_pool:
            # Vary grades slightly according to CGPA
            g = grade
            if cgpa > 8.8 and g in ["B", "B-"]:
                g = "A-"
            elif cgpa < 7.0 and g in ["A", "A-"]:
                g = "C"
            completed.append({
                "course_code": c_code,
                "grade": g,
                "semester_completed": max(1, min(current_sem - 1, 1))
            })

        # Diagnostic scores roughly correlated with CGPA and goal
        prog_score = round(min(0.98, max(0.20, random.gauss(cgpa / 10.0, 0.1))), 2)
        dsa_score = round(min(0.95, max(0.15, random.gauss((cgpa / 10.0) - 0.1, 0.15))), 2)

        # Edge Cases
        interests = []
        constraints = {
            "credit_headroom_next_semester": random.choice([4.0, 6.0, 8.0]),
            "no_co_taking_courses": [["COL351", "COL352"]],
            "max_weekly_hours": hours
        }

        # Edge case 1: Backlog / Low CGPA
        if i % 15 == 0:
            cgpa = 6.45  # Near eligibility cut-off
            completed[-1]["grade"] = "D"

        # Edge case 2: Goal conflict (Interest in ML, but low linear algebra)
        if i % 7 == 0:
            interests = ["machine learning", "deep learning"]
            # Find MTL101 and downgrade
            for c in completed:
                if c["course_code"] == "MTL101":
                    c["grade"] = "C-"

        # Edge case 3: High performer with overload eligibility
        if i % 10 == 0:
            cgpa = 9.15
            constraints["overload_requested"] = True

        profiles.append({
            "student_id": student_id,
            "name": name,
            "programme": prog,
            "year": year,
            "current_semester": current_sem,
            "cgpa": cgpa,
            "goal_id": goal,
            "target_role": goal.replace("goal_", "").title(),
            "available_hours_per_week": hours,
            "remaining_elective_slots": slots,
            "completed_courses": completed,
            "interests": interests,
            "diagnostic_evidence": [
                { "skill_id": "skill_prog_fundamentals", "value": prog_score, "source_type": "assessed_diagnostic" },
                { "skill_id": "skill_dsa_trees", "value": dsa_score, "source_type": "assessed_diagnostic" }
            ],
            "constraints": constraints,
            "preferences": {
                "format": ["short videos", "hands-on coding problems"]
            }
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

    print(f"Generated {len(profiles)} synthetic profiles in {OUTPUT_FILE}")
    return profiles

if __name__ == "__main__":
    generate_profiles(count=75)

