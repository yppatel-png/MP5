"""
Independent Plan Validity Unit & Parity Tests (§2.3 Personalisation)
Implements an independent, minimal standalone plan validator decoupled from the rule engine.
Validates:
1. Credit ceilings (minimum 12.0, standard cap 24.0, overload cap 27.0 if CGPA >= 8.0).
2. Strict prerequisite ordering (prerequisites must be completed in strictly prior semesters).
3. Semester offering parity (Odd / Autumn vs. Even / Spring).
4. No re-assignment of already mastered/completed content.
Compares independent validation results against the production Rule Registry across profiles.
Disagreements between independent validator and rule registry are treated as test failures.
"""

import copy
import json
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from backend.db.seed_loader import load_seed_data
from backend.planner.solver import multi_semester_planner
from backend.rules import rule_registry
from backend.student.diagnostic import diagnostic_engine
from backend.student.model import StudentStore, StudentProfile

ROOT_DIR = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT_DIR / "data" / "seed_bhilai"


def load_raw_curriculum_catalog() -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]]]:
    """Loads raw courses and prerequisite mappings directly from plain JSON seed files."""
    with open(SEED_DIR / "courses.json", "r", encoding="utf-8") as f:
        courses_list = json.load(f)
    catalog = {(c.get("code") or c.get("course_code", "")).upper(): c for c in courses_list}

    with open(SEED_DIR / "prerequisites.json", "r", encoding="utf-8") as f:
        prereq_list = json.load(f)

    prereq_map: Dict[str, List[str]] = {}
    for p in prereq_list:
        target = (p.get("course_code") or p.get("code", "")).upper()
        req = (p.get("requires_code") or p.get("prereq_code", "")).upper()
        if target and req:
            prereq_map.setdefault(target, []).append(req)

    return catalog, prereq_map


def validate_plan_independently(
    plan: Dict[str, Any],
    profile: Dict[str, Any],
    catalog: Dict[str, Dict[str, Any]],
    prereq_map: Dict[str, List[str]],
) -> Dict[str, Any]:
    """
    Minimal standalone plan validator written independently of the rule engine.
    Returns: {"is_valid": bool, "violations": List[str], "warnings": List[str]}
    """
    violations: List[str] = []
    warnings: List[str] = []
    cgpa = float(profile.get("cgpa", 7.0))
    completed_codes = {
        (c["course_code"] if isinstance(c, dict) else str(c)).upper()
        for c in profile.get("completed_courses", [])
    }

    max_credit_cap = 27.0 if cgpa >= 8.0 else 24.0
    min_credit_floor = 12.0

    mastered_so_far: Set[str] = set(completed_codes)
    semesters = plan.get("semesters", [])
    total_semesters = len(semesters)

    for idx, sem in enumerate(semesters):
        sem_num = sem.get("semester_number", idx + 1)
        courses = sem.get("courses", [])

        # 1. Credit ceiling & floor check
        sem_credits = 0.0
        for c in courses:
            code = (c.get("code") or c.get("course_code", "")).upper()
            cat_entry = catalog.get(code, {})
            credits = cat_entry.get("credits") or c.get("credits") or 0.0
            sem_credits += float(credits)

        if sem_credits > max_credit_cap:
            violations.append(
                f"Credit overload in Semester {sem_num}: {sem_credits:.1f} credits exceeds cap {max_credit_cap:.1f}."
            )

        if courses and sem_credits < min_credit_floor:
            warnings.append(
                f"Credit underload in Semester {sem_num}: {sem_credits:.1f} credits below recommended floor {min_credit_floor:.1f}."
            )

        # 2. Per-course prerequisite, parity, and duplication checks
        sem_course_codes: List[str] = []
        for c in courses:
            code = (c.get("code") or c.get("course_code", "")).upper()
            sem_course_codes.append(code)

            # Check duplication / already mastered
            if code in completed_codes:
                violations.append(
                    f"Mastered course re-assigned in Semester {sem_num}: {code} was already completed."
                )

            # Check catalog validity
            cat_entry = catalog.get(code)
            if not cat_entry:
                violations.append(f"Unknown or hallucinated course in Semester {sem_num}: {code}.")
                continue

            # Check semester offering slot / annual parity
            slot = cat_entry.get("semester_offered", "catalogue_unscheduled")
            if slot and slot != "catalogue_unscheduled":
                is_sem_odd = (sem_num % 2 == 1)
                slot_clean = str(slot).lower().strip()
                if slot_clean in ["both", "all", "any", "either", "any_semester"]:
                    slot_matches = True
                elif slot_clean in ["odd", "autumn", "monsoon"]:
                    slot_matches = is_sem_odd
                elif slot_clean in ["even", "spring", "winter"]:
                    slot_matches = not is_sem_odd
                elif slot_clean.startswith("semester_"):
                    try:
                        orig_sem = int(slot_clean.split("_")[1])
                        slot_matches = ((orig_sem % 2 == 1) == is_sem_odd)
                    except (ValueError, IndexError):
                        slot_matches = (slot == f"semester_{sem_num}")
                else:
                    slot_matches = (slot == f"semester_{sem_num}")
                if not slot_matches:
                    violations.append(
                        f"Semester offering slot clash in Semester {sem_num}: {code} is scheduled for {slot}."
                    )

            # Check prerequisite satisfaction (must be completed strictly prior to current semester)
            for req in prereq_map.get(code, []):
                if req in catalog and req not in mastered_so_far:
                    violations.append(
                        f"Unmet prerequisite for {code} in Semester {sem_num}: required course {req} not completed."
                    )

        # Update mastered courses for subsequent semesters
        mastered_so_far.update(sem_course_codes)

    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
    }


