"""
Central Academic Rule Registry.
Coordinates execution of all deterministic rules, context enrichment,
certificate generation, and tamper verification.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Type, Optional

from backend.rules.base import Rule, RuleResult, RuleStatus, RuleCategory
from backend.rules.credit_rules import (
    SemesterMinCreditsRule,
    SemesterMaxCreditsRule,
    DegreeTotalCreditsRule,
    StudentCreditCapPreferenceRule,
)
from backend.rules.prerequisite_rules import (
    PrerequisiteChainRule,
    SemesterParityRule,
    CoRequisiteRule,
    BacklogSequenceRule,
)
from backend.rules.eligibility_rules import (
    MinorEligibilityRule,
    OnlineCreditCapRule,
)
from backend.rules.workload_rules import (
    NoCoTakingPairRule,
    WeeklyTimeBudgetRule,
    NoDuplicateRegistrationRule,
    StudentAvoidPairsRule,
    NoAlreadyMasteredRule,
)
from backend.rules.integrity_rules import CourseExistsCatalogueRule
from backend.rules.certificate import (
    PlanCertificate,
    build_certificate,
    get_kb_hash,
    RULE_SET_VERSION,
)
from backend.db.seed_profile import get_institute_profile, get_seed_dir
from backend.rules.bhilai_rules import build_bhilai_rules

SEED_DIR = get_seed_dir()

def load_seed(filename: str):
    with open(SEED_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

class RuleRegistry:
    """
    Registry for all accredited and preference rules in the institute.
    """

    def __init__(self):
        if get_institute_profile() == "iit_bhilai":
            self._rules = build_bhilai_rules()
        else:
            self._rules = [
                CourseExistsCatalogueRule(),
                PrerequisiteChainRule(),
                SemesterParityRule(),
                CoRequisiteRule(),
                BacklogSequenceRule(),
                SemesterMinCreditsRule(),
                SemesterMaxCreditsRule(),
                DegreeTotalCreditsRule(),
                MinorEligibilityRule(),
                OnlineCreditCapRule(),
                NoCoTakingPairRule(),
                WeeklyTimeBudgetRule(),
                NoDuplicateRegistrationRule(),
                StudentAvoidPairsRule(),
                StudentCreditCapPreferenceRule(),
                NoAlreadyMasteredRule(),
            ]

        # Cache seed data
        self.raw_courses = load_seed("courses.json")
        self.raw_prereqs = load_seed("prerequisites.json")
        self.raw_academic_rules = load_seed("academic_rules.json")

        self.courses_db: Dict[str, Dict[str, Any]] = {
            c["code"].upper(): c for c in self.raw_courses
        }

        self.prereq_map: Dict[str, List[str]] = {}
        for p in self.raw_prereqs:
            self.prereq_map.setdefault(p["course_code"].upper(), []).append(p["requires_code"].upper())

    def register_rule(self, rule: Rule):
        self._rules.append(rule)

    def get_rules(self) -> List[Rule]:
        return list(self._rules)

    def build_context(self, plan: Dict[str, Any], student_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a comprehensive context dictionary for deterministic rule evaluation.
        """
        completed = student_profile.get("completed_courses", [])
        clean_completed = []
        for c in completed:
            if isinstance(c, dict):
                clean_completed.append(c)
            elif isinstance(c, str):
                clean_completed.append({"course_code": c.upper(), "grade": "B", "credits": 4.0})

        return {
            "student_id": student_profile.get("id", student_profile.get("student_id", "STU001")),
            "cgpa": float(student_profile.get("cgpa", 8.0)),
            "programme": student_profile.get("programme", "iit_bhilai_btech_cse_2023"),
            "completed_courses": clean_completed,
            "backlogs": student_profile.get("backlogs", []),
            "constraints": student_profile.get("constraints", {}),
            "skills_state": student_profile.get("skills_state", []),
            "courses_db": self.courses_db,
            "prereq_map": self.prereq_map,
            "coreq_map": {},
            "raw_rules": self.raw_academic_rules,
            "available_hours_per_week": student_profile.get("available_hours_per_week", 12.0),
        }

    def run_all(self, plan: Dict[str, Any], student_profile: Dict[str, Any]) -> List[RuleResult]:
        """
        Executes all registered rules deterministically against the plan.
        """
        ctx = self.build_context(plan, student_profile)
        all_results: List[RuleResult] = []

        for rule in self._rules:
            try:
                res_list = rule.check(plan, ctx)
                all_results.extend(res_list)
            except Exception as e:
                all_results.append(RuleResult(
                    rule_id=rule.id,
                    rule_title=rule.title,
                    category=rule.category,
                    scope=rule.scope,
                    scope_ref="execution_error",
                    status=RuleStatus.FAIL,
                    observed=str(e),
                    limit="clean execution",
                    margin=-1.0,
                    message=f"Rule check failed with exception: {e}",
                    clause_id=rule.clause_id,
                    section_title=rule.section_title,
                    source_url=rule.source_url,
                ))

        return all_results

    def generate_certificate(
        self,
        plan: Dict[str, Any],
        student_profile: Dict[str, Any],
        plan_version_id: Optional[str] = None,
        generated_at: Optional[str] = None
    ) -> PlanCertificate:
        """
        Evaluates all rules, generates certificate summary and returns a sealed PlanCertificate.
        """
        results = self.run_all(plan, student_profile)
        return build_certificate(
            plan,
            student_profile,
            results,
            plan_version_id=plan_version_id,
            generated_at=generated_at
        )

    def verify_plan(
        self,
        plan: Dict[str, Any],
        student_profile: Dict[str, Any],
        expected_certificate_hash: Optional[str] = None,
        generated_at: Optional[str] = None,
        plan_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Re-evaluates all rules from scratch and checks whether the plan has been tampered with.
        """
        fresh_cert = self.generate_certificate(
            plan,
            student_profile,
            plan_version_id=plan_version_id,
            generated_at=generated_at
        )
        is_tampered = False
        diff = []

        if expected_certificate_hash:
            if fresh_cert.certificate_hash != expected_certificate_hash:
                is_tampered = True
                diff.append({
                    "type": "hash_mismatch",
                    "expected": expected_certificate_hash,
                    "recalculated": fresh_cert.certificate_hash,
                    "reason": "Plan content, courses, or rule results have been altered since certificate generation."
                })

        return {
            "tampered": is_tampered,
            "is_tamper_free": not is_tampered,
            "is_valid": fresh_cert.is_valid,
            "certificate_hash": fresh_cert.certificate_hash,
            "expected_hash": expected_certificate_hash,
            "summary": fresh_cert.summary.model_dump(),
            "results": [r.model_dump() for r in fresh_cert.results],
            "diff": diff,
        }

    def to_legacy_report(self, results: List[RuleResult]) -> Dict[str, Any]:
        """
        Formats results into legacy dictionary format.
        """
        rule_checks = []
        errors = []

        for r in results:
            passed = (r.status in [RuleStatus.PASS, RuleStatus.NOT_APPLICABLE])
            rule_checks.append({
                "rule_id": r.rule_id,
                "name": r.rule_title,
                "passed": passed,
                "description": r.section_title or r.rule_title,
                "details": r.message,
                "clause_id": r.clause_id,
                "margin": r.margin,
            })
            if r.status == RuleStatus.FAIL:
                errors.append(f"[{r.clause_id or r.rule_id}] {r.message}")

        rules_passed = sum(1 for c in rule_checks if c["passed"])
        is_valid = (len(errors) == 0 and rules_passed == len(rule_checks))

        return {
            "is_valid": is_valid,
            "rules_evaluated": len(rule_checks),
            "rules_passed": rules_passed,
            "rule_results": rule_checks,
            "errors": errors,
        }

rule_registry = RuleRegistry()
