"""
Multi-Semester Academic Constraint Planner.
Implements deterministic greedy scheduler + independent validator respecting:
- Prerequisite DAG ordering (prereqs in strictly earlier semesters)
- Semester offering parity (Odd / Even / Both)
- Credit minimums and maximum caps per semester
- Minor degree eligibility & elective slot headroom
- Mutually exclusive "no-co-taking" course pairs
- Weekly time budgeting
- Grounded in IIT Bhilai BTech CSE official curriculum structure
"""

import json
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict

from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_seed_dir, get_institute_profile
from backend.planner.candidate import candidate_retriever
from backend.rules.params import (
    get_standard_credit_cap,
    get_min_semester_credits,
    get_overload_credit_cap,
    get_overload_cgpa_threshold,
    get_minor_cgpa_cutoff,
    get_workload_hours_ratio,
)

SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def check_offering_parity(offering: str, sem_num: int) -> bool:
    """Verifies whether a course offering aligns with semester odd/even schedule."""
    if not offering:
        return True
    off = offering.lower().strip()
    is_odd = (sem_num % 2 == 1)
    if off in ("both", "catalogue_unscheduled", "all", ""):
        return True
    if off == "odd":
        return is_odd
    if off == "even":
        return not is_odd
    if off.startswith("semester_"):
        try:
            target_sem = int(off.split("_")[1])
            return (target_sem % 2 == 1) == is_odd
        except (ValueError, IndexError):
            return True
    return True


def has_no_co_clash(code: str, scheduled_codes: List[str], no_co_pairs: List[List[str]]) -> bool:
    """Verifies that scheduling code does not violate mutually exclusive co-taking pairs."""
    c_up = code.upper()
    sched_set = {c.upper() for c in scheduled_codes}
    for pair in no_co_pairs:
        if len(pair) >= 2:
            p0, p1 = pair[0].upper(), pair[1].upper()
            if c_up == p0 and p1 in sched_set:
                return True
            if c_up == p1 and p0 in sched_set:
                return True
    return False


def check_prereqs_met(code: str, prereq_map: Dict[str, List[str]], scheduled_so_far: Set[str]) -> Tuple[bool, List[str]]:
    """Checks whether all hard prerequisite courses have been completed strictly prior."""
    reqs = prereq_map.get(code, [])
    unmet = [r for r in reqs if r.upper() not in scheduled_so_far]
    return len(unmet) == 0, unmet


def is_workload_sustainable(sem_workload: float, course_workload: float, max_weekly_hours: Optional[float]) -> bool:
    """Evaluates whether adding course_workload keeps semester weekly hours realistic."""
    new_workload = sem_workload + course_workload
    if new_workload > 48.0:
        return False
    if max_weekly_hours is not None:
        est_self_study = new_workload * 0.35
        if max_weekly_hours <= 8.0 and est_self_study > max_weekly_hours:
            return False
        if est_self_study > max_weekly_hours * 2.0 and est_self_study > get_standard_credit_cap():
            return False
    return True


