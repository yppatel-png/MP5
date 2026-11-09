"""
Conflict Detection & GapAlert Engine.
Detects discrepancies between student aspirations and verified academic evidence,
generating actionable, choice-driven GapAlerts with explicit trade-offs.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.student.model import StudentStore, StudentProfile
from backend.student.diagnostic import diagnostic_engine
from backend.student.interests import FIXED_INTERESTS, INTEREST_TO_SKILLS_MAP
from backend.db.seed_profile import get_seed_dir

SEED_DIR = get_seed_dir()

def _load_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

class ConflictDetector:
    def __init__(self):
        self._goal_templates = {g["goal_id"]: g for g in _load_json("goal_templates.json")}
        self._course_skills = _load_json("course_skills.json")
        self._courses = {c["code"]: c for c in _load_json("courses.json")}

    def _find_courses_for_skill(self, skill_id: str) -> List[Dict[str, Any]]:
        """Finds catalogue courses that teach the given skill."""
        matching_codes = [
            cs["course_code"] for cs in self._course_skills
            if cs["skill_id"] == skill_id
        ]
        results = []
        for code in matching_codes:
            if code in self._courses:
                results.append(self._courses[code])
        return results

    def detect_conflicts(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Scans for divergences between declared interests/goals and empirical evidence.
        Returns a list of structured GapAlerts.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return []

        skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
        alerts: List[Dict[str, Any]] = []

        # Canonical interest matching: check exact canonical interest names
        # Avoid substring bugs (e.g. 'ml' in 'html' or 'data' in 'metadata')
        canonical_interests = [
            fi for fi in FIXED_INTERESTS
            if any(fi.lower() == i.strip().lower() for i in profile.interests)
        ]
        goal_id = profile.goal_id
        active_goal = self._goal_templates.get(goal_id, {})
        required_skills = {r["skill_id"]: r for r in active_goal.get("required_skills", [])}

        # Conflict 1: AI / Data Science / Research aspiration with weak math/prob foundations
        wants_ai = (
            "AI/ML" in canonical_interests
            or goal_id in ("goal_research", "goal_higher_studies", "goal_ai", "goal_data_science")
        )

        if wants_ai:
            prob_data = skill_matrix.get("probability_statistics", {})
            disc_data = skill_matrix.get("discrete_mathematics", {})

            # Format evidence strings accurately; never assume 0.5 for unassessed skills
            if prob_data.get("evidence_source") == "none":
                prob_str = "not yet assessed"
                prob_level = None
            else:
                prob_level = prob_data.get("p_mastery", 0.0)
                prob_src = prob_data.get("evidence_source", "assessed")
                prob_str = f"{round(prob_level * 100)}% (source: {prob_src})"

            if disc_data.get("evidence_source") == "none":
                disc_str = "not yet assessed"
                disc_level = None
            else:
                disc_level = disc_data.get("p_mastery", 0.0)
                disc_src = disc_data.get("evidence_source", "assessed")
                disc_str = f"{round(disc_level * 100)}% (source: {disc_src})"

            has_weak_prob = prob_level is None or prob_level < 0.60
            has_weak_disc = disc_level is None or disc_level < 0.60

            if has_weak_prob or has_weak_disc:
                # Find course teaching foundational math / probability dynamically
                math_courses = self._find_courses_for_skill("probability_statistics") + self._find_courses_for_skill("discrete_mathematics")
                rec_course_code = "MAL201" if any(c["code"] == "MAL201" for c in math_courses) else (math_courses[0]["code"] if math_courses else "MAL403")
                rec_course = self._courses.get(rec_course_code, {"credits": 4, "title": "Linear Algebra & Mathematical Foundations"})
                rec_credits = rec_course.get("credits", 4)

                alerts.append({
                    "alert_id": "gap_alert_ml_linear_algebra",
                    "severity": "high",
                    "title": "Prerequisite Foundation Gap: Artificial Intelligence & Mathematical Foundations",
                    "evidence": (
                        f"You have an AI/ML career focus, but empirical evidence in foundational mathematics is weak or unverified. "
                        f"Probability & Statistics: {prob_str}; Discrete Mathematics: {disc_str}. "
                        "Advanced AI/ML coursework requires verified probabilistic and mathematical maturity."
                    ),
                    "options": [
                        {
                            "option_id": "opt_close_gap",
                            "action": f"Take {rec_course_code} ({rec_course.get('title', 'Foundations')})",
                            "description": f"Enroll in {rec_course_code} or complete core mathematical foundation modules before enrolling in advanced AI electives.",
                            "cost": f"1 semester, {rec_credits} credits",
                            "recommended": True
                        },
                        {
                            "option_id": "opt_self_paced_bridge",
                            "action": "Take Self-Paced Bridge Course",
                            "description": "Complete self-paced mathematical foundations bridge using curated open learning resources.",
                            "cost": "3 weeks, 0 additional credits (open resources)",
                            "recommended": False
                        },
                        {
                            "option_id": "opt_adjust_goal",
                            "action": "Adjust Career Target",
                            "description": "Shift primary focus to Software Engineering & Systems, where advanced mathematical foundations are not a barrier.",
                            "cost": "0 delay, 0 credits",
                            "recommended": False
                        }
                    ]
                })

        # Conflict 2: Software role with Data Structures & Algorithms deficiency
        if goal_id == "goal_software":
            ds_req = required_skills.get("data_structures", {"target_level": 0.85})
            algo_req = required_skills.get("algorithms", {"target_level": 0.85})
            target_dsa = max(ds_req.get("target_level", 0.85), algo_req.get("target_level", 0.85))

            ds_data = skill_matrix.get("data_structures", {})
            algo_data = skill_matrix.get("algorithms", {})

            ds_src = ds_data.get("evidence_source", "none")
            algo_src = algo_data.get("evidence_source", "none")

            if ds_src == "none" and algo_src == "none":
                dsa_level = None
                dsa_str = "not yet assessed"
            else:
                ds_val = ds_data.get("p_mastery", 0.0) if ds_src != "none" else 0.0
                algo_val = algo_data.get("p_mastery", 0.0) if algo_src != "none" else 0.0
                dsa_level = (ds_val + algo_val) / 2.0
                dsa_str = f"{round(dsa_level * 100)}% (tested/prior)"

            if dsa_level is None or dsa_level < target_dsa:
                dsa_courses = self._find_courses_for_skill("data_structures")
                dsa_code = dsa_courses[0]["code"] if dsa_courses else "CSL202"
                dsa_credits = self._courses.get(dsa_code, {}).get("credits", 4)

                alerts.append({
                    "alert_id": "gap_alert_swe_dsa_deficiency",
                    "severity": "high",
                    "title": "Critical Core Gap: Data Structures & Algorithms",
                    "evidence": (
                        f"Targeting Software Development roles requires {round(target_dsa*100)}% DSA proficiency. "
                        f"Your current capability is {dsa_str}."
                    ),
                    "options": [
                        {
                            "option_id": "opt_prioritize_dsa",
                            "action": f"Prioritize {dsa_code} & Active Practice",
                            "description": f"Dedicate upcoming elective headroom to {dsa_code} and hands-on algorithmic practice exercises.",
                            "cost": f"1 semester, {dsa_credits} credits",
                            "recommended": True
                        },
                        {
                            "option_id": "opt_extend_timeline",
                            "action": "Extend Timeline by 1 Semester",
                            "description": "Shift placement readiness milestone by one semester to build thorough algorithmic foundations without CGPA strain.",
                            "cost": "1 additional semester",
                            "recommended": False
                        }
                    ]
                })

        # Conflict 3: High academic ambition with severely constrained time
        if profile.available_hours_per_week < 8.0 and len(profile.completed_courses) < 10:
            alerts.append({
                "alert_id": "gap_alert_time_workload_strain",
                "severity": "medium",
                "title": "Time Constraint & Workload Risk",
                "evidence": f"You specified only {profile.available_hours_per_week} hours/week available outside classes. Standard elective tracks require 10–12 hours/week.",
                "options": [
                    {
                        "option_id": "opt_cap_credits",
                        "action": "Cap Elective Load",
                        "description": "Restrict next semester to essential course slots and utilize high-yield micro-learning resources.",
                        "cost": "Lightens schedule by 4 hrs/week",
                        "recommended": True
                    },
                    {
                        "option_id": "opt_increase_time",
                        "action": "Increase Study Allocation",
                        "description": "Adjust available weekly hours to at least 10 hrs/week to stay on track for target role readiness.",
                        "cost": "+3 hrs/week commitment",
                        "recommended": False
                    }
                ]
            })

        return alerts

conflict_detector = ConflictDetector()
