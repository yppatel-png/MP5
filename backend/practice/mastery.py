"""
Mastery & Goal Readiness Engine.
Implements the explicit distinction between:
  'Course Completed' (accredited attendance/grade, baseline prior)
  vs.
  'Demonstrated Proficiency' (empirically proven retention across multi-item tests).
Computes composite goal-level readiness and generates actionable 'What's Missing' checklists.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.student.model import StudentStore, StudentProfile
from backend.student.diagnostic import diagnostic_engine
from backend.db.seed_profile import get_seed_dir

SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

class MasteryEngine:
    def __init__(self):
        self.skills = {s["skill_id"]: s for s in load_seed_json("skills.json")}
        self.goal_templates = {g["goal_id"]: g for g in load_seed_json("goal_templates.json")}
        self.course_skills = load_seed_json("course_skills.json")

    def evaluate_skill_state(self, student_id: str, skill_id: str) -> Dict[str, Any]:
        """
        Determines the exact proficiency state for a skill:
        - 'demonstrated_proficiency': empirical test passes (score >= 0.85 on >= 2 items)
        - 'course_completed_only': passed accredited course, but lacks recent independent evidence
        - 'in_progress': some practice attempts recorded, below mastery threshold
        - 'not_started': zero coursework and zero evidence
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            profile = StudentProfile(student_id=student_id, name="Student", programme="CH1")

        # Check if taught by any completed course
        completed_course_codes = set(c.course_code.upper() for c in profile.completed_courses)
        courses_teaching_skill = [
            cs["course_code"] for cs in self.course_skills if cs["skill_id"] == skill_id
        ]
        has_completed_course = any(c in completed_course_codes for c in courses_teaching_skill)

        # Retrieve empirical evidence events
        events = StudentStore.get_evidence_for_student(student_id, skill_id=skill_id)
        active_test_events = [
            ev for ev in events
            if ev.get("source_type") in ["assessed_diagnostic", "quiz", "timed_project", "exercise"]
        ]

        # Count independent items passed
        passed_items = set()
        for ev in active_test_events:
            if float(ev.get("value", 0.0)) >= 0.70:
                ref = ev.get("item_ref") or str(ev.get("id"))
                passed_items.add(ref)

        # Compute current BKT probability
        skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
        skill_data = skill_matrix.get(skill_id, {})
        p_mastery = float(skill_data.get("p_mastery", 0.1))

        # Classification Logic
        has_demonstrated_proficiency = (p_mastery >= 0.85 and len(passed_items) >= 2)

        if has_demonstrated_proficiency:
            status = "demonstrated_proficiency"
            status_label = "Demonstrated Proficiency (Empirically Verified)"
        elif has_completed_course:
            status = "course_completed_only"
            status_label = "Course Completed (Pending Active Verification)"
        elif len(active_test_events) > 0:
            status = "in_progress"
            status_label = "In Progress"
        else:
            status = "not_started"
            status_label = "Not Started"

        return {
            "skill_id": skill_id,
            "skill_name": self.skills.get(skill_id, {}).get("name", skill_id),
            "status": status,
            "status_label": status_label,
            "p_mastery": round(p_mastery, 3),
            "has_completed_course": has_completed_course,
            "has_demonstrated_proficiency": has_demonstrated_proficiency,
            "passed_items_count": len(passed_items),
            "evidence_count": len(events)
        }

    def compute_goal_readiness(
        self,
        student_id: str,
        goal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes composite goal-level readiness and generates the actionable 'What's Missing' checklist.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        active_goal_id = goal_id or profile.goal_id
        goal_meta = self.goal_templates.get(active_goal_id)
        if goal_meta is None:
            raise ValueError(f"Unknown learning goal: {active_goal_id}")

        required_skills = goal_meta.get("required_skills", [])
        milestones = goal_meta.get("milestones", [])
        if not required_skills and not milestones:
            return {
                "status": "unavailable",
                "message": "No source-backed skill map or readiness milestones are included in this curriculum snapshot.",
                "student_id": student_id,
                "goal_id": active_goal_id,
                "goal_name": goal_meta["name"],
                "target_role": goal_meta["target_role"],
                "overall_readiness_percentage": None,
                "metrics": {
                    "total_goal_skills": 0,
                    "proficient_skills_count": 0,
                    "course_completed_skills_count": 0,
                    "project_milestone_completed": False,
                },
                "skills_breakdown": [],
                "whats_missing": [],
            }

        skills_breakdown = []
        proficient_count = 0
        course_completed_count = 0
        whats_missing = []

        total_skill_weight = 0.0
        earned_skill_weight = 0.0

        for req in required_skills:
            sk_id = req["skill_id"]
            target = req["target_level"]
            is_critical = req.get("critical", False)
            weight = 1.5 if is_critical else 1.0
            total_skill_weight += weight

            state = self.evaluate_skill_state(student_id, sk_id)
            skills_breakdown.append({**state, "target_level": target, "critical": is_critical})

            if state["status"] == "demonstrated_proficiency":
                proficient_count += 1
                earned_skill_weight += weight * 1.0
            elif state["status"] == "course_completed_only":
                course_completed_count += 1
                earned_skill_weight += weight * 0.55
                whats_missing.append({
                    "type": "skill_verification",
                    "skill_id": sk_id,
                    "title": f"Verify retention in {state['skill_name']}",
                    "description": f"You completed coursework covering {state['skill_name']}, but need 2 independent practice passes to demonstrate verified proficiency.",
                    "urgency": "medium"
                })
            else:
                whats_missing.append({
                    "type": "skill_gap",
                    "skill_id": sk_id,
                    "title": f"Acquire foundational mastery in {state['skill_name']}",
                    "description": f"Target role requires {round(target*100)}% mastery. Current level is {round(state['p_mastery']*100)}%.",
                    "urgency": "high" if is_critical else "medium"
                })

        # Milestone Readiness
        all_attempts = StudentStore.get_evidence_for_student(student_id)
        has_project_submission = any(ev.get("source_type") == "timed_project" for ev in all_attempts)
        if not has_project_submission:
            whats_missing.append({
                "type": "project_milestone",
                "title": "Complete Capstone Project Checkpoint",
                "description": f"Submit an end-to-end practical project milestone aligned with {goal_meta['name']}.",
                "urgency": "high"
            })

        # Calculate composite readiness percentage:
        # 65% skill demonstration + 20% coursework + 15% milestone project
        skill_score = (earned_skill_weight / max(1e-6, total_skill_weight)) * 65.0
        course_score = (course_completed_count / max(1, len(required_skills))) * 20.0
        project_score = 15.0 if has_project_submission else 0.0

        overall_readiness = round(min(100.0, skill_score + course_score + project_score), 1)

        return {
            "student_id": student_id,
            "goal_id": active_goal_id,
            "goal_name": goal_meta["name"],
            "target_role": goal_meta["target_role"],
            "overall_readiness_percentage": overall_readiness,
            "metrics": {
                "total_goal_skills": len(required_skills),
                "proficient_skills_count": proficient_count,
                "course_completed_skills_count": course_completed_count,
                "project_milestone_completed": has_project_submission
            },
            "skills_breakdown": skills_breakdown,
            "whats_missing": whats_missing
        }

mastery_engine = MasteryEngine()
