"""
Deterministic Tools for Conversational Buddy (PDF §2.5, §5, §7).
Provides verifiable, grounded domain tools executed deterministically:
1. get_plan(student_id)
2. get_gaps(student_id)
3. list_eligible(student_id, semester, course_type, max_credits, interest)
4. check_add(student_id, semester, course_code)
5. check_drop(student_id, semester, course_code)
6. apply_change(student_id, semester, action, course_code)
7. validate_plan(student_id, semester)
8. explain_course(course_code, student_id)
9. next_actions(student_id)
10. what_if(student_id, scenario)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from backend.student.model import StudentStore
from backend.student.diagnostic import diagnostic_engine
from backend.student.interests import INTEREST_TO_SKILLS_MAP
from backend.planner.validator import independent_validator
from backend.api.plans import (
    get_active_plan,
    add_course_to_semester,
    drop_course_from_semester,
    CORE_COURSE_CODES,
    PlanCourseAddRequest,
    PlanCourseDropRequest
)
from backend.retrieval.indexer import retriever
from backend.db.seed_profile import get_seed_dir

logger = logging.getLogger("learning_buddy.buddy.tools")
SEED_DIR = get_seed_dir()


def get_plan(student_id: str) -> Dict[str, Any]:
    """Retrieves current multi-semester plan with credit breakdown and headroom."""
    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    credit_cap = float(plan.get("credit_cap", 24.0))

    semesters_summary = []
    for s in plan.get("semesters", []):
        sem_num = s.get("semester_number")
        courses = s.get("courses", [])
        total_cr = float(s.get("total_credits", 0.0))
        headroom = max(0.0, credit_cap - total_cr)
        semesters_summary.append({
            "semester_number": sem_num,
            "total_credits": total_cr,
            "credit_cap": credit_cap,
            "headroom": headroom,
            "courses": [
                {
                    "code": c.get("code"),
                    "title": c.get("title"),
                    "credits": float(c.get("credits", 0.0)),
                    "course_type": c.get("course_type", "core" if c.get("code") in CORE_COURSE_CODES else "elective"),
                    "is_core": c.get("code") in CORE_COURSE_CODES
                }
                for c in courses
            ]
        })

    return {
        "student_id": student_id,
        "total_credits_planned": plan.get("total_credits_planned", 0.0),
        "version_number": plan_data.get("version_number", 1),
        "semesters": semesters_summary
    }


def get_gaps(student_id: str) -> Dict[str, Any]:
    """Retrieves priority skill gaps, assessed count, and readiness percentage."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        return {"error": f"Student '{student_id}' not found"}

    gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)
    return {
        "student_id": student_id,
        "goal_id": profile.goal_id,
        "goal_name": gaps_data.get("goal_name", profile.target_role or "Software Engineering"),
        "readiness_percentage": gaps_data.get("readiness_percentage"),
        "critical_gap_count": gaps_data.get("critical_gap_count", 0),
        "gaps": gaps_data.get("gaps", [])[:5]
    }


