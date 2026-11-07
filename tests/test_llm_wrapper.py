"""
Automated tests for LiteLLM wrapper, offline fallback, caching, and safety guardrails.
"""

import unittest
import json
from backend.llm.client import llm_client, call_logger
from backend.llm.cache import llm_cache

class TestLLMWrapper(unittest.TestCase):
    def setUp(self):
        llm_cache.clear()

    def test_offline_fallback_goal_intake(self):
        # Even with no LLM key, goal intake returns structured valid JSON
        from unittest.mock import patch
        messages = [{"role": "user", "content": "I want to become a software engineer at a top tech company"}]
        with patch.object(llm_client, "is_live", return_value=False):
            res = llm_client.generate(call_type="GOAL_INTAKE", messages=messages)
            self.assertTrue(res["fallback_used"])
            self.assertIn("content", res)
            
            parsed = json.loads(res["content"])
            self.assertEqual(parsed["goal_id"], "goal_software")
            self.assertEqual(parsed["target_role"], "Software Development Engineer")

    def test_offline_fallback_explain_plan(self):
        from unittest.mock import patch
        mock_plan = [
            {"semester": 3, "code": "CSL202", "title": "Data Structures", "credits": 4, "skills_targeted": ["Data Structures", "Algorithms"]},
            {"semester": 3, "code": "EEL101", "title": "Basic Electronics Engineering", "credits": 4, "skills_targeted": []}
        ]
        with patch.object(llm_client, "is_live", return_value=False):
            res = llm_client.generate(
                call_type="EXPLAIN_PLAN",
                messages=[{"role": "user", "content": "Explain my schedule"}],
                fallback_data={"plan_items": mock_plan, "student_name": "Aarav"}
            )
            self.assertTrue(res["fallback_used"])
            self.assertIn("CSL202", res["content"])
            self.assertIn("Semester 3", res["content"])

    def test_caching_layer(self):
        messages = [{"role": "user", "content": "What is Bayesian Knowledge Tracing?"}]
        res1 = llm_client.generate(call_type="BUDDY_CHAT", messages=messages)
        
        # Second call with same message must hit cache
        res2 = llm_client.generate(call_type="BUDDY_CHAT", messages=messages)
        self.assertEqual(res1["content"], res2["content"])
        
        stats = llm_cache.stats()
        self.assertGreaterEqual(stats["cache_hits"], 1)

    def test_course_code_hallucination_filter(self):
        valid_courses = ["CSL202", "CSL252", "MAL403"]
        test_text = "You should take CSL202 and FAK999 for machine learning."
        verified = llm_client._verify_course_codes(test_text, valid_courses)
        self.assertIn("CSL202", verified)
        self.assertIn("FAK999 (Note: Unverified course code)", verified)

    def test_security_unset_model_and_token(self):
        import os
        import importlib
        import backend.config
        old_model = os.environ.get("LLM_MODEL")
        old_token = os.environ.get("ADMIN_API_TOKEN")
        try:
            os.environ["LLM_MODEL"] = ""
            os.environ["ADMIN_API_TOKEN"] = ""
            importlib.reload(backend.config)
            cfg = backend.config.settings
            self.assertTrue(cfg.OFFLINE_MODE)
            self.assertIsNone(cfg.LLM_MODEL)
            self.assertTrue(len(cfg.ADMIN_API_TOKEN) >= 32)
        finally:
            if old_model is not None:
                os.environ["LLM_MODEL"] = old_model
            else:
                os.environ.pop("LLM_MODEL", None)
            if old_token is not None:
                os.environ["ADMIN_API_TOKEN"] = old_token
            else:
                os.environ.pop("ADMIN_API_TOKEN", None)
            importlib.reload(backend.config)

    def test_telemetry_logging(self):
        summary = call_logger.get_summary()
        self.assertIn("total_calls", summary)
        self.assertIn("p50_latency_ms", summary)
        self.assertGreater(summary["total_calls"], 0)

if __name__ == "__main__":
    unittest.main()
