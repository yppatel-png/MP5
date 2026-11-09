"""Source-aware Bhilai checks with explicit provenance for every result."""

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.db.seed_profile import get_seed_dir
from backend.rules.base import (
    Rule,
    RuleCategory,
    RuleResult,
    RuleScope,
    RuleStatus,
)

SEED_DIR = get_seed_dir()


def load_seed(name: str) -> list[dict[str, Any]]:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def result(
    rule_id: str,
    title: str,
    category: RuleCategory,
    scope: RuleScope,
    scope_ref: str,
    status: RuleStatus,
    observed: Any,
    limit: Any,
    message: str,
    provenance: str,
    source_page: int | None = None,
    reason: str | None = None,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_title=title,
        category=category,
        scope=scope,
        scope_ref=scope_ref,
        status=status,
        observed=observed,
        limit=limit,
        message=message,
        clause_id=f"PDF p. {source_page}" if source_page else "pending ordinance",
        section_title="Verified source fact" if provenance == "verified" else "Demo assumption",
        source_url="",
        provenance=provenance,
        reason=reason,
        source_page=source_page,
    )


class BhilaiCatalogueRule(Rule):
    id = "rule_course_catalogue_exists"
    title = "Course catalogue identity"
    category = RuleCategory.EXISTENCE
    scope = RuleScope.COURSE

    def __init__(self) -> None:
        self.courses = {course["code"]: course for course in load_seed("courses.json")}

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        output = []
        for semester in plan.get("semesters", []):
            for course in semester.get("courses", []):
                code = course.get("code", "")
                exists = code in self.courses
                metadata = self.courses.get(code, {})
                output.append(result(
                    self.id,
                    self.title,
                    self.category,
                    self.scope,
                    f"course:{code}",
                    RuleStatus.PASS if exists else RuleStatus.FAIL,
                    code,
                    "A course code in the source-backed catalogue",
                    f"{code} is matched in the Bhilai demo catalogue." if exists else f"{code} is not in the Bhilai catalogue.",
                    metadata.get("provenance", "verified"),
                    metadata.get("source_page"),
                ))
        if not output:
            output.append(result(
                self.id, self.title, self.category, RuleScope.PLAN, "plan:courses",
                RuleStatus.WARN, 0, "One or more catalogued courses",
                "No course was recommended; the curriculum catalog remains available.",
                "verified", 21,
            ))
        return output


class BhilaiPrerequisiteRule(Rule):
    id = "rule_prereq_strict_enforcement"
    title = "Printed prerequisite sequence"
    category = RuleCategory.PREREQUISITES
    scope = RuleScope.PLAN

    def __init__(self) -> None:
        self.prerequisites = load_seed("prerequisites.json")

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        completed = {}
        for item in ctx.get("completed_courses", []):
            if isinstance(item, dict):
                completed[str(item.get("course_code", "")).upper()] = str(item.get("grade") or "B").upper()
            else:
                completed[str(item).upper()] = "B"
        course_semesters = {
            str(course.get("code", "")).upper(): int(semester.get("semester_number", 0))
            for semester in plan.get("semesters", [])
            for course in semester.get("courses", [])
        }
        issues = []
        checked = 0
        for prerequisite in self.prerequisites:
            course = prerequisite["course_code"].upper()
            required = prerequisite["requires_code"].upper()
            if course not in course_semesters:
                continue
            checked += 1
            required_semester = course_semesters.get(required)
            grade = completed.get(required)
            if grade and grade != "F":
                continue
            if required_semester is not None and required_semester < course_semesters[course]:
                continue
            issues.append(f"{course} requires prior completion of {required}.")
        status = RuleStatus.FAIL if issues else RuleStatus.PASS
        return [result(
            self.id, self.title, self.category, self.scope, "plan:prerequisites",
            status, issues or f"{checked} source-listed prerequisite(s) checked",
            "All printed prerequisites passed before course registration",
            "; ".join(issues) if issues else "All printed prerequisite references are satisfied in an earlier semester or completed-course history.",
            "verified", 11,
        )]


