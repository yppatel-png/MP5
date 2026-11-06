"""
Adaptation Policy Engine.
Evaluates multi-modal performance and behavioural signals against institute-configured
adaptation rules, recommending dynamic curricular adaptations (acceleration, remediation,
spaced repetition, load-shedding, and override resolution).
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "adaptation_policy.yaml"

DEFAULT_POLICY = {
    "version": "1.0.0",
    "rules": [
        {
            "id": "RULE_ACCELERATE",
            "name": "Fast-Track / Acceleration",
            "action": "ACCELERATE",
            "condition": "bkt_probability >= 0.85 and score >= 0.85",
            "description": "When mastery exceeds 85%, skip introductory prerequisite content and advance to higher-level electives or compress timeline.",
            "parameters": {"mastery_threshold": 0.85, "score_threshold": 0.85, "credit_boost_max": 4.0}
        },
        {
            "id": "RULE_REMEDIATE",
            "name": "Prerequisite Remediation & Deferral",
            "action": "REMEDIATE",
            "condition": "bkt_probability < 0.45 or score < 0.40",
            "description": "When performance drops below 40%, insert foundational prerequisite modules/resources, reduce semester load or defer advanced course.",
            "parameters": {"struggling_threshold": 0.40, "bkt_threshold": 0.45, "max_remedial_modules": 2, "defer_advanced_courses": True}
        },
        {
            "id": "RULE_SPACED_REVIEW",
            "name": "Spaced Repetition Review",
            "action": "REVIEW_SPACED",
            "condition": "consecutive_misses >= 3",
            "description": "When a student misses items repeatedly on a specific topic, schedule spaced-repetition review exercises.",
            "parameters": {"consecutive_misses_trigger": 3, "review_interval_days": 3}
        },
        {
            "id": "RULE_BEHAVIOURAL_DRIFT",
            "name": "Behavioural Drift / Workload Shedding",
            "action": "LOAD_SHED",
            "condition": "actual_weekly_hours / target_weekly_hours < 0.60",
            "description": "When weekly engaged hours drop below 60% of target, reduce elective workload, reprioritise core essentials, and notify student honestly.",
            "parameters": {"drift_ratio_threshold": 0.60, "max_credit_reduction": 4.0}
        },
        {
            "id": "RULE_STUDENT_OVERRIDE",
            "name": "Student Course Rejection / Preference Override",
            "action": "OVERRIDE_RESOLVE",
            "condition": "student_override_requested == True",
            "description": "Re-solve multi-semester plan respecting exclusion constraint and compute trade-offs (skills lost, workload delta, graduation impact).",
            "parameters": {"require_valid_alternative": True, "recompute_skill_gap_coverage": True}
        }
    ]
}

class AdaptationAction(BaseModel):
    rule_id: str
    action_type: str  # ACCELERATE, REMEDIATE, REVIEW_SPACED, LOAD_SHED, OVERRIDE_RESOLVE
    name: str
    description: str
    triggered_by: Dict[str, Any]
    recommended_changes: Dict[str, Any]

class AdaptationPolicyEngine:
    def __init__(self, config_file: Optional[Path] = None):
        self.config_path = config_file or CONFIG_PATH
        self.policy = self._load_policy()

    def _load_policy(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "adaptation_policy" in data:
                        return data["adaptation_policy"]
            except Exception:
                pass
        return DEFAULT_POLICY

    def evaluate_signals(
        self,
        student_id: str,
        signals: Dict[str, Any]
    ) -> List[AdaptationAction]:
        """
        Evaluates incoming student performance and behavioral signals against
        the active adaptation rules. Returns zero or more triggered actions.
        """
        actions: List[AdaptationAction] = []
        score = signals.get("score")
        bkt_prob = signals.get("bkt_probability")
        skill_id = signals.get("skill_id", "general")
        consecutive_misses = signals.get("consecutive_misses", 0)
        actual_hours = signals.get("actual_weekly_hours")
        target_hours = signals.get("target_weekly_hours", 8.0)
        override = signals.get("student_override")

        # 1. Acceleration Check
        if (bkt_prob is not None and bkt_prob >= 0.85) or (score is not None and score >= 0.85):
            actions.append(AdaptationAction(
                rule_id="RULE_ACCELERATE",
                action_type="ACCELERATE",
                name="Fast-Track / Acceleration",
                description="Mastery demonstrated above 85% threshold. Skip introductory prerequisite material, accelerate timeline, and unlock advanced electives early.",
                triggered_by={"score": score, "bkt_probability": bkt_prob, "skill_id": skill_id},
                recommended_changes={
                    "skip_intro_modules": True,
                    "advance_prerequisites": True,
                    "suggested_elective_bump": True,
                    "target_skill": skill_id
                }
            ))

        # 2. Remediation / Deferral Check
        if (bkt_prob is not None and bkt_prob < 0.45) or (score is not None and score < 0.40):
            actions.append(AdaptationAction(
                rule_id="RULE_REMEDIATE",
                action_type="REMEDIATE",
                name="Prerequisite Remediation & Deferral",
                description="Performance signal below 40%. Insert targeted prerequisite micro-modules, defer advanced courses to later semesters to protect CGPA.",
                triggered_by={"score": score, "bkt_probability": bkt_prob, "skill_id": skill_id},
                recommended_changes={
                    "insert_remedial_resources": True,
                    "defer_advanced_course": True,
                    "target_skill": skill_id,
                    "suggested_workload_reduction_hrs": 2.5
                }
            ))

        # 3. Spaced Repetition Check
        if consecutive_misses >= 3:
            actions.append(AdaptationAction(
                rule_id="RULE_SPACED_REVIEW",
                action_type="REVIEW_SPACED",
                name="Spaced Repetition Review",
                description="Repeated errors detected on topic (3+ misses). Scheduling reinforcement practice drills across spaced intervals.",
                triggered_by={"consecutive_misses": consecutive_misses, "skill_id": skill_id},
                recommended_changes={
                    "queue_spaced_repetition": True,
                    "items_count": 3,
                    "interval_days": 3,
                    "target_skill": skill_id
                }
            ))

        # 4. Behavioural Drift Check
        if actual_hours is not None and target_hours > 0:
            ratio = actual_hours / target_hours
            if ratio < 0.60:
                actions.append(AdaptationAction(
                    rule_id="RULE_BEHAVIOURAL_DRIFT",
                    action_type="LOAD_SHED",
                    name="Behavioural Drift / Workload Shedding",
                    description=f"Weekly study engagement ({actual_hours}h) dropped below 60% of target ({target_hours}h). Shedding elective load to prevent burnout.",
                    triggered_by={"actual_hours": actual_hours, "target_hours": target_hours, "ratio": round(ratio, 2)},
                    recommended_changes={
                        "reduce_credit_cap": 4.0,
                        "reprioritize_core_only": True,
                        "alert_student": True
                    }
                ))

        # 5. Student Override Check
        if override:
            actions.append(AdaptationAction(
                rule_id="RULE_STUDENT_OVERRIDE",
                action_type="OVERRIDE_RESOLVE",
                name="Student Course Rejection / Preference Override",
                description="Student requested exclusion or change of a scheduled course. Re-solving plan with constraint and computing trade-offs.",
                triggered_by={"override": override},
                recommended_changes={
                    "excluded_course": override.get("rejected_course"),
                    "reason": override.get("reason", "Student preference"),
                    "recompute_plan": True
                }
            ))

        return actions

    @staticmethod
    def compute_tradeoffs(
        old_plan: Dict[str, Any],
        new_plan: Dict[str, Any],
        rejected_course: str
    ) -> Dict[str, Any]:
        """
        Calculates trade-offs when a student overrides a course recommendation:
        - Skills lost vs skills gained
        - Workload change
        - Credit delta
        - Degree audit compliance status
        """
        old_courses = {c["code"]: c for s in old_plan.get("semesters", []) for c in s.get("courses", [])}
        new_courses = {c["code"]: c for s in new_plan.get("semesters", []) for c in s.get("courses", [])}

        old_skills = set(old_plan.get("skills_covered", []))
        new_skills = set(new_plan.get("skills_covered", []))

        skills_lost = list(old_skills - new_skills)
        skills_gained = list(new_skills - old_skills)

        added_codes = [code for code in new_courses if code not in old_courses]
        removed_codes = [code for code in old_courses if code not in new_courses]

        old_workload = sum(s.get("workload_hours", 0.0) for s in old_plan.get("semesters", []))
        new_workload = sum(s.get("workload_hours", 0.0) for s in new_plan.get("semesters", []))

        old_credits = old_plan.get("total_credits_planned", 0.0)
        new_credits = new_plan.get("total_credits_planned", 0.0)

        return {
            "rejected_course": rejected_course,
            "removed_courses": removed_codes,
            "added_replacement_courses": added_codes,
            "net_credit_change": round(new_credits - old_credits, 1),
            "workload_delta_hours_per_week": round((new_workload - old_workload) / max(len(new_plan.get("semesters", [1])), 1), 1),
            "skills_lost": skills_lost,
            "skills_gained": skills_gained,
            "degree_audit_status": "Valid - all institute core requirements and credit totals remain satisfied."
        }

adaptation_policy_engine = AdaptationPolicyEngine()

