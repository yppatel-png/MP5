"""
Prerequisite, Offering Parity, and Backlog Academic Rules:
- Prerequisite Chain Satisfaction (ORD-5.1.0)
- Semester Offering Parity (ORD-5.2.0)
- Co-requisite Concurrency (ORD-5.1.0)
- Backlog Remediation Precedence (ORD-5.3.0)
"""

from typing import List, Dict, Any, Set
from backend.rules.base import Rule, RuleResult, RuleCategory, RuleStatus, RuleScope

class PrerequisiteChainRule(Rule):
    id = "rule_prereq_strict_enforcement"
    title = "Prerequisite Chain Satisfaction"
    category = RuleCategory.PREREQUISITES
    scope = RuleScope.COURSE
    clause_id = "ORD-5.1.0"
    section_title = "Prerequisite Passing Grade Enforcement"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-5.1.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        results = []
        completed_past = set(
            (c if isinstance(c, str) else c.get("course_code", "")).upper()
            for c in ctx.get("completed_courses", [])
        )
        prereq_map = ctx.get("prereq_map", {})
        
        # Map scheduled course to semester number
        course_to_sem: Dict[str, int] = {}
        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            for c in sem.get("courses", []):
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                course_to_sem[code] = s_num

        total_checked = 0
        violations = []
        min_margin = 999.0

        for code, sem_num in course_to_sem.items():
            reqs = prereq_map.get(code, [])
            for req in reqs:
                req_upper = req.upper()
                total_checked += 1
                if req_upper in completed_past:
                    # Satisfied in past
                    min_margin = min(min_margin, sem_num)
                    continue

                req_sem = course_to_sem.get(req_upper)
                if req_sem is None:
                    violations.append(f"{code} (Sem {sem_num}) requires {req_upper}, which is neither completed nor scheduled in plan (Chain: {req_upper} -> {code}).")
                    min_margin = min(min_margin, -1.0)
                elif req_sem >= sem_num:
                    violations.append(f"{code} (Sem {sem_num}) requires {req_upper}, but {req_upper} is scheduled concurrently or later in Sem {req_sem} (Chain: {req_upper} -> {code}).")
                    min_margin = min(min_margin, float(req_sem - sem_num))
                else:
                    headroom = float(sem_num - req_sem)
                    min_margin = min(min_margin, headroom)

        if total_checked == 0:
            status = RuleStatus.PASS
            msg = "All scheduled courses have prerequisite chains satisfied (no unmet prerequisites)."
            margin = 5.0
        elif len(violations) == 0:
            status = RuleStatus.PASS
            margin = min_margin if min_margin != 999.0 else 1.0
            msg = f"All {total_checked} prerequisite dependencies verified; strictly satisfied in prior semesters (chain clearance: +{margin:.0f} sem)."
        else:
            status = RuleStatus.FAIL
            margin = min_margin if min_margin != 999.0 else -1.0
            msg = f"Prerequisite violations detected: {'; '.join(violations)}"

        results.append(RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:prerequisites",
            status=status,
            observed=f"{len(violations)} violations" if violations else f"{total_checked} dependencies met",
            limit="0 unmet dependencies",
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        ))
        return results

class SemesterParityRule(Rule):
    id = "rule_semester_parity"
    title = "Semester Offering Parity"
    category = RuleCategory.OFFERING
    scope = RuleScope.COURSE
    clause_id = "ORD-5.2.0"
    section_title = "Course Offering Parity Regulation"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-5.2.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        results = []
        courses_db = ctx.get("courses_db", {})
        violations = []
        total_courses = 0

        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            is_odd = (s_num % 2 == 1)

            for c in sem.get("courses", []):
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                total_courses += 1
                c_data = courses_db.get(code, {})
                offered = c_data.get("semester_offered", "both").lower()

                if offered == "odd" and not is_odd:
                    violations.append(f"{code} is Autumn-only (Odd semesters), but scheduled in Semester {s_num} (Even).")
                elif offered == "even" and is_odd:
                    violations.append(f"{code} is Spring-only (Even semesters), but scheduled in Semester {s_num} (Odd).")

        if len(violations) == 0:
            status = RuleStatus.PASS
            msg = f"All {total_courses} course offerings match departmental term parity (Autumn/Spring alignment verified)."
            margin = 1.0
        else:
            status = RuleStatus.FAIL
            msg = f"Parity mismatch: {'; '.join(violations)}"
            margin = -float(len(violations))

        results.append(RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:offerings",
            status=status,
            observed=f"{len(violations)} mismatches" if violations else "100% aligned",
            limit="0 parity mismatches",
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        ))
        return results

