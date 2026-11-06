import unittest

from backend.api.buddy import ChatRequest, send_chat_message
from backend.api.plans import (
    PlanGenerateRequest,
    generate_student_plan,
    get_active_plan,
    get_plan_certificate,
)
from backend.buddy.memory import buddy_memory
from backend.db.seed_loader import load_seed_data
from backend.student.summary import derive_student_status


class TestStudentSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_status_thresholds(self):
        self.assertEqual(derive_student_status(2, 3, 100, 0), "insufficient_evidence")
        self.assertEqual(derive_student_status(3, 3, 49, 0), "behind")
        self.assertEqual(derive_student_status(3, 3, 90, 2), "behind")
        self.assertEqual(derive_student_status(3, 3, None, 0), "needs_attention")
        self.assertEqual(derive_student_status(3, 3, 79, 0), "needs_attention")
        self.assertEqual(derive_student_status(3, 3, 90, 1), "needs_attention")
        self.assertEqual(derive_student_status(3, 3, 80, 0), "on_track")
        with self.assertRaises(ValueError):
            derive_student_status(3, 3, 101, 0)

    def test_summary_is_shared_across_plan_certificate_and_buddy(self):
        buddy_memory.clear_history("S1024")
        generated = generate_student_plan(PlanGenerateRequest(student_id="S1024"))
        summary = generated["student_summary"]

        self.assertEqual(summary["status"], "insufficient_evidence")
        self.assertIsNone(summary["readiness_percentage"])
        self.assertIsNone(summary["adherence_percentage"])
        self.assertIsNone(summary["weekly_hours_studied"])

        active_summary = get_active_plan("S1024")["student_summary"]
        certificate_summary = get_plan_certificate("S1024")["student_summary"]
        chat_response = send_chat_message(ChatRequest(student_id="S1024", message="How am I doing?"))
        buddy_summary = chat_response["facts_used"]["student_summary"]
        first_course_code = generated["plan"]["semesters"][0]["courses"][0]["code"]
        course_response = send_chat_message(
            ChatRequest(student_id="S1024", message=f"Why was {first_course_code} recommended?")
        )

        self.assertEqual(active_summary, summary)
        self.assertEqual(certificate_summary, summary)
        self.assertEqual(buddy_summary, summary)
        self.assertIn(summary["status_message"], chat_response["reply"])
        self.assertIsNone(course_response["facts_used"]["course_explanation"]["reason"])
        self.assertIn("evidence-based skill rationale", course_response["reply"])


if __name__ == "__main__":
    unittest.main()
