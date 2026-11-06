"""
Unit Tests for Phase 7: Full Visual Frontend.
Verifies all Section 13 UI screens, static assets, DOM anchors,
API client integration, and FastAPI routing.
"""

import unittest
from pathlib import Path
from backend.main import app, root

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

class TestVisualFrontend(unittest.TestCase):
    def test_01_frontend_files_exist(self):
        """Verify index.html, style.css, and app.js exist."""
        index_file = FRONTEND_DIR / "index.html"
        css_file = FRONTEND_DIR / "static" / "css" / "style.css"
        js_file = FRONTEND_DIR / "static" / "js" / "app.js"

        self.assertTrue(index_file.exists(), "frontend/index.html missing")
        self.assertTrue(css_file.exists(), "frontend/static/css/style.css missing")
        self.assertTrue(js_file.exists(), "frontend/static/js/app.js missing")

    def test_02_html_structure_and_screens(self):
        """Verify all Section 13 screens and components exist in index.html."""
        index_file = FRONTEND_DIR / "index.html"
        with open(index_file, "r", encoding="utf-8") as f:
            html = f.read()

        # Check essential navigation tabs
        self.assertIn('data-target="dashboard"', html)
        self.assertIn('data-target="plan"', html)
        self.assertIn('data-target="practice"', html)
        self.assertIn('data-target="mastery"', html)
        self.assertIn('data-target="diagnostic"', html)
        self.assertIn('data-target="admin"', html)

        # Check essential screen views
        self.assertIn('id="view-dashboard"', html)
        self.assertIn('id="view-plan"', html)
        self.assertIn('id="view-practice"', html)
        self.assertIn('id="view-mastery"', html)
        self.assertIn('id="view-diagnostic"', html)
        self.assertIn('id="view-admin"', html)

        # Personas are fetched at runtime rather than embedded in the page.
        self.assertIn('id="persona-select"', html)
        self.assertIn('/static/js/api.js', html)
        for student_id in ("S1024", "S1025", "S1026", "S1027"):
            self.assertNotIn(student_id, html)

        # Check interactive drawers
        self.assertIn('id="buddy-drawer"', html)
        self.assertIn('id="why-drawer"', html)

        # Check code runner elements
        self.assertTrue('id="practice-code-area"' in html or 'id="practice-code"' in html)
        self.assertTrue('id="sandbox-console"' in html or 'id="practice-output"' in html)

    def test_03_css_design_system(self):
        """Verify theme colors come from tokens and the page does not override them."""
        css_file = FRONTEND_DIR / "static" / "css" / "style.css"
        tokens_file = FRONTEND_DIR / "static" / "css" / "tokens.css"
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
        with open(tokens_file, "r", encoding="utf-8") as f:
            tokens = f.read()

        self.assertNotIn("--bg:", css)
        self.assertIn("color-scheme: light", tokens)
        self.assertIn('color-scheme: dark', tokens)
        self.assertIn('--bg: #FAF9F7', tokens)
        self.assertIn('--bg: #121110', tokens)
        self.assertIn('--ink: #1B1A17', tokens)
        self.assertIn('--ink: #F2EFE9', tokens)
        self.assertTrue(".course-tile" in css or ".course-card" in css)
        self.assertTrue(".heatmap-tiles-grid" in css or ".heatmap-grid" in css)
        self.assertIn(".drawer", css)

    def test_04_theme_initialization_respects_saved_and_system_preferences(self):
        js_file = FRONTEND_DIR / "static" / "js" / "app.js"
        with open(js_file, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("localStorage.getItem('theme')", js)
        self.assertIn("prefers-color-scheme: dark", js)
        self.assertIn("value === 'light' || value === 'dark'", js)

    def test_05_js_app_wiring(self):
        """Verify dashboard requests flow through the OpenAPI-typed client."""
        app_file = FRONTEND_DIR / "static" / "js" / "app.js"
        api_file = FRONTEND_DIR / "src" / "api.ts"
        with open(app_file, "r", encoding="utf-8") as f:
            app_js = f.read()
        with open(api_file, "r", encoding="utf-8") as f:
            api_ts = f.read()

        for method in (
            "getStudents",
            "getProfile",
            "getPlan",
            "getSummary",
            "getSkills",
            "getExercises",
            "getSeedConsistency",
            "getHealth",
            "sendChat",
        ):
            self.assertIn(f"api.{method}(", app_js)

        for endpoint in (
            "'/api/students'",
            "`/api/students/profile/",
            "`/api/students/${",
            "`/api/students/skills/",
            "`/api/plans/${",
            "`/api/practice/exercises${query}`",
            "'/api/health'",
            "'/api/admin/seed-consistency'",
            "'/api/buddy/chat'",
        ):
            self.assertIn(endpoint, api_ts)
        self.assertIn("runScenario", app_js)

    def test_06_fastapi_root_serves_frontend(self):
        """Verify root route serves the frontend HTML."""
        res = root()
        self.assertTrue(hasattr(res, "path"))
        self.assertIn("index.html", res.path)

if __name__ == "__main__":
    unittest.main()
