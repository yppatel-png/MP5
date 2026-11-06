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
from backend.student.summary import build_student_summary
from backend.planner.schemas import ActivePlanResponse
from backend.db.seed_profile import get_institute_profile

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

def require_supported_planning() -> None:
    if get_institute_profile() == "iit_bhilai":
        raise HTTPException(
            status_code=409,
            detail=(
                "Personalized degree planning and academic-rule certification are "
                "disabled for the IIT Bhilai demo because the supplied source does "
                "not establish prerequisites, elective eligibility, or semester credit limits."
            ),
        )

@router.post("/generate")
def generate_student_plan(req: PlanGenerateRequest) -> Dict[str, Any]:
    """
    Generates a provably valid multi-semester course plan, validates it via RuleRegistry,
    generates a sealed cryptographic PlanCertificate, creates a versioned snapshot,
    and returns a factual explanation.
    """
    require_supported_planning()
    profile = StudentStore.get_profile(req.student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{req.student_id}' not found.")

    # Check for infeasible credit requests first
    if req.credit_cap_override and req.credit_cap_override > 24.0:
        return infeasible_handler.handle_excessive_credit_request(req.student_id, req.credit_cap_override)

    active_goal = req.goal_override or profile.goal_id
    credit_cap = req.credit_cap_override or (24.0 if profile.cgpa >= 8.5 else 22.0)

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
        max_weekly_hours=profile.available_hours_per_week,
        overload_allowed=(profile.cgpa >= 8.5)
    )
    effective_credit_cap = 24.0 if profile.cgpa >= 8.5 else credit_cap
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
    require_supported_planning()
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
    require_supported_planning()
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
    require_supported_planning()
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
    require_supported_planning()
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
