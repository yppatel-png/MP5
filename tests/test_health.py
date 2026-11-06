"""
Automated unit tests for Health and System status endpoints.
Tests endpoints directly to ensure tests run reliably without extra network test clients.
"""

import unittest
from backend.main import root
from backend.api.health import health_check
from backend.config import settings

class TestHealthEndpoint(unittest.TestCase):
    def test_root_endpoint(self):
        res = root()
        # Verify it returns HTML dashboard containing key links
        if hasattr(res, "path"):
            with open(res.path, "r", encoding="utf-8") as f:
                body = f.read()
        else:
            body = res.body.decode("utf-8")
        self.assertIn("Adobe Personalised Learning Buddy", body)

    def test_health_check_endpoint(self):
        res = health_check()
        self.assertEqual(res["status"], "healthy")
        self.assertIn("llm", res)
        self.assertIn("telemetry", res)
        self.assertIn("database", res)
        # Verify secret key value is never leaked in response
        if settings.LLM_API_KEY:
            self.assertNotIn(settings.LLM_API_KEY, str(res))
        self.assertIn("is_live", res["llm"])
        self.assertIn("key_configured", res["llm"])

if __name__ == "__main__":
    unittest.main()
