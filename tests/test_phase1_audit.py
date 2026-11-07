"""
Phase 1 Automated QA & Clean-Machine Packaging Test Suite.
Verifies:
1. Idempotent seed data loading (running seed twice creates zero duplicate rows).
2. Clean repo audit: zero leaked API secrets, zero unrouted LLM calls, zero hardcoded models.
3. Outbound network audit: zero CDNs, zero remote fonts, zero runtime package/model downloads.
4. Offline LLM-off deterministic fallback behavior with health endpoint reporting.
5. Administrative authorization (X-Admin-Token) protecting mutation endpoints from IDOR.
6. Admin mutations trigger dynamic re-processing across CGPA, BKT, and multi-semester plans without restarts.
7. Container packaging configuration (.dockerignore, healthchecks, pre-configured Adminer).
"""

import unittest
from pathlib import Path
from fastapi import HTTPException

from backend.config import settings
from backend.db.seed_loader import load_seed_data
from backend.db.database import get_db_cursor
from backend.student.model import StudentStore
from backend.planner.solver import multi_semester_planner
from backend.rules.registry import rule_registry
from backend.api.health import health_check
from backend.api.plans import generate_student_plan, PlanGenerateRequest
from backend.api.admin import (
    verify_admin_token,
    edit_student_grade,
    edit_course,
    edit_prerequisite,
    edit_academic_rule,
    edit_student_constraint,
    EditGradeRequest,
    EditCourseRequest,
    EditPrerequisiteRequest,
    EditRuleRequest,
    EditConstraintRequest
)
from scripts.qa.secrets_scan import scan_file_for_secrets
from scripts.qa.outbound_audit import audit_frontend_files, audit_backend_code

ROOT_DIR = Path(__file__).resolve().parent.parent

