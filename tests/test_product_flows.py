"""Integration checks for judge-facing workflows that cross the API boundary."""

import unittest

from fastapi.testclient import TestClient

from backend.config import settings
from backend.db.seed_loader import load_seed_data
from backend.main import app


class TestProductFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_diagnostic_and_practice_record_real_evidence(self):
        question_response = self.client.get(
            "/api/students/BH-SW-001/diagnostic/next",
            params={"answered": ""},
        )
        self.assertEqual(question_response.status_code, 200)
        exercise = question_response.json()["exercise"]
        self.assertIn(exercise["type"], {"mcq", "short"})
        answer = {
            "exercise_id": exercise["exercise_id"],
            "selected_option": exercise["options"][0] if exercise["options"] else None,
            "text_answer": "A reasoned diagnostic answer.",
        }
        diagnostic_response = self.client.post(
            "/api/students/BH-SW-001/diagnostic/submit",
            json=answer,
        )
        self.assertEqual(diagnostic_response.status_code, 200)
        self.assertIn("updated_skill", diagnostic_response.json())

        exercises = self.client.get("/api/practice/exercises").json()
        mcq = next(exercise for exercise in exercises if exercise["type"] == "mcq")
        correct = mcq["answer_key"]["correct"] if "answer_key" in mcq else None
        if correct is None:
            from backend.practice.runner import exercise_runner

            correct = exercise_runner.exercises[mcq["exercise_id"]]["answer_key"]["correct"]
        practice_response = self.client.post(
            "/api/practice/run",
            json={
                "student_id": "BH-SW-001",
                "exercise_id": mcq["exercise_id"],
                "selected_option": correct,
            },
        )
        self.assertEqual(practice_response.status_code, 200)
        self.assertTrue(practice_response.json()["is_correct"])
        self.assertGreaterEqual(practice_response.json()["score"], 0.85)

    def test_adaptation_is_saved_as_the_active_plan_version(self):
        before = self.client.get("/api/plans/BH-SW-001")
        self.assertEqual(before.status_code, 200)
        previous_version = before.json()["version_number"]

        simulation = self.client.post(
            "/api/adapt/simulate",
            json={"scenario_id": "scenario_weak_quiz", "student_id": "BH-SW-001", "params": {}},
        )
        self.assertEqual(simulation.status_code, 200, simulation.text)
        self.assertTrue(simulation.json()["validation"]["is_valid"])

        after = self.client.get("/api/plans/BH-SW-001")
        self.assertEqual(after.status_code, 200)
        self.assertEqual(after.json()["version_number"], previous_version + 1)
        self.assertTrue(after.json()["certificate"]["certificate_hash"])

    def test_admin_requires_token_and_updates_profile_fields(self):
        payload = {
            "student_id": "BH-SW-001",
            "constraints": {"cgpa": 7.6, "available_hours_per_week": 9},
        }
        denied = self.client.post("/api/admin/constraint", json=payload)
        self.assertEqual(denied.status_code, 401)

        accepted = self.client.post(
            "/api/admin/constraint",
            json=payload,
            headers={"X-Admin-Token": settings.ADMIN_API_TOKEN},
        )
        self.assertEqual(accepted.status_code, 200, accepted.text)
        profile = self.client.get("/api/students/profile/BH-SW-001").json()
        self.assertEqual(profile["cgpa"], 7.6)
        self.assertEqual(profile["available_hours_per_week"], 9)

    def test_onboarding_rejects_out_of_range_profile_data(self):
        profile = self.client.get("/api/students/profile/BH-SW-001").json()
        profile["cgpa"] = 12
        response = self.client.post("/api/students", json=profile)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
