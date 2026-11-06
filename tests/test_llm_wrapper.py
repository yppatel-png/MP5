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
        messages = [{"role": "user", "content": "I want to become a software engineer at a top tech company"}]
        res = llm_client.generate(call_type="GOAL_INTAKE", messages=messages)
        self.assertTrue(res["fallback_used"])
        self.assertIn("content", res)
        
        parsed = json.loads(res["content"])
        self.assertEqual(parsed["goal_id"], "goal_software")
        self.assertEqual(parsed["target_role"], "Software Development Engineer")

    def test_offline_fallback_explain_plan(self):
        mock_plan = [
            {"semester": 3, "code": "COL106", "title": "Data Structures & Algorithms", "credits": 4, "skills_targeted": ["Data Structures", "Algorithms"]},
            {"semester": 3, "code": "ELL100", "title": "Intro to Electrical Eng", "credits": 4, "skills_targeted": []}
        ]
        res = llm_client.generate(
            call_type="EXPLAIN_PLAN",
            messages=[{"role": "user", "content": "Explain my schedule"}],
            fallback_data={"plan_items": mock_plan, "student_name": "Aryan"}
        )
        self.assertTrue(res["fallback_used"])
        self.assertIn("COL106", res["content"])
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
        valid_courses = ["COL106", "COL215", "MTL106"]
        test_text = "You should take COL106 and FAK999 for machine learning."
        verified = llm_client._verify_course_codes(test_text, valid_courses)
        self.assertIn("COL106", verified)
        self.assertIn("FAK999 (Note: Unverified course code)", verified)

    def test_telemetry_logging(self):
        summary = call_logger.get_summary()
        self.assertIn("total_calls", summary)
        self.assertIn("p50_latency_ms", summary)
        self.assertGreater(summary["total_calls"], 0)

if __name__ == "__main__":
    unittest.main()

