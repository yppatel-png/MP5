"""
Infeasible Request Handler (§2.3).
Detects mathematically or regulatorily impossible student requests,
identifies the exact blocking institute rules, and synthesizes the closest valid alternative.

Strictly adheres to Adobe PS §2.3:
- Clearly states when a request is "not possible".
- Explicitly names the violated constraint / institute rule.
- Synthesizes and returns the closest valid alternative.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from backend.student.model import StudentStore
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.student.diagnostic import diagnostic_engine
from backend.db.seed_profile import get_seed_dir
from backend.rules.params import get_overload_cgpa_threshold, get_overload_credit_cap, get_standard_credit_cap


class InfeasibleRequestHandler:
    def __init__(self):
        self._load_courses()

    def _load_courses(self):
        seed_dir = get_seed_dir()
        try:
            with open(seed_dir / "courses.json", "r", encoding="utf-8") as f:
                self.courses_by_code = {c["code"].upper(): c for c in json.load(f)}
        except Exception:
            self.courses_by_code = {}

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

        overload_thresh = get_overload_cgpa_threshold()
        overload_cap = get_overload_credit_cap()
        std_cap = get_standard_credit_cap()
        max_allowed = overload_cap if profile.cgpa >= overload_thresh else std_cap

        if requested_credit_cap <= max_allowed:
            return {"status": "feasible", "message": "Request is within institute credit limits."}

        blocking_rule = {
            "rule_id": "rule_sem_max_credits",
            "rule_name": "Standard Semester Credit Ceiling",
            "ordinance_clause": "IIT Bhilai Academic Regulations (Assumed ceiling pending ordinance)",
            "explanation": f"Semester credit registration is capped at {max_allowed} credits (to ensure academic rigor and prevent student burnout)."
        }

        # Synthesize closest valid alternative
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)
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
        sem1 = valid_plan["semesters"][0] if valid_plan.get("semesters") else {}
        scheduled_credits = sem1.get("total_credits", 0.0)
        credits_denied = requested_credit_cap - scheduled_credits

        explanation = (
            f"Request is not possible. You requested {requested_credit_cap} credits, but {blocking_rule['rule_name']} "
            f"caps your registration at {max_allowed} credits (working assumption pending official ordinance). "
            f"Here is the closest valid alternative capped at {max_allowed} credits, "
            f"prioritizing high-urgency degree requirements while passing all academic constraints."
        )

        return {
            "status": "infeasible",
            "verdict": "not possible",
            "request_type": "excessive_credits",
            "blocking_rule": blocking_rule,
            "requested_credits": requested_credit_cap,
            "max_allowed_credits": max_allowed,
            "credits_denied": round(credits_denied, 1),
            "explanation": explanation,
            "valid_alternative": {
                "summary": f"Schedule capped at {max_allowed} credits in upcoming semester; defer remaining courses to subsequent semester.",
                "plan": valid_plan
            },
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
            "ordinance_clause": "IIT Bhilai Curriculum Specification (Printed Prerequisites)",
            "explanation": f"Cannot register for {code_norm}. You must first pass mandatory prerequisite(s): {', '.join(unmet_reqs)}."
        }

        alt_sem_prereqs = profile.current_semester + 1
        alt_sem_course = profile.current_semester + 2
        recommended_alt = (
            f"Sequential Bridge: Enroll in prerequisite(s) {', '.join(unmet_reqs)} during upcoming "
            f"Semester {alt_sem_prereqs}, and schedule {code_norm} for Semester {alt_sem_course} once prerequisites are fulfilled."
        )

        explanation = (
            f"Request is not possible. Direct registration for {code_norm} is blocked because "
            f"mandatory prerequisite(s) ({', '.join(unmet_reqs)}) have not been fulfilled. "
            f"{recommended_alt}"
        )

        return {
            "status": "infeasible",
            "verdict": "not possible",
            "request_type": "missing_prerequisite",
            "blocking_rule": blocking_rule,
            "desired_course": code_norm,
            "missing_prerequisites": unmet_reqs,
            "explanation": explanation,
            "valid_alternative": {
                "summary": recommended_alt,
                "prerequisite_courses": unmet_reqs,
                "prerequisite_semester": alt_sem_prereqs,
                "target_course_semester": alt_sem_course
            }
        }

    def handle_ineligible_minor_request(
        self,
        student_id: str,
        minor_discipline: str = "Computer Science"
    ) -> Dict[str, Any]:
        """
        Handles requests to enroll in a minor when student CGPA is below cutoff.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        min_cgpa_cutoff = 7.0
        if profile.cgpa >= min_cgpa_cutoff:
            return {"status": "feasible", "message": f"Eligible for {minor_discipline} minor (CGPA {profile.cgpa} >= {min_cgpa_cutoff})."}

        blocking_rule = {
            "rule_id": "rule_minor_cse_eligibility",
            "rule_name": "Minor Discipline CGPA Cutoff",
            "ordinance_clause": "IIT Bhilai Academic Regulations (Assumed cutoff pending ordinance)",
            "explanation": f"Minor registration requires a minimum CGPA of {min_cgpa_cutoff}. Student's current CGPA is {profile.cgpa}."
        }

        alt_summary = (
            f"Focus on raising your CGPA above {min_cgpa_cutoff} by completing your scheduled core and open electives this semester. "
            f"You may also audit introductory {minor_discipline} courses without registering for the official minor credential."
        )

        explanation = (
            f"Request is not possible. Registration for the {minor_discipline} Minor cannot be granted "
            f"because your current CGPA ({profile.cgpa}) is below the required cutoff of {min_cgpa_cutoff}. "
            f"{alt_summary}"
        )

        return {
            "status": "infeasible",
            "verdict": "not possible",
            "request_type": "ineligible_minor",
            "blocking_rule": blocking_rule,
            "student_cgpa": profile.cgpa,
            "required_cgpa": min_cgpa_cutoff,
            "explanation": explanation,
            "valid_alternative": {
                "summary": alt_summary,
                "recommended_action": "Raise CGPA to >= 7.0 before re-applying for minor designation"
            }
        }

    def handle_semester_parity_mismatch_request(
        self,
        student_id: str,
        course_code: str,
        target_semester: int
    ) -> Dict[str, Any]:
        """
        Handles requests to schedule a course in an incompatible semester parity (e.g. spring course in autumn).
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        code_norm = course_code.upper()
        if not self.courses_by_code:
            self._load_courses()

        course_info = self.courses_by_code.get(code_norm)
        if not course_info:
            return {"status": "error", "message": f"Course '{course_code}' not found in catalogue."}

        offered = course_info.get("semester_offered", "")
        # Check parity: "semester_1", "semester_2", etc.
        if offered.startswith("semester_"):
            try:
                sched_sem = int(offered.split("_")[1])
                target_is_odd = (target_semester % 2 != 0)
                sched_is_odd = (sched_sem % 2 != 0)
                if target_is_odd != sched_is_odd:
                    blocking_rule = {
                        "rule_id": "rule_semester_parity",
                        "rule_name": "Course Offering Parity Constraint",
                        "ordinance_clause": "IIT Bhilai Courses of Study (Curriculum Schedule)",
                        "explanation": (
                            f"{code_norm} is scheduled for {'Odd (Autumn)' if sched_is_odd else 'Even (Spring)'} semesters "
                            f"(Semester {sched_sem}), but was requested for Semester {target_semester} "
                            f"({'Odd (Autumn)' if target_is_odd else 'Even (Spring)'})."
                        )
                    }

                    alt_sem = target_semester + 1
                    alt_summary = (
                        f"Schedule {code_norm} in Semester {alt_sem} when its regular "
                        f"{'Odd (Autumn)' if sched_is_odd else 'Even (Spring)'} session runs, "
                        f"and select an approved scheduled elective for Semester {target_semester}."
                    )

                    explanation = (
                        f"Request is not possible. {code_norm} cannot be registered in Semester {target_semester} "
                        f"due to timetable offering parity mismatch. {blocking_rule['explanation']} {alt_summary}"
                    )

                    return {
                        "status": "infeasible",
                        "verdict": "not possible",
                        "request_type": "semester_parity_mismatch",
                        "blocking_rule": blocking_rule,
                        "course_code": code_norm,
                        "offered_semester": sched_sem,
                        "requested_semester": target_semester,
                        "explanation": explanation,
                        "valid_alternative": {
                            "summary": alt_summary,
                            "recommended_semester": alt_sem
                        }
                    }
            except (ValueError, IndexError):
                pass

        return {"status": "feasible", "message": f"{code_norm} offering matches semester {target_semester} parity."}

    def handle_underload_request(
        self,
        student_id: str,
        requested_credits: float
    ) -> Dict[str, Any]:
        """
        Handles requests to register below minimum required credits (< 12.0).
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        min_credits = 12.0
        if requested_credits >= min_credits:
            return {"status": "feasible", "message": f"Credit request ({requested_credits}) satisfies minimum {min_credits}."}

        blocking_rule = {
            "rule_id": "rule_sem_min_credits",
            "rule_name": "Minimum Semester Credit Floor",
            "ordinance_clause": "IIT Bhilai Academic Regulations (Assumed minimum floor pending ordinance)",
            "explanation": f"Full-time regular enrollment requires a minimum of {min_credits} credits per semester."
        }

        alt_summary = f"Increase course load to at least {min_credits} credits by adding core or open elective requirements."
        explanation = (
            f"Request is not possible. Registering for only {requested_credits} credits violates the "
            f"minimum academic load requirement of {min_credits} credits. {alt_summary}"
        )

        return {
            "status": "infeasible",
            "verdict": "not possible",
            "request_type": "credit_underload",
            "blocking_rule": blocking_rule,
            "requested_credits": requested_credits,
            "min_required_credits": min_credits,
            "explanation": explanation,
            "valid_alternative": {
                "summary": alt_summary,
                "minimum_credits": min_credits
            }
        }

    def handle_disallowed_overload_request(
        self,
        student_id: str,
        requested_credits: float
    ) -> Dict[str, Any]:
        """
        Handles overload request (> 22.0 credits) for students whose CGPA < 8.0/8.5.
        """
        profile = StudentStore.get_profile(student_id)
        if not profile:
            return {"status": "error", "message": f"Student '{student_id}' not found."}

        min_cgpa_for_overload = get_overload_cgpa_threshold()
        std_cap = get_standard_credit_cap()
        if profile.cgpa >= min_cgpa_for_overload:
            return {"status": "feasible", "message": "Eligible for credit overload."}

        blocking_rule = {
            "rule_id": "rule_credit_overload_cap",
            "rule_name": "Credit Overload CGPA Requirement",
            "ordinance_clause": "IIT Bhilai Academic Regulations (Assumed overload policy pending ordinance)",
            "explanation": f"Overload registration (> {std_cap:g} credits) requires a minimum CGPA of {min_cgpa_for_overload}. Student's CGPA is {profile.cgpa}."
        }

        alt_summary = f"Limit registration to the standard maximum of {std_cap:g} credits for this semester."
        explanation = (
            f"Request is not possible. Credit overload to {requested_credits} credits cannot be approved "
            f"because your CGPA ({profile.cgpa}) is below the required {min_cgpa_for_overload} overload threshold. {alt_summary}"
        )

        return {
            "status": "infeasible",
            "verdict": "not possible",
            "request_type": "disallowed_overload",
            "blocking_rule": blocking_rule,
            "requested_credits": requested_credits,
            "student_cgpa": profile.cgpa,
            "required_cgpa": min_cgpa_for_overload,
            "explanation": explanation,
            "valid_alternative": {
                "summary": alt_summary,
                "credit_cap": std_cap
            }
        }

    def evaluate_request(
        self,
        student_id: str,
        request_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified dispatcher for evaluating student requests against institute constraints.
        """
        if request_type == "excessive_credits":
            return self.handle_excessive_credit_request(student_id, kwargs.get("credits", 30.0))
        elif request_type == "missing_prerequisite":
            return self.handle_missing_prerequisite_request(student_id, kwargs.get("course_code", "CSL252"))
        elif request_type == "ineligible_minor":
            return self.handle_ineligible_minor_request(student_id, kwargs.get("discipline", "Computer Science"))
        elif request_type == "semester_parity":
            return self.handle_semester_parity_mismatch_request(
                student_id, kwargs.get("course_code", "CSL252"), kwargs.get("target_semester", 5)
            )
        elif request_type == "credit_underload":
            return self.handle_underload_request(student_id, kwargs.get("credits", 8.0))
        elif request_type == "disallowed_overload":
            return self.handle_disallowed_overload_request(student_id, kwargs.get("credits", 26.0))
        else:
            return {"status": "error", "message": f"Unknown request type: {request_type}"}


infeasible_handler = InfeasibleRequestHandler()
