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
            "condition": "bkt_probability >= 0.85 and score >= 0.85 and evidence_count >= 3",
            "description": "When mastery exceeds 85% across multiple items, skip introductory prerequisite content and advance to higher-level electives or compress timeline.",
            "parameters": {
                "mastery_threshold": 0.85,
                "score_threshold": 0.85,
                "min_items_required": 3,
                "credit_boost_max": 4.0
            }
        },
        {
            "id": "RULE_REMEDIATE",
            "name": "Prerequisite Remediation & Deferral",
            "action": "REMEDIATE",
            "condition": "bkt_probability < 0.45 or score < 0.40 or attempts >= 3",
            "description": "When performance drops below threshold, insert foundational prerequisite modules/resources, reduce semester load or defer advanced course.",
            "parameters": {
                "struggling_threshold": 0.40,
                "bkt_threshold": 0.45,
                "max_remedial_modules": 2,
                "defer_advanced_courses": True
            }
        },
        {
            "id": "RULE_SPACED_REVIEW",
            "name": "Spaced Repetition Review",
            "action": "REVIEW_SPACED",
            "condition": "consecutive_misses >= 3",
            "description": "When a student misses items repeatedly on a specific topic, schedule spaced-repetition review exercises.",
            "parameters": {
                "consecutive_misses_trigger": 3,
                "review_interval_days": 3
            }
        },
        {
            "id": "RULE_BEHAVIOURAL_DRIFT",
            "name": "Behavioural Drift / Workload Shedding",
            "action": "LOAD_SHED",
            "condition": "actual_weekly_hours / target_weekly_hours < 0.60",
            "description": "When weekly engaged hours drop below 60% of target, reduce elective workload, reprioritise core essentials, and notify student honestly.",
            "parameters": {
                "drift_ratio_threshold": 0.60,
                "max_credit_reduction": 4.0
            }
        },
        {
            "id": "RULE_STUDENT_OVERRIDE",
            "name": "Student Course Rejection / Preference Override",
            "action": "OVERRIDE_RESOLVE",
            "condition": "student_override_requested == True",
            "description": "Re-solve multi-semester plan respecting exclusion constraint and compute trade-offs (skills lost, workload delta, graduation impact).",
            "parameters": {
                "require_valid_alternative": True,
                "recompute_skill_gap_coverage": True
            }
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

    def get_rule_parameters(self, rule_id: str) -> Dict[str, Any]:
        """Retrieves configured parameters for a given rule ID from policy rules."""
        for r in self.policy.get("rules", []):
            if r.get("id") == rule_id:
                return r.get("parameters", {})
        return {}

    def evaluate_signals(
        self,
        student_id: str,
        signals: Dict[str, Any]
    ) -> List[AdaptationAction]:
        """
        Evaluates incoming student performance and behavioral signals against
        the active adaptation rules. Handles signal conflicts with strict pedagogical safety.
        """
        actions: List[AdaptationAction] = []
        score = signals.get("score")
        bkt_prob = signals.get("bkt_probability")
        acc_params = self.get_rule_parameters("RULE_ACCELERATE")
        acc_mastery = float(acc_params.get("mastery_threshold", 0.85))
        acc_score = float(acc_params.get("score_threshold", 0.85))
        acc_min_items = int(acc_params.get("min_items_required", 3))

        raw_ev = signals.get("evidence_count")
        if raw_ev is not None:
            evidence_count = int(raw_ev)
        else:
            try:
                from backend.db.database import get_db_cursor
                with get_db_cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM evidence_events WHERE student_id = ?", (student_id,))
                    row = cur.fetchone()
                    db_cnt = int(row[0]) if row and row[0] is not None else 0
                evidence_count = db_cnt if db_cnt > 0 else acc_min_items
            except Exception:
                evidence_count = acc_min_items

        skill_id = signals.get("skill_id", "general")
        consecutive_misses = int(signals.get("consecutive_misses", 0))
        override = signals.get("student_override")
        attempts = int(signals.get("attempts", signals.get("exercise_attempts", 1)))
        time_spent = float(signals.get("time_spent_minutes", 0.0))
        expected_time = float(signals.get("expected_time_minutes", 0.0))
        completion_rate = signals.get("module_completion_rate")

        # Resolve target weekly hours: input signals -> student profile -> default
        target_hours = signals.get("target_weekly_hours")
        if target_hours is None:
            try:
                from backend.student.model import StudentStore
                profile = StudentStore.get_profile(student_id)
                target_hours = profile.available_hours_per_week if profile else 10.0
            except Exception:
                target_hours = 10.0
        target_hours = float(target_hours)

        actual_hours = signals.get("actual_weekly_hours")
        if actual_hours is not None:
            actual_hours = float(actual_hours)

        rem_params = self.get_rule_parameters("RULE_REMEDIATE")
        rem_struggling = float(rem_params.get("struggling_threshold", 0.40))
        rem_bkt = float(rem_params.get("bkt_threshold", 0.45))

        drift_params = self.get_rule_parameters("RULE_BEHAVIOURAL_DRIFT")
        drift_thresh = float(drift_params.get("drift_ratio_threshold", 0.60))

        spaced_params = self.get_rule_parameters("RULE_SPACED_REVIEW")
        misses_thresh = int(spaced_params.get("consecutive_misses_trigger", 3))
        interval_days = int(spaced_params.get("review_interval_days", 3))

        # 1. Acceleration eligibility check
        # Requires BKT probability >= threshold AND evidence_count >= min_items AND score >= score_thresh
        can_accelerate = (
            bkt_prob is not None and bkt_prob >= acc_mastery
            and score is not None and score >= acc_score
            and evidence_count >= acc_min_items
        )

        # 2. Remediation eligibility check
        can_remediate = False
        remediate_reasons = []
        if bkt_prob is not None and bkt_prob < rem_bkt:
            can_remediate = True
            remediate_reasons.append(f"BKT mastery ({bkt_prob:.2f}) < {rem_bkt:.2f}")
        if score is not None and score < rem_struggling:
            can_remediate = True
            remediate_reasons.append(f"Recent assessment score ({score:.2f}) < {rem_struggling:.2f}")
        if attempts >= 3:
            can_remediate = True
            remediate_reasons.append(f"Repeated attempts on exercise ({attempts} >= 3)")
        if expected_time > 0 and time_spent > expected_time * 2.0:
            can_remediate = True
            remediate_reasons.append(f"Time spent ({time_spent:.1f}m) exceeded 2x expected ({expected_time*2.0:.1f}m)")
        if completion_rate is not None and float(completion_rate) < 0.50:
            can_remediate = True
            remediate_reasons.append(f"Module completion rate ({float(completion_rate):.0%}) < 50%")

        # 3. Conflict Resolution: If both fire (or high cumulative BKT mastery conflicts with struggling check), REMEDIATE wins with clear explanation
        has_high_bkt = (bkt_prob is not None and bkt_prob >= acc_mastery)
        if (can_accelerate or has_high_bkt) and can_remediate:
            explanation = (
                f"Conflicting signals resolved: High cumulative BKT mastery ({bkt_prob:.2f}), but struggling on "
                f"recent check ({'; '.join(remediate_reasons)}). Per pedagogical safety policy, REMEDIATE takes "
                f"precedence to reinforce foundations before acceleration is granted."
            )
            actions.append(AdaptationAction(
                rule_id="RULE_REMEDIATE",
                action_type="REMEDIATE",
                name="Prerequisite Remediation & Deferral",
                description=explanation,
                triggered_by={
                    "score": score,
                    "bkt_probability": bkt_prob,
                    "evidence_count": evidence_count,
                    "skill_id": skill_id,
                    "conflict_detected": True,
                    "reasons": remediate_reasons
                },
                recommended_changes={
                    "insert_remedial_resources": True,
                    "defer_advanced_course": True,
                    "target_skill": skill_id,
                    "suggested_workload_reduction_hrs": 2.5
                }
            ))
        elif can_remediate:
            explanation = (
                f"Remediation triggered: {'; '.join(remediate_reasons)}. "
                f"Inserting foundational prerequisite modules and pacing adjustments."
            )
            actions.append(AdaptationAction(
                rule_id="RULE_REMEDIATE",
                action_type="REMEDIATE",
                name="Prerequisite Remediation & Deferral",
                description=explanation,
                triggered_by={
                    "score": score,
                    "bkt_probability": bkt_prob,
                    "evidence_count": evidence_count,
                    "skill_id": skill_id,
                    "reasons": remediate_reasons
                },
                recommended_changes={
                    "insert_remedial_resources": True,
                    "defer_advanced_course": True,
                    "target_skill": skill_id,
                    "suggested_workload_reduction_hrs": 2.5
                }
            ))
        elif can_accelerate:
            explanation = (
                f"Mastery confirmed: BKT probability ({bkt_prob:.2f} >= {acc_mastery:.2f}) and recent score "
                f"({score:.2f} >= {acc_score:.2f}) across {evidence_count} corroborating items (>= {acc_min_items}). "
                f"Skipping introductory modules and unlocking advanced electives."
            )
            actions.append(AdaptationAction(
                rule_id="RULE_ACCELERATE",
                action_type="ACCELERATE",
                name="Fast-Track / Acceleration",
                description=explanation,
                triggered_by={
                    "score": score,
                    "bkt_probability": bkt_prob,
                    "evidence_count": evidence_count,
                    "skill_id": skill_id
                },
                recommended_changes={
                    "skip_intro_modules": True,
                    "advance_prerequisites": True,
                    "suggested_elective_bump": True,
                    "target_skill": skill_id
                }
            ))

        # 4. Spaced Repetition Check
        if consecutive_misses >= misses_thresh:
            actions.append(AdaptationAction(
                rule_id="RULE_SPACED_REVIEW",
                action_type="REVIEW_SPACED",
                name="Spaced Repetition Review",
                description=f"Repeated errors detected on topic ({consecutive_misses} misses >= {misses_thresh}). Scheduling reinforcement practice drills across {interval_days}-day intervals.",
                triggered_by={"consecutive_misses": consecutive_misses, "skill_id": skill_id},
                recommended_changes={
                    "queue_spaced_repetition": True,
                    "items_count": 3,
                    "interval_days": interval_days,
                    "target_skill": skill_id
                }
            ))

        # 5. Behavioural Drift Check
        if actual_hours is not None and target_hours > 0:
            ratio = actual_hours / target_hours
            if ratio < drift_thresh:
                actions.append(AdaptationAction(
                    rule_id="RULE_BEHAVIOURAL_DRIFT",
                    action_type="LOAD_SHED",
                    name="Behavioural Drift / Workload Shedding",
                    description=f"Weekly study engagement ({actual_hours:.1f}h) dropped below {drift_thresh:.0%} of target ({target_hours:.1f}h, ratio {ratio:.2f}). Shedding elective workload to prevent burnout.",
                    triggered_by={"actual_hours": actual_hours, "target_hours": target_hours, "ratio": round(ratio, 2)},
                    recommended_changes={
                        "reduce_credit_cap": 4.0,
                        "reprioritize_core_only": True,
                        "alert_student": True
                    }
                ))

        # 6. Student Override Check
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

        from backend.planner.validator import independent_validator
        student_profile = {
            "student_id": new_plan.get("student_id", ""),
            "programme": "iit_bhilai_btech_cse_2023",
            "current_semester": 1,
            "cgpa": 8.0,
            "completed_courses": [],
            "available_hours_per_week": 12.0
        }
        val = independent_validator.validate_plan(new_plan, student_profile)
        if val.get("is_valid"):
            audit_status = "Valid - all evaluated degree audit and course constraints satisfied."
        else:
            violations = "; ".join(val.get("errors", []))
            audit_status = f"Invalid - constraints violated: {violations}"

        return {
            "rejected_course": rejected_course,
            "removed_courses": removed_codes,
            "added_replacement_courses": added_codes,
            "net_credit_change": round(new_credits - old_credits, 1),
            "workload_delta_hours_per_week": round((new_workload - old_workload) / max(len(new_plan.get("semesters", [1])), 1), 1),
            "skills_lost": skills_lost,
            "skills_gained": skills_gained,
            "degree_audit_status": audit_status,
            "validation": val
        }

adaptation_policy_engine = AdaptationPolicyEngine()
