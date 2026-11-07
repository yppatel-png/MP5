"""
Conflict Detection & GapAlert Engine.
Detects discrepancies between student aspirations and verified academic evidence,
generating actionable, choice-driven GapAlerts with explicit trade-offs.
"""

from typing import List, Dict, Any, Optional
from backend.student.model import StudentStore, StudentProfile
from backend.student.diagnostic import diagnostic_engine


class ConflictDetector:
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

        interests_lower = [i.lower() for i in profile.interests]
        goal_id = profile.goal_id

        # Conflict 1: AI / Research interest with weak foundations
        wants_ai = any(
            "machine learning" in i or "ml" in i or "data science" in i or "ai" in i or "artificial intelligence" in i
            for i in interests_lower
        ) or goal_id in ("goal_research", "goal_higher_studies")
        if wants_ai:
            prob_data = skill_matrix.get("probability_statistics") or skill_matrix.get("skill_probability", {})
            disc_data = skill_matrix.get("discrete_mathematics") or skill_matrix.get("skill_linear_algebra", {})
            prob_level = prob_data.get("p_mastery", 0.5)
            disc_level = disc_data.get("p_mastery", 0.5)

            if prob_level < 0.60 or disc_level < 0.50:
                alerts.append({
                    "alert_id": "gap_alert_ml_linear_algebra",
                    "severity": "high",
                    "title": "Prerequisite Foundation Gap: Artificial Intelligence & Machine Learning",
                    "evidence": (
                        f"You declared interest in AI/ML, but your Probability & Statistics mastery is "
                        f"{round(prob_level*100)}% and Discrete Mathematics is {round(disc_level*100)}%. "
                        "Advanced AI topics require robust probabilistic and algorithmic foundations."
                    ),
                    "options": [
                        {
                            "option_id": "opt_close_gap",
                            "action": "Close the Foundation Gap",
                            "description": "Insert foundational Probability & Discrete Math practice modules before enrolling in advanced AI electives.",
                            "cost": "3 weeks, 0 additional credits (open resources)",
                            "recommended": True
                        },
                        {
                            "option_id": "opt_adjust_goal",
                            "action": "Adjust Career Target",
                            "description": "Shift primary focus to Software Engineering & Systems, where deep probabilistic models are not a primary barrier.",
                            "cost": "0 weeks delay",
                            "recommended": False
                        },
                        {
                            "option_id": "opt_proceed_with_risk",
                            "action": "Proceed with Academic Risk",
                            "description": "Retain advanced AI electives in next semester's schedule, acknowledging workload strain.",
                            "cost": "High workload peak (14+ hrs/week)",
                            "recommended": False
                        }
                    ]
                })

        # Conflict 2: Software role with Data Structures & Algorithms deficiency
        if goal_id == "goal_software":
            ds_data = skill_matrix.get("data_structures") or skill_matrix.get("skill_dsa_trees", {})
            algo_data = skill_matrix.get("algorithms") or skill_matrix.get("skill_dsa_linear", {})
            dsa_level = (ds_data.get("p_mastery", 0.5) + algo_data.get("p_mastery", 0.5)) / 2.0

            if dsa_level < 0.70:
                alerts.append({
                    "alert_id": "gap_alert_swe_dsa_deficiency",
                    "severity": "high",
                    "title": "Critical Core Gap: Data Structures & Algorithms",
                    "evidence": (
                        f"Targeting Software Development roles requires at least 85% DSA proficiency. "
                        f"Your tested diagnostic mastery is currently {round(dsa_level*100)}%."
                    ),
                    "options": [
                        {
                            "option_id": "opt_prioritize_dsa",
                            "action": "Prioritize CSL202/CSL252 & Active Practice",
                            "description": "Dedicate upcoming elective headroom to Data Structures (CSL202) and hands-on algorithmic practice exercises.",
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
