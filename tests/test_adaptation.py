"""
Unit Tests for Phase 5: Adaptation Policy & Simulation Engine.
Verifies policy rules, strong vs. weak quiz adaptation, plan diffing,
student course override trade-offs, behavioural drift, and fast-forward scenarios.
"""

import unittest
from backend.db.seed_loader import load_seed_data
from backend.adapt.policy import adaptation_policy_engine
from backend.adapt.simulator import adaptation_simulator, SCRIPTED_SCENARIOS
from backend.api.adapt import (
    list_simulation_scenarios,
    simulate_scenario,
    submit_course_override,
    evaluate_adaptation_signals,
    get_adaptation_audit_log,
    SimulateScenarioRequest,
    CourseOverrideRequest,
    SignalEvaluationRequest
)

class TestAdaptationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Reset and seed database state for clean test baseline."""
        load_seed_data()

    def test_01_adaptation_policy_loading(self):
        """Verify adaptation policy correctly parses configured YAML rules."""
        self.assertIsNotNone(adaptation_policy_engine.policy)
        rules = adaptation_policy_engine.policy.get("rules", [])
        rule_ids = [r["id"] for r in rules]
        self.assertIn("RULE_ACCELERATE", rule_ids)
        self.assertIn("RULE_REMEDIATE", rule_ids)
        self.assertIn("RULE_SPACED_REVIEW", rule_ids)
        self.assertIn("RULE_BEHAVIOURAL_DRIFT", rule_ids)
        self.assertIn("RULE_STUDENT_OVERRIDE", rule_ids)

    def test_02_policy_signal_evaluations(self):
        """Test policy engine triggers correct actions based on score, bkt, drift, and override."""
        # Strong score
        actions = adaptation_policy_engine.evaluate_signals("BH-SW-001", {"score": 0.95, "bkt_probability": 0.90})
        self.assertTrue(any(a.action_type == "ACCELERATE" for a in actions))

        # Weak score
        actions = adaptation_policy_engine.evaluate_signals("BH-SW-001", {"score": 0.20, "bkt_probability": 0.25})
        self.assertTrue(any(a.action_type == "REMEDIATE" for a in actions))

        # Repeated misses
        actions = adaptation_policy_engine.evaluate_signals("BH-SW-001", {"consecutive_misses": 4})
        self.assertTrue(any(a.action_type == "REVIEW_SPACED" for a in actions))

        # Behavioural drift
        actions = adaptation_policy_engine.evaluate_signals("BH-SW-001", {"actual_weekly_hours": 3.0, "target_weekly_hours": 8.0})
        self.assertTrue(any(a.action_type == "LOAD_SHED" for a in actions))

        # Student override
        actions = adaptation_policy_engine.evaluate_signals("BH-SW-001", {"student_override": {"rejected_course": "CSL303"}})
        self.assertTrue(any(a.action_type == "OVERRIDE_RESOLVE" for a in actions))

    def test_03_strong_quiz_adaptation(self):
        """Verify strong quiz triggers acceleration and produces an independently valid plan."""
        res = adaptation_simulator.run_strong_quiz("BH-SW-001")
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["action_triggered"], "ACCELERATE")
        self.assertTrue(res["bkt_update"]["mastered"])
        self.assertTrue(res["validation"]["is_valid"])
        self.assertTrue(any(k in res["plan_diff"] for k in ["added_courses", "removed_courses", "rescheduled_courses"]))
        self.assertTrue(len(res["explanation"]) > 20)

    def test_04_weak_quiz_adaptation(self):
        """Verify weak quiz triggers remediation, inserts practice resources, and produces valid plan."""
        res = adaptation_simulator.run_weak_quiz("BH-SW-001")
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["action_triggered"], "REMEDIATE")
        self.assertFalse(res["bkt_update"]["mastered"])
        self.assertTrue(res["validation"]["is_valid"])
        self.assertEqual(res["remedial_resources_added"], 2)
        # Verify remedial resources exist in the adapted plan's first semester
        first_sem = res["adapted_plan"]["semesters"][0]
        self.assertIn("remedial_resources", first_sem)
        self.assertEqual(len(first_sem["remedial_resources"]), 2)

    def test_05_course_override_and_tradeoffs(self):
        """Verify student course rejection excludes the course and calculates trade-offs."""
        res = adaptation_simulator.run_course_override("BH-SW-001", rejected_course="CSL303")
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["action_triggered"], "OVERRIDE_RESOLVE")
        self.assertTrue(res["validation"]["is_valid"])

        # Verify CSL303 is absent from all scheduled semesters
        scheduled_codes = [c["code"] for s in res["adapted_plan"]["semesters"] for c in s["courses"]]
        self.assertNotIn("CSL303", scheduled_codes)

        # Check trade-off calculation
        tradeoffs = res["tradeoffs"]
        self.assertEqual(tradeoffs["rejected_course"], "CSL303")
        self.assertIn("CSL303", tradeoffs["removed_courses"])
        self.assertIn("database_systems", tradeoffs["skills_lost"])

    def test_06_behavioural_drift_loadshedding(self):
        """Verify low study hours triggers workload reduction with a valid schedule."""
        res = adaptation_simulator.run_behavioural_drift("BH-SW-001", logged_weekly_hours=3.0)
        self.assertEqual(res["status"], "adapted")
        self.assertEqual(res["action_triggered"], "LOAD_SHED")
        self.assertTrue(res["validation"]["is_valid"])
        self.assertIn("engagement", res["explanation"].lower())

    def test_07_fast_forward_scenario(self):
        """Verify fast-forward advances student semester, records completed course, and re-plans."""
        res = adaptation_simulator.run_fast_forward("BH-SW-001")
        self.assertEqual(res["status"], "fast_forwarded")
        self.assertEqual(res["new_semester"], 4)
        self.assertTrue(res["validation"]["is_valid"])
        self.assertIn("Fast-forwarded to Semester 5", res["explanation"])

    def test_08_api_endpoints_and_audit_history(self):
        """Verify REST endpoints for scenarios, simulation, overrides, signal evaluation, and audit log."""
        # 1. Scenarios catalog
        scenarios_res = list_simulation_scenarios()
        self.assertEqual(scenarios_res["count"], 5)

        # 2. Simulate endpoint
        sim_res = simulate_scenario(SimulateScenarioRequest(scenario_id="scenario_strong_quiz", student_id="BH-SW-001"))
        self.assertEqual(sim_res["status"], "adapted")

        # 3. Override endpoint
        ovr_res = submit_course_override(CourseOverrideRequest(student_id="BH-SW-001", rejected_course="CSL303"))
        self.assertEqual(ovr_res["status"], "adapted")

        # 4. Signal evaluation endpoint
        eval_res = evaluate_adaptation_signals(SignalEvaluationRequest(
            student_id="BH-SW-001",
            signals={"score": 0.95, "bkt_probability": 0.90}
        ))
        self.assertGreaterEqual(eval_res["actions_triggered_count"], 1)

        # 5. Audit log endpoint
        audit_res = get_adaptation_audit_log("BH-SW-001")
        self.assertGreaterEqual(audit_res["total_events"], 1)
        first_event = audit_res["events"][0]
        self.assertIn("action_type", first_event)
        self.assertIn("explanation", first_event)

if __name__ == "__main__":
    unittest.main()
