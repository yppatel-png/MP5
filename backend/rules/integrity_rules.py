"""
Academic Integrity and Catalogue Existence Rules:
- 100% Accredited Course Catalogue Citation (ORD-1.1.0)
"""

from typing import List, Dict, Any
from backend.rules.base import Rule, RuleResult, RuleCategory, RuleStatus, RuleScope

class CourseExistsCatalogueRule(Rule):
    id = "rule_course_exists_kb"
    title = "100% Accredited Course Catalogue Citation"
    category = RuleCategory.EXISTENCE
    scope = RuleScope.COURSE
    clause_id = "ORD-1.1.0"
    section_title = "Accredited Course Catalogue Verification"
    source_url = "https://home.iitbhilai.ac.in/academic-rules/ordinance-section-1.1.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        courses_db = ctx.get("courses_db", {})
        invalid_codes = []
        total_courses = 0

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            for c in sem.get("courses", []):
                total_courses += 1
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                if code not in courses_db:
                    invalid_codes.append(f"{code} (Sem {s_num})")

        if len(invalid_codes) == 0:
            status = RuleStatus.PASS
            msg = f"All {total_courses} scheduled courses verified against accredited institute catalogue (zero hallucinated codes)."
            margin = 0.0
        else:
            status = RuleStatus.FAIL
            msg = f"Unrecognized course codes detected: {', '.join(invalid_codes)}"
            margin = -float(len(invalid_codes))

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:catalogue",
            status=status,
            observed=f"{len(invalid_codes)} unrecognized" if invalid_codes else f"{total_courses} accredited",
            limit="0 unrecognized codes",
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

