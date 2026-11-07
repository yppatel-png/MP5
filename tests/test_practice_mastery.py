"""
Automated unit tests for Phase 4: Learn, Practise, & Mastery Engine.
Verifies MCQ grading, code sandbox execution, rubric evaluation, grounded question validation,
and the critical 'Completed Course' vs 'Demonstrated Proficiency' distinction.
"""

import unittest
import time
from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.practice.runner import exercise_runner
from backend.practice.generator import question_generator
from backend.practice.mastery import mastery_engine
from backend.api.practice import submit_exercise, get_student_mastery_report, ExerciseSubmissionModel

class TestPracticeAndMastery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_mcq_deterministic_grading(self):
        """Verifies deterministic MCQ grading against answer key."""
        mcq_ex = next((ex for ex in exercise_runner.exercises.values() if ex["type"] == "mcq"), None)
        self.assertIsNotNone(mcq_ex)

        correct_ans = mcq_ex["answer_key"]["correct"]
        ex_id = mcq_ex["exercise_id"]

        # Test correct submission
        res_correct = exercise_runner.evaluate_submission(
            student_id="BH-SW-001",
            exercise_id=ex_id,
            submission={"selected_option": correct_ans}
        )
        self.assertEqual(res_correct["score"], 1.0)
        self.assertTrue(res_correct["is_correct"])

        # Test incorrect submission
        res_wrong = exercise_runner.evaluate_submission(
            student_id="BH-SW-001",
            exercise_id=ex_id,
            submission={"selected_option": "COMPLETELY_WRONG_OPTION_XYZ"}
        )
        self.assertEqual(res_wrong["score"], 0.0)
        self.assertFalse(res_wrong["is_correct"])

    def test_code_sandbox_execution(self):
        """Tests sandboxed Python code execution with unit test cases."""
        # Ensure a code exercise is present for sandbox testing
        code_ex = {
            "exercise_id": "test_code_palindrome",
            "type": "code",
            "difficulty": 2,
            "skill_id": "programming_fundamentals",
            "prompt": "Write a function is_palindrome(s: str) -> bool",
            "answer_key": {
                "test_cases": [
                    {"input": "'racecar'", "expected": True},
                    {"input": "'hello'", "expected": False}
                ]
            }
        }
        exercise_runner.exercises[code_ex["exercise_id"]] = code_ex
        ex_id = code_ex["exercise_id"]

        # Valid palindrome solution
        valid_code = """
def is_palindrome(s: str) -> bool:
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
"""
        res_pass = exercise_runner.evaluate_submission(
            student_id="BH-SW-001",
            exercise_id=ex_id,
            submission={"code": valid_code}
        )
        self.assertEqual(res_pass["score"], 1.0)
        self.assertTrue(res_pass["is_correct"])

        # Security check: forbidden constructs
        malicious_code = "import os\nos.system('dir')"
        res_security = exercise_runner.evaluate_submission(
            student_id="BH-SW-001",
            exercise_id=ex_id,
            submission={"code": malicious_code}
        )
        self.assertEqual(res_security["score"], 0.0)
        self.assertFalse(res_security["is_correct"])
        self.assertIn("Security restriction", res_security["feedback"])

        start = time.monotonic()
        timeout_result = exercise_runner.evaluate_submission(
            student_id="BH-SW-001",
            exercise_id=ex_id,
            submission={"code": "while True:\n    pass"},
        )
        self.assertEqual(timeout_result["score"], 0.0)
        self.assertLess(time.monotonic() - start, 8.0)

    def test_question_generator_validation_rules(self):
        """Tests that the question generator validator rejects invalid/hallucinated questions."""
        sample_module_text = "Data Structures: Binary search tree invariants, rotations, and AVL height balancing."

        # Case 1: Valid question
        valid_q = {
            "question": "What is the primary condition enforced by AVL height balancing?",
            "options": ["Height difference <= 1", "Height difference == 0", "All nodes are red", "Heap order property"],
            "answer": "Height difference <= 1",
            "grounded_quote": "AVL height balancing"
        }
        is_val, errs = question_generator.validate_question(valid_q, sample_module_text)
        self.assertTrue(is_val)
        self.assertEqual(len(errs), 0)

        # Case 2: Duplicate options
        dup_q = {
            "question": "What is the primary condition enforced by AVL height balancing?",
            "options": ["Height difference <= 1", "Height difference <= 1", "All nodes are red", "Heap order"],
            "answer": "Height difference <= 1",
            "grounded_quote": "AVL height balancing"
        }
        is_val, errs = question_generator.validate_question(dup_q, sample_module_text)
        self.assertFalse(is_val)
        self.assertTrue(any("Duplicate" in e for e in errs))

        # Case 3: Grounded quote does not exist in module text (hallucination)
        hallucinated_q = {
            "question": "What is the primary condition enforced by AVL height balancing?",
            "options": ["Opt A", "Opt B", "Opt C", "Opt D"],
            "answer": "Opt A",
            "grounded_quote": "Quantum electrodynamics and tensor flow"
        }
        is_val, errs = question_generator.validate_question(hallucinated_q, sample_module_text)
        self.assertFalse(is_val)
        self.assertTrue(any("Hallucination check failed" in e for e in errs))

    def test_completed_course_vs_demonstrated_proficiency(self):
        """
        Critical Scenario:
        Distinguishes 'Course Completed' from 'Demonstrated Proficiency' for programming_fundamentals.
        """
        # Create student who completed CSL100 (Grade B) but has ZERO active test attempts
        test_student_id = "S_TEST_MASTERY_01"
        profile = StudentProfile(
            student_id=test_student_id,
            name="Testing Student",
            programme="iit_bhilai_btech_cse_2023",
            cgpa=8.0,
            goal_id="goal_software",
            completed_courses=[CompletedCourse(course_code="CSL100", grade="B", semester_completed=1)]
        )
        StudentStore.save_profile(profile)

        # 1. Before active test evidence: Status MUST be 'course_completed_only'
        initial_state = mastery_engine.evaluate_skill_state(test_student_id, "programming_fundamentals")
        self.assertEqual(initial_state["status"], "course_completed_only")
        self.assertTrue(initial_state["has_completed_course"])
        self.assertFalse(initial_state["has_demonstrated_proficiency"])

        # 2. Student passes 2 independent exercises (empirically demonstrating retention)
        # Attempt 1
        exercise_runner.evaluate_submission(
            student_id=test_student_id,
            exercise_id="ex_mod_csl100_1",
            submission={"selected_option": "C programming"}
        )
        # Attempt 2
        exercise_runner.evaluate_submission(
            student_id=test_student_id,
            exercise_id="ex_mod_csl100_2",
            submission={"selected_option": "Control flow"}
        )

        # 3. After active corroborating evidence: Status MUST transition to 'demonstrated_proficiency'
        updated_state = mastery_engine.evaluate_skill_state(test_student_id, "programming_fundamentals")
        self.assertEqual(updated_state["status"], "demonstrated_proficiency")
        self.assertTrue(updated_state["has_demonstrated_proficiency"])
        self.assertGreaterEqual(updated_state["p_mastery"], 0.85)

    def test_goal_readiness_and_whats_missing_checklist(self):
        """Verifies goal readiness percentage and actionable 'What's Missing' items."""
        report = get_student_mastery_report("BH-SW-001")
        self.assertEqual(report["student_id"], "BH-SW-001")
        self.assertIn("overall_readiness_percentage", report)
        self.assertIn("skills_breakdown", report)
        self.assertIn("whats_missing", report)

        # BH-SW-001 has critical gaps, so whats_missing must contain actionable items
        self.assertGreater(len(report["whats_missing"]), 0)
        missing_titles = [m["title"] for m in report["whats_missing"]]
        self.assertTrue(any("Data Structures" in t or "Algorithm" in t or "Operating" in t or "Database" in t or "Software" in t for t in missing_titles))

if __name__ == "__main__":
    unittest.main()
