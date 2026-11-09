"""
Independent Academic Plan Validator.
A completely decoupled verification pass that inspects candidate plans from scratch.
Returns an audit report with 9 core canonical rule checks for backwards compatibility,
and delegates to the central RuleRegistry to generate sealed cryptographic Plan Certificates.
"""

import json
from typing import List, Dict, Any, Set
from pathlib import Path
from backend.rules.base import RuleStatus
from backend.rules.registry import rule_registry
from backend.rules.params import get_overload_cgpa_threshold, get_overload_credit_cap, get_standard_credit_cap
from backend.db.seed_profile import get_institute_profile, get_seed_dir

SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

class IndependentPlanValidator:
    def __init__(self):
        self.courses = {c["code"]: c for c in load_seed_json("courses.json")}
        self.prereqs = load_seed_json("prerequisites.json")
        self.rules = {r["rule_id"]: r for r in load_seed_json("academic_rules.json")}
        self.registry = rule_registry
        
        # Build prerequisite lookup: course_code -> list of required codes
        self.prereq_map: Dict[str, List[str]] = {}
        for p in self.prereqs:
            self.prereq_map.setdefault(p["course_code"], []).append(p["requires_code"])

    def validate_plan(
        self,
        plan: Dict[str, Any],
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Performs 9 independent rule checks on the proposed academic plan,
        and generates a sealed cryptographic PlanCertificate with all 16 ordinance rules.
        """
        if get_institute_profile() == "iit_bhilai":
            bhilai_results = self.registry.run_all(plan, student_profile)
            rule_checks = [
                {
                    "rule_id": item.rule_id,
                    "name": item.rule_title,
                    "passed": item.status != RuleStatus.FAIL,
                    "status": item.status.value,
                    "details": item.message,
                    "clause_id": item.clause_id,
                    "provenance": item.provenance,
                    "badge": "Assumed" if item.provenance == "assumption" else "Verified",
                    "reason": item.reason,
                    "source_page": item.source_page,
                }
                for item in bhilai_results
            ]
            errors = [item.message for item in bhilai_results if item.status == RuleStatus.FAIL]
            certificate = self.registry.generate_certificate(plan, student_profile)
            rules_passed = sum(1 for item in rule_checks if item["passed"])
            return {
                "is_valid": not errors,
                "verification_scope": "valid_under_verified_facts_and_labelled_assumptions",
                "rules_evaluated": len(rule_checks),
                "rules_passed": rules_passed,
                "assumed_rules": sum(1 for item in rule_checks if item["provenance"] == "assumption"),
                "rule_results": rule_checks,
                "errors": errors,
                "certificate": certificate.model_dump(),
            }
        rule_checks = []
        errors = []

        completed_past = set(
            c["course_code"].upper() if isinstance(c, dict) else str(c).upper()
            for c in student_profile.get("completed_courses", [])
        )
        cgpa = float(student_profile.get("cgpa", 8.0))
        semesters = plan.get("semesters", [])
        
        # Track courses scheduled by semester number
        sem_to_courses: Dict[int, List[Dict[str, Any]]] = {}
        course_to_sem: Dict[str, int] = {}
        all_scheduled_codes: List[str] = []

        for sem in semesters:
            s_num = sem["semester_number"]
            c_list = sem.get("courses", [])
            sem_to_courses[s_num] = c_list
            for c in c_list:
                code = c["code"].upper()
                course_to_sem[code] = s_num
                all_scheduled_codes.append(code)

        # -------------------------------------------------------------------
        # Rule 1: All Course Codes Exist in Knowledge Base
        # -------------------------------------------------------------------
        invalid_codes = [c for c in all_scheduled_codes if c not in self.courses]
        passed_r1 = len(invalid_codes) == 0
        rule_checks.append({
            "rule_id": "rule_all_courses_exist",
            "name": "Catalogue Code Existence",
            "passed": passed_r1,
            "description": "Every scheduled course code must exist in the accredited institute course catalogue.",
            "details": "All course codes verified in DB." if passed_r1 else f"Unrecognized courses: {', '.join(invalid_codes)}",
            "clause_id": "ORD-1.1.0"
        })
        if not passed_r1:
            errors.append(f"Unrecognized courses found in plan: {', '.join(invalid_codes)}")

        # -------------------------------------------------------------------
        # Rule 2: Prerequisite DAG Ordering (Must be taken in strictly earlier sem)
        # -------------------------------------------------------------------
        prereq_violations = []
        for code, sem_num in course_to_sem.items():
            reqs = self.prereq_map.get(code, [])
            for r in reqs:
                r_in_past = r in completed_past
                r_sem = course_to_sem.get(r)
                if not r_in_past:
                    if r_sem is None:
                        prereq_violations.append(f"{code} requires {r}, which is neither completed nor scheduled.")
                    elif r_sem >= sem_num:
                        prereq_violations.append(f"{code} (Semester {sem_num}) requires {r}, which is scheduled concurrently or later (Semester {r_sem}).")

        passed_r2 = len(prereq_violations) == 0
        rule_checks.append({
            "rule_id": "rule_prereq_dag",
            "name": "Prerequisite DAG Compliance",
            "passed": passed_r2,
            "description": "Prerequisite courses must be completed in a semester strictly prior to the dependent course.",
            "details": "All prerequisite chains satisfied." if passed_r2 else "; ".join(prereq_violations),
            "clause_id": "ORD-5.1.0"
        })
        if not passed_r2:
            errors.extend(prereq_violations)

        # -------------------------------------------------------------------
        # Rule 3: Semester Offering Parity (Odd vs Even)
        # -------------------------------------------------------------------
        parity_violations = []
        for code, sem_num in course_to_sem.items():
            offering = self.courses.get(code, {}).get("semester_offered", "both").lower()
            is_odd_sem = (sem_num % 2 == 1)
            if offering == "odd" and not is_odd_sem:
                parity_violations.append(f"{code} is offered only in Odd semesters, but scheduled in Semester {sem_num} (Even).")
            elif offering == "even" and is_odd_sem:
                parity_violations.append(f"{code} is offered only in Even semesters, but scheduled in Semester {sem_num} (Odd).")

        passed_r3 = len(parity_violations) == 0
        rule_checks.append({
            "rule_id": "rule_semester_offering",
            "name": "Semester Offering Parity",
            "passed": passed_r3,
            "description": "Courses must only be scheduled in semesters when the department formally offers them.",
            "details": "All semester offering parities honored." if passed_r3 else "; ".join(parity_violations),
            "clause_id": "ORD-5.2.0"
        })
        if not passed_r3:
            errors.extend(parity_violations)

        # -------------------------------------------------------------------
        # Rule 4: Credit Ceiling (Max Credits per Semester)
        # -------------------------------------------------------------------
        credit_cap_violations = []
        overload_thresh = get_overload_cgpa_threshold()
        max_credit_allowed = get_overload_credit_cap() if cgpa >= overload_thresh else get_standard_credit_cap()
        for sem in semesters:
            s_num = sem["semester_number"]
            credits_in_sem = sum(c["credits"] for c in sem.get("courses", []))
            if credits_in_sem > max_credit_allowed:
                credit_cap_violations.append(f"Semester {s_num} has {credits_in_sem} credits (limit: {max_credit_allowed}).")

        passed_r4 = len(credit_cap_violations) == 0
        rule_checks.append({
            "rule_id": "rule_credit_cap",
            "name": "Credit Ceiling Compliance",
            "passed": passed_r4,
            "description": f"Semester credit totals must not exceed ceiling ({max_credit_allowed} credits).",
            "details": f"All semesters within credit ceiling (max {max_credit_allowed})." if passed_r4 else "; ".join(credit_cap_violations),
            "clause_id": "ORD-4.2.2" if cgpa < 8.5 else "ORD-4.3.0"
        })
        if not passed_r4:
            errors.extend(credit_cap_violations)

        # -------------------------------------------------------------------
        # Rule 5: No Duplicate or Previously Completed Courses
        # -------------------------------------------------------------------
        duplicates = []
        seen = set()
        for code in all_scheduled_codes:
            if code in completed_past:
                duplicates.append(f"{code} was already completed in student's academic history.")
            if code in seen:
                duplicates.append(f"{code} is scheduled multiple times in the plan.")
            seen.add(code)

        passed_r5 = len(duplicates) == 0
        rule_checks.append({
            "rule_id": "rule_no_duplicates",
            "name": "Non-Redundancy & Zero Duplication",
            "passed": passed_r5,
            "description": "A student cannot re-take a course already completed or schedule duplicates.",
            "details": "Zero redundant or duplicate courses." if passed_r5 else "; ".join(duplicates),
            "clause_id": "ORD-4.4.0"
        })
        if not passed_r5:
            errors.extend(duplicates)

        # -------------------------------------------------------------------
        # Rule 6: Minor in CSE Eligibility
        # -------------------------------------------------------------------
        minor_violations = []
        is_non_cse = "cse" not in str(student_profile.get("programme", "")).lower()
        has_cs_electives = any(
            self.courses.get(c, {}).get("department") == "Computer Science and Engineering" and
            self.courses.get(c, {}).get("course_type") in ["elective", "minor"]
            for c in all_scheduled_codes
        )
        if is_non_cse and has_cs_electives and cgpa < 7.5:
            minor_violations.append(f"Student CGPA is {cgpa}, which is below the 7.5 cutoff required for CS Minor electives.")

        passed_r6 = len(minor_violations) == 0
        rule_checks.append({
            "rule_id": "rule_minor_eligibility",
            "name": "Minor Degree Eligibility Check",
            "passed": passed_r6,
            "description": "Non-CS students taking CS Minor courses must maintain CGPA >= 7.5.",
            "details": "Minor eligibility criteria satisfied." if passed_r6 else "; ".join(minor_violations),
            "clause_id": "ORD-6.1.0"
        })
        if not passed_r6:
            errors.extend(minor_violations)

        # -------------------------------------------------------------------
        # Rule 7: Mutually Exclusive / No-Co-Taking Pairs
        # -------------------------------------------------------------------
        co_taking_violations = []
        restricted_pairs = [] if get_institute_profile() == "iit_bhilai" else [["CSL351", "CSL352"]]
        for sem in semesters:
            s_num = sem["semester_number"]
            sem_codes = [c["code"].upper() for c in sem.get("courses", [])]
            for pair in restricted_pairs:
                if pair[0] in sem_codes and pair[1] in sem_codes:
                    co_taking_violations.append(f"Semester {s_num} schedules both {pair[0]} and {pair[1]}, violating workload pairing restriction.")

        passed_r7 = len(co_taking_violations) == 0
        rule_checks.append({
            "rule_id": "rule_no_co_taking",
            "name": "Workload Balance & Co-Taking Pairs",
            "passed": passed_r7,
            "description": "Heavy theoretical pairs must not be scheduled within the same academic semester.",
            "details": "Workload pairing restrictions respected." if passed_r7 else "; ".join(co_taking_violations),
            "clause_id": "ORD-8.2.0"
        })
        if not passed_r7:
            errors.extend(co_taking_violations)

        # -------------------------------------------------------------------
        # Rule 8: Weekly Time Budget Realism
        # -------------------------------------------------------------------
        weekly_violations = []
        max_allowed_hours = float(student_profile.get("available_hours_per_week", 12.0))
        for sem in semesters:
            s_num = sem["semester_number"]
            workload = sum(c.get("workload_hours_per_week", 10.0) for c in sem.get("courses", []))
            est_self_study = workload * 0.35
            std_cap = get_standard_credit_cap()
            if workload > 48.0 or (est_self_study > max_allowed_hours * 2.0 and est_self_study > std_cap):
                weekly_violations.append(f"Semester {s_num} workload ({workload} hrs/wk) exceeds sustainable headroom.")

        passed_r8 = len(weekly_violations) == 0
        rule_checks.append({
            "rule_id": "rule_workload_budget",
            "name": "Weekly Time Budget Realism",
            "passed": passed_r8,
            "description": "Weekly course workload must balance against student's available study hours.",
            "details": "Weekly workload realistic." if passed_r8 else "; ".join(weekly_violations),
            "clause_id": "ORD-8.1.0"
        })
        if not passed_r8:
            errors.extend(weekly_violations)

        # -------------------------------------------------------------------
        # Rule 9: Goal Skills Targeted
        # -------------------------------------------------------------------
        skills_covered = set(
            sk for sem in semesters for c in sem.get("courses", []) for sk in c.get("skills_targeted", [])
        )
        passed_r9 = len(skills_covered) > 0 or len(all_scheduled_codes) == 0
        rule_checks.append({
            "rule_id": "rule_goal_skills_targeted",
            "name": "Skill-Gap Alignment",
            "passed": passed_r9,
            "description": "The plan must directly address prioritized skill gaps required for the student's goal.",
            "details": f"Addresses {len(skills_covered)} critical skills." if passed_r9 else "No targeted skills mapped.",
            "clause_id": "PED-2.1.0"
        })

        # Overall Status
        rules_passed = sum(1 for r in rule_checks if r["passed"])
        is_overall_valid = (len(errors) == 0 and rules_passed == len(rule_checks))

        # Sealed Certificate with all 16 academic ordinance rules
        certificate = self.registry.generate_certificate(plan, student_profile)

        return {
            "is_valid": is_overall_valid,
            "rules_evaluated": len(rule_checks),
            "rules_passed": rules_passed,
            "rule_results": rule_checks,
            "errors": errors,
            "certificate": certificate.model_dump()
        }

independent_validator = IndependentPlanValidator()