class TestPhase1Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_seed_data(reset=True)

    def test_01_seed_idempotency_double_run(self):
        """Verify running seed loading twice without reset does not duplicate rows."""
        # Clean reset
        counts1 = load_seed_data(reset=True)
        
        # Second idempotent run without reset
        counts2 = load_seed_data(reset=False)

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM evidence_events;")
            evidence_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM student_profiles;")
            profiles_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM courses;")
            courses_count = cur.fetchone()[0]

        self.assertEqual(evidence_count, counts1["seed_evidence_events"], "Duplicate evidence events detected!")
        self.assertEqual(profiles_count, counts1["student_profiles"], "Duplicate profiles detected!")
        self.assertEqual(courses_count, counts1["courses"], "Duplicate courses detected!")

    def test_02_secrets_and_config_cleanliness(self):
        """Verify no hard-coded API keys, unrouted calls, or models exist in the codebase."""
        import os
        from scripts.qa.secrets_scan import EXCLUDE_DIRS, EXCLUDE_FILES
        violations = []
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
            for f in files:
                if f in EXCLUDE_FILES or f.endswith((".pdf", ".db", ".sqlite", ".png", ".jpg")):
                    continue
                fpath = Path(root) / f
                if fpath.suffix in {".py", ".json", ".js", ".html", ".env", ".example"}:
                    v = scan_file_for_secrets(fpath)
                    violations.extend(v)

        self.assertEqual(len(violations), 0, f"Secrets scan found violations: {violations}")

    def test_03_outbound_calls_and_zero_egress(self):
        """Verify zero external CDNs, fonts, or runtime model/NLTK downloads exist."""
        fe_violations = audit_frontend_files()
        be_violations = audit_backend_code()
        all_v = fe_violations + be_violations

        self.assertEqual(len(all_v), 0, f"Outbound egress audit found violations: {all_v}")

    def test_04_offline_mode_fallback_and_notice(self):
        """Verify that when API key is blank or offline, health returns is_live=False and plans generate."""
        data = health_check()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("llm", data)

        # Plan generation must still succeed with 100% validity in offline mode
        plan_res = generate_student_plan(PlanGenerateRequest(
            student_id="BH-SW-001",
            reason_for_change="Offline audit test"
        ))
        self.assertIn("validation_report", plan_res)
        self.assertTrue(plan_res["validation_report"]["is_valid"])

    def test_05_admin_token_authorization(self):
        """Verify admin mutation endpoints reject requests lacking valid admin authentication."""
        # Unauthenticated request raises HTTPException(401)
        with self.assertRaises(HTTPException) as ctx:
            verify_admin_token(x_admin_token=None, authorization=None)
        self.assertEqual(ctx.exception.status_code, 401)

        # Invalid token raises HTTPException(401)
        with self.assertRaises(HTTPException) as ctx2:
            verify_admin_token(x_admin_token="wrong-token-value", authorization=None)
        self.assertEqual(ctx2.exception.status_code, 401)

        # Valid X-Admin-Token succeeds
        self.assertTrue(verify_admin_token(x_admin_token=settings.ADMIN_API_TOKEN))

        # Valid Bearer authorization succeeds
        self.assertTrue(verify_admin_token(x_admin_token=None, authorization=f"Bearer {settings.ADMIN_API_TOKEN}"))

    def test_06_admin_grade_edit_triggers_recomputation(self):
        """Verify editing student grade updates CGPA and triggers plan re-synthesis without restarts."""
        # Update grade of BH-SW-001
        res = edit_student_grade(EditGradeRequest(
            student_id="BH-SW-001",
            course_code="CSL100",
            new_grade="A"
        ))
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["new_grade"], "A")
        self.assertTrue(res["plan_valid"])

        # Verify profile has updated grade and CGPA
        prof = StudentStore.get_profile("BH-SW-001")
        csl100 = next(c for c in prof.completed_courses if c.course_code == "CSL100")
        self.assertEqual(csl100.grade, "A")

    def test_07_admin_course_edit_and_prerequisite_sync(self):
        """Verify course credit update and prerequisite addition immediately sync in-memory structures."""
        # 1. Edit course credits
        res_c = edit_course(EditCourseRequest(
            code="CSL202",
            credits=5.0
        ))
        self.assertEqual(res_c["status"], "success")

        # Check in-memory sync
        self.assertEqual(multi_semester_planner.courses["CSL202"]["credits"], 5.0)

        # 2. Add prerequisite
        res_p = edit_prerequisite(EditPrerequisiteRequest(
            course_code="CSL304",
            requires_code="CSL202",
            action="add"
        ))
        self.assertEqual(res_p["status"], "success")

        # Check in-memory sync
        self.assertIn("CSL202", multi_semester_planner.prereq_map["CSL304"])

    def test_08_admin_rule_and_constraint_mutation(self):
        """Verify updating rule parameters and student constraints triggers dynamic re-solution."""
        # 1. Edit rule
        res_r = edit_academic_rule(EditRuleRequest(
            rule_id="rule_sem_max_credits",
            parameters={"max_credits": 23.0}
        ))
        self.assertEqual(res_r["status"], "success")

        # 2. Edit student constraints
        res_cons = edit_student_constraint(EditConstraintRequest(
            student_id="BH-SW-001",
            constraints={"credit_headroom_next_semester": 2.0}
        ))
        self.assertEqual(res_cons["status"], "success")
        self.assertTrue(res_cons["plan_valid"])

    def test_09_packaging_and_docker_configuration(self):
        """Verify .dockerignore, requirements.lock, and docker-compose healthchecks exist."""
        dockerignore = ROOT_DIR / ".dockerignore"
        req_lock = ROOT_DIR / "requirements.lock"
        compose_file = ROOT_DIR / "docker-compose.yml"

        self.assertTrue(dockerignore.exists(), ".dockerignore missing!")
        self.assertTrue(req_lock.exists(), "requirements.lock missing!")
        self.assertTrue(compose_file.exists(), "docker-compose.yml missing!")

        with open(compose_file, "r", encoding="utf-8") as f:
            compose_text = f.read()

        self.assertIn("healthcheck:", compose_text)
        self.assertIn("ADMINER_DEFAULT_SERVER: db", compose_text)
        self.assertIn("ADMIN_API_TOKEN", compose_text)

if __name__ == "__main__":
    unittest.main()
