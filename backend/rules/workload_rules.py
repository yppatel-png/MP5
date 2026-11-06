"""
Workload Balance, Redundancy, and Student Preference Academic Rules:
- Mutually Exclusive Heavy Theory Coursework (ORD-8.2.0)
- Weekly Time & Workload Budget (ORD-8.1.0)
- Duplicate Registration Prevention (ORD-4.4.0)
- Student Avoid Pairs Preference (student_preference)
- Zero Redundant Instruction on Mastered Skills (PED-2.1.0)
"""

from typing import List, Dict, Any, Set
from backend.rules.base import Rule, RuleResult, RuleCategory, RuleStatus, RuleScope

class NoCoTakingPairRule(Rule):
    id = "rule_no_co_taking_heavy_dsa_discrete"
    title = "Workload Balance: Do Not Co-take Heavy Theory"
    category = RuleCategory.TIME
    scope = RuleScope.SEMESTER
    clause_id = "ORD-8.2.0"
    section_title = "Workload Optimization: Mutually Exclusive Theory Coursework"
    source_url = "https://cse.iitd.ac.in/curriculum/undergraduate-advising-notes"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        pair = ["COL351", "COL352"]
        violations = []

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            codes = set(
                (c if isinstance(c, str) else c.get("code", "")).upper()
                for c in sem.get("courses", [])
            )
            if pair[0] in codes and pair[1] in codes:
                violations.append(f"Semester {s_num}: both {pair[0]} and {pair[1]} are scheduled together.")

        if len(violations) == 0:
            status = RuleStatus.PASS
            msg = f"Heavy theory pair ({pair[0]} & {pair[1]}) properly separated across semesters."
            margin = 1.0
        else:
            status = RuleStatus.FAIL
            msg = f"Heavy theory collision: {'; '.join(violations)}"
            margin = -1.0

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:workload_pairs",
            status=status,
            observed=f"{len(violations)} co-taking collisions",
            limit="0 co-taking collisions",
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class WeeklyTimeBudgetRule(Rule):
    id = "rule_weekly_time_budget"
    title = "Weekly Workload Feasibility"
    category = RuleCategory.TIME
    scope = RuleScope.SEMESTER
    clause_id = "ORD-8.1.0"
    section_title = "Student Weekly Self-Study and Contact Hour Budget"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-8.1.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        results = []
        # Max sustainable total weekly hours (contact + self-study) is typically 48 hrs/wk
        max_sustainable_weekly = 48.0

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            # Default workload per course: ~10 hrs/wk or credits * 2.5
            total_weekly_hours = sum(
                float(c.get("workload_hours_per_week", float(c.get("credits", 4.0)) * 2.5))
                for c in sem.get("courses", [])
            )
            margin = round(max_sustainable_weekly - total_weekly_hours, 1)

            if total_weekly_hours <= max_sustainable_weekly:
                status = RuleStatus.PASS
                msg = f"Semester {s_num}: {total_weekly_hours:.1f} hrs/wk planned load (within {max_sustainable_weekly:.1f} hr budget; headroom +{margin:.1f} hrs/wk)."
            else:
                status = RuleStatus.FAIL
                msg = f"Semester {s_num}: {total_weekly_hours:.1f} hrs/wk exceeds sustainable budget of {max_sustainable_weekly:.1f} hrs/wk by {abs(margin):.1f} hrs."

            results.append(RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref=f"semester:{s_num}",
                status=status,
                observed=f"{total_weekly_hours:.1f} hrs/wk",
                limit=f"{max_sustainable_weekly:.1f} hrs/wk",
                margin=margin,
                message=msg,
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            ))
        return results

