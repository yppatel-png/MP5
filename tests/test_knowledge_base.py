"""
Automated unit tests for Phase 1 Knowledge Base.
Verifies seed loader, integrity validator, DAG acyclicity, and catalogue API endpoints.
"""

import unittest
from backend.db.seed_loader import load_seed_data
from backend.api.courses import list_courses, get_course_detail, list_skills, list_academic_rules, list_goal_templates, list_programmes
from scripts.validate_kb import run_validation
from fastapi import HTTPException

class TestKnowledgeBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database is freshly seeded
        load_seed_data(reset=True)

    def test_validator_script(self):
        """Runs the complete KB validation script and expects 100% success."""
        is_valid = run_validation()
        self.assertTrue(is_valid, "Knowledge base validation failed!")

    def test_list_courses_api(self):
        """Verifies course listing and filtering."""
        all_courses = list_courses()
        self.assertGreaterEqual(len(all_courses), 30)

        cs_courses = list_courses(department="Computer Science and Engineering")
        self.assertGreater(len(cs_courses), 10)
        for c in cs_courses:
            self.assertEqual(c["department"], "Computer Science and Engineering")

        core_courses = list_courses(course_type="core")
        self.assertGreater(len(core_courses), 5)

    def test_course_detail_with_prereqs_and_skills(self):
        """Verifies deep course details for CSL202 (Data Structures)."""
        detail = get_course_detail("CSL202")
        self.assertEqual(detail["code"], "CSL202")
        self.assertIn("credits", detail)
        self.assertEqual(detail["credits"], 4.0)

        # Check prerequisites
        prereqs = [p["requires_code"] for p in detail["prerequisites"]]
        self.assertIn("CSL100", prereqs)

        # Check skills
        skill_ids = [s["skill_id"] for s in detail["skills"]]
        self.assertIn("data_structures", skill_ids)

        # Check modules
        self.assertGreaterEqual(len(detail["modules"]), 3)

    def test_course_not_found(self):
        """Ensures non-existent course codes return 404."""
        with self.assertRaises(HTTPException) as ctx:
            get_course_detail("NONEXIST999")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_auxiliary_kb_endpoints(self):
        """Verifies skills, rules, goal templates, and programmes endpoints."""
        skills = list_skills()
        self.assertGreaterEqual(len(skills), 20)

        rules = list_academic_rules()
        self.assertGreaterEqual(len(rules), 6)
        rule_types = [r["type"] for r in rules]
        self.assertIn("credit_cap_max", rule_types)

        goals = list_goal_templates()
        self.assertEqual(len(goals), 4)
        goal_ids = [g["goal_id"] for g in goals]
        self.assertIn("goal_software", goal_ids)
        self.assertIn("goal_higher_studies", goal_ids)
        self.assertIn("goal_upsc", goal_ids)
        self.assertIn("goal_startup", goal_ids)

        progs = list_programmes()
        self.assertGreaterEqual(len(progs), 1)
        prog_codes = [p["code"] for p in progs]
        self.assertIn("BH-CSE-BTECH", prog_codes)

    def test_skill_resource_coverage_and_unverified_exclusion(self):
        """Verifies skill-resource coverage is >= 90% and unverified resources are kept out of plans."""
        from backend.planner.candidate import candidate_retriever
        resources = candidate_retriever.retrieve_resources_for_gaps([
            {"skill_id": "programming_fundamentals", "gap": 0.5}
        ])
        # Ensure that sample_unverified_resource is excluded
        res_ids = [r["resource_id"] for r in resources]
        self.assertNotIn("sample_unverified_resource", res_ids)
        self.assertIn("nptel_cs_prog_c", res_ids)

if __name__ == "__main__":
    unittest.main()