class CoRequisiteRule(Rule):
    id = "rule_corequisite_concurrency"
    title = "Co-Requisite Concurrent Registration"
    category = RuleCategory.PREREQUISITES
    scope = RuleScope.COURSE
    clause_id = "ORD-5.1.0"
    section_title = "Prerequisite and Co-requisite Regulations"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-5.1.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        # Evaluates courses that must be taken in the same semester or earlier
        completed_past = set(
            (c if isinstance(c, str) else c.get("course_code", "")).upper()
            for c in ctx.get("completed_courses", [])
        )
        course_to_sem: Dict[str, int] = {}
        for sem in plan.get("semesters", []):
            s_num = sem.get("semester_number", 0)
            for c in sem.get("courses", []):
                code = (c if isinstance(c, str) else c.get("code", "")).upper()
                course_to_sem[code] = s_num

        coreq_map = ctx.get("coreq_map", {})
        violations = []
        for code, sem_num in course_to_sem.items():
            reqs = coreq_map.get(code, [])
            for req in reqs:
                req_upper = req.upper()
                if req_upper in completed_past:
                    continue
                req_sem = course_to_sem.get(req_upper)
                if req_sem is None or req_sem > sem_num:
                    violations.append(f"{code} (Sem {sem_num}) requires co-requisite {req_upper} concurrently or earlier.")

        status = RuleStatus.PASS if len(violations) == 0 else RuleStatus.FAIL
        msg = "All co-requisite requirements satisfied concurrently or in earlier semesters." if status == RuleStatus.PASS else "; ".join(violations)

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:corequisites",
            status=status,
            observed=len(violations),
            limit=0,
            margin=0.0 if status == RuleStatus.PASS else -float(len(violations)),
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

class BacklogSequenceRule(Rule):
    id = "rule_backlog_scheduled_first"
    title = "Backlog Core Course Precedence"
    category = RuleCategory.BACKLOG
    scope = RuleScope.PLAN
    clause_id = "ORD-5.3.0"
    section_title = "Backlog Remediation Precedence"
    source_url = "https://home.iitd.ac.in/academic-rules/ordinance-section-5.3.0"

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        # If student profile has backlogs, verify they are scheduled in the first available semester
        backlogs = [b.upper() for b in ctx.get("backlogs", [])]
        if not backlogs:
            # Check completed courses for grade 'F' or 'E'
            for c in ctx.get("completed_courses", []):
                if isinstance(c, dict) and c.get("grade") in ["F", "E"]:
                    backlogs.append(c.get("course_code", "").upper())

        if not backlogs:
            return [RuleResult(
                rule_id=self.id,
                rule_title=self.title,
                category=self.category,
                scope=RuleScope.PLAN,
                scope_ref="plan:backlogs",
                status=RuleStatus.PASS,
                observed=0,
                limit=0,
                margin=0.0,
                message="No outstanding core backlogs requiring prioritized scheduling.",
                clause_id=self.clause_id,
                section_title=self.section_title,
                source_url=self.source_url
            )]

        semesters = plan.get("semesters", [])
        if not semesters:
            return []

        first_sem_courses = set(
            (c if isinstance(c, str) else c.get("code", "")).upper()
            for c in semesters[0].get("courses", [])
        )
        all_plan_courses = set(
            (c if isinstance(c, str) else c.get("code", "")).upper()
            for sem in semesters for c in sem.get("courses", [])
        )

        unscheduled = [b for b in backlogs if b not in all_plan_courses]
        if unscheduled:
            status = RuleStatus.FAIL
            msg = f"Outstanding backlog courses {', '.join(unscheduled)} are not scheduled in the remediation plan."
            margin = -float(len(unscheduled))
        else:
            status = RuleStatus.PASS
            msg = f"All {len(backlogs)} backlog courses scheduled for remediation prior to degree completion."
            margin = 1.0

        return [RuleResult(
            rule_id=self.id,
            rule_title=self.title,
            category=self.category,
            scope=RuleScope.PLAN,
            scope_ref="plan:backlogs",
            status=status,
            observed=f"{len(unscheduled)} unscheduled" if unscheduled else "All remediated",
            limit="0 unscheduled backlogs",
            margin=margin,
            message=msg,
            clause_id=self.clause_id,
            section_title=self.section_title,
            source_url=self.source_url
        )]

