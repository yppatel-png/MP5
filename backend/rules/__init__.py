"""
Academic Rules & Verification Module.
Export core rule primitives, registry, certificate, and PDF builder.
"""

from backend.rules.base import (
    Rule,
    RuleResult,
    RuleCategory,
    RuleStatus,
    RuleScope,
)
from backend.rules.certificate import (
    PlanCertificate,
    CertificateSummary,
    TightestMargin,
    build_certificate,
    get_kb_hash,
    RULE_SET_VERSION,
)
from backend.rules.registry import RuleRegistry, rule_registry
from backend.rules.pdf_builder import PurePDFBuilder, pdf_builder

__all__ = [
    "Rule",
    "RuleResult",
    "RuleCategory",
    "RuleStatus",
    "RuleScope",
    "PlanCertificate",
    "CertificateSummary",
    "TightestMargin",
    "build_certificate",
    "get_kb_hash",
    "RULE_SET_VERSION",
    "RuleRegistry",
    "rule_registry",
    "PurePDFBuilder",
    "pdf_builder",
]

