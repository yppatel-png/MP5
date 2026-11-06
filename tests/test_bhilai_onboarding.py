"""Source and onboarding checks for the IIT Bhilai CSE student flow."""

import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import database
from backend.db.seed_loader import load_seed_data
from backend.main import app


class TestBhilaiOnboarding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = database.DB_PATH
        database.DB_PATH = Path(cls.temp_dir.name) / "onboarding-test.db"
        load_seed_data(reset=True)
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        database.DB_PATH = cls.original_db_path
        cls.temp_dir.cleanup()

    def _profile_payload(self, **overrides):
        payload = {
            "name": "New Bhilai Student",
            "programme_id": "iit_bhilai_btech_cse_2023",
            "current_semester": 3,
            "cgpa": 8.2,
            "available_hours_per_week": 12,
            "goal": "Explore AI and systems",
            "interests": ["AI", "systems"],
            "completed_course_codes": ["CSL100", "MAL100"],
            "shortlisted_course_codes": ["CSL304", "CSL622"],
        }
        payload.update(overrides)
        return payload

    def test_programme_data_matches_source_credit_totals_and_catalogue(self):
        response = self.client.get("/api/curricula")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        programmes = {item["degree"]: item for item in data["programmes"]}
        btech = programmes["BTech"]
        mtech = programmes["MTech"]
        phd = programmes["PhD"]

        self.assertEqual(sum(row["stated_credits"] for row in btech["semesters"]), 144)
        self.assertEqual(sum(btech["credit_categories"].values()), 144)
        self.assertEqual(btech["additional_non_graded_core_units"], 12)
        self.assertEqual(sum(row["stated_credits"] for row in mtech["semesters"]), 54)
        self.assertEqual(sum(mtech["credit_categories"].values()), 54)
        self.assertEqual(phd["status"], "programme_listed_curriculum_unavailable")
        self.assertEqual(len(data["catalogue_courses"]), 44)
        self.assertIn("eligibility not specified", data["catalogue_courses"][-1]["programme_table_status"])

    def test_new_profile_is_saved_and_reloadable_without_becoming_a_seeded_persona(self):
        created = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(),
        )
        self.assertEqual(created.status_code, 201, created.text)
        profile = created.json()
        self.assertTrue(profile["student_id"].startswith("BH-"))
        self.assertEqual(profile["completed_course_codes"], ["CSL100", "MAL100"])
        self.assertEqual(profile["shortlisted_course_codes"], ["CSL304", "CSL622"])

        loaded = self.client.get(f"/api/onboarding/profiles/{profile['student_id']}")
        self.assertEqual(loaded.status_code, 200, loaded.text)
        self.assertEqual(loaded.json(), profile)
        persona_ids = {
            item["student_id"] for item in self.client.get("/api/students").json()
        }
        self.assertNotIn(profile["student_id"], persona_ids)

    def test_update_changes_saved_profile_and_revalidates_course_choices(self):
        created = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(),
        )
        profile_id = created.json()["student_id"]
        payload = self._profile_payload(
            cgpa=8.5,
            current_semester=4,
            completed_course_codes=["CSL100", "MAL100", "CSL201"],
        )
        updated = self.client.put(
            f"/api/onboarding/profiles/{profile_id}",
            json=payload,
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["cgpa"], 8.5)
        self.assertEqual(
            self.client.get(f"/api/onboarding/profiles/{profile_id}").json()["current_semester"],
            4,
        )

    def test_unknown_programme_and_course_combinations_are_rejected(self):
        unsupported = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(programme_id="iit_bhilai_phd_cse"),
        )
        self.assertEqual(unsupported.status_code, 422)

        unknown_course = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(completed_course_codes=["NOT_A_COURSE"]),
        )
        self.assertEqual(unknown_course.status_code, 422)

        duplicate_course = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(completed_course_codes=["CSL100", "CSL100"]),
        )
        self.assertEqual(duplicate_course.status_code, 422)
        self.assertIn("only be entered once", duplicate_course.json()["detail"])

        unavailable_semester = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(current_semester=9),
        )
        self.assertEqual(unavailable_semester.status_code, 422)

    def test_assistant_local_mode_uses_source_curriculum_without_calling_gemini(self):
        profile = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(current_semester=1, completed_course_codes=[]),
        ).json()
        with patch("backend.api.onboarding.llm_client.generate") as generate:
            response = self.client.post(
                "/api/onboarding/assistant",
                json={
                    "profile_id": profile["student_id"],
                    "question": "What should I do next?",
                    "share_with_gemini": False,
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["mode"], "local")
        self.assertIn("CSL100", response.json()["reply"])
        self.assertIn("not sent to Gemini", response.json()["privacy_note"])
        generate.assert_not_called()

    def test_gemini_assistant_context_omits_profile_name_and_id(self):
        profile = self.client.post(
            "/api/onboarding/profiles",
            json=self._profile_payload(),
        ).json()
        with patch(
            "backend.api.onboarding.llm_client.generate",
            return_value={"content": "Review your current semester courses.", "fallback_used": False},
        ) as generate:
            response = self.client.post(
                "/api/onboarding/assistant",
                json={
                    "profile_id": profile["student_id"],
                    "question": "What are my next steps?",
                    "share_with_gemini": True,
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["mode"], "gemini")
        messages = generate.call_args.kwargs["messages"]
        prompt = "\n".join(message["content"] for message in messages)
        self.assertNotIn(profile["name"], prompt)
        self.assertNotIn(profile["student_id"], prompt)
        self.assertIn("CSL100", prompt)
        self.assertIn("does not establish PE/OE eligibility", prompt)


if __name__ == "__main__":
    unittest.main()