class MultiSemesterPlanner:
    def __init__(self):
        self.courses = {c["code"]: c for c in load_seed_json("courses.json")}
        self.prereqs = load_seed_json("prerequisites.json")
        self.academic_rules = {r["rule_id"]: r for r in load_seed_json("academic_rules.json")}
        self.goal_templates = {g["goal_id"]: g for g in load_seed_json("goal_templates.json")}
        
        # Build prerequisite map: course_code -> list of required course_codes
        self.prereq_map: Dict[str, List[str]] = {}
        for p in self.prereqs:
            self.prereq_map.setdefault(p["course_code"], []).append(p["requires_code"])

        # Load official IIT Bhilai BTech CSE curriculum structure
        try:
            curricula = load_seed_json("iit_bhilai_cse_curricula.json")
            btech = next(p for p in curricula.get("programmes", []) if p.get("id") == "iit_bhilai_btech_cse_2023")
            self.semester_templates = {s["semester"]: s for s in btech.get("semesters", [])}
        except Exception:
            self.semester_templates = {}

    def plan_curriculum(
        self,
        student_id: Any,
        programme_code: Optional[str] = None,
        current_semester: Optional[int] = None,
        cgpa: Optional[float] = None,
        completed_courses: Optional[List[str]] = None,
        skill_gaps: Optional[List[Dict[str, Any]]] = None,
        goal_id: str = "goal_software",
        credit_cap: Optional[float] = None,
        min_credits: Optional[float] = None,
        max_weekly_hours: Optional[float] = None,
        no_co_taking_pairs: Optional[List[List[str]]] = None,
        overload_allowed: bool = False,
        excluded_courses: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        skill_matrix: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Multi-semester curriculum solver supporting both parameter list and StudentProfile object.
        Synthesizes a multi-semester academic schedule grounded in the official curriculum.
        Guarantees validity by combining a deterministic constraint scheduler with an independent validator.
        """
        if hasattr(student_id, "student_id") and hasattr(student_id, "current_semester"):
            profile = student_id
            raw_completed = profile.completed_courses or []
            comp_codes = [c.course_code if hasattr(c, "course_code") else str(c) for c in raw_completed]
            return self.plan_curriculum(
                student_id=profile.student_id,
                programme_code=getattr(profile, "programme", "iit_bhilai_btech_cse_2023"),
                current_semester=profile.current_semester,
                cgpa=profile.cgpa,
                completed_courses=comp_codes,
                skill_gaps=skill_gaps or [],
                goal_id=getattr(profile, "goal_id", "goal_software"),
                credit_cap=credit_cap,
                min_credits=min_credits,
                max_weekly_hours=getattr(profile, "available_hours_per_week", None),
                no_co_taking_pairs=no_co_taking_pairs,
                overload_allowed=overload_allowed,
                excluded_courses=excluded_courses,
                interests=getattr(profile, "interests", None),
                skill_matrix=skill_matrix,
                preferences=getattr(profile, "preferences", None)
            )

        programme_code = programme_code or "iit_bhilai_btech_cse_2023"
        current_semester = current_semester if current_semester is not None else 1
        cgpa = cgpa if cgpa is not None else 8.0
        completed_courses = completed_courses or []
        skill_gaps = skill_gaps or []

        if credit_cap is None:
            credit_cap = get_standard_credit_cap()
        if min_credits is None:
            min_credits = get_min_semester_credits()

        completed_set = set(c.upper() for c in completed_courses)
        excluded_set = set(c.upper() for c in (excluded_courses or []))
        start_sem = current_semester + 1
        end_sem = 8
        semesters_to_plan = list(range(start_sem, end_sem + 1))

        if not semesters_to_plan:
            semesters_to_plan = [current_semester]

        # Retrieve candidates covering skill gaps with mastered drops and interest weighting
        candidates = candidate_retriever.retrieve_candidates_for_gaps(
            skill_gaps=skill_gaps,
            completed_course_codes=completed_set,
            programme_code=programme_code,
            cgpa=cgpa,
            skill_matrix=skill_matrix,
            interests=interests
        )

        # Filter out student-excluded courses (override constraint)
        if excluded_set:
            candidates = [c for c in candidates if c["code"].upper() not in excluded_set]

        # Check Minor eligibility if non-CS student taking CSE courses
        minor_threshold = get_minor_cgpa_cutoff()
        is_minor_eligible = cgpa >= minor_threshold

        # Format no-co-taking pairs
        all_no_co_pairs = []
        if no_co_taking_pairs:
            all_no_co_pairs.extend(no_co_taking_pairs)

        # Effective semester credit cap
        overload_threshold = get_overload_cgpa_threshold()
        overload_limit = get_overload_credit_cap()
        effective_cap = overload_limit if (overload_allowed and cgpa >= overload_threshold) else credit_cap

        # Solve using Deterministic Greedy Constraint Scheduler with Deferred Core Rescheduling
        plan_result, engine_used, unscheduled_required, infeasible_reasons = self._solve_topological(
            current_semester=current_semester,
            semesters=semesters_to_plan,
            candidates=candidates,
            completed_set=completed_set,
            credit_cap=effective_cap,
            min_credits=min_credits,
            max_weekly_hours=max_weekly_hours,
            no_co_pairs=all_no_co_pairs,
            is_minor_eligible=is_minor_eligible,
            goal_id=goal_id,
            excluded_set=excluded_set
        )

        # Fill non-credit layers: relevance-based resources & forward-carried milestones (P1-3)
        all_resources = candidate_retriever.resources
        used_resource_ids = set()
        preferred_format = str((preferences or {}).get("preferred_format", "")).lower()

        for idx, sem_obj in enumerate(plan_result):
            sem_courses = sem_obj.get("courses", [])
            sem_skills = set(sk for c in sem_courses for sk in c.get("skills_targeted", []))
            top_gap_skills = set(g["skill_id"] for g in skill_gaps[:3])
            target_skills = sem_skills or top_gap_skills

            sem_res = []
            for r in all_resources:
                if len(sem_res) >= 2:
                    break
                r_id = r["resource_id"]
                if r_id in used_resource_ids:
                    continue
                if r.get("status") == "needs_verification" or not r.get("license_verified", True):
                    continue
                common_skills = set(r.get("skill_ids", [])).intersection(target_skills)
                if common_skills:
                    common_list = sorted(list(common_skills))
                    sk_label = common_list[0].replace("_", " ").title()
                    why = f"Reinforces critical capability in {sk_label} targeted in Semester {sem_obj['semester_number']}."
                    r_format = str(r.get("format", "")).lower()
                    if preferred_format and preferred_format in r_format:
                        why += f" Aligns with your preferred {preferred_format} learning style."

                    sem_res.append({
                        "resource_id": r["resource_id"],
                        "title": r["title"],
                        "provider": r["provider"],
                        "url": r["url"],
                        "format": r["format"],
                        "est_minutes": r["est_minutes"],
                        "credit_eligible": bool(r.get("credit_eligible")),
                        "skills_covered": common_list,
                        "why_this_resource": why
                    })
                    used_resource_ids.add(r_id)
            sem_obj["resources"] = sem_res

        # Forward-carried milestones: semester_offset <= idx+1, carrying forward unattached
        goal_meta = self.goal_templates.get(goal_id, self.goal_templates.get("goal_software", {}))
        milestones = goal_meta.get("milestones", [])
        pending_milestones = list(milestones)
        for idx, sem_obj in enumerate(plan_result):
            current_offset = idx + 1
            is_last = (idx == len(plan_result) - 1)
            if is_last:
                sem_obj["milestones"] = list(pending_milestones)
                pending_milestones = []
            else:
                sem_milestones = [m for m in pending_milestones if m.get("semester_offset", 1) <= current_offset]
                sem_obj["milestones"] = sem_milestones
                assigned_ids = {m["milestone_id"] for m in sem_milestones}
                pending_milestones = [m for m in pending_milestones if m["milestone_id"] not in assigned_ids]

        total_credits = sum(s["total_credits"] for s in plan_result)
        skills_covered = list(set(
            sk for s in plan_result for c in s["courses"] for sk in c.get("skills_targeted", [])
        ))

        # Build raw plan for independent verification
        raw_plan = {
            "student_id": student_id,
            "goal_id": goal_id,
            "total_credits_planned": round(total_credits, 1),
            "semesters": plan_result
        }

        # Validate with independent validator
        from backend.planner.validator import independent_validator
        profile_dict = {
            "student_id": student_id,
            "programme": programme_code,
            "current_semester": current_semester,
            "cgpa": cgpa,
            "completed_courses": [{"course_code": c} for c in completed_courses],
            "available_hours_per_week": max_weekly_hours if max_weekly_hours else 12.0
        }
        validation = independent_validator.validate_plan(raw_plan, profile_dict)

        # Determine feasibility status
        if unscheduled_required or not validation.get("is_valid"):
            status = "infeasible"
            all_reasons = list(infeasible_reasons)
            for err in validation.get("errors", []):
                if err not in all_reasons:
                    all_reasons.append(err)
        else:
            status = "feasible"
            all_reasons = []

        return {
            "status": status,
            "student_id": student_id,
            "goal_id": goal_id,
            "solver_engine": "deterministic greedy scheduler + independent validator",
            "total_credits_planned": round(total_credits, 1),
            "semesters_planned_count": len(plan_result),
            "skills_covered": skills_covered,
            "semesters": plan_result,
            "validation": validation,
            "unscheduled_required": [item["code"] for item in unscheduled_required],
            "infeasible_reasons": all_reasons
        }

    def _solve_topological(
        self,
        current_semester: int,
        semesters: List[int],
        candidates: List[Dict[str, Any]],
        completed_set: Set[str],
        credit_cap: float,
        min_credits: float,
        max_weekly_hours: Optional[float],
        no_co_pairs: List[List[str]],
        is_minor_eligible: bool,
        goal_id: str = "goal_software",
        excluded_set: Optional[Set[str]] = None
    ) -> Tuple[List[Dict[str, Any]], str, List[Dict[str, Any]], List[str]]:
        """
        Deterministic, curriculum-aware constraint scheduler with deferred core rescheduling.
        Schedules:
        1. Mandatory Programme Core courses per official syllabus (including past backlogs and deferred core).
        2. Goal-aligned Liberal Arts electives.
        3. Goal-aligned and gap-targeted Programme Electives (CSL5xx).
        Evaluates prerequisite DAGs, semester offering parity, and credit/hour bounds.
        """
        scheduled_so_far = set(completed_set)
        semester_plans = []
        already_scheduled_codes = set()
        workload_ratio = get_workload_hours_ratio()

        # Build candidate lookup for reasons and targeted skills
        candidate_map = {c["code"]: c for c in candidates}
        goal_tmpl = self.goal_templates.get(goal_id, self.goal_templates.get("goal_software", {}))
        elec_order = [item["code"] for item in goal_tmpl.get("preferred_electives", [])]
        la_order = [(item["code"], item.get("reason", "Liberal Arts requirement.")) for item in goal_tmpl.get("preferred_liberal_arts", [])]
        la_pointer = 0

        # Calculate initial completed credits
        completed_credits = sum(float(self.courses.get(c, {}).get("credits", 0.0)) for c in completed_set)
        running_credits = completed_credits

        # Initialize deferred_core queue with uncompleted core courses from past semesters (backlogs)
        deferred_core: List[Dict[str, Any]] = []
        for s in range(1, current_semester + 1):
            s_template = self.semester_templates.get(s, {})
            for c_entry in s_template.get("courses", []):
                code = c_entry.get("code")
                if not code or c_entry.get("placeholder"):
                    continue
                code_up = code.upper()
                if code_up not in completed_set and (not excluded_set or code_up not in excluded_set):
                    if code in self.courses:
                        c_meta = self.courses[code]
                        c_type = (c_meta.get("type") or c_meta.get("course_type") or "").lower()
                        if c_type in ["core", "institute_core", "program_linked", "programme_core"]:
                            deferred_core.append({
                                "code": code,
                                "original_semester": s,
                                "is_backlog": True
                            })

        for sem in semesters:
            is_odd = (sem % 2 == 1)
            season = "Odd (Autumn)" if is_odd else "Even (Spring)"
            sem_courses = []
            sem_credits = 0.0
            sem_workload = 0.0
            sem_template = self.semester_templates.get(sem, {})
            typical_cr = float(sem_template.get("stated_credits", 18.0))

            # ------------------------------------------------------------------
            # Phase A: Mandatory Programme Core Courses Scheduled for this Semester + Deferred Core
            # ------------------------------------------------------------------
            current_sem_core: List[Dict[str, Any]] = []
            for c_entry in sem_template.get("courses", []):
                code = c_entry.get("code")
                if not code or c_entry.get("placeholder"):
                    continue
                code_up = code.upper()
                if code_up in scheduled_so_far or code_up in already_scheduled_codes:
                    continue
                if excluded_set and code_up in excluded_set:
                    continue
                if code not in self.courses:
                    continue

                course_meta = self.courses[code]
                c_type = (course_meta.get("type") or course_meta.get("course_type") or "").lower()
                if c_type in ["core", "institute_core", "program_linked", "programme_core"]:
                    current_sem_core.append({
                        "code": code,
                        "original_semester": sem,
                        "is_backlog": False
                    })

            # Core queue: past deferred/backlogs first, then current semester core
            core_queue = deferred_core + current_sem_core
            deferred_core = []

            for core_item in core_queue:
                code = core_item["code"]
                code_up = code.upper()
                if code_up in scheduled_so_far or code_up in already_scheduled_codes:
                    continue

                course_meta = self.courses[code]
                credits = float(course_meta["credits"])
                workload = float(course_meta.get("workload_hours_per_week") or credits * workload_ratio)

                # 1. Check offering parity
                offering = course_meta.get("semester_offered", "catalogue_unscheduled")
                if not check_offering_parity(offering, sem):
                    deferred_core.append(core_item)
                    continue

                # 2. Check hard prerequisites
                prereqs_ok, unmet = check_prereqs_met(code, self.prereq_map, scheduled_so_far)
                if not prereqs_ok:
                    deferred_core.append(core_item)
                    continue

                # 3. Check credit ceiling
                if sem_credits + credits > credit_cap:
                    deferred_core.append(core_item)
                    continue

                # 4. Check max weekly hours
                if not is_workload_sustainable(sem_workload, workload, max_weekly_hours):
                    deferred_core.append(core_item)
                    continue

                # 5. Check no-co-taking pairs
                current_codes = [c["code"] for c in sem_courses]
                if has_no_co_clash(code, current_codes, no_co_pairs):
                    deferred_core.append(core_item)
                    continue

                # Reason grounding
                cand_info = candidate_map.get(code)
                if core_item.get("is_backlog"):
                    reason = f"Backlog requirement from Semester {core_item['original_semester']} (rescheduled to Semester {sem})."
                elif core_item["original_semester"] != sem:
                    reason = f"Deferred core requirement from Semester {core_item['original_semester']} (rescheduled to Semester {sem})."
                elif cand_info and cand_info.get("reasons"):
                    reason = cand_info["reasons"][0]
                else:
                    reason = f"Required in Semester {sem} (Programme Core) per Courses of Study p.21-22."

                skills_targeted = (
                    cand_info["skills_targeted"] if cand_info and cand_info.get("skills_targeted")
                    else course_meta.get("skills_covered", [])
                )

                sem_courses.append({
                    "code": code,
                    "title": course_meta["title"],
                    "credits": credits,
                    "course_type": course_meta.get("course_type", "programme_core"),
                    "type": course_meta.get("type") or "core",
                    "workload_hours_per_week": workload,
                    "skills_targeted": skills_targeted,
                    "reason": reason,
                    "provenance": course_meta.get("provenance", "verified"),
                    "source_page": course_meta.get("source_page", 21),
                    "offering_assumption": False,
                })
                sem_credits += credits
                sem_workload += workload
                already_scheduled_codes.add(code_up)

            # ------------------------------------------------------------------
            # Phase B: Liberal Arts Requirement Slot
            # ------------------------------------------------------------------
            has_la_slot = any(
                c.get("category") == "LA" and c.get("placeholder") 
                for c in sem_template.get("courses", [])
            ) or (sem in (3, 4, 5, 6) and not any(c.get("course_type") == "liberal_arts" for c in sem_courses))

            if has_la_slot:
                while la_pointer < len(la_order):
                    la_code, la_reason = la_order[la_pointer]
                    la_pointer += 1
                    la_up = la_code.upper()
                    if (
                        la_up not in scheduled_so_far
                        and la_up not in already_scheduled_codes
                        and (not excluded_set or la_up not in excluded_set)
                        and la_code in self.courses
                    ):
                        la_meta = self.courses[la_code]
                        la_credits = float(la_meta["credits"])
                        la_workload = float(la_meta.get("workload_hours_per_week") or la_credits * workload_ratio)

                        # Parity check
                        if not check_offering_parity(la_meta.get("semester_offered", ""), sem):
                            continue
                        # Prereq check
                        prereqs_ok, _ = check_prereqs_met(la_code, self.prereq_map, scheduled_so_far)
                        if not prereqs_ok:
                            continue
                        # Credit cap check
                        if sem_credits + la_credits > credit_cap:
                            continue
                        # Hours check
                        if not is_workload_sustainable(sem_workload, la_workload, max_weekly_hours):
                            continue
                        # No-co-taking check
                        current_codes = [c["code"] for c in sem_courses]
                        if has_no_co_clash(la_code, current_codes, no_co_pairs):
                            continue

                        sem_courses.append({
                            "code": la_code,
                            "title": la_meta["title"],
                            "credits": la_credits,
                            "course_type": "liberal_arts",
                            "type": "liberal_arts",
                            "workload_hours_per_week": la_workload,
                            "skills_targeted": la_meta.get("skills_covered", []),
                            "reason": la_reason,
                            "provenance": "team_authored",
                            "source_page": None,
                            "offering_assumption": True,
                        })
                        sem_credits += la_credits
                        sem_workload += la_workload
                        already_scheduled_codes.add(la_up)
                        break

            # ------------------------------------------------------------------
            # Phase C: Gap-Targeted & Goal-Aligned Programme Electives (CSL5xx)
            # ------------------------------------------------------------------
            max_electives_this_sem = 1 if sem == 5 else (2 if sem == 6 else 3)
            electives_added_count = 0

            # Build prioritized elective candidate list: diagnostic gap candidates first, then goal electives
            elective_pool = []
            seen_pool = set()
            for cand in candidates:
                c_code = cand["code"]
                c_up = c_code.upper()
                if c_up not in seen_pool and c_up not in scheduled_so_far and c_up not in already_scheduled_codes:
                    elective_pool.append(c_code)
                    seen_pool.add(c_up)
            for e_code in elec_order:
                e_up = e_code.upper()
                if e_up not in seen_pool and e_up not in scheduled_so_far and e_up not in already_scheduled_codes:
                    elective_pool.append(e_code)
                    seen_pool.add(e_up)

            for code in elective_pool:
                if electives_added_count >= max_electives_this_sem:
                    break
                if sem_credits >= typical_cr or sem_credits >= credit_cap:
                    break
                code_up = code.upper()
                if code_up in scheduled_so_far or code_up in already_scheduled_codes or (excluded_set and code_up in excluded_set):
                    continue
                if code not in self.courses:
                    continue

                course_meta = self.courses[code]
                credits = float(course_meta["credits"])
                workload = float(course_meta.get("workload_hours_per_week") or credits * workload_ratio)

                # Check credit ceiling
                if sem_credits + credits > credit_cap:
                    continue

                # Check max weekly hours
                if not is_workload_sustainable(sem_workload, workload, max_weekly_hours):
                    continue

                # Check offering parity
                offering = course_meta.get("semester_offered", "catalogue_unscheduled")
                if not check_offering_parity(offering, sem):
                    continue

                # Check hard prerequisites
                prereqs_ok, _ = check_prereqs_met(code, self.prereq_map, scheduled_so_far)
                if not prereqs_ok:
                    continue

                # Check Minor eligibility
                if course_meta.get("department") == "Computer Science and Engineering" and not is_minor_eligible:
                    if course_meta.get("course_type") in ["elective", "minor"]:
                        continue

                # Check no-co-taking pairs
                current_codes = [c["code"] for c in sem_courses]
                if has_no_co_clash(code, current_codes, no_co_pairs):
                    continue

                # Reason grounding
                cand_info = candidate_map.get(code)
                reason = (
                    cand_info["reasons"][0] if cand_info and cand_info.get("reasons")
                    else next((item["reason"] for item in goal_tmpl.get("preferred_electives", []) if item["code"] == code),
                              f"Programme elective ({credits:g} cr): recommended for your goal to build specialized CS capabilities.")
                )
                skills_targeted = (
                    cand_info["skills_targeted"] if cand_info and cand_info.get("skills_targeted")
                    else course_meta.get("skills_covered", [])
                )

                raw_type = course_meta.get("course_type") or course_meta.get("type") or "programme_elective"
                norm_type = "open_elective" if raw_type == "open_elective" else "programme_elective"
                sem_courses.append({
                    "code": code,
                    "title": course_meta["title"],
                    "credits": credits,
                    "course_type": raw_type,
                    "type": norm_type,
                    "workload_hours_per_week": workload,
                    "skills_targeted": skills_targeted,
                    "reason": reason,
                    "provenance": course_meta.get("provenance", "team_authored"),
                    "source_page": course_meta.get("source_page") if course_meta.get("provenance") == "verified" else None,
                    "offering_assumption": offering == "catalogue_unscheduled",
                })
                sem_credits += credits
                sem_workload += workload
                already_scheduled_codes.add(code_up)
                electives_added_count += 1

            # ------------------------------------------------------------------
            # Phase D: Enforce Minimum Credit Floor (min_credits)
            # ------------------------------------------------------------------
            if sem_credits < min_credits:
                # Try adding more electives from pool to satisfy minimum credit floor
                for code in elective_pool:
                    if sem_credits >= min_credits or sem_credits >= credit_cap:
                        break
                    code_up = code.upper()
                    if code_up in scheduled_so_far or code_up in already_scheduled_codes or (excluded_set and code_up in excluded_set):
                        continue
                    if code not in self.courses:
                        continue

                    course_meta = self.courses[code]
                    credits = float(course_meta["credits"])
                    workload = float(course_meta.get("workload_hours_per_week") or credits * workload_ratio)

                    if sem_credits + credits > credit_cap:
                        continue
                    if not is_workload_sustainable(sem_workload, workload, max_weekly_hours):
                        continue
                    if not check_offering_parity(course_meta.get("semester_offered", "catalogue_unscheduled"), sem):
                        continue
                    prereqs_ok, _ = check_prereqs_met(code, self.prereq_map, scheduled_so_far)
                    if not prereqs_ok:
                        continue
                    if course_meta.get("department") == "Computer Science and Engineering" and not is_minor_eligible:
                        if course_meta.get("course_type") in ["elective", "minor"]:
                            continue
                    current_codes = [c["code"] for c in sem_courses]
                    if has_no_co_clash(code, current_codes, no_co_pairs):
                        continue

                    cand_info = candidate_map.get(code)
                    reason = (
                        cand_info["reasons"][0] if cand_info and cand_info.get("reasons")
                        else f"Elective to satisfy minimum semester credit floor ({min_credits} cr)."
                    )
                    skills_targeted = (
                        cand_info["skills_targeted"] if cand_info and cand_info.get("skills_targeted")
                        else course_meta.get("skills_covered", [])
                    )
                    raw_type = course_meta.get("course_type") or course_meta.get("type") or "programme_elective"
                    norm_type = "open_elective" if raw_type == "open_elective" else "programme_elective"
                    sem_courses.append({
                        "code": code,
                        "title": course_meta["title"],
                        "credits": credits,
                        "course_type": raw_type,
                        "type": norm_type,
                        "workload_hours_per_week": workload,
                        "skills_targeted": skills_targeted,
                        "reason": reason,
                        "provenance": course_meta.get("provenance", "team_authored"),
                        "source_page": course_meta.get("source_page") if course_meta.get("provenance") == "verified" else None,
                        "offering_assumption": True,
                    })
                    sem_credits += credits
                    sem_workload += workload
                    already_scheduled_codes.add(code_up)

            # Update cumulative completed set for next semester's prerequisite checks
            for c in sem_courses:
                scheduled_so_far.add(c["code"].upper())

            running_credits += sem_credits

            # Sort courses within this semester so the top goal-aligned course appears first
            goal_prios = elec_order
            def _sem_course_sort_key(c_item: Dict[str, Any]) -> Tuple[int, int]:
                code = c_item.get("code", "")
                if code in goal_prios:
                    return (0, goal_prios.index(code))
                return (1, 0)
            sem_courses.sort(key=_sem_course_sort_key)

            semester_plans.append({
                "semester_number": sem,
                "season": season,
                "total_credits": round(sem_credits, 1),
                "typical_credits": typical_cr,
                "credit_summary": f"planned {sem_credits:.1f} cr of {typical_cr:.1f} typical",
                "running_total_credits": round(running_credits, 1),
                "workload_hours": round(sem_workload, 1),
                "courses": sem_courses
            })

        # Check for unplaced required core courses
        unscheduled_required = [
            item for item in deferred_core
            if item["code"].upper() not in already_scheduled_codes and item["code"].upper() not in scheduled_so_far
        ]

        infeasible_reasons = []
        for item in unscheduled_required:
            code = item["code"]
            reqs = self.prereq_map.get(code, [])
            unmet_reqs = [r for r in reqs if r.upper() not in scheduled_so_far]
            if unmet_reqs:
                infeasible_reasons.append(
                    f"Core course {code} cannot be scheduled: prerequisite {', '.join(unmet_reqs)} unmet."
                )
            elif max_weekly_hours is not None:
                infeasible_reasons.append(
                    f"Core course {code} cannot be scheduled within available weekly study limit ({max_weekly_hours}h/wk)."
                )
            else:
                infeasible_reasons.append(
                    f"Core course {code} could not be placed due to credit ceiling ({credit_cap} cr) or scheduling constraints."
                )

        return semester_plans, "deterministic greedy scheduler + independent validator", unscheduled_required, infeasible_reasons


multi_semester_planner = MultiSemesterPlanner()
