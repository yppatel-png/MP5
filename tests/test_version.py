"""
Unit test for /api/version endpoint.
Verifies git commit, build time, and app.js SHA-256 hash.
Ensures git_hash returned by /api/version equals HEAD.
"""

import subprocess
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import BASE_DIR

class TestVersionEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_api_version_returns_valid_metadata(self):
        response = self.client.get("/api/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("git_hash", data)
        self.assertIn("build_time", data)
        self.assertIn("app_js_hash", data)
        self.assertTrue(len(data["git_hash"]) > 0)
        self.assertTrue(len(data["build_time"]) > 0)
        self.assertTrue(len(data["app_js_hash"]) > 0)

    def test_version_equals_git_head(self):
        response = self.client.get("/api/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Compute actual HEAD commit from git
        head_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(BASE_DIR),
            text=True
        ).strip()

        self.assertEqual(
            data["git_hash"],
            head_commit,
            f"Expected /api/version git_hash '{data['git_hash']}' to equal git HEAD '{head_commit}'"
        )

    def test_version_alias_endpoint(self):
        response = self.client.get("/version")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("git_hash", data)

if __name__ == "__main__":
    unittest.main()
