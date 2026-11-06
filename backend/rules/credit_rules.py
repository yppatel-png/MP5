"""
Credit-based Academic Rules:
- Minimum credits per semester (ORD-4.2.1)
- Maximum credits per semester / Overload (ORD-4.2.2 / ORD-4.3.0)
- Degree total credit target (ORD-3.1.0)
- Student requested credit cap preference (student_preference)
"""

from typing import List, Dict, Any
from backend.rules.base import Rule, RuleResult, RuleCategory, RuleStatus, RuleScope

class SemesterMinCreditsRule(Rule):
    id = "rule_sem_min_credits"
    title = "Minimum Semester Registration Limit"
    category = RuleCategory.CREDITS
    scope = RuleScope.SEMESTER
    clause_id = "ORD-4.2.1"
    section_title = "Minimum Semester Registration Limit"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-4.2.1"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        results = []
        semesters = plan.get("semesters", [])
        min_limit = 14.0

        for sem in semesters:
            s_num = sem.get("semester_number", 0)
            credits = float(sem.get("total_credits", 0.0))
            margin = round(credits - min_limit, 1)

            if credits >= min_limit:
                status = RuleStatus.PASS
                msg = f"Semester {s_num}: {credits:.1f} credits registered (meets {min_limit:.1f} minimum; margin +{margin:.1f})."
            elif s_num == 8:
                # Graduating semester dispensation under ORD-4.2.1
                status = RuleStatus.PASS
                msg = f"Semester {s_num}: {credits:.1f} credits registered (graduating semester dispensation under ORD-4.2.1)."
            elif credits == 0.0:
                status = RuleStatus.WARN
                msg = f"Semester {s_num}: 0 elective credits scheduled (internship or off-term)."
            else:
                status = RuleStatus.WARN
                msg = f"Semester {s_num}: {credits:.1f} elective credits registered (advisory: ensure core curriculum brings total to {min_limit:.1f} minimum)."

            results.append(RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref=f"semester:{s_num}",
                status=status,
                observed=credits,
                limit=min_limit,
                margin=margin,
                message=msg,
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            ))
        return results

class SemesterMaxCreditsRule(Rule):
    id = "rule_sem_max_credits"
    title = "Maximum Semester Credit Ceiling"
    category = RuleCategory.CREDITS
    scope = RuleScope.SEMESTER
    clause_id = "ORD-4.2.2"
    section_title = "Maximum Standard Semester Credit Ceiling"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-4.2.2"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        results = []
        semesters = plan.get("semesters", [])
        cgpa = float(ctx.get("cgpa", 8.0))
        overload_eligible = cgpa >= 8.5
        max_limit = 24.0 if overload_eligible else 22.0
        clause = "ORD-4.3.0" if overload_eligible else "ORD-4.2.2"

        for sem in semesters:
            s_num = sem.get("semester_number", 0)
            credits = float(sem.get("total_credits", 0.0))
            margin = round(max_limit - credits, 1)

            if credits <= max_limit:
                status = RuleStatus.PASS
                msg = f"Semester {s_num}: {credits:.1f} credits within {'overload' if overload_eligible else 'standard'} cap ({max_limit:.1f} max; headroom +{margin:.1f})."
            else:
                status = RuleStatus.FAIL
                msg = f"Semester {s_num}: {credits:.1f} credits breaches {'overload' if overload_eligible else 'standard'} cap ({max_limit:.1f} max by {abs(margin):.1f})."

            results.append(RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref=f"semester:{s_num}",
                status=status,
                observed=credits,
                limit=max_limit,
                margin=margin,
                message=msg,
                clause_id=clause,
                section_title=self.section_title,
                source_url=self.source_url
            ))
        return results

class DegreeTotalCreditsRule(Rule):
    id = "rule_degree_total_credits"
    title = "Degree Graduation Credit Requirements"
    category = RuleCategory.CREDITS
    scope = RuleScope.PLAN
    clause_id = "ORD-3.1.0"
    section_title = "Degree Graduation Credit Requirements"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-3.1.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        min_required = 142.0
        past_courses = ctx.get("completed_courses", [])
        courses_db = ctx.get("courses_db", {})
        
        past_credits = sum(float(courses_db.get(c if isinstance(c, str) else c.get("course_code", ""), {}).get("credits", 4.0)) for c in past_courses)
        planned_credits = sum(float(s.get("total_credits", 0.0)) for s in plan.get("semesters", []))
        total_projected = round(past_credits + planned_credits, 1)
        margin = round(total_projected - min_required, 1)

        if total_projected >= min_required:
            status = RuleStatus.PASS
            msg = f"Projected degree completion: {total_projected:.1f} credits meets {min_required:.1f} degree target (margin +{margin:.1f})."
        else:
            status = RuleStatus.WARN
            msg = f"Projected degree completion: {total_projected:.1f} credits tracked towards {min_required:.1f} graduation target (balance in general core)."

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref="plan:graduation",
            status=status,
            observed=total_projected,
            limit=min_required,
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class StudentCreditCapPreferenceRule(Rule):
    id = "rule_student_credit_cap"
    title = "Student Credit Ceiling Preference"
    category = RuleCategory.PREFERENCE
    scope = RuleScope.SEMESTER
    clause_id = "student_preference"
    section_title = "Student Requested Credit Ceiling"
    source_url = "https://local-advisor/preferences/workload"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        constraints = ctx.get("constraints", {})
        pref_headroom = constraints.get("credit_headroom_next_semester")
        if pref_headroom is None:
            return []

        results = []
        first_sem = (plan.get("semesters", []) or [{}])[0]
        if not first_sem:
            return []

        s_num = first_sem.get("semester_number", 0)
        credits = float(first_sem.get("total_credits", 0.0))
        preferred_cap = 16.0 + float(pref_headroom)
        margin = round(preferred_cap - credits, 1)

        status = RuleStatus.PASS if credits <= preferred_cap + 1.0 else RuleStatus.WARN
        msg = f"Next semester (Sem {s_num}): {credits:.1f} credits (preferred target: {preferred_cap:.1f} cr; margin {margin:+.1f})."

        results.append(RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref=f"semester:{s_num}",
            status=status,
            observed=credits,
            limit=preferred_cap,
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        ))
        return results
