"""
Curriculum Planning & Verification API Endpoints.
Provides plan generation, independent rule verification, cryptographic Plan Certificates,
audit history, and infeasible request handling.
"""

from fastapi import APIRouter, HTTPException, Response
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from datetime import datetime

from backend.student.model import StudentStore
from backend.student.diagnostic import diagnostic_engine
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.planner.explainer import plan_explainer
from backend.planner.infeasible import infeasible_handler
from backend.rules import rule_registry, pdf_builder, PlanCertificate
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_seed_dir
from backend.student.summary import build_student_summary
from backend.planner.schemas import ActivePlanResponse

SEED_DIR = get_seed_dir()

router = APIRouter(prefix="/plans", tags=["Curriculum Planning & Verification"])

class PlanGenerateRequest(BaseModel):
    student_id: str
    credit_cap_override: Optional[float] = None
    goal_override: Optional[str] = None
    reason_for_change: Optional[str] = "Routine schedule generation"

class InfeasibleRequestModel(BaseModel):
    student_id: str
    requested_credits: Optional[float] = None
    desired_course_code: Optional[str] = None

class CertificateVerifyRequest(BaseModel):
    expected_hash: Optional[str] = None

@router.post("/generate")
def generate_student_plan(req: PlanGenerateRequest) -> Dict[str, Any]:
    """
    Generates a provably valid multi-semester course plan, validates it via RuleRegistry,
    generates a sealed cryptographic PlanCertificate, creates a versioned snapshot,
    and returns a factual explanation.
    """
    profile = StudentStore.get_profile(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    # Check for infeasible credit requests first
    rules = multi_semester_planner.academic_rules
    standard_cap = float(rules.get("rule_sem_max_credits", {}).get("parameters", {}).get("max_credits", 22.0))
    overload_rule = rules.get("rule_credit_overload_cap", {}).get("parameters", {})
    overload_cap = float(overload_rule.get("max_overload_credits", 24.0))
    overload_threshold = float(overload_rule.get("min_cgpa_required", 8.5))
    maximum_cap = overload_cap if profile.cgpa >= overload_threshold else standard_cap
    if req.credit_cap_override and req.credit_cap_override > maximum_cap:
        return infeasible_handler.handle_excessive_credit_request(req.student_id, req.credit_cap_override)

    active_goal = req.goal_override or profile.goal_id
    credit_cap = req.credit_cap_override or standard_cap
    minimum_credits = float(
        rules.get("rule_sem_min_credits", {}).get("parameters", {}).get("min_credits", 14.0)
    )

    # 1. Compute gaps
    gaps_data = diagnostic_engine.compute_skill_gaps(req.student_id, goal_id=active_goal)

    # 2. Plan curriculum via solver
    plan = multi_semester_planner.plan_curriculum(
        student_id=req.student_id,
        programme_code=profile.programme,
        current_semester=profile.current_semester,
        cgpa=profile.cgpa,
        completed_courses=[c.course_code for c in profile.completed_courses],
        skill_gaps=gaps_data.get("gaps", []),
        goal_id=active_goal,
        credit_cap=credit_cap,
        min_credits=minimum_credits,
        max_weekly_hours=profile.available_hours_per_week,
        overload_allowed=(profile.cgpa >= overload_threshold)
    )
    effective_credit_cap = req.credit_cap_override or maximum_cap
    plan["credit_cap"] = effective_credit_cap
    student_summary = build_student_summary(
        profile=profile,
        plan=plan,
        readiness_percentage=gaps_data.get("readiness_percentage"),
        priority_gap_count=gaps_data.get("critical_gap_count", 0),
        goal_name=gaps_data.get("goal_name"),
        credit_cap=effective_credit_cap,
    )

    # 3. Independent Validation Pass & Sealed Certificate
    profile_dict = profile.model_dump()
    validation_report = independent_validator.validate_plan(plan, profile_dict)
    if not validation_report["is_valid"]:
        raise HTTPException(
            status_code=500,
            detail=f"Generated plan failed independent validation: {'; '.join(validation_report['errors'])}"
        )

    # Determine next version
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT version_number, plan_json FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
            (req.student_id,)
        )
        prev_row = cur.fetchone()
        
        prev_version = 0
        prev_plan = None
        if prev_row:
            prev_version = prev_row["version_number"]
            prev_plan = json.loads(prev_row["plan_json"])

        next_version = prev_version + 1
        plan_version_id = f"{req.student_id}_v{next_version}"

    # Generate sealed certificate
    certificate = rule_registry.generate_certificate(plan, profile_dict, plan_version_id=plan_version_id)
    validation_report["certificate"] = certificate.model_dump()

    # 4. Versioning & Diffing
    plan_diff = plan_explainer.generate_plan_diff(
        old_plan=prev_plan,
        new_plan=plan,
        reason_for_change=req.reason_for_change or "Curriculum optimization"
    )

    with get_db_cursor() as cur:
        cur.execute("""
        INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
        VALUES (?, ?, ?, ?, ?);
        """, (
            req.student_id,
            next_version,
            json.dumps(plan),
            json.dumps(plan_diff),
            json.dumps(validation_report)
        ))

    # 5. Natural Language Explanation
    explanation = plan_explainer.explain_plan_in_natural_language(plan, profile.name)

    return {
        "student_id": req.student_id,
        "version_number": next_version,
        "plan": plan,
        "validation_report": validation_report,
        "certificate": certificate.model_dump(),
        "diff": plan_diff,
        "explanation": explanation,
        "student_summary": student_summary.model_dump()
    }

