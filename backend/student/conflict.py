"""
Conflict Detection & GapAlert Engine.
Detects discrepancies between student aspirations and verified academic evidence,
generating actionable, choice-driven GapAlerts with explicit trade-offs.
"""

from typing import List, Dict, Any, Optional
from backend.student.model import StudentStore, StudentProfile
from backend.student.diagnostic import diagnostic_engine
from backend.db.seed_profile import get_institute_profile

class ConflictDetector:
    def detect_conflicts(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Scans for divergences between declared interests/goals and empirical evidence.
        Returns a list of structured GapAlerts.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return []
        if get_institute_profile() == "iit_bhilai":
            return []

        skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
        alerts: List[Dict[str, Any]] = []

        interests_lower = [i.lower() for i in profile.interests]
        goal_id = profile.goal_id

        # Conflict 1: Machine Learning interest with weak Linear Algebra or Probability
        wants_ml = any("machine learning" in i or "ml" in i or "data science" in i or "ai" in i for i in interests_lower) or goal_id == "goal_research"
        if wants_ml:
            la_data = skill_matrix.get("skill_linear_algebra", {})
            prob_data = skill_matrix.get("skill_probability", {})
            la_level = la_data.get("p_mastery", 0.5)
            prob_level = prob_data.get("p_mastery", 0.5)

            if la_level < 0.60 or prob_level < 0.50:
                alerts.append({
                    "alert_id": "gap_alert_ml_linear_algebra",
                    "severity": "high",
                    "title": "Prerequisite Foundation Gap: Machine Learning",
                    "evidence": f"You declared strong interest in Machine Learning, but your Linear Algebra mastery is {round(la_level*100)}% and Probability is {round(prob_level*100)}%. Core ML optimization requires robust matrix eigensystem and gradient foundations.",
                    "options": [
                        {
                            "option_id": "opt_close_gap",
                            "action": "Close the Foundation Gap",
                            "description": "Insert foundational Linear Algebra & Probability practice modules before taking COL774.",
                            "cost": "3 weeks, 0 additional credits (open resources)",
                            "recommended": True
                        },
                        {
                            "option_id": "opt_adjust_goal",
                            "action": "Adjust Career Target",
                            "description": "Shift primary focus to Software Engineering & Backend Systems, where deep matrix mathematics is not a critical barrier.",
                            "cost": "0 weeks delay",
                            "recommended": False
                        },
                        {
                            "option_id": "opt_proceed_with_risk",
                            "action": "Proceed with Academic Risk",
                            "description": "Retain Machine Learning in next semester's schedule, acknowledging a high risk of grade penalty in COL774.",
                            "cost": "High workload peak (14+ hrs/week)",
                            "recommended": False
                        }
                    ]
                })

        # Conflict 2: Software role with severe Data Structures & Algorithms deficiency
        if goal_id == "goal_software":
            dsa_data = skill_matrix.get("skill_dsa_trees", {})
            dsa_linear = skill_matrix.get("skill_dsa_linear", {})
            dsa_level = (dsa_data.get("p_mastery", 0.5) + dsa_linear.get("p_mastery", 0.5)) / 2.0

            if dsa_level < 0.45:
                alerts.append({
                    "alert_id": "gap_alert_swe_dsa_deficiency",
                    "severity": "high",
                    "title": "Critical Core Gap: Data Structures & Algorithms",
                    "evidence": f"Targeting Software Development Engineer roles requires at least 85% DSA proficiency. Your tested diagnostic mastery is currently {round(dsa_level*100)}%.",
                    "options": [
                        {
                            "option_id": "opt_prioritize_dsa",
                            "action": "Prioritize COL106 & Active Practice",
                            "description": "Dedicate upcoming elective headroom to COL106 and 50 hands-on algorithmic practice exercises.",
                            "cost": "1 semester, 4 credits",
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
                        "description": "Restrict next semester to 1 elective slot and utilize high-yield micro-learning resources.",
                        "cost": "Lightens schedule by 4 hrs/week",
                        "recommended": True
                    },
                    {
                        "option_id": "opt_increase_time",
                        "action": "Increase Study Allocation",
                        "description": "Adjust available weekly hours to at least 10 hrs/week to stay on track for placement readiness.",
                        "cost": "+3 hrs/week commitment",
                        "recommended": False
                    }
                ]
            })

        return alerts

conflict_detector = ConflictDetector()
