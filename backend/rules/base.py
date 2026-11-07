"""
Rule Base Classes & Result Schemas for Independent Verification.
Every institute rule defines its scope, ordinance clause linkage,
deterministic evaluation logic, and template-based explanation.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RuleCategory(str, Enum):
    CREDITS = "credits"
    PREREQUISITES = "prerequisites"
    OFFERING = "offering"
    ELIGIBILITY = "eligibility"
    PREFERENCE = "preference"
    TIME = "time"
    REDUNDANCY = "redundancy"
    EXISTENCE = "existence"
    BACKLOG = "backlog"

class RuleStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    NOT_APPLICABLE = "not_applicable"

class RuleScope(str, Enum):
    PLAN = "plan"
    SEMESTER = "semester"
    COURSE = "course"

class RuleResult(BaseModel):
    rule_id: str
    rule_title: str
    category: RuleCategory
    scope: RuleScope
    scope_ref: str = "plan"                 # e.g. "semester:5" or "course:COL351"
    status: RuleStatus
    observed: Any
    limit: Any
    margin: Optional[float] = None          # Positive = headroom remaining, Negative = violation magnitude
    message: str
    clause_id: Optional[str] = None         # e.g. "ORD-4.2.1" or "student_preference"
    section_title: Optional[str] = None
    source_url: Optional[str] = None
    provenance: str = "verified"
    reason: Optional[str] = None
    source_page: Optional[int] = None

class Rule:
    """Base class for all deterministic academic rules."""
    id: str = "base_rule"
    title: str = "Base Academic Rule"
    category: RuleCategory = RuleCategory.CREDITS
    scope: RuleScope = RuleScope.PLAN
    clause_id: Optional[str] = None
    section_title: Optional[str] = None
    source_url: Optional[str] = None

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        """
        Executes deterministic evaluation against the proposed plan and student context.
        Returns a list of RuleResults (one per evaluated scope_ref).
        """
        raise NotImplementedError

    def explain(self, result: RuleResult) -> str:
        """
        Returns a factual, deterministic plain-text explanation of the result.
        No LLM calls required.
        """
        return result.message
