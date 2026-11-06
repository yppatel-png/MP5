"""
Infeasible Request Handler.
Detects mathematically or regulatorily impossible student requests,
identifies the exact blocking institute rules, and synthesizes the closest valid alternative.
"""

from typing import List, Dict, Any, Optional
from backend.student.model import StudentStore
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.student.diagnostic import diagnostic_engine

class InfeasibleRequestHandler:
    def handle_excessive_credit_request(
        self,
        student_id: str,
        requested_credit_cap: float
    ) -> Dict[str, Any]:
        """
        Handles requests exceeding institute credit limits (e.g. 'give me 30 credits').
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        max_allowed = 24.0 if profile.cgpa >= 8.5 else 22.0

        if requested_credit_cap <= max_allowed:
            # Feasible, return regular plan
            return {"status": "feasible", "message": "Request is within institute credit limits."}

        # Infeasible: Identify blocking rule
        blocking_rule = {
            "rule_id": "rule_credit_cap_standard",
            "rule_name": "Standard Semester Credit Ceiling",
            "ordinance_clause": "IIT Delhi UG Ordinance Section 4.2",
            "explanation": f"You requested {requested_credit_cap} credits. Institute regulations strictly cap semester course registration at {max_allowed} credits (to ensure academic rigor and prevent student burnout)."
        }

        # Synthesize the closest valid alternative
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id)
        valid_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=max_allowed,
            overload_allowed=(profile.cgpa >= 8.5)
        )

        validation = independent_validator.validate_plan(valid_plan, profile.model_dump())

        # Determine which courses were capped out
        sem1 = valid_plan["semesters"][0] if valid_plan.get("semesters") else {}
        scheduled_credits = sem1.get("total_credits", 0.0)
        credits_denied = requested_credit_cap - scheduled_credits

        return {
            "status": "infeasible",
            "blocking_rule": blocking_rule,
            "requested_credits": requested_credit_cap,
            "max_allowed_credits": max_allowed,
            "credits_denied": round(credits_denied, 1),
            "explanation": (
                f"{blocking_rule['explanation']} "
                f"Here is the closest provably valid option capped at {max_allowed} credits, "
                f"which prioritizes your highest-urgency skill gaps while strictly passing all academic rules."
            ),
            "closest_valid_plan": valid_plan,
            "validation_report": validation
        }

    def handle_missing_prerequisite_request(
        self,
        student_id: str,
        desired_course_code: str
    ) -> Dict[str, Any]:
        """
        Handles requests to take an advanced course when prerequisites are unfulfilled.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        code_norm = desired_course_code.upper()
        reqs = multi_semester_planner.prereq_map.get(code_norm, [])
        completed_codes = set(c.course_code.upper() for c in profile.completed_courses)
        unmet_reqs = [r for r in reqs if r not in completed_codes]

        if not unmet_reqs:
            return {"status": "feasible", "message": f"Prerequisites for '{desired_course_code}' are satisfied."}

        blocking_rule = {
            "rule_id": "rule_prereq_strict_enforcement",
            "rule_name": "Prerequisite Passing Grade Enforcement",
            "ordinance_clause": "IIT Delhi UG Ordinance Section 5.1",
            "explanation": f"Cannot register for {code_norm}. You must first pass mandatory prerequisite(s): {', '.join(unmet_reqs)}."
        }

        # Construct recommended sequential bridge
        return {
            "status": "infeasible",
            "blocking_rule": blocking_rule,
            "desired_course": code_norm,
            "missing_prerequisites": unmet_reqs,
            "recommended_resolution": (
                f"Take {', '.join(unmet_reqs)} in upcoming Semester {profile.current_semester + 1}, "
                f"then take {code_norm} in Semester {profile.current_semester + 2}."
            )
        }

infeasible_handler = InfeasibleRequestHandler()