@router.get("/{student_id}", response_model=ActivePlanResponse)
def get_active_plan(student_id: str) -> Dict[str, Any]:
    """Retrieves the latest saved plan version and certificate for a student."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    with get_db_cursor() as cur:
        cur.execute("""
        SELECT version_number, plan_json, diff_from_previous_json, validation_report_json, created_at
        FROM plan_versions
        WHERE student_id = ?
        ORDER BY version_number DESC LIMIT 1
        """, (student_id,))
        row = cur.fetchone()
        if not row:
            # Auto-generate first plan if none exists
            return generate_student_plan(PlanGenerateRequest(student_id=student_id))

        val_report = json.loads(row["validation_report_json"])
        plan = json.loads(row["plan_json"])
        gaps_data = diagnostic_engine.compute_skill_gaps(
            student_id,
            goal_id=plan.get("goal_id", profile.goal_id)
        )
        student_summary = build_student_summary(
            profile=profile,
            plan=plan,
            readiness_percentage=gaps_data.get("readiness_percentage"),
            priority_gap_count=gaps_data.get("critical_gap_count", 0),
            goal_name=gaps_data.get("goal_name"),
            credit_cap=plan.get("credit_cap"),
        )
        
        # Ensure certificate is present
        cert_data = val_report.get("certificate")
        if not cert_data:
            cert = rule_registry.generate_certificate(
                plan, profile.model_dump(), plan_version_id=f"{student_id}_v{row['version_number']}"
            )
            cert_data = cert.model_dump()
            val_report["certificate"] = cert_data

        return {
            "student_id": student_id,
            "version_number": row["version_number"],
            "plan": plan,
            "diff": json.loads(row["diff_from_previous_json"] or "{}"),
            "validation_report": val_report,
            "certificate": cert_data,
            "student_summary": student_summary.model_dump(),
            "created_at": str(row["created_at"])
        }

@router.get("/{student_id}/certificate")
def get_plan_certificate(student_id: str) -> Dict[str, Any]:
    """
    Returns the cryptographic PlanCertificate for the student's active plan.
    """
    plan_data = get_active_plan(student_id)
    return {
        **plan_data.get("certificate", {}),
        "student_summary": plan_data.get("student_summary"),
    }

@router.post("/{student_id}/certificate/verify")
def verify_plan_certificate(student_id: str, req: Optional[CertificateVerifyRequest] = None) -> Dict[str, Any]:
    """
    Re-evaluates all 16 academic rules from scratch against the stored plan,
    checks cryptographic canonical hash match, and returns tamper detection results.
    """
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    stored_cert = plan_data.get("certificate", {})
    expected_hash = (req.expected_hash if req and req.expected_hash else None) or stored_cert.get("certificate_hash")

    verification = rule_registry.verify_plan(
        plan=plan,
        student_profile=profile.model_dump(),
        expected_certificate_hash=expected_hash,
        generated_at=stored_cert.get("generated_at"),
        plan_version_id=stored_cert.get("plan_version_id")
    )
    return verification

@router.get("/{student_id}/certificate.pdf")
def export_plan_certificate_pdf(student_id: str):
    """
    Exports a clean, official one-page printable PDF certificate
    with ordinance citations, verification seal, and rule audit table.
    """
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found.")

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    cert_dict = plan_data.get("certificate")
    if not cert_dict:
        cert = rule_registry.generate_certificate(plan, profile.model_dump())
    else:
        cert = PlanCertificate(**cert_dict)

    pdf_bytes = pdf_builder.build_certificate_pdf(cert, profile.model_dump())
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=academic_plan_certificate_{student_id}.pdf"
        }
    )

@router.get("/{student_id}/history")
def get_plan_history(student_id: str) -> List[Dict[str, Any]]:
    """Returns chronological versions and diffs for auditability."""
    with get_db_cursor() as cur:
        cur.execute("""
        SELECT version_number, diff_from_previous_json, validation_report_json, created_at
        FROM plan_versions
        WHERE student_id = ?
        ORDER BY version_number ASC
        """, (student_id,))
        rows = cur.fetchall()
        return [
            {
                "version_number": r["version_number"],
                "diff": json.loads(r["diff_from_previous_json"] or "{}"),
                "rules_passed": json.loads(r["validation_report_json"]).get("rules_passed", 16),
                "created_at": str(r["created_at"])
            }
            for r in rows
        ]

@router.post("/infeasible")
def infeasible_request(req: InfeasibleRequestModel) -> Dict[str, Any]:
    """Demonstrates how the planner handles mathematically or regulatorily infeasible requests."""
    if req.requested_credits:
        return infeasible_handler.handle_excessive_credit_request(req.student_id, req.requested_credits)
    elif req.desired_course_code:
        return infeasible_handler.handle_missing_prerequisite_request(req.student_id, req.desired_course_code)
    else:
        raise HTTPException(status_code=400, detail="Provide requested_credits or desired_course_code to test.")

# Backward-compatible alias used by the tests and older callers.
test_infeasible_request = infeasible_request
infeasible_request.__test__ = False
test_infeasible_request.__test__ = False

# ==============================================================================
# INTERACTIVE PLAN OPERATIONS (PDF §2.3, §7)
# ==============================================================================

CORE_COURSE_CODES = {
    "CSL100", "MAL100", "CYL100", "PHL101", "CYL101", "CYP102", "PHP102", "NCN100",
    "MAL101", "MEP102", "EEL101", "ECL101", "BML101", "LAN103",
    "MAL403", "CSL201", "CSL202", "CSP203", "LAL100",
    "CSL251", "CSL252", "CSL253", "LAL101",
    "CSL301", "CSL302", "CSL303", "CSL304",
    "CSL351", "CSP352", "UGQ301",
    "CSQ401"
}

class PlanCourseAddRequest(BaseModel):
    semester: int
    course_code: str

class PlanCourseDropRequest(BaseModel):
    semester: int
    course_code: str

class PlanCourseSwapRequest(BaseModel):
    semester: int
    drop_code: str
    add_code: str

@router.get("/{student_id}/eligible")
def list_eligible_courses(student_id: str, semester: int) -> Dict[str, Any]:
    """
    Lists electives and open electives for a semester, classified as eligible or ineligible
    with exact reasons and interest match ranking (PDF §2.3).
    """
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    credit_cap = float(plan.get("credit_cap", 24.0))

    # Find target semester
    sem_obj = next((s for s in plan.get("semesters", []) if s["semester_number"] == semester), None)
    current_credits = float(sem_obj["total_credits"]) if sem_obj else 0.0
    headroom = max(0.0, credit_cap - current_credits)

    # Prereqs available: completed courses + courses planned in strictly earlier semesters
    completed_codes = {c.course_code for c in profile.completed_courses}
    planned_earlier = set()
    all_planned = set()
    for s in plan.get("semesters", []):
        for c in s.get("courses", []):
            code = c.get("code")
            if code:
                all_planned.add(code)
                if s["semester_number"] < semester:
                    planned_earlier.add(code)
    available_prereqs = completed_codes | planned_earlier

    # Import interest mappings
    from backend.student.interests import INTEREST_TO_SKILLS_MAP

    # Load course skills mapping
    course_skills_file = SEED_DIR / "course_skills.json"
    course_skills_map = {}
    if course_skills_file.exists():
        with open(course_skills_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                course_skills_map.setdefault(item["course_code"], []).append(item["skill_id"])

    # Load full catalogue
    results = []
    for code, c in independent_validator.courses.items():
        is_core = code in CORE_COURSE_CODES or c.get("course_type") in ("core", "institute_core", "program_compulsory")
        # Focus on electives, open electives, and catalogue offerings
        if is_core and code in all_planned:
            continue

        c_credits = float(c.get("credits", 3.0) or 0.0)
        reqs = independent_validator.prereq_map.get(code, [])
        unmet_prereqs = [r for r in reqs if r not in available_prereqs]

        # Check interest match
        match_interest = None
        course_skills = set(course_skills_map.get(code, []))
        for interest in profile.interests:
            target_skills = set(INTEREST_TO_SKILLS_MAP.get(interest, []))
            if course_skills & target_skills:
                match_interest = interest
                break

        # Check eligibility
        eligible = True
        ineligible_reason = None

        if code in completed_codes:
            eligible = False
            ineligible_reason = "Already completed in previous semester"
        elif unmet_prereqs:
            eligible = False
            prereq_names = [f"{r} ({independent_validator.courses.get(r, {}).get('title', r)})" for r in unmet_prereqs]
            ineligible_reason = f"Missing prerequisite: {', '.join(prereq_names)}"
        elif code in all_planned:
            eligible = False
            ineligible_reason = "Already planned in curriculum"
        elif c_credits > headroom:
            eligible = False
            ineligible_reason = f"Exceeds semester credit limit ({headroom:.1f} cr headroom available, course requires {c_credits} cr)"

        results.append({
            "code": code,
            "title": c.get("title", code),
            "credits": c_credits,
            "course_type": c.get("course_type", "elective"),
            "department": c.get("department", "CSE"),
            "eligible": eligible,
            "ineligible_reason": ineligible_reason,
            "match_interest": match_interest,
            "is_core": is_core
        })

    # Sort: eligible first (matching student interests at top), then ineligible
    def sort_key(x):
        return (
            not x["eligible"],
            0 if x["match_interest"] else 1,
            x["code"]
        )
    results.sort(key=sort_key)

    return {
        "student_id": student_id,
        "semester": semester,
        "credit_cap": credit_cap,
        "current_credits": current_credits,
        "headroom": headroom,
        "courses": results
    }

@router.post("/{student_id}/courses/add")
def add_course_to_semester(student_id: str, req: PlanCourseAddRequest) -> Dict[str, Any]:
    """Adds an eligible elective/open elective to a semester with instant deterministic re-validation."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    course = independent_validator.courses.get(req.course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course code '{req.course_code}' not found in catalogue.")

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    credit_cap = float(plan.get("credit_cap", 24.0))

    sem_obj = next((s for s in plan.get("semesters", []) if s["semester_number"] == req.semester), None)
    if not sem_obj:
        raise HTTPException(status_code=404, detail=f"Semester {req.semester} not found in plan.")

    cur_credits = float(sem_obj["total_credits"])
    course_credits = float(course.get("credits", 3.0) or 0.0)
    headroom = credit_cap - cur_credits

    # Check credit cap
    if cur_credits + course_credits > credit_cap:
        # Find best alternative that fits headroom
        alt_course = None
        for c_code, c_data in independent_validator.courses.items():
            c_cr = float(c_data.get("credits", 3.0) or 0.0)
            if 0 < c_cr <= headroom and c_code not in CORE_COURSE_CODES:
                alt_course = f"{c_code} ({c_data.get('title')}, {c_cr} cr)"
                break

        msg = f"Adding {req.course_code} ({course_credits} cr) to Semester {req.semester} exceeds the {credit_cap} credit cap (current: {cur_credits} cr, headroom: {headroom:.1f} cr)."
        raise HTTPException(status_code=400, detail={
            "error": msg,
            "message": msg,
            "headroom": headroom,
            "suggested_alternative": alt_course or "Consider swapping an elective or taking this course in a later semester."
        })

    # Check prerequisites
    completed_codes = {c.course_code for c in profile.completed_courses}
    planned_earlier = set()
    for s in plan.get("semesters", []):
        for c in s.get("courses", []):
            if c.get("code"):
                if s["semester_number"] < req.semester:
                    planned_earlier.add(c["code"])
                if c["code"] == req.course_code:
                    raise HTTPException(status_code=400, detail=f"{req.course_code} is already planned in Semester {s['semester_number']}.")
    
    available_prereqs = completed_codes | planned_earlier
    reqs = independent_validator.prereq_map.get(req.course_code, [])
    unmet = [r for r in reqs if r not in available_prereqs]
    if unmet:
        raise HTTPException(status_code=400, detail=f"Cannot add {req.course_code}: Missing prerequisite(s): {', '.join(unmet)}.")

    # Add course entry
    course_entry = {
        "code": course["code"],
        "title": course.get("title", course["code"]),
        "credits": course_credits,
        "course_type": course.get("course_type", "open_elective"),
        "department": course.get("department", "CSE"),
        "reason": f"Student elective selection matching interest",
        "skills_targeted": []
    }
    sem_obj["courses"].append(course_entry)
    sem_obj["total_credits"] = cur_credits + course_credits
    plan["total_credits"] = sum(s["total_credits"] for s in plan["semesters"])

    # Re-validate deterministically
    profile_dict = profile.model_dump()
    val_report = independent_validator.validate_plan(plan, profile_dict)
    
    # Save new plan version
    with get_db_cursor() as cur:
        cur.execute("SELECT MAX(version_number) as max_v FROM plan_versions WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        next_v = (row["max_v"] or 1) + 1
        plan_diff = {
            "action": "add_course",
            "semester": req.semester,
            "course": req.course_code,
            "credits_before": cur_credits,
            "credits_after": sem_obj["total_credits"],
            "description": f"Added {req.course_code} ({course_credits} cr) to Semester {req.semester}"
        }
        cur.execute("""
        INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
        VALUES (?, ?, ?, ?, ?)
        """, (student_id, next_v, json.dumps(plan), json.dumps(plan_diff), json.dumps(val_report)))

    return {
        "success": True,
        "message": f"Added {req.course_code} ({course_credits} cr) to Semester {req.semester}.",
        "plan": plan,
        "diff": plan_diff,
        "validation_report": val_report,
        "credits_before": cur_credits,
        "credits_after": sem_obj["total_credits"],
        "credit_cap": credit_cap
    }

@router.post("/{student_id}/courses/drop")
def drop_course_from_semester(student_id: str, req: PlanCourseDropRequest) -> Dict[str, Any]:
    """Drops an elective/open elective from a semester. Rejects dropping core compulsory courses."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    # Core course lock check
    if req.course_code in CORE_COURSE_CODES:
        error_msg = f"{req.course_code} is a compulsory Core course under IIT Bhilai curriculum regulations and cannot be dropped."
        raise HTTPException(status_code=400, detail={
            "error": error_msg,
            "message": error_msg,
            "is_core": True,
            "course_code": req.course_code
        })

    course = independent_validator.courses.get(req.course_code)
    if course and course.get("course_type") in ("core", "institute_core", "program_compulsory"):
        error_msg = f"{req.course_code} is a compulsory Core course under IIT Bhilai curriculum regulations and cannot be dropped."
        raise HTTPException(status_code=400, detail={
            "error": error_msg,
            "message": error_msg,
            "is_core": True,
            "course_code": req.course_code
        })

    plan_data = get_active_plan(student_id)
    plan = plan_data.get("plan", {})
    sem_obj = next((s for s in plan.get("semesters", []) if s["semester_number"] == req.semester), None)
    if not sem_obj:
        raise HTTPException(status_code=404, detail=f"Semester {req.semester} not found in plan.")

    found_idx = next((i for i, c in enumerate(sem_obj["courses"]) if c["code"] == req.course_code), None)
    if found_idx is None:
        raise HTTPException(status_code=404, detail=f"Course {req.course_code} is not in Semester {req.semester}.")

    dropped_course = sem_obj["courses"].pop(found_idx)
    course_credits = float(dropped_course.get("credits", 0.0) or 0.0)
    cur_credits = float(sem_obj["total_credits"])
    sem_obj["total_credits"] = max(0.0, cur_credits - course_credits)
    plan["total_credits"] = sum(s["total_credits"] for s in plan["semesters"])

    profile_dict = profile.model_dump()
    val_report = independent_validator.validate_plan(plan, profile_dict)

    with get_db_cursor() as cur:
        cur.execute("SELECT MAX(version_number) as max_v FROM plan_versions WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        next_v = (row["max_v"] or 1) + 1
        plan_diff = {
            "action": "drop_course",
            "semester": req.semester,
            "course": req.course_code,
            "credits_before": cur_credits,
            "credits_after": sem_obj["total_credits"],
            "description": f"Dropped {req.course_code} ({course_credits} cr) from Semester {req.semester}"
        }
        cur.execute("""
        INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
        VALUES (?, ?, ?, ?, ?)
        """, (student_id, next_v, json.dumps(plan), json.dumps(plan_diff), json.dumps(val_report)))

    return {
        "success": True,
        "message": f"Dropped {req.course_code} from Semester {req.semester}.",
        "plan": plan,
        "diff": plan_diff,
        "validation_report": val_report,
        "credits_before": cur_credits,
        "credits_after": sem_obj["total_credits"]
    }

@router.post("/{student_id}/courses/swap")
def swap_course_in_semester(student_id: str, req: PlanCourseSwapRequest) -> Dict[str, Any]:
    """Swaps an elective with another eligible course."""
    drop_res = drop_course_from_semester(student_id, PlanCourseDropRequest(semester=req.semester, course_code=req.drop_code))
    try:
        add_res = add_course_to_semester(student_id, PlanCourseAddRequest(semester=req.semester, course_code=req.add_code))
        return {
            "success": True,
            "message": f"Successfully swapped {req.drop_code} for {req.add_code} in Semester {req.semester}.",
            "plan": add_res["plan"],
            "validation_report": add_res["validation_report"]
        }
    except Exception as exc:
        # Revert drop if add failed
        add_course_to_semester(student_id, PlanCourseAddRequest(semester=req.semester, course_code=req.drop_code))
        raise exc
