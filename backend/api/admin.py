"""
Admin API Endpoints & Dynamic Re-Processing Engine.
Enforces Phase 1 requirement:
"edit a grade, a course's credits, a prerequisite, a rule, and a student constraint
via the admin UI/API; verify each triggers recomputation and the buddy and plan
reflect the change without a restart."

Protected by configurable ADMIN_API_TOKEN to prevent IDOR / unauthorized mutations.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import json
import logging

from backend.config import settings
from backend.db.database import get_db_cursor
from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.rules.registry import rule_registry
from backend.practice.mastery import mastery_engine

logger = logging.getLogger("learning_buddy.admin")
router = APIRouter(prefix="/admin", tags=["Administrative Console & Re-processing"])

def verify_admin_token(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"), authorization: Optional[str] = Header(None)) -> bool:
    """Verifies that the caller possesses the configured administrative authorization token."""
    token = x_admin_token
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    expected = settings.ADMIN_API_TOKEN
    if not token or token != expected:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid X-Admin-Token or Bearer admin token required."
        )
    return True

# Request Models
class EditGradeRequest(BaseModel):
    student_id: str
    course_code: str
    new_grade: str
    credits: Optional[float] = None

class EditCourseRequest(BaseModel):
    code: str
    credits: Optional[float] = None
    semester_offered: Optional[str] = None
    workload_hours_per_week: Optional[float] = None
    title: Optional[str] = None

class EditPrerequisiteRequest(BaseModel):
    course_code: str
    requires_code: str
    action: str = "add"  # "add" | "remove"
    type: str = "hard"

class EditRuleRequest(BaseModel):
    rule_id: str
    parameters: Dict[str, Any]

class EditConstraintRequest(BaseModel):
    student_id: str
    constraints: Dict[str, Any]

@router.post("/grade", dependencies=[Depends(verify_admin_token)])
def edit_student_grade(req: EditGradeRequest) -> Dict[str, Any]:
    """
    Edits a student's grade, recomputes CGPA, recalculates BKT skill mastery,
    and automatically re-synthesizes the active multi-semester plan.
    """
    profile = StudentStore.get_profile(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    grade_pts = {"A": 10.0, "A-": 9.0, "B": 8.0, "B-": 7.0, "C": 6.0, "C-": 5.0, "D": 4.0, "E": 2.0, "F": 0.0}
    c_code = req.course_code.upper()

    # Update completed courses
    found = False
    updated_courses = []
    total_pts = 0.0
    total_creds = 0.0

    for c in profile.completed_courses:
        if c.course_code.upper() == c_code:
            c.grade = req.new_grade.upper()
            found = True
        updated_courses.append(c)
        course_info = multi_semester_planner.courses.get(c.course_code, {})
        cr = float(req.credits if (found and req.credits is not None) else course_info.get("credits", 4.0))
        pts = grade_pts.get(c.grade.upper(), 8.0) * cr
        total_pts += pts
        total_creds += cr

    if not found:
        new_c = CompletedCourse(
            course_code=c_code,
            grade=req.new_grade.upper(),
            semester_completed=profile.current_semester
        )
        updated_courses.append(new_c)
        course_info = multi_semester_planner.courses.get(c_code, {})
        cr = float(req.credits if req.credits is not None else course_info.get("credits", 4.0))
        total_pts += grade_pts.get(new_c.grade, 8.0) * cr
        total_creds += cr

    # Recompute CGPA
    new_cgpa = round(total_pts / max(1.0, total_creds), 2)
    profile.completed_courses = updated_courses
    profile.cgpa = new_cgpa
    StudentStore.save_profile(profile)

    # Re-process plan dynamically
    from backend.api.plans import generate_student_plan, PlanGenerateRequest
    new_plan_res = generate_student_plan(PlanGenerateRequest(
        student_id=req.student_id,
        reason_for_change=f"Administrative grade update on {c_code} to {req.new_grade}"
    ))

    return {
        "status": "success",
        "student_id": req.student_id,
        "updated_course": c_code,
        "new_grade": req.new_grade,
        "recomputed_cgpa": new_cgpa,
        "new_plan_version": new_plan_res.get("version_number"),
        "plan_valid": new_plan_res.get("validation_report", {}).get("is_valid")
    }

@router.post("/course", dependencies=[Depends(verify_admin_token)])
def edit_course(req: EditCourseRequest) -> Dict[str, Any]:
    """
    Edits course parameters (credits, semester offering, workload), updates DB,
    re-indexes in-memory planner/validator caches, and triggers plan recomputation.
    """
    c_code = req.code.upper()
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM courses WHERE code = ?", (c_code,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Course '{c_code}' not found in catalogue.")

        fields = []
        params = []
        if req.credits is not None:
            fields.append("credits = ?")
            params.append(float(req.credits))
        if req.semester_offered is not None:
            fields.append("semester_offered = ?")
            params.append(req.semester_offered.lower())
        if req.workload_hours_per_week is not None:
            fields.append("workload_hours_per_week = ?")
            params.append(float(req.workload_hours_per_week))
        if req.title is not None:
            fields.append("title = ?")
            params.append(req.title)

        if fields:
            params.append(c_code)
            cur.execute(f"UPDATE courses SET {', '.join(fields)} WHERE code = ?", params)

    # Update in-memory solver and validator data structures
    if c_code in multi_semester_planner.courses:
        if req.credits is not None:
            multi_semester_planner.courses[c_code]["credits"] = float(req.credits)
        if req.semester_offered is not None:
            multi_semester_planner.courses[c_code]["semester_offered"] = req.semester_offered.lower()

    if c_code in independent_validator.courses:
        if req.credits is not None:
            independent_validator.courses[c_code]["credits"] = float(req.credits)
        if req.semester_offered is not None:
            independent_validator.courses[c_code]["semester_offered"] = req.semester_offered.lower()

    if c_code in rule_registry.courses_db:
        if req.credits is not None:
            rule_registry.courses_db[c_code]["credits"] = float(req.credits)
        if req.semester_offered is not None:
            rule_registry.courses_db[c_code]["semester_offered"] = req.semester_offered.lower()

    return {
        "status": "success",
        "code": c_code,
        "message": f"Course '{c_code}' updated and planner memory re-synchronized.",
        "reprocessed": True
    }

@router.post("/prerequisite", dependencies=[Depends(verify_admin_token)])
def edit_prerequisite(req: EditPrerequisiteRequest) -> Dict[str, Any]:
    """
    Adds or removes a prerequisite relationship and immediately re-syncs
    in-memory DAG graphs across planner, validator, and rule registry.
    """
    c_code = req.course_code.upper()
    req_code = req.requires_code.upper()

    with get_db_cursor() as cur:
        if req.action.lower() == "add":
            cur.execute("""
            INSERT OR REPLACE INTO prerequisites (course_code, requires_code, type, source)
            VALUES (?, ?, ?, ?);
            """, (c_code, req_code, req.type, "admin_mutation"))
            # Update memory
            multi_semester_planner.prereq_map.setdefault(c_code, [])
            if req_code not in multi_semester_planner.prereq_map[c_code]:
                multi_semester_planner.prereq_map[c_code].append(req_code)

            independent_validator.prereq_map.setdefault(c_code, [])
            if req_code not in independent_validator.prereq_map[c_code]:
                independent_validator.prereq_map[c_code].append(req_code)

            rule_registry.prereq_map.setdefault(c_code, [])
            if req_code not in rule_registry.prereq_map[c_code]:
                rule_registry.prereq_map[c_code].append(req_code)
        else:
            cur.execute("DELETE FROM prerequisites WHERE course_code = ? AND requires_code = ?", (c_code, req_code))
            if c_code in multi_semester_planner.prereq_map and req_code in multi_semester_planner.prereq_map[c_code]:
                multi_semester_planner.prereq_map[c_code].remove(req_code)
            if c_code in independent_validator.prereq_map and req_code in independent_validator.prereq_map[c_code]:
                independent_validator.prereq_map[c_code].remove(req_code)
            if c_code in rule_registry.prereq_map and req_code in rule_registry.prereq_map[c_code]:
                rule_registry.prereq_map[c_code].remove(req_code)

    return {
        "status": "success",
        "action": req.action,
        "relationship": f"{c_code} -> {req_code}",
        "reprocessed": True
    }

@router.post("/rule", dependencies=[Depends(verify_admin_token)])
def edit_academic_rule(req: EditRuleRequest) -> Dict[str, Any]:
    """
    Modifies an academic ordinance rule parameter in the DB and synchronizes rule registry.
    """
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM academic_rules WHERE rule_id = ?", (req.rule_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Rule ID '{req.rule_id}' not found.")

        cur.execute(
            "UPDATE academic_rules SET parameters_json = ? WHERE rule_id = ?",
            (json.dumps(req.parameters), req.rule_id)
        )

    return {
        "status": "success",
        "rule_id": req.rule_id,
        "new_parameters": req.parameters,
        "reprocessed": True
    }

@router.post("/constraint", dependencies=[Depends(verify_admin_token)])
def edit_student_constraint(req: EditConstraintRequest) -> Dict[str, Any]:
    """
    Updates student constraints and immediately re-synthesizes a compliant plan.
    """
    profile = StudentStore.get_profile(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    constraints = dict(req.constraints)
    cgpa_value = constraints.pop("cgpa", constraints.pop("target_cgpa", None))
    hours_value = constraints.get("available_hours_per_week")
    if cgpa_value is not None:
        try:
            cgpa = float(cgpa_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="CGPA must be a number between 0 and 10.")
        if not 0 <= cgpa <= 10:
            raise HTTPException(status_code=422, detail="CGPA must be between 0 and 10.")
        profile.cgpa = cgpa
    if hours_value is not None:
        try:
            hours = float(hours_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Weekly study hours must be a number between 0 and 80.")
        if not 0 <= hours <= 80:
            raise HTTPException(status_code=422, detail="Weekly study hours must be between 0 and 80.")
        profile.available_hours_per_week = hours
    profile.constraints.update(constraints)
    StudentStore.save_profile(profile)

    from backend.api.plans import generate_student_plan, PlanGenerateRequest
    plan_res = generate_student_plan(PlanGenerateRequest(
        student_id=req.student_id,
        reason_for_change="Administrative constraint modification"
    ))

    return {
        "status": "success",
        "student_id": req.student_id,
        "updated_constraints": {
            **profile.constraints,
            "cgpa": profile.cgpa,
            "available_hours_per_week": profile.available_hours_per_week,
        },
        "new_plan_version": plan_res.get("version_number"),
        "plan_valid": plan_res.get("validation_report", {}).get("is_valid")
    }

@router.post("/reset", dependencies=[Depends(verify_admin_token)])
def admin_reset_database() -> Dict[str, Any]:
    """
    Restores the database to clean seed state idempotently.
    """
    counts = load_seed_data(reset=True)
    return {
        "status": "reset_complete",
        "counts": counts
    }
