import tempfile
import unittest
from pathlib import Path

from backend.db import database
from backend.db.seed_loader import load_seed_data
from backend.api.students import list_students, get_student_summary


class TestSeededStudentSummaryAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_db_path = database.DB_PATH
        database.DB_PATH = Path(cls.temp_dir.name) / "summary-api.db"
        load_seed_data(reset=True)

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.original_db_path
        cls.temp_dir.cleanup()

    def test_summary_endpoint_returns_a_summary_for_every_student(self):
        students = list_students()
        self.assertTrue(students, "The seeded student list must not be empty.")

        for student in students:
            with self.subTest(student_id=student.student_id):
                summary = get_student_summary(student.student_id)
                self.assertEqual(summary.student_id, student.student_id)
                self.assertTrue(summary.status_message)


if __name__ == "__main__":
    unittest.main()