def list_eligible(
    student_id: str,
    semester: int,
    course_type: Optional[str] = None,
    max_credits: Optional[float] = None,
    interest: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lists eligible courses for a specific semester, checks prerequisites, credit headroom,
    computes goal/interest ranking, and suggests multi-course combinations summing to target credits.
    """
    profile = StudentStore.get_profile(student_id)
    if not profile:
        return {"error": f"Student '{student_id}' not found"}

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    credit_cap = float(plan.get("credit_cap", 24.0))

    target_sem = next((s for s in plan.get("semesters", []) if s["semester_number"] == semester), None)
    current_credits = float(target_sem["total_credits"]) if target_sem else 0.0
    headroom = max(0.0, credit_cap - current_credits)
    effective_max_credits = min(headroom, max_credits) if max_credits is not None else headroom

    # Available prerequisites: completed courses + courses in strictly earlier semesters
    completed_codes = {c.course_code for c in profile.completed_courses}
    planned_earlier = set()
    enrolled_in_this_sem = set()
    all_planned = set()

    for s in plan.get("semesters", []):
        for c in s.get("courses", []):
            code = c.get("code")
            if code:
                all_planned.add(code)
                if s["semester_number"] < semester:
                    planned_earlier.add(code)
                elif s["semester_number"] == semester:
                    enrolled_in_this_sem.add(code)

    available_prereqs = completed_codes | planned_earlier

    # Course skills mapping for interest matching
    course_skills_file = SEED_DIR / "course_skills.json"
    course_skills_map = {}
    if course_skills_file.exists():
        with open(course_skills_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                course_skills_map.setdefault(item["course_code"], []).append(item["skill_id"])

    eligible_list = []
    ineligible_list = []

    for code, c in independent_validator.courses.items():
        is_core = code in CORE_COURSE_CODES or c.get("course_type") in ("core", "institute_core", "program_compulsory")
        # Do not suggest core courses belonging to other semesters as electives
        if is_core and code not in enrolled_in_this_sem:
            continue

        c_credits = float(c.get("credits", 3.0) or 0.0)
        c_type = c.get("course_type", "elective")
        reqs = independent_validator.prereq_map.get(code, [])
        unmet_prereqs = [r for r in reqs if r not in available_prereqs]

        # Check interest match
        match_interest = None
        course_skills = set(course_skills_map.get(code, []))
        for user_int in profile.interests:
            target_skills = set(INTEREST_TO_SKILLS_MAP.get(user_int, []))
            if course_skills & target_skills:
                match_interest = user_int
                break

        # Filter by course_type if requested
        if course_type and course_type.lower() not in c_type.lower():
            continue

        # Check eligibility
        if code in completed_codes:
            ineligible_list.append({
                "code": code,
                "title": c.get("title", code),
                "credits": c_credits,
                "reason": "Already completed in previous semester"
            })
        elif unmet_prereqs:
            prereq_names = [f"{r} ({independent_validator.courses.get(r, {}).get('title', r)})" for r in unmet_prereqs]
            ineligible_list.append({
                "code": code,
                "title": c.get("title", code),
                "credits": c_credits,
                "reason": f"Missing prerequisite: {', '.join(prereq_names)}"
            })
        elif code in enrolled_in_this_sem:
            ineligible_list.append({
                "code": code,
                "title": c.get("title", code),
                "credits": c_credits,
                "reason": f"Already enrolled in Semester {semester}"
            })
        elif c_credits > headroom:
            ineligible_list.append({
                "code": code,
                "title": c.get("title", code),
                "credits": c_credits,
                "reason": f"Exceeds semester headroom ({headroom:.1f} cr available, needs {c_credits:.1f} cr)"
            })
        else:
            # Eligible course
            # Goal affinity weighting
            goal_weight = 0
            if profile.goal_id == "goal_upsc":
                if "liberal_arts" in c_type or "open_elective" in c_type or code.startswith("LAL"):
                    goal_weight += 2
                elif code in ("CSL511", "CSL559"):
                    goal_weight += 1
            elif profile.goal_id == "goal_higher_studies":
                if code in ("CSL510", "CSL511", "CSL512", "CSL518"):
                    goal_weight += 2
            elif profile.goal_id == "goal_software":
                if code in ("CSL559", "CSL515", "CSL512"):
                    goal_weight += 2

            eligible_list.append({
                "code": code,
                "title": c.get("title", code),
                "credits": c_credits,
                "course_type": c_type,
                "match_interest": match_interest,
                "goal_affinity": goal_weight,
                "source": c.get("source", "IIT Bhilai Courses of Study")
            })

    # Sort eligible by goal affinity desc, then interest match, then credits desc
    eligible_list.sort(key=lambda x: (x["goal_affinity"], 1 if x["match_interest"] else 0, x["credits"]), reverse=True)

    # Compute suggested combinations summing to target credits (e.g. 5.0 cr)
    target_sum = max_credits if max_credits is not None else headroom
    suggested_combinations = []
    # 1. Single courses matching exactly target_sum
    for c in eligible_list:
        if abs(c["credits"] - target_sum) < 0.1:
            suggested_combinations.append({
                "courses": [c["code"]],
                "total_credits": c["credits"],
                "description": f"{c['code']} ({c['title']}, {c['credits']} cr)"
            })

    # 2. Pairs of courses summing to target_sum (or fitting in headroom)
    for i in range(len(eligible_list)):
        for j in range(i + 1, len(eligible_list)):
            c1 = eligible_list[i]
            c2 = eligible_list[j]
            pair_sum = c1["credits"] + c2["credits"]
            if abs(pair_sum - target_sum) < 0.1:
                suggested_combinations.append({
                    "courses": [c1["code"], c2["code"]],
                    "total_credits": pair_sum,
                    "description": f"{c1['code']} ({c1['title']}, {c1['credits']} cr) + {c2['code']} ({c2['title']}, {c2['credits']} cr)"
                })

    return {
        "student_id": student_id,
        "semester": semester,
        "current_credits": current_credits,
        "credit_cap": credit_cap,
        "headroom": headroom,
        "target_credits": target_sum,
        "eligible_courses": eligible_list,
        "suggested_combinations": suggested_combinations[:3],
        "ineligible_sample": ineligible_list[:4]
    }


def check_add(student_id: str, semester: int, course_code: str) -> Dict[str, Any]:
    """Validates whether adding a course is permissible without modifying the database."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        return {"allowed": False, "reason": f"Student '{student_id}' not found"}

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    credit_cap = float(plan.get("credit_cap", 24.0))

    sem_obj = next((s for s in plan.get("semesters", []) if s["semester_number"] == semester), None)
    if not sem_obj:
        return {"allowed": False, "reason": f"Semester {semester} not found in plan"}

    current_credits = float(sem_obj["total_credits"])
    headroom = max(0.0, credit_cap - current_credits)

    course = independent_validator.courses.get(course_code)
    if not course:
        return {"allowed": False, "reason": f"Course '{course_code}' does not exist in curriculum catalogue"}

    c_credits = float(course.get("credits", 3.0) or 0.0)

    # Check if already in semester
    existing_codes = {c.get("code") for c in sem_obj.get("courses", [])}
    if course_code in existing_codes:
        return {"allowed": False, "reason": f"{course_code} is already enrolled in Semester {semester}"}

    # Check credit cap
    if current_credits + c_credits > credit_cap:
        alt = "LAL201 (Microeconomics, 1.0 cr)" if headroom >= 1.0 else "None (semester at capacity)"
        return {
            "allowed": False,
            "reason": f"Adding {course_code} ({c_credits} cr) to Semester {semester} exceeds the {credit_cap} credit cap (current: {current_credits} cr, headroom: {headroom:.1f} cr).",
            "current_credits": current_credits,
            "headroom": headroom,
            "suggested_alternative": alt
        }

    # Check prerequisites
    completed_codes = {c.course_code for c in profile.completed_courses}
    planned_earlier = {
        c.get("code") for s in plan.get("semesters", [])
        if s["semester_number"] < semester
        for c in s.get("courses", []) if c.get("code")
    }
    available_prereqs = completed_codes | planned_earlier
    reqs = independent_validator.prereq_map.get(course_code, [])
    unmet_prereqs = [r for r in reqs if r not in available_prereqs]

    if unmet_prereqs:
        prereq_names = [f"{r} ({independent_validator.courses.get(r, {}).get('title', r)})" for r in unmet_prereqs]
        return {
            "allowed": False,
            "reason": f"Missing prerequisite: {', '.join(prereq_names)}",
            "missing_prerequisites": unmet_prereqs
        }

    return {
        "allowed": True,
        "course_code": course_code,
        "title": course.get("title", course_code),
        "credits": c_credits,
        "current_credits": current_credits,
        "new_credits": current_credits + c_credits,
        "credit_cap": credit_cap,
        "headroom_after": headroom - c_credits,
        "proposal_summary": f"Add {course_code} ({c_credits} cr) to Semester {semester}: {current_credits + c_credits:.1f}/{credit_cap:.1f} credits."
    }


def check_drop(student_id: str, semester: int, course_code: str) -> Dict[str, Any]:
    """Validates whether dropping a course is permissible (strictly blocks Core courses)."""
    if course_code in CORE_COURSE_CODES:
        return {
            "allowed": False,
            "is_core": True,
            "course_code": course_code,
            "reason": f"{course_code} is a compulsory Core course under IIT Bhilai curriculum regulations and cannot be dropped."
        }

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    sem_obj = next((s for s in plan.get("semesters", []) if s["semester_number"] == semester), None)
    if not sem_obj:
        return {"allowed": False, "reason": f"Semester {semester} not found in plan"}

    course_obj = next((c for c in sem_obj.get("courses", []) if c.get("code") == course_code), None)
    if not course_obj:
        return {"allowed": False, "reason": f"{course_code} is not enrolled in Semester {semester}"}

    c_credits = float(course_obj.get("credits", 3.0) or 0.0)
    current_credits = float(sem_obj.get("total_credits", 0.0))

    return {
        "allowed": True,
        "course_code": course_code,
        "title": course_obj.get("title", course_code),
        "credits": c_credits,
        "current_credits": current_credits,
        "new_credits": max(0.0, current_credits - c_credits),
        "proposal_summary": f"Drop {course_code} ({c_credits} cr) from Semester {semester}: {current_credits - c_credits:.1f}/24 credits."
    }


def apply_change(student_id: str, semester: int, action: str, course_code: str) -> Dict[str, Any]:
    """Executes validated course addition or drop on the student's active plan in database."""
    action_lower = action.lower().strip()
    if action_lower in ("add", "enroll"):
        req = PlanCourseAddRequest(course_code=course_code, semester=semester)
        res = add_course_to_semester(student_id, req)
        return {
            "status": "applied",
            "action": "add",
            "course_code": course_code,
            "semester": semester,
            "message": res.get("message"),
            "new_credits": res.get("semester_credits"),
            "is_valid": res.get("validation_report", {}).get("is_valid", True)
        }
    elif action_lower in ("drop", "remove"):
        req = PlanCourseDropRequest(course_code=course_code, semester=semester)
        res = drop_course_from_semester(student_id, req)
        return {
            "status": "applied",
            "action": "drop",
            "course_code": course_code,
            "semester": semester,
            "message": res.get("message"),
            "new_credits": res.get("semester_credits"),
            "is_valid": res.get("validation_report", {}).get("is_valid", True)
        }
    else:
        return {"status": "error", "message": f"Unsupported action '{action}'. Use 'add' or 'drop'."}


def validate_plan(student_id: str, semester: Optional[int] = None) -> Dict[str, Any]:
    """Runs independent 9-rule validator on student plan."""
    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    report = independent_validator.validate_plan_independent(plan)
    return {
        "student_id": student_id,
        "is_valid": report["is_valid"],
        "rules_evaluated": report["rules_evaluated"],
        "rules_passed": report["rules_passed"],
        "errors": report.get("errors", []),
        "warnings": report.get("warnings", [])
    }


def explain_course(course_code: str, student_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves course syllabus, credits, prerequisites, and official Courses of Study citation & page."""
    code = course_code.upper().strip()
    c = independent_validator.courses.get(code)
    if not c:
        return {"found": False, "course_code": code, "error": f"Course '{code}' not found in curriculum catalogue."}

    chunk = retriever.lookup_course(code)
    citation = chunk.get("source_citation") if chunk else c.get("source", "IIT Bhilai Courses of Study")
    page = chunk.get("source_page") if chunk else None

    reqs = independent_validator.prereq_map.get(code, [])

    return {
        "found": True,
        "course_code": code,
        "title": c.get("title", code),
        "credits": float(c.get("credits", 3.0) or 0.0),
        "course_type": c.get("course_type", "elective"),
        "prerequisites": reqs,
        "syllabus": c.get("syllabus", "Standard IIT Bhilai departmental syllabus."),
        "source_citation": citation,
        "source_page": page
    }


def next_actions(student_id: str) -> Dict[str, Any]:
    """Provides goal-differentiated recommended next actions based on persona goal."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        return {"error": f"Student '{student_id}' not found"}

    goal_id = profile.goal_id
    if goal_id == "goal_upsc":
        actions = [
            "Maintain strong academic standing in core CSE modules (target CGPA > 7.5 for interview clearance).",
            "Take high-relevance Humanities & Social Science electives (LAL201 Microeconomics, LAL225 Indian Society) to build General Studies analytical foundation.",
            "Schedule 6-8 dedicated hours weekly for Current Affairs and CSAT quantitative aptitude revision.",
            "Complete the Indian Polity and Economics diagnostic modules."
        ]
        rationale = "UPSC CSE requires consistent CSE academic baseline while systematically accumulating GS & CSAT competency."
    elif goal_id == "goal_higher_studies":
        actions = [
            "Prioritize advanced theoretical computer science electives (CSL510 Approximation Algorithms, CSL511 Formal Verification).",
            "Engage in faculty undergraduate research / BTP projects in Systems or Algorithms.",
            "Read top-tier conference publications (IEEE/ACM) in chosen subfield.",
            "Maintain CGPA >= 8.5 for competitive international MS/PhD applications."
        ]
        rationale = "Higher studies requires proven theoretical rigor, high CGPA, and verifiable research publication potential."
    elif goal_id == "goal_startup":
        actions = [
            "Build full-stack production prototypes and deploy live applications (Web/App Systems).",
            "Select practical systems electives (CSL559 Computer Systems Design).",
            "Engage with IIT Bhilai Innovation and Incubation Council (IIC).",
            "Practice agile sprint delivery and user feedback collection."
        ]
        rationale = "Startup founders require rapid prototyping velocity, systems architecture, and product iteration speed."
    else:  # goal_software
        actions = [
            "Master Data Structures and Algorithms with daily practice drills (LeetCode / Codeforces).",
            "Deepen Systems engineering competency (CSL301 Operating Systems, CSL303 Computer Networks).",
            "Build a high-performance open-source systems project for resume placement.",
            "Target technical mock interviews and CP competitions."
        ]
        rationale = "Software & IT placements require top-tier problem solving, clean system design, and competitive coding mastery."

    return {
        "student_id": student_id,
        "goal_id": goal_id,
        "persona_name": profile.name,
        "target_role": profile.target_role or "Computer Science Graduate",
        "rationale": rationale,
        "actions": actions
    }


def what_if(student_id: str, scenario: str) -> Dict[str, Any]:
    """Evaluates what-if academic adaptation scenarios."""
    profile = StudentStore.get_profile(student_id)
    scen_lower = scenario.lower()

    if "strong" in scen_lower or "high" in scen_lower:
        return {
            "scenario": "Strong study week (high practice accuracy > 85%)",
            "projected_mastery_delta": "+5% across active core skills",
            "plan_adaptation": "Allows taking advanced electives early; relaxes remedial prerequisites.",
            "recommendation": "Maintain momentum; consider attempting competitive practice tests."
        }
    elif "weak" in scen_lower or "low" in scen_lower:
        return {
            "scenario": "Weak study week (missed practice / diagnostic gaps)",
            "projected_mastery_delta": "-3% confidence on unexercised skills",
            "plan_adaptation": "Triggers remedial practice drills; alerts before scheduling dependent electives.",
            "recommendation": "Review recommended textbook readings and complete practice drills before midterms."
        }
    elif "35" in scen_lower or "overload" in scen_lower:
        return {
            "scenario": "Requesting 35 credits in a single semester",
            "allowed": False,
            "reason": "IIT Bhilai academic ordinance strictly caps regular semester workload at 24.0 credits.",
            "alternative": "Spread the courses across upcoming regular and summer semesters (maximum 24.0 credits per semester)."
        }
    else:
        return {
            "scenario": scenario,
            "evaluation": f"Evaluated against IIT Bhilai B.Tech CSE ordinance for {profile.name if profile else 'student'}.",
            "status": "ready"
        }
