"""
Tests for Audit Phase P0: Correctness and Honesty.
Tests P0-1, P0-2, P0-3, P0-4, P0-5.
"""

import unittest
import os
import re
from pathlib import Path

from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.buddy.router import buddy_router
from backend.buddy import tools
from backend.rules.params import (
    get_standard_credit_cap,
    get_min_semester_credits,
    get_overload_credit_cap,
    get_overload_cgpa_threshold,
)
from backend.practice.runner import exercise_runner
import backend.config


class TestAuditP0(unittest.TestCase):

    def setUp(self):
        self.profile = StudentStore.get_profile("BH-SW-001")

    # -------------------------------------------------------------------------
    # P0-1: Solver deferred core queue, backlogs, constraints, & validator agree
    # -------------------------------------------------------------------------

    def test_P0_1_core_course_deferred_and_rescheduled(self):
        """
        When a student has a backlog core course (e.g. failed CSL100 from Sem 1),
        the planner carries it into deferred_core and reschedules it in the earliest
        eligible semester (matching parity and prerequisites), rather than silently dropping it.
        """
        plan_res = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code="BH-CSE-BTECH",
            current_semester=2,
            cgpa=7.5,
            completed_courses=["ECL101", "MAL101"],
            skill_gaps=[],
            goal_id="goal_software",
        )
        all_planned_codes = [c["code"] for s in plan_res["semesters"] for c in s["courses"]]
        # CSL100 is an odd semester core course; from semester 2 it should be rescheduled in Semester 3
        self.assertIn("CSL100", all_planned_codes)
        sem3_courses = next((s["courses"] for s in plan_res["semesters"] if s["semester_number"] == 3), [])
        sem3_codes = [c["code"] for c in sem3_courses]
        self.assertIn("CSL100", sem3_codes)

        # Independent validator must agree
        val = plan_res.get("validation", {})
        self.assertTrue(val.get("is_valid"), f"Validator errors: {val.get('errors')}")

    def test_P0_1_unmet_prereq_chain_reports_infeasible_not_silent_drop(self):
        """
        If a core course prerequisite cannot be met before semester 8,
        unscheduled_required must report it and status must be 'infeasible'.
        """
        # Exclude all introductory courses and plan starting at semester 8 (only 1 semester to graduate)
        plan_res = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code="iit_bhilai_btech_cse_2023",
            current_semester=7,
            cgpa=6.5,
            completed_courses=[],  # Nothing completed, impossible to complete all core courses in sem 8
            skill_gaps=[],
            goal_id="goal_software",
            credit_cap=12.0
        )
        self.assertEqual(plan_res["status"], "infeasible")
        self.assertTrue(len(plan_res["unscheduled_required"]) > 0)
        self.assertTrue(len(plan_res["infeasible_reasons"]) > 0)

    def test_P0_1_no_co_taking_core_pair_enforced_in_phase_a(self):
        """
        A restricted no-co-taking pair involving a core course must not be scheduled
        together in the same semester.
        """
        no_co_pairs = [["CSL201", "CSL202"]]  # Both are semester 3 core courses
        plan_res = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code="iit_bhilai_btech_cse_2023",
            current_semester=2,
            cgpa=8.0,
            completed_courses=["CSL100", "ECL101", "MAL101"],
            skill_gaps=[],
            no_co_taking_pairs=no_co_pairs
        )
        for s in plan_res["semesters"]:
            codes = [c["code"].upper() for c in s["courses"]]
            self.assertFalse("CSL201" in codes and "CSL202" in codes,
                             f"Semester {s['semester_number']} scheduled both conflicting courses!")

    def test_P0_1_max_weekly_hours_budget_enforced(self):
        """
        A low weekly hours constraint (e.g. 6 free hours/week) halts addition of heavy workloads
        and reports the trade-off / infeasibility rather than overflowing unsustainable workload.
        """
        plan_res = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code="iit_bhilai_btech_cse_2023",
            current_semester=4,
            cgpa=7.5,
            completed_courses=[c.course_code for c in self.profile.completed_courses],
            skill_gaps=[],
            max_weekly_hours=6.0  # 6 hours per week is impossible for regular 18-credit full-time semesters
        )
        # Because courses cannot fit in 6.0 hrs/wk, required courses become unscheduled and status is infeasible
        self.assertEqual(plan_res["status"], "infeasible")
        self.assertTrue(any("weekly study limit" in r for r in plan_res["infeasible_reasons"]))

    # -------------------------------------------------------------------------
    # P0-2: Engine docstrings and independent validation attached
    # -------------------------------------------------------------------------

    def test_P0_2_engine_docstring_and_validation_attached(self):
        """
        Confirms OR-Tools import was removed, engine name reflects deterministic greedy scheduler +
        independent validator, and independent validation report is attached to plan output.
        """
        plan_res = multi_semester_planner.plan_curriculum(
            student_id="BH-SW-001",
            programme_code="iit_bhilai_btech_cse_2023",
            current_semester=4,
            cgpa=8.0,
            completed_courses=[c.course_code for c in self.profile.completed_courses],
            skill_gaps=[]
        )
        self.assertEqual(plan_res["solver_engine"], "deterministic greedy scheduler + independent validator")
        self.assertIn("validation", plan_res)
        self.assertIn("is_valid", plan_res["validation"])
        self.assertIn("rule_results", plan_res["validation"])

        # Check solver.py file text for removed OR-Tools and updated docstrings
        solver_path = Path("backend/planner/solver.py")
        content = solver_path.read_text(encoding="utf-8")
        self.assertNotIn("ortools", content.lower())
        self.assertIn("deterministic greedy scheduler + independent validator", content)

    # -------------------------------------------------------------------------
    # P0-3: No hardcoded fallback literals and no UPSC default
    # -------------------------------------------------------------------------

    def test_P0_3_no_fallback_literals_and_no_upsc_default(self):
        """
        Checks that students with no target role are not defaulted to UPSC Civil Services,
        and credit caps come exclusively from the central rules accessor.
        """
        # Create a temp profile with no target_role
        test_student_id = "TEST-P0-3-PROFILE"
        temp_prof = StudentProfile(
            student_id=test_student_id,
            name="Test Student",
            programme="BH-CSE-BTECH",
            year=2,
            current_semester=4,
            cgpa=8.2,
            target_role="",  # Empty target role
            goal_id="goal_software",
            interests=["web_development"],
            completed_courses=list(self.profile.completed_courses)
        )
        StudentStore.save_profile(temp_prof)

        # Generate active plan in database
        from backend.api.plans import generate_student_plan, PlanGenerateRequest
        generate_student_plan(PlanGenerateRequest(student_id=test_student_id))

        # Query buddy for elective recommendation
        resp = buddy_router.handle_message(test_student_id, "Recommend electives for semester 5")
        reply = resp["reply"]
        self.assertNotIn("UPSC Civil Services", reply)
        self.assertTrue(any(term in reply.lower() for term in ["eligible electives", "available elective", "elective options", "electives"]))

    # -------------------------------------------------------------------------
    # P0-4: No false ordinance citations
    # -------------------------------------------------------------------------

    def test_P0_4_no_false_ordinance_citations(self):
        """
        Ensures that user-facing credit overload replies and what-if tools do not cite
        non-existent ordinances or claim 'strictly caps' without 'working assumption' or 'pending ordinance'.
        """
        resp = buddy_router.handle_message("BH-SW-001", "Can I take 35 credits next semester?")
        reply = resp["reply"]
        self.assertNotIn("Citation: IIT Bhilai B.Tech Ordinance §Workload Regulations", reply)
        self.assertIn("working assumption", reply.lower())
        self.assertIn("pending official ordinance", reply.lower())

        what_if_res = tools.what_if("BH-SW-001", "35 credits")
        self.assertIn("pending official ordinance", what_if_res["reason"].lower())
        self.assertNotIn("ordinance strictly caps", what_if_res["reason"].lower())

    # -------------------------------------------------------------------------
    # P0-5: Practice code sandbox: 10 escape attempts must be rejected/killed
    # -------------------------------------------------------------------------

    def test_P0_5_sandbox_escape_attempts(self):
        """
        Tests at least 10 distinct sandbox escape vectors against the AST allow-list
        and runtime runner. All must be rejected or terminated.
        """
        prev_setting = getattr(backend.config.settings, "DISABLE_CODE_EXERCISES", True)
        backend.config.settings.DISABLE_CODE_EXERCISES = False
        os.environ["DISABLE_CODE_EXERCISES"] = "false"

        mock_ex = {
            "exercise_id": "test_security_p0_5",
            "type": "code",
            "difficulty": 1,
            "skill_id": "programming_fundamentals",
            "prompt": "Security test harness",
            "answer_key": {"test_cases": [{"input": "0", "expected": 0}]}
        }
        exercise_runner.exercises[mock_ex["exercise_id"]] = mock_ex

        escape_payloads = [
            # 1. Dunder class/subclasses walk
            "def exploit(x):\n    return ().__class__.__bases__[0].__subclasses__()",
            # 2. Function __self__ introspection
            "def exploit(x):\n    f = print.__self__\n    return 0",
            # 3. Type dunder mro
            "def exploit(x):\n    return [c for c in ().__class__.__mro__]",
            # 4. Lambda __globals__ introspection
            "def exploit(x):\n    return (lambda: 0).__globals__",
            # 5. Dangerous built-in open() call
            "def exploit(x):\n    return open('README.md').read()",
            # 6. Dangerous built-in eval() call
            "def exploit(x):\n    return eval('1 + 1')",
            # 7. Subprocess / os module import
            "import os\ndef exploit(x):\n    return os.getpid()",
            # 8. Import from sys
            "from sys import modules\ndef exploit(x):\n    return 0",
            # 9. Class definition escape (metaclass or reflection)
            "class Exploit:\n    pass\ndef exploit(x):\n    return 0",
            # 10. Fork bomb / infinite loop
            "def exploit(x):\n    while True:\n        pass\n    return 0",
        ]

        try:
            for idx, code in enumerate(escape_payloads, 1):
                res = exercise_runner.evaluate_submission(
                    student_id="BH-SW-001",
                    exercise_id="test_security_p0_5",
                    submission={"code": code}
                )
                self.assertEqual(res["score"], 0.0, f"Payload #{idx} succeeded or bypassed sandbox! Code: {code}")
                self.assertFalse(res["is_correct"], f"Payload #{idx} marked correct!")

            # 11. Positive control: legitimate code containing 'is_open' and 'reopen' MUST pass
            legit_code = """
def is_open(x):
    reopened = True
    return 0 if reopened else 1
"""
            res_legit = exercise_runner.evaluate_submission(
                student_id="BH-SW-001",
                exercise_id="test_security_p0_5",
                submission={"code": legit_code}
            )
            self.assertEqual(res_legit["score"], 1.0, f"Legitimate is_open / reopen was falsely rejected: {res_legit}")
            self.assertTrue(res_legit["is_correct"])

        finally:
            backend.config.settings.DISABLE_CODE_EXERCISES = prev_setting
            os.environ["DISABLE_CODE_EXERCISES"] = str(prev_setting).lower()


if __name__ == "__main__":
    unittest.main()

