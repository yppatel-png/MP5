"""
Eligibility and Credit Transfer Academic Rules:
- Minor Area in Computer Science Eligibility (ORD-6.1.0)
- Online Credit Transfer Ceiling (NPTEL / SWAYAM) (ORD-7.1.0)
"""

from typing import List, Dict, Any
from backend.rules.base import Rule, RuleResult, RuleCategory, RuleStatus, RuleScope

class MinorEligibilityRule(Rule):
    id = "rule_minor_cse_eligibility"
    title = "Minor Area in Computer Science Eligibility"
    category = RuleCategory.ELIGIBILITY
    scope = RuleScope.PLAN
    clause_id = "ORD-6.1.0"
    section_title = "Minor Area in Computer Science Eligibility"
    source_url = "https://home.iitbhilai.ac.in/academic-rules/minor-guidelines-2023"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        programme = ctx.get("programme", "CS1")
        cgpa = float(ctx.get("cgpa", 8.0))
        courses_db = ctx.get("courses_db", {})
        cutoff = 7.5

        # Identify all courses scheduled in the plan
        all_courses = [
            (c if isinstance(c, str) else c.get("code", "")).upper()
            for sem in plan.get("semesters", [])
            for c in sem.get("courses", [])
        ]

        has_col_minor_electives = any(
            courses_db.get(code, {}).get("department") == "Computer Science and Engineering" and
            courses_db.get(code, {}).get("course_type") in ["elective", "minor"]
            for code in all_courses
        )

        margin = round(cgpa - cutoff, 2)

        # If student is CS major, minor in CS is not applicable
        if programme in ["CS1", "CS5"]:
            return [RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref="plan:minor",
                status=RuleStatus.NOT_APPLICABLE,
                observed=f"Enrolled in {programme}",
                limit=f"Non-CS programme (CGPA >={cutoff})",
                margin=margin,
                message=f"Student enrolled in primary CS degree ({programme}); Minor in CSE does not apply.",
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            )]

        if not has_col_minor_electives:
            return [RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref="plan:minor",
                status=RuleStatus.PASS,
                observed=f"CGPA {cgpa:.2f}, no CS minor courses scheduled",
                limit=f"CGPA >= {cutoff:.2f}",
                margin=margin,
                message="No CS minor electives scheduled in the current plan; eligibility satisfied.",
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            )]

        if cgpa >= cutoff:
            status = RuleStatus.PASS
            msg = f"CGPA {cgpa:.2f} satisfies the {cutoff:.2f} minimum requirement for CS Minor coursework (headroom +{margin:.2f})."
        else:
            status = RuleStatus.FAIL
            msg = f"CGPA {cgpa:.2f} does not meet the {cutoff:.2f} minimum cutoff required for CS Minor coursework (deficit {abs(margin):.2f})."

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref="plan:minor",
            status=status,
            observed=cgpa,
            limit=cutoff,
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class OnlineCreditCapRule(Rule):
    id = "rule_online_credit_transfer_limit"
    title = "NPTEL/SWAYAM Online Credit Ceiling"
    category = RuleCategory.ELIGIBILITY
    scope = RuleScope.PLAN
    clause_id = "ORD-7.1.0"
    section_title = "Online Credit Transfer Ceiling (NPTEL / SWAYAM)"
    source_url = "https://home.iitbhilai.ac.in/academic-rules/nptel-transfer-policy"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        max_total_online = 12.0
        max_per_sem = 1
        courses_db = ctx.get("courses_db", {})

        total_online_credits = 0.0
        sem_violations = []

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            online_in_sem = 0
            for c in sem.get("courses", []):
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                c_data = courses_db.get(code, {})
                # Check tag or type for online / mooc / nptel
                is_online = c_data.get("is_online", False) or c_data.get("course_type") == "online" or "nptel" in code.lower()
                if is_online:
                    online_in_sem += 1
                    total_online_credits += float(c_data.get("credits", 3.0))

            if online_in_sem > max_per_sem:
                sem_violations.append(f"Semester {s_num}: {online_in_sem} online courses scheduled (max {max_per_sem}/sem).")

        margin_total = round(max_total_online - total_online_credits, 1)

        if total_online_credits <= max_total_online and len(sem_violations) == 0:
            status = RuleStatus.PASS
            msg = f"{total_online_credits:.1f} online credits scheduled within {max_total_online:.1f} cap (headroom +{margin_total:.1f} cr; max 1/sem respected)."
        else:
            status = RuleStatus.FAIL
            issues = []
            if total_online_credits > max_total_online:
                issues.append(f"Total online credits ({total_online_credits:.1f}) exceeds {max_total_online:.1f} ceiling")
            issues.extend(sem_violations)
            msg = f"Online course violation: {'; '.join(issues)}."

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref="plan:online_transfer",
            status=status,
            observed=f"{total_online_credits:.1f} credits",
            limit=f"{max_total_online:.1f} credits",
            margin=margin_total,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