class NoDuplicateRegistrationRule(Rule):
    id = "rule_no_duplicate_courses"
    title = "Zero Duplicate Course Registrations"
    category = RuleCategory.REDUNDANCY
    scope = RuleScope.PLAN
    clause_id = "ORD-4.4.0"
    section_title = "Duplicate Registration Prevention"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-4.4.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        completed_past = set(
            (c if isinstance(c, str) else c.get("course_code", "")).upper()
            for c in ctx.get("completed_courses", [])
            if (isinstance(c, dict) and c.get("grade") not in ["F", "E"]) or isinstance(c, str)
        )
        seen_in_plan = set()
        duplicates = []

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            for c in sem.get("courses", []):
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                if code in completed_past:
                    duplicates.append(f"{code} (Semester {s_num}) was already completed with a passing grade in prior terms.")
                if code in seen_in_plan:
                    duplicates.append(f"{code} is scheduled multiple times in the academic plan.")
                seen_in_plan.add(code)

        if len(duplicates) == 0:
            status = RuleStatus.PASS
            msg = f"Zero course duplication verified across {len(seen_in_plan)} planned courses."
            margin = 0.0
        else:
            status = RuleStatus.FAIL
            msg = f"Duplication violation: {'; '.join(duplicates)}"
            margin = -float(len(duplicates))

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref="plan:duplication",
            status=status,
            observed=len(duplicates),
            limit=0,
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class StudentAvoidPairsRule(Rule):
    id = "rule_student_avoid_pairs"
    title = "Student Course Separation Preference"
    category = RuleCategory.PREFERENCE
    scope = RuleScope.SEMESTER
    clause_id = "student_preference"
    section_title = "Student Requested Course Separation"
    source_url = "https://local-advisor/preferences/co-taking"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        constraints = ctx.get("constraints", {})
        avoid_pairs = constraints.get("no_co_taking_courses", [])
        if not avoid_pairs:
            return []

        violations = []
        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            sem_codes = set(
                (c if isinstance(c, str) else c.get("code", "")).upper()
                for c in sem.get("courses", [])
            )
            for pair in avoid_pairs:
                if len(pair) == 2 and pair[0].upper() in sem_codes and pair[1].upper() in sem_codes:
                    violations.append(f"Semester {s_num}: both {pair[0]} and {pair[1]} scheduled together against student preference.")

        status = RuleStatus.PASS if len(violations) == 0 else RuleStatus.WARN
        msg = "All student-requested course separation preferences respected." if status == RuleStatus.PASS else "; ".join(violations)

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:student_avoid_pairs",
            status=status,
            observed=len(violations),
            limit=0,
            margin=0.0 if status == RuleStatus.PASS else -float(len(violations)),
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class NoAlreadyMasteredRule(Rule):
    id = "rule_no_already_mastered"
    title = "Zero Redundant Instruction on Mastered Skills"
    category = RuleCategory.REDUNDANCY
    scope = RuleScope.PLAN
    clause_id = "PED-2.1.0"
    section_title = "Pedagogical Efficiency: Zero Redundant Instruction"
    source_url = "https://local-advisor/pedagogical-standards/mastery"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        mastered_skills = set(
            sk.get("skill_id", "")
            for sk in ctx.get("skills_state", [])
            if float(sk.get("p_mastery", 0.0)) >= 0.90
        )
        if not mastered_skills:
            return [RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=self.scope,
                scope_ref="plan:pedagogical_efficiency",
                status=RuleStatus.PASS,
                observed=0,
                limit=0,
                margin=0.0,
                message="No redundant remedial instruction scheduled for already-mastered concepts.",
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            )]

        # Check if any remedial module targeting mastered skills is forced
        redundant_items = []
        for sem in plan.get("semesters", []):
            for c in sem.get("courses", []):
                if c.get("is_remedial") and any(sk in mastered_skills for sk in c.get("skills_targeted", [])):
                    redundant_items.append(f"{c.get('code')} (remedial on mastered skill)")

        status = RuleStatus.PASS if len(redundant_items) == 0 else RuleStatus.WARN
        msg = f"Zero redundant remedial courses assigned across {len(mastered_skills)} mastered skills." if status == RuleStatus.PASS else f"Potential redundancy: {', '.join(redundant_items)}"

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=self.scope,
            scope_ref="plan:pedagogical_efficiency",
            status=status,
            observed=len(redundant_items),
            limit=0,
            margin=0.0 if status == RuleStatus.PASS else -float(len(redundant_items)),
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

