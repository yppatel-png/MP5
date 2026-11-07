"""
Automated unit tests for Phase 2: Student Model, BKT Estimator, Adaptive Diagnostic & GapAlerts.
Verifies Hero Persona BH-SW-001 gap outputs, conflict alerts, and BKT mathematics.
"""

import unittest
from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentStore, StudentProfile, CompletedCourse, EvidenceEvent
from backend.student.bkt import bkt_estimator
from backend.student.diagnostic import diagnostic_engine
from backend.student.conflict import conflict_detector
from backend.api.students import get_student, get_student_gaps, get_next_diagnostic_question, submit_diagnostic_answer, AnswerSubmission

class TestStudentDiagnostic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_bkt_mathematics(self):
        """Verifies Bayesian Knowledge Tracing updates on positive vs negative evidence."""
        # Initial estimate with no evidence
        res0 = bkt_estimator.estimate_skill_mastery([], prior_probability=0.2)
        self.assertEqual(res0["p_mastery"], 0.2)
        self.assertFalse(res0["mastered"])

        # Positive evidence (score=1.0) must increase mastery probability
        ev_pos = [{"value": 1.0, "source_type": "quiz", "confidence": 0.7}]
        res1 = bkt_estimator.estimate_skill_mastery(ev_pos, prior_probability=0.2)
        self.assertGreater(res1["p_mastery"], 0.2)

        # Repeated strong evidence leads to mastery
        ev_multi = [
            {"value": 1.0, "source_type": "quiz", "confidence": 0.7},
            {"value": 1.0, "source_type": "timed_project", "confidence": 0.9},
            {"value": 0.95, "source_type": "assessed_diagnostic", "confidence": 1.0}
        ]
        res_mastered = bkt_estimator.estimate_skill_mastery(ev_multi, prior_probability=0.2)
        self.assertGreaterEqual(res_mastered["p_mastery"], 0.85)
        self.assertTrue(res_mastered["mastered"])

        # Negative evidence drops probability
        ev_neg = [{"value": 0.1, "source_type": "quiz", "confidence": 0.7}]
        res_fail = bkt_estimator.estimate_skill_mastery(ev_neg, prior_probability=0.7)
        self.assertLess(res_fail["p_mastery"], 0.7)

    def test_bh_sw_001_profile_and_sensible_gaps(self):
        """Verifies canonical Hero Persona BH-SW-001 gap computation and conflict alert."""
        student = StudentStore.get_profile("BH-SW-001")
        self.assertIsNotNone(student)
        self.assertEqual(student.student_id, "BH-SW-001")
        self.assertEqual(student.programme, "BH-CSE-BTECH")
        self.assertEqual(student.goal_id, "goal_software")
        self.assertEqual(student.cgpa, 8.4)

        # Compute skill gaps
        gap_report = diagnostic_engine.compute_skill_gaps("BH-SW-001")
        self.assertEqual(gap_report["student_id"], "BH-SW-001")
        self.assertEqual(gap_report["goal_id"], "goal_software")

        # In BH-SW-001: DSA and systems are critical gaps
        critical_gap_skills = [g["skill_id"] for g in gap_report["gaps"] if g["critical"]]
        self.assertTrue(any(s in critical_gap_skills for s in ["data_structures", "algorithms", "operating_systems"]))

        # Programming fundamentals should be present in matrix/profile
        prog_data = next((g for g in gap_report["gaps"] + gap_report["strengths"] if g["skill_id"] == "programming_fundamentals"), None)
        self.assertIsNotNone(prog_data)

        # Check Conflict Detection
        alerts = conflict_detector.detect_conflicts("BH-SW-001")
        self.assertGreaterEqual(len(alerts), 1)

    def test_adaptive_diagnostic_question_flow(self):
        """Tests that adaptive question selector picks high-entropy questions and updates state."""
        # Get first question
        q1 = diagnostic_engine.get_next_question("BH-SW-001", answered_exercise_ids=[])
        self.assertFalse(q1["diagnostic_complete"])
        self.assertIn("exercise", q1)
        ex1 = q1["exercise"]
        self.assertIn("exercise_id", ex1)
        self.assertIn("prompt", ex1)

        # Submit answer to first question
        submission = AnswerSubmission(
            exercise_id=ex1["exercise_id"],
            selected_option=ex1.get("options", ["opt"])[0] if ex1.get("options") else "test answer"
        )
        res = submit_diagnostic_answer("BH-SW-001", submission)
        self.assertIn("is_correct", res)
        self.assertIn("updated_skill", res)
        self.assertIn("p_mastery", res["updated_skill"])

        # Next question should not repeat the answered exercise
        q2 = diagnostic_engine.get_next_question("BH-SW-001", answered_exercise_ids=[ex1["exercise_id"]])
        if not q2["diagnostic_complete"]:
            self.assertNotEqual(q2["exercise"]["exercise_id"], ex1["exercise_id"])

    def test_student_api_endpoints(self):
        """Verifies student API endpoints."""
        student_data = get_student("BH-SW-001")
        self.assertEqual(student_data["profile"]["student_id"], "BH-SW-001")
        self.assertIn("skill_matrix", student_data)
        self.assertIn("programming_fundamentals", student_data["skill_matrix"])

        gaps_res = get_student_gaps("BH-SW-001")
        self.assertIn("gaps", gaps_res)
        self.assertIn("alerts", gaps_res)
        self.assertIn("readiness_percentage", gaps_res)

if __name__ == "__main__":
    unittest.main()