class TestPlanValidityIndependent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)
        cls.catalog, cls.prereq_map = load_raw_curriculum_catalog()

    def test_01_independent_vs_engine_parity_on_hero_personas(self):
        """Verifies 100% agreement between independent validator and Rule Registry on hero personas."""
        personas = ["BH-SW-001", "BH-HS-001", "BH-UP-001"]

        for pid in personas:
            profile = StudentStore.get_profile(pid)
            self.assertIsNotNone(profile, f"Hero persona {pid} must exist.")
            gaps = diagnostic_engine.compute_skill_gaps(pid)
            plan = multi_semester_planner.plan_curriculum(
                student_id=pid,
                programme_code=profile.programme,
                current_semester=profile.current_semester,
                cgpa=profile.cgpa,
                completed_courses=[c.course_code for c in profile.completed_courses],
                skill_gaps=gaps.get("gaps", []),
                goal_id=profile.goal_id,
            )

            # 1. Independent validation
            indep_res = validate_plan_independently(
                plan, profile.model_dump(), self.catalog, self.prereq_map
            )

            # 2. Production rule registry evaluation
            cert = rule_registry.generate_certificate(plan, profile.model_dump())

            # 3. Assert mutual agreement
            self.assertTrue(
                indep_res["is_valid"],
                f"Independent validator rejected plan for {pid}: {indep_res['violations']}",
            )
            self.assertTrue(
                cert.is_valid,
                f"Rule Registry rejected plan for {pid}: {cert.summary.failed} failed checks",
            )
            self.assertEqual(
                indep_res["is_valid"],
                cert.is_valid,
                f"Parity mismatch for {pid}: independent={indep_res['is_valid']}, engine={cert.is_valid}",
            )

    def test_02_independent_vs_engine_on_synthetic_profiles(self):
        """Verifies mutual agreement across a representative sample of synthetic profiles."""
        synthetic_ids = ["BH-SYN-001", "BH-SYN-002", "BH-SYN-003", "BH-SYN-004", "BH-SYN-005"]

        for sid in synthetic_ids:
            profile = StudentStore.get_profile(sid)
            if not profile:
                eval_file = ROOT_DIR / "data" / "eval" / "synthetic_profiles.json"
                if eval_file.exists():
                    with open(eval_file, "r", encoding="utf-8") as f:
                        for sp in json.load(f):
                            if sp["student_id"] == sid:
                                profile = StudentProfile(**sp)
                                StudentStore.save_profile(profile)
                                break
            if not profile:
                continue
            gaps = diagnostic_engine.compute_skill_gaps(sid)
            plan = multi_semester_planner.plan_curriculum(
                student_id=sid,
                programme_code=profile.programme,
                current_semester=profile.current_semester,
                cgpa=profile.cgpa,
                completed_courses=[c.course_code for c in profile.completed_courses],
                skill_gaps=gaps.get("gaps", []),
                goal_id=profile.goal_id,
            )

            indep_res = validate_plan_independently(
                plan, profile.model_dump(), self.catalog, self.prereq_map
            )
            cert = rule_registry.generate_certificate(plan, profile.model_dump())

            self.assertEqual(
                indep_res["is_valid"],
                cert.is_valid,
                f"Disagreement on synthetic student {sid}: independent={indep_res['is_valid']} vs engine={cert.is_valid}",
            )

    def test_03_detect_prerequisite_inversion_mutation(self):
        """Mutation test: Both independent validator and engine must catch inverted prerequisite order."""
        profile = StudentStore.get_profile("BH-SW-001")
        gaps = diagnostic_engine.compute_skill_gaps("BH-SW-001")
        plan = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps.get("gaps", []),
            goal_id=profile.goal_id,
        )

        # Mutate plan: schedule CSL252 (requires CSL202) into Semester 5, but remove CSL202 from history
        mutated_plan = copy.deepcopy(plan)
        mutated_profile = profile.model_dump()
        # Remove CSL202 from completed courses and earlier semesters
        mutated_profile["completed_courses"] = [
            c for c in mutated_profile["completed_courses"] if c.get("course_code") != "CSL202"
        ]
        # Insert CSL252 in first plan semester
        mutated_plan["semesters"][0]["courses"].append({
            "code": "CSL252",
            "title": "Discrete Mathematics & Graph Theory",
            "credits": 4.0,
            "course_type": "core",
        })

        indep = validate_plan_independently(
            mutated_plan, mutated_profile, self.catalog, self.prereq_map
        )
        cert = rule_registry.generate_certificate(mutated_plan, mutated_profile)

        # Both must independently detect failure
        self.assertFalse(indep["is_valid"], "Independent validator must catch unmet prerequisite.")
        self.assertFalse(cert.is_valid, "Rule Registry must catch unmet prerequisite.")
        self.assertEqual(indep["is_valid"], cert.is_valid)

    def test_04_detect_credit_overload_mutation(self):
        """Mutation test: Both independent validator and engine must catch semester credit overload."""
        profile = StudentStore.get_profile("BH-SW-001")
        plan = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=7.0,  # Standard cap 24.0
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=[],
            goal_id=profile.goal_id,
        )

        mutated_plan = copy.deepcopy(plan)
        # Add 10 courses totaling 35+ credits to semester 1, pushing it well above any cap
        mutated_plan["semesters"][0]["courses"] = [
            {"code": "CSL301", "title": "Operating Systems", "credits": 4.0},
            {"code": "CSL302", "title": "Computer Networks", "credits": 4.0},
            {"code": "CSL303", "title": "Database Management Systems", "credits": 4.0},
            {"code": "CSL304", "title": "Artificial Intelligence", "credits": 4.0},
            {"code": "CSL510", "title": "Advanced Operating Systems", "credits": 4.0},
            {"code": "CSL511", "title": "Distributed Algorithms", "credits": 4.0},
            {"code": "CSL512", "title": "Advanced Database Systems", "credits": 4.0},
            {"code": "CSL515", "title": "Advanced Computer Networks", "credits": 4.0},
            {"code": "CSL518", "title": "Deep Learning", "credits": 4.0},
            {"code": "CSL559", "title": "Machine Learning", "credits": 4.0},
        ]
        mutated_plan["semesters"][0]["total_credits"] = sum(
            c.get("credits", 0.0) for c in mutated_plan["semesters"][0]["courses"]
        )

        profile_data = {**profile.model_dump(), "cgpa": 7.0}
        indep = validate_plan_independently(
            mutated_plan, profile_data, self.catalog, self.prereq_map
        )
        cert = rule_registry.generate_certificate(mutated_plan, profile_data)

        self.assertFalse(indep["is_valid"], "Independent validator must catch credit overload.")
        self.assertFalse(cert.is_valid, "Rule Registry must catch credit overload.")
        self.assertEqual(indep["is_valid"], cert.is_valid)

    def test_05_detect_mastered_course_reassignment(self):
        """Mutation test: Both independent validator and engine must catch assigning already completed course."""
        profile = StudentStore.get_profile("BH-SW-001")
        plan = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=[],
            goal_id=profile.goal_id,
        )

        mutated_plan = copy.deepcopy(plan)
        # Re-assign CSL100 (which is in completed_courses) into Semester 5
        mutated_plan["semesters"][0]["courses"].append({
            "code": "CSL100",
            "title": "Computer Programming",
            "credits": 4.0,
            "course_type": "core",
        })

        indep = validate_plan_independently(
            mutated_plan, profile.model_dump(), self.catalog, self.prereq_map
        )
        cert = rule_registry.generate_certificate(mutated_plan, profile.model_dump())

        self.assertFalse(indep["is_valid"], "Independent validator must flag mastered course re-assignment.")
        self.assertFalse(cert.is_valid, "Rule Registry must flag mastered course re-assignment.")
        self.assertEqual(indep["is_valid"], cert.is_valid)


if __name__ == "__main__":
    unittest.main()
