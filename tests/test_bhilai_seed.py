import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.db import database
from backend.db.seed_loader import load_seed_data
from backend.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = PROJECT_ROOT / "data" / "seed_bhilai"
SOURCE_FILE = PROJECT_ROOT / "data" / "seed" / "iit_bhilai_cse_curricula.json"


class TestBhilaiSeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = database.DB_PATH
        database.DB_PATH = Path(cls.temp_dir.name) / "bhilai-test.db"
        load_seed_data(reset=True)
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        database.DB_PATH = cls.original_db_path
        cls.temp_dir.cleanup()

    def test_seed_courses_match_source_catalogue_and_semester_slots(self):
        source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
        btech = next(
            item for item in source["programmes"]
            if item["id"] == "iit_bhilai_btech_cse_2023"
        )
        catalogue = {
            item["code"]: item for item in source["catalogue_courses"]
            if item["programme_table_status"] == "BTech IC"
            or item["programme_table_status"] == "BTech PC"
        }
        scheduled = {
            course["code"]: semester["semester"]
            for semester in btech["semesters"]
            for course in semester["courses"]
            if not course.get("placeholder") and course["code"] in catalogue
        }
        seeded = json.loads((SEED_DIR / "courses.json").read_text(encoding="utf-8"))

        self.assertEqual({course["code"] for course in seeded}, set(scheduled))
        for course in seeded:
            with self.subTest(course=course["code"]):
                source_course = catalogue[course["code"]]
                self.assertEqual(course["title"], source_course["title"])
                self.assertEqual(course["credits"], source_course["credits"])
                self.assertEqual(
                    course["semester_offered"],
                    f"semester_{scheduled[course['code']]}",
                )
                self.assertIn("IIT Bhilai Courses of Study", course["source"])

    def test_every_seeded_student_has_a_summary_and_unsupported_rules_are_not_claimed(self):
        self.assertEqual(self.client.get("/api/health").json()["institute_profile"], "iit_bhilai")
        students_response = self.client.get("/api/students")
        self.assertEqual(students_response.status_code, 200, students_response.text)
        students = students_response.json()
        self.assertEqual(len(students), 3)

        for student in students:
            with self.subTest(student_id=student["student_id"]):
                response = self.client.get(
                    f"/api/students/{student['student_id']}/summary"
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIsNone(response.json()["credit_cap"])

        self.assertEqual(self.client.get("/api/rules").json(), [])
        self.assertEqual(
            self.client.post(
                "/api/plans/generate",
                json={"student_id": students[0]["student_id"]},
            ).status_code,
            409,
        )
        diagnostic = self.client.get(
            f"/api/students/{students[0]['student_id']}/diagnostic/next"
        )
        self.assertEqual(diagnostic.status_code, 200, diagnostic.text)
        self.assertFalse(diagnostic.json()["available"])

    def test_buddy_answers_course_lookup_from_the_seed_without_live_ai(self):
        student = self.client.get("/api/students").json()[0]

        def deterministic_fallback(**kwargs):
            return {
                "content": kwargs["fallback_data"]["deterministic_reply"],
                "fallback_used": True,
            }

        with patch(
            "backend.buddy.router.llm_client.generate",
            side_effect=deterministic_fallback,
        ) as generate:
            response = self.client.post(
                "/api/buddy/chat",
                json={
                    "student_id": student["student_id"],
                    "message": "Why was CSL100 listed?",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Introduction to Programming", response.json()["reply"])
        self.assertIn("Semester 1", response.json()["reply"])
        self.assertIn("not a personalized recommendation", response.json()["reply"])
        generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
