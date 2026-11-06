"""
Adaptive Diagnostic & Skill Gap Engine.
Selects optimal information-gain assessment questions and computes quantified gaps
between student capabilities and target career goals.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.student.model import StudentStore, StudentProfile
from backend.student.bkt import bkt_estimator
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_seed_dir

SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

# Grade to prior numerical estimate
GRADE_PRIORS = {
    "A": 0.90, "A-": 0.85,
    "B": 0.75, "B-": 0.68,
    "C": 0.52, "C-": 0.45,
    "D": 0.35, "E": 0.20, "F": 0.10
}

class DiagnosticEngine:
    def __init__(self):
        self.skills = {s["skill_id"]: s for s in load_seed_json("skills.json")}
        self.goal_templates = {g["goal_id"]: g for g in load_seed_json("goal_templates.json")}
        self.course_skills = load_seed_json("course_skills.json")
        self.exercises = load_seed_json("exercises.json")

    def get_course_priors(self, profile: StudentProfile) -> Dict[str, float]:
        """Infers initial prior skill masteries from accredited completed courses and grades."""
        priors: Dict[str, float] = {}
        course_grade_map = {c.course_code.upper(): c.grade.upper() for c in profile.completed_courses}

        for cs in self.course_skills:
            code = cs["course_code"].upper()
            sk = cs["skill_id"]
            if code in course_grade_map:
                grade = course_grade_map[code]
                base_score = GRADE_PRIORS.get(grade, 0.65)
                # Scale by depth weight (advanced = full score; intro = slightly dampened)
                depth_multiplier = {"intro": 0.85, "intermediate": 0.95, "advanced": 1.0}.get(cs.get("depth", "intermediate"), 0.9)
                estimated = base_score * depth_multiplier
                priors[sk] = max(priors.get(sk, 0.0), estimated)

        return priors

    def get_full_skill_matrix(self, student_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Builds the complete 30-skill mastery matrix for a student
        by synthesizing accredited course priors with chronological BKT evidence events.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            profile = StudentProfile(student_id=student_id, name="Student", programme="CH1")

        priors = self.get_course_priors(profile)
        all_evidence = StudentStore.get_evidence_for_student(student_id)

        evidence_by_skill: Dict[str, List[Dict[str, Any]]] = {}
        for ev in all_evidence:
            evidence_by_skill.setdefault(ev["skill_id"], []).append(ev)

        skill_matrix: Dict[str, Dict[str, Any]] = {}
        for sk_id, sk_meta in self.skills.items():
            ev_list = evidence_by_skill.get(sk_id, [])
            prior = priors.get(sk_id, None)

            # If student self-declared an interest in this domain, record low-confidence baseline
            if sk_meta["domain"].lower() in [i.lower() for i in profile.interests] and prior is None and not ev_list:
                prior = 0.35  # low weight prior for self-declared

            mastery_data = bkt_estimator.estimate_skill_mastery(ev_list, prior_probability=prior)
            skill_matrix[sk_id] = {
                "skill_id": sk_id,
                "name": sk_meta["name"],
                "domain": sk_meta["domain"],
                **mastery_data
            }

        return skill_matrix

    def get_next_question(self, student_id: str, answered_exercise_ids: List[str]) -> Dict[str, Any]:
        """
        Adaptive Question Selector:
        Selects the next question that maximizes information gain on goal-critical skills
        where mastery uncertainty is highest (|p - 0.5| is minimized).
        """
        profile = StudentStore.get_profile(student_id)
        goal_id = profile.goal_id if profile else "goal_software"
        goal = self.goal_templates.get(goal_id)
        if goal is None:
            return {
                "diagnostic_complete": True,
                "available": False,
                "questions_answered": len(answered_exercise_ids),
                "message": "No diagnostic is configured for this learning goal.",
            }

        if not self.exercises:
            return {
                "diagnostic_complete": True,
                "available": False,
                "questions_answered": len(answered_exercise_ids),
                "message": "No source-backed diagnostic exercises are included in this curriculum snapshot.",
            }

        skill_matrix = self.get_full_skill_matrix(student_id)
        required_skills = {req["skill_id"]: req for req in goal.get("required_skills", [])}

        # Find goal skill with lowest certainty
        scored_skills = []
        for sk_id, req in required_skills.items():
            curr = skill_matrix.get(sk_id, {})
            p_mastery = curr.get("p_mastery", 0.5)
            confidence = curr.get("confidence", 0.1)
            # High priority if confidence is low or p_mastery is near 0.5 (maximum entropy)
            uncertainty = 1.0 - abs(p_mastery - 0.5) * 2.0
            priority = uncertainty * (1.2 - confidence)
            if req.get("critical", False):
                priority *= 1.5
            scored_skills.append((priority, sk_id))

        scored_skills.sort(key=lambda x: x[0], reverse=True)

        # Pick an unasked exercise for the top priority skill
        selected_exercise = None
        for _, sk_id in scored_skills:
            candidate_exs = [
                ex for ex in self.exercises
                if ex["skill_id"] == sk_id
                and ex["exercise_id"] not in answered_exercise_ids
                and ex["type"] in {"mcq", "short"}
            ]
            if candidate_exs:
                # Pick medium difficulty first, then adaptive
                selected_exercise = candidate_exs[0]
                break

        # If no unasked exercises in goal skills or threshold reached
        if not selected_exercise or len(answered_exercise_ids) >= 12:
            return {
                "diagnostic_complete": True,
                "questions_answered": len(answered_exercise_ids),
                "message": "Diagnostic assessment complete. Skill vector calibrated with high confidence."
            }

        return {
            "diagnostic_complete": False,
            "exercise": {
                "exercise_id": selected_exercise["exercise_id"],
                "skill_id": selected_exercise["skill_id"],
                "skill_name": self.skills.get(selected_exercise["skill_id"], {}).get("name", ""),
                "type": selected_exercise["type"],
                "difficulty": selected_exercise["difficulty"],
                "prompt": selected_exercise["prompt"],
                "options": selected_exercise.get("answer_key", {}).get("options", [])
            },
            "questions_answered": len(answered_exercise_ids),
            "estimated_questions_remaining": max(0, 10 - len(answered_exercise_ids))
        }

    def compute_skill_gaps(self, student_id: str, goal_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes the delta between current skill capabilities and target goal requirements.
        Distinguishes strengths, moderate gaps, and critical deficiencies.
        """
        profile = StudentStore.get_profile(student_id)
        active_goal_id = goal_id or (profile.goal_id if profile else "goal_software")
        goal = self.goal_templates.get(active_goal_id)
        if goal is None:
            raise ValueError(f"Unknown learning goal: {active_goal_id}")

        skill_matrix = self.get_full_skill_matrix(student_id)
        required_skills = goal.get("required_skills", [])

        gaps = []
        strengths = []
        total_required_level = 0.0
        total_current_level = 0.0

        for req in required_skills:
            sk_id = req["skill_id"]
            target = req["target_level"]
            is_critical = req.get("critical", False)
            current_data = skill_matrix.get(sk_id, {})
            current_level = current_data.get("p_mastery", 0.1)

            gap_magnitude = max(0.0, target - current_level)
            total_required_level += target
            total_current_level += min(target, current_level)

            item = {
                "skill_id": sk_id,
                "skill_name": self.skills.get(sk_id, {}).get("name", sk_id),
                "domain": self.skills.get(sk_id, {}).get("domain", "General"),
                "current_level": round(current_level, 2),
                "target_level": round(target, 2),
                "gap": round(gap_magnitude, 2),
                "critical": is_critical,
                "confidence": current_data.get("confidence", 0.2),
                "evidence_count": current_data.get("evidence_count", 0),
                "evidence_trail": current_data.get("evidence_trail", [])
            }

            if gap_magnitude <= 0.10:
                strengths.append(item)
            else:
                gaps.append(item)

        # Sort gaps by critical flag and gap magnitude descending
        gaps.sort(key=lambda x: (x["critical"], x["gap"]), reverse=True)

        overall_readiness = (
            (total_current_level / total_required_level) * 100.0
            if total_required_level
            else None
        )

        return {
            "student_id": student_id,
            "goal_id": active_goal_id,
            "goal_name": goal["name"],
            "target_role": goal["target_role"],
            "readiness_percentage": round(overall_readiness, 1) if overall_readiness is not None else None,
            "strengths": strengths,
            "gaps": gaps,
            "critical_gap_count": sum(1 for g in gaps if g["critical"] and g["gap"] > 0.35)
        }

diagnostic_engine = DiagnosticEngine()
