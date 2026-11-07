"""
Automated unit tests for Phase 3: Planner, Independent Validator, Determinism, & Infeasible Handling.
Verifies that all generated plans pass 100% of independent validator rules.
"""

import unittest
from pathlib import Path
import json

from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentProfile, StudentStore
from backend.api.plans import (
    generate_student_plan,
    get_active_plan,
    get_plan_history,
    test_infeasible_request,
    PlanGenerateRequest,
    InfeasibleRequestModel,
)
from backend.planner.validator import independent_validator
from backend.planner.solver import multi_semester_planner
from backend.student.diagnostic import diagnostic_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestPlanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_bh_sw_001_plan_generation_and_validation(self):
        """Generates plan for Hero Persona BH-SW-001 and verifies 100% pass on validator rules."""
        res = generate_student_plan(PlanGenerateRequest(student_id="BH-SW-001"))
        self.assertEqual(res["student_id"], "BH-SW-001")
        self.assertGreaterEqual(res["version_number"], 1)

        plan = res["plan"]
        self.assertIn("semesters", plan)
        self.assertGreater(len(plan["semesters"]), 0)

        # Check Independent Validation Report
        report = res["validation_report"]
        self.assertTrue(report["is_valid"], f"Plan failed validation! Errors: {report.get('errors')}")
        self.assertGreaterEqual(report["rules_evaluated"], 8)
        self.assertEqual(report["rules_passed"], report["rules_evaluated"])

        # Verify specific course sequencing for BH-SW-001 (Bhilai BTech CSE)
        scheduled_courses = [c["code"] for s in plan["semesters"] for c in s.get("courses", [])]
        self.assertIn("CSL303", scheduled_courses)

    def test_planner_determinism(self):
        """Verifies that identical inputs produce exactly identical multi-semester plans."""
        res1 = generate_student_plan(PlanGenerateRequest(student_id="BH-SW-001", reason_for_change="Determinism run 1"))
        res2 = generate_student_plan(PlanGenerateRequest(student_id="BH-SW-001", reason_for_change="Determinism run 2"))

        plan1 = res1["plan"]
        plan2 = res2["plan"]

        self.assertEqual(plan1["total_credits_planned"], plan2["total_credits_planned"])
        self.assertEqual(len(plan1["semesters"]), len(plan2["semesters"]))

        for s1, s2 in zip(plan1["semesters"], plan2["semesters"]):
            codes1 = [c["code"] for c in s1["courses"]]
            codes2 = [c["code"] for c in s2["courses"]]
            self.assertEqual(codes1, codes2)

    def test_infeasible_credit_request_handling(self):
        """Handles request for 30 credits (exceeding limit) and returns best valid plan."""
        infeasible_res = test_infeasible_request(InfeasibleRequestModel(student_id="BH-SW-001", requested_credits=30.0))
        self.assertEqual(infeasible_res["status"], "infeasible")
        self.assertIn("blocking_rule", infeasible_res)
        self.assertEqual(infeasible_res["blocking_rule"]["rule_id"], "rule_credit_cap_standard")
        self.assertEqual(infeasible_res["max_allowed_credits"], 22.0)
        self.assertIn("closest_valid_plan", infeasible_res)

        # Closest valid plan must be valid
        val = infeasible_res["validation_report"]
        self.assertTrue(val["is_valid"])

    def test_infeasible_missing_prerequisite_request(self):
        """Handles request for advanced course without completed prerequisite."""
        # Desired CSL252 requires CSL202 (unfulfilled for BH-SYN-001)
        infeasible_res = test_infeasible_request(InfeasibleRequestModel(student_id="BH-SYN-001", desired_course_code="CSL252"))
        self.assertEqual(infeasible_res["status"], "infeasible")
        self.assertIn("missing_prerequisites", infeasible_res)
        self.assertIn("CSL202", infeasible_res["missing_prerequisites"])

    def test_plan_versioning_and_diff(self):
        """Tests plan version evolution and semantic diff calculation."""
        # Generate initial plan (v1)
        res_v1 = generate_student_plan(PlanGenerateRequest(student_id="BH-SW-001", goal_override="goal_software"))
        v1_num = res_v1["version_number"]

        # Adapt plan to new goal (v2)
        res_v2 = generate_student_plan(PlanGenerateRequest(student_id="BH-SW-001", goal_override="goal_higher_studies", reason_for_change="Pivot to Higher Studies"))
        v2_num = res_v2["version_number"]
        self.assertGreater(v2_num, v1_num)

        # Verify diff
        diff = res_v2["diff"]
        self.assertIn("reason", diff)
        self.assertEqual(diff["reason"], "Pivot to Higher Studies")

        # History endpoint
        history = get_plan_history("BH-SW-001")
        self.assertGreaterEqual(len(history), 2)

    def test_multi_persona_plan_validations(self):
        """Verifies that all hero personas produce 100% valid plans."""
        personas = ["BH-SW-001", "BH-HS-001", "BH-UP-001"]
        for pid in personas:
            res = generate_student_plan(PlanGenerateRequest(student_id=pid))
            self.assertTrue(res["validation_report"]["is_valid"], f"Plan for {pid} failed validation!")
            self.assertEqual(res["validation_report"]["rules_passed"], res["validation_report"]["rules_evaluated"])

    def test_50_synthetic_profiles_plan_validity(self):
        """Evaluates 50 diverse synthetic profiles to prove the planner is not hand-tuned for a few personas."""
        synth_path = PROJECT_ROOT / "data" / "seed_bhilai" / "synthetic_profiles.json"
        with open(synth_path, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        passed_count = 0
        total_tested = min(50, len(profiles))

        for p_data in profiles[:total_tested]:
            # Save profile to store temporarily
            p_obj = StudentProfile(
                student_id=p_data["student_id"],
                name=p_data["name"],
                programme=p_data["programme"],
                year=p_data["year"],
                current_semester=p_data["current_semester"],
                cgpa=p_data["cgpa"],
                goal_id=p_data["goal_id"],
                target_role=p_data.get("target_role"),
                available_hours_per_week=p_data.get("available_hours_per_week", 12.0),
                remaining_elective_slots=p_data.get("remaining_elective_slots", 4),
                completed_courses=[{"course_code": c["course_code"], "grade": c["grade"], "semester_completed": c.get("semester_completed", 1)} for c in p_data.get("completed_courses", [])],
                interests=p_data.get("interests", []),
                constraints=p_data.get("constraints", {}),
                preferences=p_data.get("preferences", {})
            )
            StudentStore.save_profile(p_obj)

            gaps = diagnostic_engine.compute_skill_gaps(p_obj.student_id)
            plan = multi_semester_planner.plan_curriculum(
                student_id=p_obj.student_id,
                programme_code=p_obj.programme,
                current_semester=p_obj.current_semester,
                cgpa=p_obj.cgpa,
                completed_courses=[c.course_code for c in p_obj.completed_courses],
                skill_gaps=gaps.get("gaps", []),
                goal_id=p_obj.goal_id
            )

            val = independent_validator.validate_plan(plan, p_obj.model_dump())
            self.assertTrue(val["is_valid"], f"Profile {p_obj.student_id} failed validation! Errors: {val.get('errors')}")
            self.assertEqual(val["rules_passed"], val["rules_evaluated"])
            passed_count += 1

        self.assertEqual(passed_count, 50)

if __name__ == "__main__":
    unittest.main()
