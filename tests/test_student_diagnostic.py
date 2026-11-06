"""
Automated unit tests for Phase 2: Student Model, BKT Estimator, Adaptive Diagnostic & GapAlerts.
Verifies Hero Persona S1024 gap outputs, conflict alerts, and BKT mathematics.
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

    def test_s1024_profile_and_sensible_gaps(self):
        """Verifies canonical Hero Persona S1024 gap computation and conflict alert."""
        s1024 = StudentStore.get_profile("S1024")
        self.assertIsNotNone(s1024)
        self.assertEqual(s1024.student_id, "S1024")
        self.assertEqual(s1024.programme, "CH1")
        self.assertEqual(s1024.goal_id, "goal_software")
        self.assertEqual(s1024.cgpa, 7.8)

        # Compute skill gaps
        gap_report = diagnostic_engine.compute_skill_gaps("S1024")
        self.assertEqual(gap_report["student_id"], "S1024")
        self.assertEqual(gap_report["goal_id"], "goal_software")

        # In S1024: DSA and Databases are critical gaps
        critical_gap_skills = [g["skill_id"] for g in gap_report["gaps"] if g["critical"]]
        self.assertIn("skill_dsa_linear", critical_gap_skills)
        self.assertIn("skill_dsa_trees", critical_gap_skills)
        self.assertIn("skill_db_relational", critical_gap_skills)

        # Programming fundamentals should be a relative strength or small gap (tested 78%)
        prog_data = next((g for g in gap_report["gaps"] + gap_report["strengths"] if g["skill_id"] == "skill_prog_fundamentals"), None)
        self.assertIsNotNone(prog_data)
        self.assertGreaterEqual(prog_data["current_level"], 0.65)

        # Check Conflict Detection
        alerts = conflict_detector.detect_conflicts("S1024")
        self.assertGreaterEqual(len(alerts), 1)
        alert_ids = [a["alert_id"] for a in alerts]
        
        # S1024 has declared interest in machine learning, but has significant DSA/SWE foundation gaps
        self.assertTrue(any("gap_alert" in aid for aid in alert_ids))

    def test_adaptive_diagnostic_question_flow(self):
        """Tests that adaptive question selector picks high-entropy questions and updates state."""
        # Get first question
        q1 = diagnostic_engine.get_next_question("S1024", answered_exercise_ids=[])
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
        res = submit_diagnostic_answer("S1024", submission)
        self.assertIn("is_correct", res)
        self.assertIn("updated_skill", res)
        self.assertIn("p_mastery", res["updated_skill"])

        # Next question should not repeat the answered exercise
        q2 = diagnostic_engine.get_next_question("S1024", answered_exercise_ids=[ex1["exercise_id"]])
        if not q2["diagnostic_complete"]:
            self.assertNotEqual(q2["exercise"]["exercise_id"], ex1["exercise_id"])

    def test_student_api_endpoints(self):
        """Verifies student API endpoints."""
        student_data = get_student("S1024")
        self.assertEqual(student_data["profile"]["student_id"], "S1024")
        self.assertIn("skill_matrix", student_data)
        self.assertIn("skill_prog_fundamentals", student_data["skill_matrix"])

        gaps_res = get_student_gaps("S1024")
        self.assertIn("gaps", gaps_res)
        self.assertIn("alerts", gaps_res)
        self.assertIn("readiness_percentage", gaps_res)

if __name__ == "__main__":
    unittest.main()

