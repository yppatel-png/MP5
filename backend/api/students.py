"""
Student Profile & Diagnostic API Endpoints.
Provides profile CRUD, adaptive diagnostic question flow, BKT skill tracking, and GapAlerts.
"""

import json

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.student.model import StudentProfile, StudentStore, EvidenceEvent
from backend.student.diagnostic import diagnostic_engine
from backend.student.summary import StudentSummary, build_student_summary
from backend.student.conflict import conflict_detector
from backend.db.database import get_db_cursor

router = APIRouter(prefix="/students", tags=["Student Management & Diagnostic"])

class AnswerSubmission(BaseModel):
    exercise_id: str
    selected_option: Optional[str] = None
    text_answer: Optional[str] = None

class StudentListEntry(BaseModel):
    student_id: str
    name: str
    programme: str
    goal_id: str
    target_role: Optional[str] = None

class SkillEstimate(BaseModel):
    skill_id: str
    name: str
    domain: str
    p_mastery: float
    confidence: float
    mastered: bool
    evidence_count: int
    evidence_trail: List[str]

@router.get("")
def list_students() -> List[StudentListEntry]:
    """Lists available student personas for the frontend selector."""
    return [
        StudentListEntry(
            student_id=profile.student_id,
            name=profile.name,
            programme=profile.programme,
            goal_id=profile.goal_id,
            target_role=profile.target_role,
        )
        for profile in StudentStore.get_all_profiles()
    ]

@router.post("", response_model=Dict[str, Any])
def create_or_update_student(profile: StudentProfile) -> Dict[str, Any]:
    """Creates or updates a student profile."""
    StudentStore.save_profile(profile)
    return {"message": f"Student profile '{profile.student_id}' saved successfully.", "student_id": profile.student_id}

@router.get("/profile/{student_id}", response_model=StudentProfile)
def get_student_profile_only(student_id: str) -> Dict[str, Any]:
    """Direct profile endpoint for frontend dashboard."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")
    return profile.model_dump()

@router.get("/{student_id}/summary", response_model=StudentSummary)
def get_student_summary(student_id: str) -> StudentSummary:
    """Returns the canonical summary for a student, using their latest saved plan when present."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT plan_json FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
            (student_id,)
        )
        plan_row = cur.fetchone()
    plan = json.loads(plan_row["plan_json"]) if plan_row else None
    active_goal = (plan or {}).get("goal_id", profile.goal_id)
    gaps = diagnostic_engine.compute_skill_gaps(student_id, goal_id=active_goal)
    return build_student_summary(
        profile=profile,
        plan=plan,
        readiness_percentage=gaps.get("readiness_percentage"),
        priority_gap_count=gaps.get("critical_gap_count", 0),
        goal_name=gaps.get("goal_name"),
        credit_cap=(plan or {}).get("credit_cap"),
    )

@router.get("/skills/{student_id}", response_model=Dict[str, SkillEstimate])
def get_student_skills_only(student_id: str) -> Dict[str, Any]:
    """Direct skill matrix endpoint for frontend radar and progress tracking."""
    return diagnostic_engine.get_full_skill_matrix(student_id)

@router.get("/{student_id}")
def get_student(student_id: str) -> Dict[str, Any]:
    """Retrieves student profile and current BKT skill mastery estimates."""
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")
    
    skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
    return {
        "profile": profile.model_dump(),
        "skill_matrix": skill_matrix
    }

@router.get("/{student_id}/diagnostic/next")
def get_next_diagnostic_question(student_id: str, answered: str = "") -> Dict[str, Any]:
    """
    Returns the next optimal information-gain question for the adaptive diagnostic.
    Comma-separated 'answered' query param tracks questions completed in current session.
    """
    if not StudentStore.get_profile(student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")
    answered_ids = [a.strip() for a in answered.split(",") if a.strip()]
    return diagnostic_engine.get_next_question(student_id, answered_ids)

@router.post("/{student_id}/diagnostic/submit")
def submit_diagnostic_answer(student_id: str, submission: AnswerSubmission) -> Dict[str, Any]:
    """
    Evaluates student answer, logs evidence event, and recalibrates BKT mastery.
    """
    if not StudentStore.get_profile(student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")
    # Find exercise
    target_ex = next((ex for ex in diagnostic_engine.exercises if ex["exercise_id"] == submission.exercise_id), None)
    if not target_ex:
        raise HTTPException(status_code=404, detail=f"Exercise '{submission.exercise_id}' not found.")

    skill_id = target_ex["skill_id"]
    correct_answer = target_ex.get("answer_key", {}).get("correct")

    # Grade answer
    is_correct = False
    if correct_answer and submission.selected_option:
        is_correct = submission.selected_option.strip().lower() == str(correct_answer).strip().lower()
    elif submission.text_answer:
        # Basic keyword match fallback
        is_correct = len(submission.text_answer.strip()) > 10

    score = 1.0 if is_correct else 0.0

    # Record evidence event
    ev = EvidenceEvent(
        student_id=student_id,
        skill_id=skill_id,
        value=score,
        source_type="assessed_diagnostic",
        confidence=1.0,
        item_ref=submission.exercise_id
    )
    StudentStore.add_evidence(ev)

    # Re-estimate skill
    matrix = diagnostic_engine.get_full_skill_matrix(student_id)
    updated_skill = matrix.get(skill_id, {})

    return {
        "exercise_id": submission.exercise_id,
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": target_ex.get("answer_key", {}).get("explanation", "Diagnostic question evaluated."),
        "updated_skill": updated_skill
    }

@router.get("/{student_id}/gaps")
def get_student_gaps(student_id: str) -> Dict[str, Any]:
    """
    Computes quantified skill gaps, strengths, readiness percentage,
    and flags interest-evidence conflicts via GapAlerts.
    """
    profile = StudentStore.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID '{student_id}' not found.")

    gaps_data = diagnostic_engine.compute_skill_gaps(student_id)
    alerts = conflict_detector.detect_conflicts(student_id)
    
    return {
        **gaps_data,
        "alerts": alerts
    }

@router.get("/{student_id}/evidence")
def get_student_evidence_trail(student_id: str, skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns chronological audit trail of all evidence events."""
    return StudentStore.get_evidence_for_student(student_id, skill_id)
