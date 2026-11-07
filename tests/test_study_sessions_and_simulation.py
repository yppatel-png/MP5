"""
Unit Tests for Feature 6: Study Activity Logging, Adherence Tracking, and Adaptation Scenarios.
Covers:
1. Study sessions persistence (POST and GET /api/students/{student_id}/study-sessions)
2. Weekly study hours and adherence percentage arithmetic reconciliation
3. StudentSummary dynamic update from study activity
4. Strong Study Week simulation scenario: adherence >= 80%, status On Track, course capacity maintained
5. Weak Study Week simulation scenario: adherence < 50%, status Behind, load-shedding to 16 credits
"""

import unittest
from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentStore, StudySessionCreate
from backend.student.summary import build_student_summary
from backend.adapt.simulator import adaptation_simulator
from backend.api.students import log_student_study_session, get_student_study_sessions


class TestStudySessionsAndSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def setUp(self):
        self.student_id = "BH-SW-001"
        self.profile = StudentStore.get_profile(self.student_id)

    def test_01_log_and_retrieve_study_sessions(self):
        """Tests logging study sessions via API and retrieving them chronologically."""
        session_req = StudySessionCreate(
            course_code="CSL202",
            duration_minutes=90,
            notes="Tree traversal and balancing practice",
            session_date="2026-11-06",
        )
        resp = log_student_study_session(self.student_id, session_req)
        self.assertIn("session_id", resp)
        self.assertEqual(resp["course_code"], "CSL202")
        self.assertEqual(resp["duration_minutes"], 90)
        self.assertGreaterEqual(resp["weekly_hours_studied"], 1.5)

        sessions = get_student_study_sessions(self.student_id)
        self.assertGreater(len(sessions), 0)
        self.assertEqual(sessions[0]["course_code"], "CSL202")

    def test_02_adherence_and_student_summary_calculation(self):
        """Tests that weekly hours and adherence percentage feed directly into the student summary."""
        metrics = StudentStore.get_weekly_study_metrics(self.student_id)
        self.assertIsNotNone(metrics["weekly_hours_studied"])
        self.assertGreater(metrics["weekly_hours_studied"], 0)

        summary = build_student_summary(
            profile=self.profile,
            plan=None,
            readiness_percentage=85.0,
            priority_gap_count=0,
        )
        self.assertIsNotNone(summary.weekly_hours_studied)
        self.assertIsNotNone(summary.adherence_percentage)

    def test_03_strong_study_week_simulation(self):
        """Simulates strong study week: 20 hrs logged, 100% adherence, On Track status."""
        res = adaptation_simulator.execute_scenario(
            scenario_id="scenario_strong_study_week",
            student_id=self.student_id,
            params={"weekly_hours": 20.0},
        )
        self.assertEqual(res["scenario_id"], "scenario_strong_study_week")
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["student_status"], "on_track")
        self.assertGreaterEqual(res["adherence_percentage"], 80.0)
        self.assertGreaterEqual(res["credit_cap"], 22.0)
        self.assertTrue(res["validation"]["is_valid"])

    def test_04_weak_study_week_simulation(self):
        """Simulates weak study week: 4 hrs logged, low adherence, Behind status, load shed to 16 credits."""
        res = adaptation_simulator.execute_scenario(
            scenario_id="scenario_weak_study_week",
            student_id=self.student_id,
            params={"weekly_hours": 4.0},
        )
        self.assertEqual(res["scenario_id"], "scenario_weak_study_week")
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["student_status"], "behind")
        self.assertLess(res["adherence_percentage"], 50.0)
        self.assertEqual(res["credit_cap"], 16.0)
        self.assertEqual(res["action_triggered"], "LOAD_SHED")
        self.assertTrue(res["validation"]["is_valid"])
        self.assertIn("16", res["explanation"])


if __name__ == "__main__":
    unittest.main()
