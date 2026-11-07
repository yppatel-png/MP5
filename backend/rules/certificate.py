"""
Cryptographic Plan Certificate Model and Canonical Hashing.
Provides tamper-detection, ordinance citations, and verification methods.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from backend.rules.base import RuleResult, RuleStatus
from backend.db.seed_profile import get_institute_profile, get_seed_dir

RULE_SET_VERSION = (
    "2026.1-IIT-BHILAI-CSE-CURRICULUM"
    if get_institute_profile() == "iit_bhilai"
    else "2026.1-IIT-BHILAI-CSE-CURRICULUM"
)
SEED_DIR = get_seed_dir()

def get_kb_hash() -> str:
    """Computes a deterministic SHA-256 hash of core seed knowledge base files."""
    hasher = hashlib.sha256()
    for filename in ["courses.json", "prerequisites.json", "academic_rules.json"]:
        fpath = SEED_DIR / filename
        if fpath.exists():
            with open(fpath, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()[:16]

def canonical_json(data: Any) -> str:
    """Produces deterministic canonical JSON serialization with sorted keys and tight delimiters."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)

class TightestMargin(BaseModel):
    rule_id: str
    rule_title: str
    margin: float
    scope_ref: str
    message: str

class CertificateSummary(BaseModel):
    total_rules: int
    passed: int
    warned: int
    failed: int
    assumed_checks_count: int = 0
    verified_checks_count: int = 0
    assumed_rules_count: int = 0
    verified_rules_count: int = 0
    assumptions_statement: str = ""
    tightest_margin: Optional[TightestMargin] = None

class PlanCertificate(BaseModel):
    plan_version_id: str
    student_id: str
    generated_at: str
    kb_version: str
    rule_set_version: str
    input_hash: str
    results: List[RuleResult]
    is_valid: bool
    summary: CertificateSummary
    certificate_hash: str = ""

    def compute_hash(self) -> str:
        """
        Calculates SHA-256 over all certificate fields except certificate_hash.
        """
        payload = self.model_dump(exclude={"certificate_hash"})
        canonical = canonical_json(payload)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def seal(self) -> "PlanCertificate":
        """Calculates and embeds the cryptographic seal."""
        self.certificate_hash = self.compute_hash()
        return self

    def verify_integrity(self) -> bool:
        """Verifies if the embedded certificate_hash matches re-computed canonical hash."""
        return self.compute_hash() == self.certificate_hash

def build_certificate(
    plan: Dict[str, Any],
    student_profile: Dict[str, Any],
    results: List[RuleResult],
    plan_version_id: Optional[str] = None,
    generated_at: Optional[str] = None
) -> PlanCertificate:
    """
    Constructs and seals a complete PlanCertificate from rule evaluation results.
    """
    student_id = student_profile.get("id", student_profile.get("student_id", "STU001"))
    plan_id = plan_version_id or plan.get("version_id", plan.get("id", f"plan_{student_id}"))
    gen_time = generated_at or plan.get("created_at") or datetime.now(timezone.utc).isoformat()
    
    # Compute input hash
    input_data = {
        "student_id": student_id,
        "cgpa": student_profile.get("cgpa"),
        "programme": student_profile.get("programme"),
        "semesters": [
            {
                "sem": s.get("semester_number"),
                "courses": [c.get("code") if isinstance(c, dict) else c for c in s.get("courses", [])]
            }
            for s in plan.get("semesters", [])
        ]
    }
    input_hash = hashlib.sha256(canonical_json(input_data).encode("utf-8")).hexdigest()[:16]

    total = len(results)
    passed = sum(1 for r in results if r.status == RuleStatus.PASS)
    warned = sum(1 for r in results if r.status == RuleStatus.WARN)
    failed = sum(1 for r in results if r.status == RuleStatus.FAIL)
    is_valid = (failed == 0)

    assumed_checks = sum(1 for r in results if getattr(r, "provenance", "verified") == "assumption")
    verified_checks = total - assumed_checks
    assumed_rules = len({r.rule_id for r in results if getattr(r, "provenance", "verified") == "assumption"})
    verified_rules = len({r.rule_id for r in results if getattr(r, "provenance", "verified") == "verified"})

    if total == 0:
        assumptions_statement = "0 rule checks evaluated"
    else:
        assumptions_statement = f"{assumed_rules} rules are assumptions, pending ordinance ({assumed_checks} of {total} checks use assumptions pending the ordinance)"

    # Calculate tightest margin
    tightest: Optional[TightestMargin] = None
    if failed > 0:
        worst_margin = 0.0
        worst_res = None
        for r in results:
            if r.status == RuleStatus.FAIL and r.margin is not None:
                if worst_res is None or r.margin < worst_margin:
                    worst_margin = r.margin
                    worst_res = r
        if worst_res:
            tightest = TightestMargin(
                rule_id=worst_res.rule_id,
                rule_title=worst_res.rule_title,
                margin=worst_res.margin or 0.0,
                scope_ref=worst_res.scope_ref,
                message=worst_res.message
            )
    else:
        best_tight_margin = 9999.0
        best_res = None
        for r in results:
            if r.status == RuleStatus.PASS and r.margin is not None and r.margin >= 0:
                if r.margin < best_tight_margin:
                    best_tight_margin = r.margin
                    best_res = r
        if best_res:
            tightest = TightestMargin(
                rule_id=best_res.rule_id,
                rule_title=best_res.rule_title,
                margin=best_res.margin or 0.0,
                scope_ref=best_res.scope_ref,
                message=best_res.message
            )

    summary = CertificateSummary(
        total_rules=total,
        passed=passed,
        warned=warned,
        failed=failed,
        assumed_checks_count=assumed_checks,
        verified_checks_count=verified_checks,
        assumed_rules_count=assumed_rules,
        verified_rules_count=verified_rules,
        assumptions_statement=assumptions_statement,
        tightest_margin=tightest
    )

    cert = PlanCertificate(
        plan_version_id=str(plan_id),
        student_id=str(student_id),
        generated_at=str(gen_time),
        kb_version=get_kb_hash(),
        rule_set_version=RULE_SET_VERSION,
        input_hash=input_hash,
        results=results,
        is_valid=is_valid,
        summary=summary
    )
    return cert.seal()
