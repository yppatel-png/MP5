"""
Unit tests for PostgreSQL / SQLite Database Adapter, Seeds Auto-Load, Adminer Students View,
and Admin Grade Recomputation.
"""

import unittest
from backend.db.database import (
    adapt_sql_for_postgres,
    get_db_cursor,
    init_db,
    is_postgres
)
from backend.db.seed_loader import load_seed_data, reset_database
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.api.admin import edit_student_grade, EditGradeRequest
from backend.config import settings

class TestDatabaseAndAdminGradeFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_sql_adaptation_for_postgres(self):
        """Verifies that SQLite DDL and DML statements are cleanly adapted to valid PostgreSQL syntax."""
        # 1. Parameter placeholder translation
        q_params = "SELECT * FROM courses WHERE code = ? AND credits = ?;"
        adapted_params = adapt_sql_for_postgres(q_params)
        self.assertIn("%s", adapted_params)
        self.assertNotIn("?", adapted_params)

        # 2. DROP TABLE with CASCADE
        q_drop = "DROP TABLE IF EXISTS student_profiles;"
        adapted_drop = adapt_sql_for_postgres(q_drop)
        self.assertEqual(adapted_drop, "DROP TABLE IF EXISTS student_profiles CASCADE;")

        # 3. INSERT OR REPLACE ON CONFLICT translation
        q_insert = """
        INSERT OR REPLACE INTO student_profiles (
            student_id, name, programme, year, current_semester, cgpa,
            goal_id, target_role, available_hours_per_week, remaining_elective_slots,
            completed_courses_json, constraints_json, preferences_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
        """
        adapted_insert = adapt_sql_for_postgres(q_insert)
        self.assertIn("INSERT INTO student_profiles", adapted_insert)
        self.assertIn("ON CONFLICT (student_id) DO UPDATE SET", adapted_insert)
        self.assertIn("name = EXCLUDED.name", adapted_insert)
        self.assertIn("cgpa = EXCLUDED.cgpa", adapted_insert)
        self.assertNotIn("?", adapted_insert)

        # 4. Prerequisites conflict on composite keys
        q_prereq = "INSERT OR REPLACE INTO prerequisites (course_code, requires_code, type, source) VALUES (?, ?, ?, ?);"
        adapted_prereq = adapt_sql_for_postgres(q_prereq)
        self.assertIn("ON CONFLICT (course_code, requires_code) DO UPDATE SET", adapted_prereq)

        # 5. Autoincrement to SERIAL
        q_serial = "CREATE TABLE test (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);"
        adapted_serial = adapt_sql_for_postgres(q_serial)
        self.assertIn("id SERIAL PRIMARY KEY", adapted_serial)

    def test_adminer_students_view(self):
        """
        Verifies that the database presents a 'students' view containing all seeded student records,
        allowing database consoles such as Adminer to immediately inspect student data.
        """
        with get_db_cursor() as cur:
            cur.execute("SELECT student_id, name, cgpa FROM students ORDER BY student_id ASC;")
            rows = cur.fetchall()
            self.assertGreater(len(rows), 0)
            first_student = dict(rows[0])
            self.assertIn("student_id", first_student)
            self.assertIn("name", first_student)
            self.assertIn("cgpa", first_student)

    def test_admin_grade_edit_updates_students_view_and_plan(self):
        """
        Critical Requirement:
        Verify that an admin grade edit updates the student record (visible in Adminer/students view)
        and automatically triggers plan re-synthesis with a new version number.
        """
        student_id = "BH-SW-001"
        profile_before = StudentStore.get_profile(student_id)
        self.assertIsNotNone(profile_before)
        initial_cgpa = profile_before.cgpa

        # Perform admin grade edit
        req = EditGradeRequest(
            student_id=student_id,
            course_code="CSL100",
            new_grade="A"
        )
        res = edit_student_grade(req)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["student_id"], student_id)
        self.assertEqual(res["updated_course"], "CSL100")
        self.assertEqual(res["new_grade"], "A")
        self.assertIn("new_plan_version", res)

        # Verify update in student_profiles store
        profile_after = StudentStore.get_profile(student_id)
        self.assertEqual(profile_after.cgpa, res["recomputed_cgpa"])

        # Verify update appears immediately in the 'students' view (which Adminer reads)
        with get_db_cursor() as cur:
            cur.execute("SELECT cgpa, completed_courses_json FROM students WHERE student_id = ?;", (student_id,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            row_dict = dict(row)
            self.assertEqual(row_dict["cgpa"], res["recomputed_cgpa"])
            self.assertIn('"grade": "A"', row_dict["completed_courses_json"])

    def test_make_reset_restores_clean_seeds(self):
        """Verifies that reset_database + load_seed_data restores a clean state."""
        counts = load_seed_data(reset=True)
        self.assertGreaterEqual(counts.get("courses", 0), 20)
        self.assertGreaterEqual(counts.get("modules", 0), 100)
        self.assertGreaterEqual(counts.get("skills", 0), 20)
        self.assertGreaterEqual(counts.get("exercises", 0), 100)

if __name__ == "__main__":
    unittest.main()
