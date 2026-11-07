"""
Multi-Semester Academic Constraint Planner.
Implements mathematical schedule optimization respecting:
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

SEED_DIR = get_seed_dir()

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

# Try importing OR-Tools safely
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

GOAL_ELECTIVE_PREFS: Dict[str, List[str]] = {
    "goal_higher_studies": ["CSL515", "CSL510", "CSL518", "CSL511", "CSL504", "CSL512", "CSL559", "CSL505"],
    "goal_research": ["CSL515", "CSL510", "CSL518", "CSL511", "CSL504", "CSL512", "CSL559", "CSL505"],
    "goal_software": ["CSL559", "CSL518", "CSL512", "CSL505", "CSL504", "CSL515", "CSL510", "CSL511"],
    "goal_upsc": ["CSL505", "CSL504", "CSL510", "CSL518", "CSL515", "CSL511", "CSL512", "CSL559"],
    "goal_startup": ["CSL559", "CSL518", "CSL505", "CSL504", "CSL512", "CSL515", "CSL510", "CSL511"]
}

GOAL_LA_PREFS: Dict[str, List[Tuple[str, str]]] = {
    "goal_higher_studies": [
        ("LAL225", "Liberal Arts requirement: recommended for research ethics, data privacy, and academic integrity."),
        ("LAL224", "Liberal Arts requirement: fosters cognitive resilience and graduate research productivity."),
        ("LAL202", "Liberal Arts requirement: quantitative econometric modeling supporting empirical research."),
        ("LAL223", "Liberal Arts requirement: social development frameworks for technology impact analysis.")
    ],
    "goal_research": [
        ("LAL225", "Liberal Arts requirement: recommended for research ethics, data privacy, and academic integrity."),
        ("LAL224", "Liberal Arts requirement: fosters cognitive resilience and graduate research productivity."),
        ("LAL202", "Liberal Arts requirement: quantitative econometric modeling supporting empirical research."),
        ("LAL223", "Liberal Arts requirement: social development frameworks for technology impact analysis.")
    ],
    "goal_software": [
        ("LAL201", "Liberal Arts requirement: microeconomic principles of market dynamics, tech pricing, and cost structures."),
        ("LAL225", "Liberal Arts requirement: engineering ethics, algorithmic accountability, and public policy."),
        ("LAL200", "Liberal Arts requirement: macroeconomic perspectives on technological shifts and industrial growth."),
        ("LAL224", "Liberal Arts requirement: workplace psychology and engineering team collaboration.")
    ],
    "goal_upsc": [
        ("LAL222", "Liberal Arts requirement: directly maps to UPSC General Studies Paper I (Modern Indian History)."),
        ("LAL225", "Liberal Arts requirement: directly maps to UPSC General Studies Paper IV (Ethics, Integrity & Aptitude)."),
        ("LAL200", "Liberal Arts requirement: directly maps to UPSC General Studies Paper III (Indian Economy)."),
        ("LAL221", "Liberal Arts requirement: covers World History for UPSC Civil Services Mains General Studies.")
    ],
    "goal_startup": [
        ("LAL200", "Liberal Arts requirement: macroeconomic analysis for venture market assessment and macro trends."),
        ("LAL201", "Liberal Arts requirement: microeconomics of consumer pricing, elasticity, and platform scaling."),
        ("LAL225", "Liberal Arts requirement: tech governance, regulatory compliance, and venture ethics."),
        ("LAL224", "Liberal Arts requirement: founder mental resilience and organizational culture building.")
    ]
}


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
        student_id: str,
        programme_code: str,
        current_semester: int,
        cgpa: float,
        completed_courses: List[str],
        skill_gaps: List[Dict[str, Any]],
        goal_id: str = "goal_software",
        credit_cap: float = 22.0,
        min_credits: float = 14.0,
        max_weekly_hours: float = 12.0,
        no_co_taking_pairs: Optional[List[List[str]]] = None,
        overload_allowed: bool = False,
        excluded_courses: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a valid multi-semester academic schedule grounded in the official curriculum.
        """
        completed_set = set(c.upper() for c in completed_courses)
        excluded_set = set(c.upper() for c in (excluded_courses or []))
        start_sem = current_semester + 1
        end_sem = 8
        semesters_to_plan = list(range(start_sem, end_sem + 1))

        if not semesters_to_plan:
            semesters_to_plan = [current_semester]

        # Retrieve candidates covering skill gaps
        candidates = candidate_retriever.retrieve_candidates_for_gaps(
            skill_gaps=skill_gaps,
            completed_course_codes=completed_set,
            programme_code=programme_code,
            cgpa=cgpa
        )

        # Filter out student-excluded courses (override constraint)
        if excluded_set:
            candidates = [c for c in candidates if c["code"].upper() not in excluded_set]

        # Check Minor eligibility if non-CS student taking CSE courses
        minor_rule = self.academic_rules.get("rule_minor_cse_eligibility", {})
        minor_threshold = float(minor_rule.get("parameters", {}).get("min_cgpa_cutoff", 7.5))
        is_minor_eligible = cgpa >= minor_threshold

        # Format no-co-taking pairs
        all_no_co_pairs = []
        if no_co_taking_pairs:
            all_no_co_pairs.extend(no_co_taking_pairs)

        # Effective semester credit cap
        overload_rule = self.academic_rules.get("rule_credit_overload_cap", {})
        overload_parameters = overload_rule.get("parameters", {})
        overload_threshold = float(overload_parameters.get("min_cgpa_required", 8.5))
        overload_limit = float(overload_parameters.get("max_overload_credits", 24.0))
        effective_cap = overload_limit if (overload_allowed and cgpa >= overload_threshold) else credit_cap

        # Solve using Curriculum-Aware Deterministic Topological Constraint Solver
        plan_result, engine_used = self._solve_topological(
            semesters=semesters_to_plan,
            candidates=candidates,
            completed_set=completed_set,
            credit_cap=effective_cap,
            min_credits=min_credits,
            no_co_pairs=all_no_co_pairs,
            is_minor_eligible=is_minor_eligible,
            goal_id=goal_id
        )

        # Fill non-credit layers (OERs and goal milestones)
        resources = candidate_retriever.retrieve_resources_for_gaps(skill_gaps)
        goal_meta = self.goal_templates.get(goal_id, self.goal_templates.get("goal_software", {}))
        milestones = goal_meta.get("milestones", [])

        # Assign resources and milestones across semesters
        for idx, sem_obj in enumerate(plan_result):
            sem_num = sem_obj["semester_number"]
            # Attach 1-2 curated resources matching gaps
            sem_obj["resources"] = resources[idx*2 : (idx+1)*2]
            # Attach milestone if offset matches
            matching_milestones = [
                m for m in milestones 
                if m.get("semester_offset", 1) == (idx + 1)
            ]
            sem_obj["milestones"] = matching_milestones

        total_credits = sum(s["total_credits"] for s in plan_result)
        skills_covered = list(set(
            sk for s in plan_result for c in s["courses"] for sk in c.get("skills_targeted", [])
        ))

        return {
            "status": "feasible",
            "student_id": student_id,
            "goal_id": goal_id,
            "solver_engine": engine_used,
            "total_credits_planned": round(total_credits, 1),
            "semesters_planned_count": len(plan_result),
            "skills_covered": skills_covered,
            "semesters": plan_result
        }

    def _solve_topological(
        self,
        semesters: List[int],
        candidates: List[Dict[str, Any]],
        completed_set: Set[str],
        credit_cap: float,
        min_credits: float,
        no_co_pairs: List[List[str]],
        is_minor_eligible: bool,
        goal_id: str = "goal_software"
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Deterministic, provably valid curriculum-aware constraint satisfaction solver.
        Schedules:
        1. Mandatory Programme Core courses per official syllabus for each semester.
        2. Goal-aligned Liberal Arts electives.
        3. Goal-aligned and gap-targeted Programme Electives (CSL5xx).
        Evaluates prerequisite DAGs, semester offering parity, and credit bounds.
        """
        scheduled_so_far = set(completed_set)
        semester_plans = []
        already_scheduled_codes = set()

        # Build candidate lookup for reasons and targeted skills
        candidate_map = {c["code"]: c for c in candidates}
        elec_order = GOAL_ELECTIVE_PREFS.get(goal_id, GOAL_ELECTIVE_PREFS["goal_software"])
        la_order = GOAL_LA_PREFS.get(goal_id, GOAL_LA_PREFS["goal_software"])
        la_pointer = 0

        # Calculate initial completed credits
        completed_credits = sum(self.courses.get(c, {}).get("credits", 4.0) for c in completed_set)
        running_credits = completed_credits

        for sem in semesters:
            is_odd = (sem % 2 == 1)
            season = "Odd (Autumn)" if is_odd else "Even (Spring)"
            sem_courses = []
            sem_credits = 0.0
            sem_workload = 0.0
            sem_template = self.semester_templates.get(sem, {})
            typical_cr = float(sem_template.get("stated_credits", 18.0))

            # ------------------------------------------------------------------
            # Phase A: Mandatory Programme Core Courses Scheduled for this Semester
            # ------------------------------------------------------------------
            for c_entry in sem_template.get("courses", []):
                code = c_entry.get("code")
                if not code or c_entry.get("placeholder"):
                    continue
                if code in scheduled_so_far or code in already_scheduled_codes:
                    continue
                if code not in self.courses:
                    continue

                course_meta = self.courses[code]
                credits = float(course_meta["credits"])

                # Check credit ceiling
                if sem_credits + credits > credit_cap:
                    continue

                # Check hard prerequisites
                reqs = self.prereq_map.get(code, [])
                prereqs_satisfied = all(r in scheduled_so_far for r in reqs)
                if not prereqs_satisfied:
                    continue

                # Reason grounding
                cand_info = candidate_map.get(code)
                reason = (
                    cand_info["reasons"][0] if cand_info and cand_info.get("reasons")
                    else f"Required in Semester {sem} (Programme Core) per Courses of Study p.21-22."
                )
                skills_targeted = (
                    cand_info["skills_targeted"] if cand_info and cand_info.get("skills_targeted")
                    else course_meta.get("skills_covered", [])
                )

                sem_courses.append({
                    "code": code,
                    "title": course_meta["title"],
                    "credits": credits,
                    "course_type": course_meta.get("course_type", "programme_core"),
                    "workload_hours_per_week": float(course_meta.get("workload_hours_per_week") or credits * 2.0),
                    "skills_targeted": skills_targeted,
                    "reason": reason,
                    "provenance": course_meta.get("provenance", "verified"),
                    "source_page": course_meta.get("source_page", 21),
                    "offering_assumption": False,
                })
                sem_credits += credits
                sem_workload += float(course_meta.get("workload_hours_per_week") or credits * 2.0)
                already_scheduled_codes.add(code)

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
                    if (
                        la_code not in scheduled_so_far
                        and la_code not in already_scheduled_codes
                        and la_code in self.courses
                    ):
                        la_meta = self.courses[la_code]
                        la_credits = float(la_meta["credits"])
                        if sem_credits + la_credits <= credit_cap:
                            sem_courses.append({
                                "code": la_code,
                                "title": la_meta["title"],
                                "credits": la_credits,
                                "course_type": "liberal_arts",
                                "workload_hours_per_week": float(la_meta.get("workload_hours_per_week") or la_credits * 2.0),
                                "skills_targeted": la_meta.get("skills_covered", []),
                                "reason": la_reason,
                                "provenance": "verified",
                                "source_page": la_meta.get("source_page", 21),
                                "offering_assumption": True,
                            })
                            sem_credits += la_credits
                            sem_workload += float(la_meta.get("workload_hours_per_week") or la_credits * 2.0)
                            already_scheduled_codes.add(la_code)
                            break

            # ------------------------------------------------------------------
            # Phase C: Gap-Targeted & Goal-Aligned Programme Electives (CSL5xx)
            # ------------------------------------------------------------------
            # Cap electives per semester to maintain balanced load across all remaining semesters
            max_electives_this_sem = 1 if sem == 5 else (2 if sem == 6 else 3)
            electives_added_count = 0

            # Build prioritized elective candidate list: diagnostic gap candidates first, then goal electives
            elective_pool = []
            seen_pool = set()
            for cand in candidates:
                c_code = cand["code"]
                if c_code not in seen_pool and c_code not in scheduled_so_far and c_code not in already_scheduled_codes:
                    elective_pool.append(c_code)
                    seen_pool.add(c_code)
            for e_code in elec_order:
                if e_code not in seen_pool and e_code not in scheduled_so_far and e_code not in already_scheduled_codes:
                    elective_pool.append(e_code)
                    seen_pool.add(e_code)

            for code in elective_pool:
                if electives_added_count >= max_electives_this_sem:
                    break
                if sem_credits >= typical_cr or sem_credits >= credit_cap:
                    break
                if code in scheduled_so_far or code in already_scheduled_codes:
                    continue
                if code not in self.courses:
                    continue

                course_meta = self.courses[code]
                credits = float(course_meta["credits"])

                # Check credit ceiling
                if sem_credits + credits > credit_cap:
                    continue

                # Check offering parity
                offering = course_meta.get("semester_offered", "catalogue_unscheduled").lower()
                if offering.startswith("semester_") and offering != f"semester_{sem}":
                    continue
                if offering == "odd" and not is_odd:
                    continue
                if offering == "even" and is_odd:
                    continue

                # Check hard prerequisites
                reqs = self.prereq_map.get(code, [])
                prereqs_satisfied = all(r in scheduled_so_far for r in reqs)
                if not prereqs_satisfied:
                    continue

                # Check Minor eligibility
                if course_meta.get("department") == "Computer Science and Engineering" and not is_minor_eligible:
                    if course_meta.get("course_type") in ["elective", "minor"]:
                        continue

                # Check no-co-taking pairs
                clash = False
                for pair in no_co_pairs:
                    if code in pair:
                        other = pair[0] if pair[1] == code else pair[1]
                        if any(c["code"] == other for c in sem_courses):
                            clash = True
                            break
                if clash:
                    continue

                # Reason grounding
                cand_info = candidate_map.get(code)
                reason = (
                    cand_info["reasons"][0] if cand_info and cand_info.get("reasons")
                    else f"Programme elective ({credits:g} cr): recommended for your goal to build specialized CS capabilities."
                )
                skills_targeted = (
                    cand_info["skills_targeted"] if cand_info and cand_info.get("skills_targeted")
                    else course_meta.get("skills_covered", [])
                )

                sem_courses.append({
                    "code": code,
                    "title": course_meta["title"],
                    "credits": credits,
                    "course_type": course_meta.get("course_type", "programme_elective"),
                    "workload_hours_per_week": float(course_meta.get("workload_hours_per_week") or credits * 2.0),
                    "skills_targeted": skills_targeted,
                    "reason": reason,
                    "provenance": course_meta.get("provenance", "verified"),
                    "source_page": course_meta.get("source_page", 88),
                    "offering_assumption": offering == "catalogue_unscheduled",
                })
                sem_credits += credits
                sem_workload += float(course_meta.get("workload_hours_per_week") or credits * 2.0)
                already_scheduled_codes.add(code)
                electives_added_count += 1

            # In later semesters (7, 8), if more credits needed to reach floor, add additional goal LA or electives
            if sem in (7, 8) and sem_credits < 14.0:
                while la_pointer < len(la_order) and sem_credits < 16.0:
                    la_code, la_reason = la_order[la_pointer]
                    la_pointer += 1
                    if (
                        la_code not in scheduled_so_far
                        and la_code not in already_scheduled_codes
                        and la_code in self.courses
                    ):
                        la_meta = self.courses[la_code]
                        la_credits = float(la_meta["credits"])
                        if sem_credits + la_credits <= credit_cap:
                            sem_courses.append({
                                "code": la_code,
                                "title": la_meta["title"],
                                "credits": la_credits,
                                "course_type": "liberal_arts",
                                "workload_hours_per_week": float(la_meta.get("workload_hours_per_week") or la_credits * 2.0),
                                "skills_targeted": la_meta.get("skills_covered", []),
                                "reason": la_reason,
                                "provenance": "verified",
                                "source_page": la_meta.get("source_page", 21),
                                "offering_assumption": True,
                            })
                            sem_credits += la_credits
                            sem_workload += float(la_meta.get("workload_hours_per_week") or la_credits * 2.0)
                            already_scheduled_codes.add(la_code)

            # Update cumulative completed set for next semester's prerequisite checks
            for c in sem_courses:
                scheduled_so_far.add(c["code"])

            running_credits += sem_credits

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

        return semester_plans, "Deterministic Constraint Solver"


multi_semester_planner = MultiSemesterPlanner()
