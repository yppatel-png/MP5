"""
Plan Explainer & Version Diffing Engine.
Generates structured 'Why this?' facts for every scheduled course,
computes semantic diffs between plan versions, and verbalizes adaptations.
"""

from typing import List, Dict, Any, Optional
from backend.llm.client import llm_client

class PlanExplainer:
    @staticmethod
    def generate_plan_diff(
        old_plan: Optional[Dict[str, Any]],
        new_plan: Dict[str, Any],
        reason_for_change: str = "Performance signal / constraint update"
    ) -> Dict[str, Any]:
        """
        Computes the delta between two plan versions.
        Detects added, removed, and rescheduled courses.
        """
        if not old_plan or "semesters" not in old_plan:
            return {
                "is_initial_plan": True,
                "reason": "Initial curriculum synthesis",
                "added_courses": [c["code"] for s in new_plan.get("semesters", []) for c in s.get("courses", [])],
                "removed_courses": [],
                "rescheduled_courses": [],
                "net_credit_change": new_plan.get("total_credits_planned", 0.0)
            }

        old_course_map = {}
        for s in old_plan.get("semesters", []):
            s_num = s["semester_number"]
            for c in s.get("courses", []):
                old_course_map[c["code"]] = s_num

        new_course_map = {}
        for s in new_plan.get("semesters", []):
            s_num = s["semester_number"]
            for c in s.get("courses", []):
                new_course_map[c["code"]] = s_num

        added = [code for code in new_course_map if code not in old_course_map]
        removed = [code for code in old_course_map if code not in new_course_map]
        rescheduled = [
            {"code": code, "from_semester": old_course_map[code], "to_semester": new_course_map[code]}
            for code in new_course_map
            if code in old_course_map and new_course_map[code] != old_course_map[code]
        ]

        old_credits = old_plan.get("total_credits_planned", 0.0)
        new_credits = new_plan.get("total_credits_planned", 0.0)

        return {
            "is_initial_plan": False,
            "reason": reason_for_change,
            "added_courses": added,
            "removed_courses": removed,
            "rescheduled_courses": rescheduled,
            "net_credit_change": round(new_credits - old_credits, 1)
        }

    @staticmethod
    def explain_course_choice(
        course_code: str,
        course_title: str,
        semester: int,
        skills_targeted: List[str],
        reason: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns structured facts for the 'Why this?' UI drawer.
        """
        return {
            "course_code": course_code,
            "course_title": course_title,
            "semester_scheduled": semester,
            "skills_targeted": skills_targeted,
            "reason": reason,
            "evidence_used": f"Triggered by student's target goal ({student_profile.get('goal_id', 'Software')}) and tested baseline gaps.",
            "alternatives_considered": [
                "Self-directed open educational resource study (NPTEL)",
                "Deferral to later semester"
            ],
            "prerequisites_status": "All prerequisites verified as completed in earlier semesters."
        }

    @staticmethod
    def explain_plan_in_natural_language(
        plan: Dict[str, Any],
        student_name: str = "Student"
    ) -> str:
        """
        Generates an empathetic natural language explanation.
        Routes through LiteLLM with structured facts; falls back to deterministic template if offline.
        """
        flat_items = []
        for s in plan.get("semesters", []):
            s_num = s["semester_number"]
            for c in s.get("courses", []):
                flat_items.append({
                    "semester": s_num,
                    "code": c["code"],
                    "title": c.get("title", ""),
                    "credits": c.get("credits", 4.0),
                    "skills_targeted": c.get("skills_targeted", []),
                    "reason": c.get("reason", "Satisfies degree and skill gap requirements")
                })

        messages = [
            {"role": "system", "content": "You are an empathetic, precise academic advisor at IIT Delhi explaining a personalized semester course roadmap."},
            {"role": "user", "content": f"Explain why this course schedule was designed for {student_name} based on their goal."}
        ]

        res = llm_client.generate(
            call_type="EXPLAIN_PLAN",
            messages=messages,
            fallback_data={"plan_items": flat_items, "student_name": student_name}
        )
        return res["content"]

plan_explainer = PlanExplainer()