class BhilaiAssumptionRules(Rule):
    id = "rule_bhilai_demo_assumptions"
    title = "Assumption-backed planning checks"
    category = RuleCategory.PREFERENCE
    scope = RuleScope.PLAN

    def __init__(self) -> None:
        self.rules = {rule["rule_id"]: rule for rule in load_seed("academic_rules.json")}
        self.programme = load_seed("programmes.json")[0]
        self.courses = {course["code"]: course for course in load_seed("courses.json")}

    def _rule(self, rule_id: str) -> dict[str, Any]:
        return self.rules[rule_id]

    def check(self, plan: Dict[str, Any], ctx: Dict[str, Any]) -> List[RuleResult]:
        checks: List[RuleResult] = []
        planned_semesters = plan.get("semesters", [])
        credits_rule = self._rule("rule_sem_min_credits")
        minimum = float(credits_rule["parameters"]["min_credits"])
        cap_rule = self._rule("rule_sem_max_credits")
        standard_cap = float(cap_rule["parameters"]["max_credits"])
        overload_rule = self._rule("rule_credit_overload_cap")
        overload_cap = float(overload_rule["parameters"]["max_overload_credits"])
        overload_cgpa = float(overload_rule["parameters"]["min_cgpa_required"])
        cgpa = float(ctx.get("cgpa", 0))
        selected_cap = overload_cap if cgpa >= overload_cgpa else standard_cap

        for semester in planned_semesters:
            number = int(semester.get("semester_number", 0))
            credits = float(semester.get("total_credits", 0))
            if not semester.get("courses"):
                status = RuleStatus.NOT_APPLICABLE
                message = f"Semester {number} has no selected courses; the assumed minimum is not evaluated."
            elif credits < minimum:
                status = RuleStatus.WARN
                message = f"Semester {number} has {credits:g} credits, below the assumed recommended {minimum:g}-credit floor."
            else:
                status = RuleStatus.PASS
                message = f"Semester {number} meets the assumed {minimum:g}-credit floor."
            checks.append(result(
                credits_rule["rule_id"], credits_rule["name"], RuleCategory.CREDITS,
                RuleScope.SEMESTER, f"semester:{number}", status, credits, minimum,
                message, "assumption", reason=credits_rule["reason"],
            ))
            checks.append(result(
                cap_rule["rule_id"], cap_rule["name"], RuleCategory.CREDITS,
                RuleScope.SEMESTER, f"semester:{number}",
                RuleStatus.PASS if credits <= selected_cap else RuleStatus.FAIL,
                credits, selected_cap,
                f"Semester {number} is within the assumed {selected_cap:g}-credit cap."
                if credits <= selected_cap else f"Semester {number} exceeds the assumed {selected_cap:g}-credit cap.",
                "assumption", reason=cap_rule["reason"] + " " + overload_rule["reason"],
            ))

            workload_hours = sum(
                float(course.get("credits", 0))
                * float(self._rule("rule_workload_hours")["parameters"]["hours_per_credit_week"])
                for course in semester.get("courses", [])
            )
            available = float(ctx.get("available_hours_per_week", 0))
            workload_rule = self._rule("rule_workload_hours")
            workload_status = RuleStatus.WARN if workload_hours > available else RuleStatus.PASS
            checks.append(result(
                workload_rule["rule_id"], workload_rule["name"], RuleCategory.TIME,
                RuleScope.SEMESTER, f"semester:{number}", workload_status,
                workload_hours, available,
                f"Estimated course workload is {workload_hours:g} hours/week against {available:g} available."
                + (" Review this estimate." if workload_status == RuleStatus.WARN else ""),
                "assumption", reason=workload_rule["reason"],
            ))

        schedule_rule = self._rule("rule_semester_parity")
        for semester in planned_semesters:
            number = int(semester.get("semester_number", 0))
            is_odd = (number % 2 == 1)
            for course in semester.get("courses", []):
                metadata = self.courses.get(course.get("code", ""), {})
                slot = metadata.get("semester_offered", "catalogue_unscheduled")
                if slot in ("catalogue_unscheduled", "both", "all", "") or not slot:
                    matches = True
                elif slot == "odd":
                    matches = is_odd
                elif slot == "even":
                    matches = not is_odd
                elif slot.startswith("semester_"):
                    try:
                        source_sem = int(slot.split("_")[1])
                        matches = (source_sem % 2 == 1) == is_odd
                    except (ValueError, IndexError):
                        matches = (slot == f"semester_{number}")
                else:
                    matches = (slot == f"semester_{number}")

                checks.append(result(
                    schedule_rule["rule_id"], schedule_rule["name"], RuleCategory.OFFERING,
                    RuleScope.COURSE, f"course:{course.get('code')}", RuleStatus.PASS if matches else RuleStatus.FAIL,
                    number, slot,
                    f"{course.get('code')} uses the assumed catalogue availability."
                    if slot in ("catalogue_unscheduled", "both", "all") and matches else
                    f"{course.get('code')} aligns with annual offering schedule (source: {slot}, scheduled: semester {number})."
                    if matches else f"{course.get('code')} is listed for {slot}, not semester {number}.",
                    "assumption", reason=schedule_rule["reason"],
                ))

        minor_rule = self._rule("rule_minor_cse_eligibility")
        minor_parameters = minor_rule["parameters"]
        checks.append(result(
            minor_rule["rule_id"], minor_rule["name"], RuleCategory.ELIGIBILITY,
            RuleScope.PLAN, "plan:minor", RuleStatus.WARN, cgpa,
            minor_parameters["min_cgpa_cutoff"],
            "Illustrative CGPA threshold only. The PDF has no CS-minor pathway, so no minor eligibility or credential is certified.",
            "assumption", reason=minor_rule["reason"],
        ))

        online_rule = self._rule("rule_online_credit_transfer_limit")
        online_credits = sum(
            float(course.get("credits", 0))
            for semester in planned_semesters
            for course in semester.get("courses", [])
            if self.courses.get(course.get("code", ""), {}).get("mode") == "online"
        )
        online_cap = float(online_rule["parameters"]["max_online_credits_total"])
        checks.append(result(
            online_rule["rule_id"], online_rule["name"], RuleCategory.ELIGIBILITY,
            RuleScope.PLAN, "plan:online-credits",
            RuleStatus.PASS if online_credits <= online_cap else RuleStatus.FAIL,
            online_credits, online_cap,
            f"{online_credits:g} online credits against the assumed {online_cap:g}-credit cap.",
            "assumption", reason=online_rule["reason"],
        ))

        completed = ctx.get("completed_courses", [])
        completed_credits = sum(
            float(self.courses.get(
                item.get("course_code", "") if isinstance(item, dict) else str(item), {}
            ).get("credits", 0))
            for item in completed
        )
        planned_credits = sum(float(semester.get("total_credits", 0)) for semester in planned_semesters)
        total_credits = completed_credits + planned_credits
        degree_target = float(self.programme["total_credits"])
        checks.append(result(
            "rule_degree_total_credits", "BTech CSE graded-credit structure",
            RuleCategory.CREDITS, RuleScope.PLAN, "plan:degree-credits",
            RuleStatus.PASS if total_credits >= degree_target else RuleStatus.WARN,
            total_credits, degree_target,
            f"Known completed plus planned credits: {total_credits:g} of {degree_target:g}. This is progress context, not graduation certification.",
            "verified", source_page=21,
        ))
        return checks


class BhilaiNoDuplicateRule(Rule):
    id = "rule_no_duplicate_courses"
    title = "Zero Duplicate Course Registrations"
    category = RuleCategory.REDUNDANCY
    scope = RuleScope.PLAN

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
                if not code:
                    continue
                if code in completed_past:
                    duplicates.append(f"{code} (Semester {s_num}) was already completed with a passing grade in prior terms.")
                if code in seen_in_plan:
                    duplicates.append(f"{code} is scheduled multiple times in the academic plan.")
                seen_in_plan.add(code)

        status = RuleStatus.FAIL if duplicates else RuleStatus.PASS
        msg = f"Zero course duplication verified across {len(seen_in_plan)} planned courses." if not duplicates else f"Duplication violation: {'; '.join(duplicates)}"

        return [result(
            self.id, self.title, self.category, self.scope, "plan:duplication",
            status, len(duplicates), 0,
            msg, "assumption", reason="Students cannot re-register for courses already passed or duplicate in a single plan. Assumed, pending ordinance.",
        )]


def build_bhilai_rules() -> list[Rule]:
    return [BhilaiCatalogueRule(), BhilaiPrerequisiteRule(), BhilaiAssumptionRules(), BhilaiNoDuplicateRule()]
