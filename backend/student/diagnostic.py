"""
Adaptive Diagnostic & Skill Gap Engine.
Selects optimal information-gain assessment questions and computes quantified gaps
between student capabilities and target career goals.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.student.model import StudentStore, StudentProfile
from backend.student.bkt import bkt_estimator
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_seed_dir
from backend.config import load_evidence_config

logger = logging.getLogger("learning_buddy.student.diagnostic")
SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

class DiagnosticEngine:
    def __init__(self):
        self.skills = {s["skill_id"]: s for s in load_seed_json("skills.json")}
        self.goal_templates = {g["goal_id"]: g for g in load_seed_json("goal_templates.json")}
        self.course_skills = load_seed_json("course_skills.json")
        self.exercises = load_seed_json("exercises.json")

    def _get_config_params(self):
        cfg = load_evidence_config()
        grade_scale = cfg.get("grade_scale", {})
        diag_params = cfg.get("diagnostic_parameters", {})
        return grade_scale, diag_params

    def get_course_priors(self, profile: StudentProfile) -> Dict[str, float]:
        """Infers initial prior skill masteries from accredited completed courses and grades."""
        priors: Dict[str, float] = {}
        grade_scale, diag_params = self._get_config_params()
        unknown_fallback = float(diag_params.get("unknown_grade_fallback", 0.50))
        course_grade_map = {c.course_code.upper(): c.grade.upper() for c in profile.completed_courses}

        for cs in self.course_skills:
            code = cs["course_code"].upper()
            sk = cs["skill_id"]
            if code in course_grade_map:
                grade = course_grade_map[code]
                if grade in grade_scale and isinstance(grade_scale[grade], (int, float)):
                    base_score = float(grade_scale[grade])
                else:
                    logger.warning(
                        "Unknown course grade '%s' for course '%s'. Falling back to configured default %s.",
                        grade, code, unknown_fallback
                    )
                    base_score = unknown_fallback
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
            profile = StudentProfile(student_id=student_id, name="Student", programme="iit_bhilai_btech_cse_2023")

        priors = self.get_course_priors(profile)
        all_evidence = StudentStore.get_evidence_for_student(student_id)

        evidence_by_skill: Dict[str, List[Dict[str, Any]]] = {}
        for ev in all_evidence:
            evidence_by_skill.setdefault(ev["skill_id"], []).append(ev)

        skill_matrix: Dict[str, Dict[str, Any]] = {}
        for sk_id, sk_meta in self.skills.items():
            ev_list = evidence_by_skill.get(sk_id, [])
            prior = priors.get(sk_id, None)

            # Determine evidence source
            if ev_list:
                has_assessed = any(
                    e.get("source_type") in {
                        "assessed_diagnostic", "timed_project", "mock_exam",
                        "quiz", "exercise", "practice", "grade"
                    }
                    for e in ev_list
                )
                if has_assessed:
                    evidence_source = "assessed"
                elif any(e.get("source_type") == "self_declared" for e in ev_list):
                    evidence_source = "self_declared"
                else:
                    evidence_source = "assessed"
            elif prior is not None:
                evidence_source = "course_grade_prior"
            elif sk_meta["domain"].lower() in [i.lower() for i in profile.interests]:
                prior = 0.35
                evidence_source = "self_declared"
            else:
                evidence_source = "none"

            mastery_data = bkt_estimator.estimate_skill_mastery(ev_list, prior_probability=prior)

            # Determine status and status label
            if evidence_source == "assessed":
                if mastery_data.get("mastered", False):
                    status = "mastered"
                    status_label = "mastered"
                else:
                    status = "assessed"
                    status_label = "in progress"
            elif evidence_source in ("course_grade_prior", "self_declared"):
                status = "unverified"
                status_label = "needs a check"
            else:
                status = "unassessed"
                status_label = "not yet assessed"

            skill_matrix[sk_id] = {
                "skill_id": sk_id,
                "name": sk_meta["name"],
                "domain": sk_meta["domain"],
                "evidence_source": evidence_source,
                "status": status,
                "status_label": status_label,
                **mastery_data
            }

        return skill_matrix

    def get_next_question(self, student_id: str, answered_exercise_ids: List[str]) -> Dict[str, Any]:
        """
        Adaptive Question Selector:
        Selects the next question that maximizes information gain on goal-critical skills
        where mastery uncertainty is highest (|p - 0.5| is minimized).
        Prioritizes unverified course-grade priors first so that course claims are calibrated.
        """
        profile = StudentStore.get_profile(student_id)
        goal_id = profile.goal_id if profile else "goal_software"
        goal = self.goal_templates.get(goal_id)
        
        _, diag_params = self._get_config_params()
        max_questions = int(diag_params.get("max_diagnostic_questions", 12))

        # Query answered exercise IDs from database server-side
        db_answered = StudentStore.get_answered_exercise_ids(student_id) if hasattr(StudentStore, "get_answered_exercise_ids") else []
        all_answered_ids = sorted(list(set(answered_exercise_ids + db_answered)))

        if goal is None:
            return {
                "diagnostic_complete": True,
                "available": False,
                "questions_answered": len(all_answered_ids),
                "message": "No diagnostic is configured for this learning goal.",
            }

        if not self.exercises:
            return {
                "diagnostic_complete": True,
                "available": False,
                "questions_answered": len(all_answered_ids),
                "message": "No source-backed diagnostic exercises are included in this curriculum snapshot.",
            }

        skill_matrix = self.get_full_skill_matrix(student_id)
        required_skills = {req["skill_id"]: req for req in goal.get("required_skills", [])}

        # Find goal skills scored by priority
        scored_skills = []
        for sk_id, req in required_skills.items():
            curr = skill_matrix.get(sk_id, {})
            p_mastery = curr.get("p_mastery", 0.5)
            confidence = curr.get("confidence", 0.1)
            ev_source = curr.get("evidence_source", "none")
            status = curr.get("status", "unassessed")

            # High priority if confidence is low or p_mastery is near 0.5 (maximum entropy)
            uncertainty = 1.0 - abs(p_mastery - 0.5) * 2.0
            priority = uncertainty * (1.2 - confidence)

            # Prioritize unverified course priors first so accredited claims are tested
            if ev_source == "course_grade_prior" or status == "unverified":
                priority += 10.0 + (1.0 - confidence)
            elif ev_source == "self_declared":
                priority += 4.0 + (1.0 - confidence)

            if req.get("critical", False):
                priority *= 1.5
            scored_skills.append((priority, sk_id))

        scored_skills.sort(key=lambda x: x[0], reverse=True)

        best_candidate = None
        best_info_gain = -1.0

        for priority, sk_id in scored_skills:
            curr = skill_matrix.get(sk_id, {})
            p_m = curr.get("p_mastery", 0.5)
            target_difficulty = max(1.0, min(4.0, 1.0 + 3.0 * p_m))

            candidate_exs = [
                ex for ex in self.exercises
                if ex["skill_id"] == sk_id
                and ex["exercise_id"] not in all_answered_ids
                and ex["type"] in {"mcq", "short"}
            ]
            for ex in candidate_exs:
                diff = float(ex.get("difficulty", 2))
                diff_match = 1.0 / (1.0 + abs(diff - target_difficulty))
                info_gain = priority * diff_match
                if info_gain > best_info_gain:
                    best_info_gain = info_gain
                    best_candidate = ex

            if best_candidate and priority >= 8.0:
                # If we found a candidate for a high-priority unverified prior skill, lock it in
                break

        selected_exercise = best_candidate

        # If no unasked exercises in goal skills or maximum threshold reached
        if not selected_exercise or len(all_answered_ids) >= max_questions:
            return {
                "available": False,
                "diagnostic_complete": True,
                "questions_answered": len(all_answered_ids),
                "message": "Diagnostic assessment complete. Skill vector calibrated with high confidence."
            }

        return {
            "available": True,
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
            "questions_answered": len(all_answered_ids),
            "estimated_questions_remaining": max(0, max_questions - len(all_answered_ids))
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

        _, diag_params = self._get_config_params()
        gap_threshold = float(diag_params.get("gap_threshold", 0.10))
        critical_gap_threshold = float(diag_params.get("critical_gap_threshold", 0.35))
        fallback_current_level = float(diag_params.get("fallback_current_level", 0.10))

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
            current_level = current_data.get("p_mastery", fallback_current_level)
            evidence_source = current_data.get("evidence_source", "none")
            status = current_data.get("status", "unassessed")
            status_label = current_data.get("status_label", "not yet assessed")

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
                "evidence_source": evidence_source,
                "status": status,
                "status_label": status_label,
                "evidence_trail": current_data.get("evidence_trail", [])
            }

            # Spec: 'completed the course' != 'demonstrated proficiency'.
            # Only confirmed assessment evidence can qualify as a strength.
            if gap_magnitude <= gap_threshold and evidence_source == "assessed":
                strengths.append(item)
            else:
                if evidence_source in ("course_grade_prior", "self_declared"):
                    item["status"] = "unverified"
                    item["status_label"] = "needs a check"
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
            "critical_gap_count": sum(1 for g in gaps if g["critical"] and g["gap"] > critical_gap_threshold)
        }

diagnostic_engine = DiagnosticEngine()
