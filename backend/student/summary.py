"""Canonical student summary shared by planning, certification, and the buddy."""

import json
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel

from backend.config import load_evidence_config
from backend.db.seed_profile import get_seed_dir
from backend.student.model import StudentProfile, StudentStore

Status = Literal["insufficient_evidence", "on_track", "needs_attention", "behind"]
SEED_DIR = get_seed_dir()


class StudentSummary(BaseModel):
    student_id: str
    programme_code: str
    programme_name: str
    goal_name: str
    year: int
    semester_index: int
    cgpa: float
    weekly_hours_available: float
    weekly_hours_studied: Optional[float]
    credit_cap: Optional[float]
    planned_credits: Optional[float]
    credit_headroom: Optional[float]
    adherence_percentage: Optional[float]
    assessed_items_count: int
    min_assessed_items: int
    readiness_percentage: Optional[float]
    priority_gap_count: int
    status: Status
    status_message: str


def derive_student_status(
    assessed_items_count: int,
    min_assessed_items: int,
    adherence_percentage: Optional[float],
    priority_gap_count: int,
) -> Status:
    if assessed_items_count < 0:
        raise ValueError("assessed_items_count cannot be negative")
    if min_assessed_items <= 0:
        raise ValueError("min_assessed_items must be positive")
    if adherence_percentage is not None and not 0 <= adherence_percentage <= 100:
        raise ValueError("adherence_percentage must be between 0 and 100")
    if priority_gap_count < 0:
        raise ValueError("priority_gap_count cannot be negative")
    if assessed_items_count < min_assessed_items:
        return "insufficient_evidence"
    if priority_gap_count >= 2 or (adherence_percentage is not None and adherence_percentage < 50):
        return "behind"
    if priority_gap_count == 1 or adherence_percentage is None or adherence_percentage < 80:
        return "needs_attention"
    return "on_track"


def _programme_details(programme_code: str) -> dict[str, Any]:
    with open(SEED_DIR / "programmes.json", "r", encoding="utf-8") as file:
        programmes = json.load(file)
    programme = next(
        (item for item in programmes if item["code"] == programme_code),
        None,
    )
    if programme is None:
        raise ValueError(f"Unknown programme code in student profile: {programme_code}")
    return programme


def _status_message(
    status: Status,
    adherence_percentage: Optional[float],
    priority_gap_count: int,
) -> str:
    if status == "insufficient_evidence":
        return "Let's set your baseline: take the diagnostic so we can estimate readiness."
    if status == "behind":
        if adherence_percentage is not None and adherence_percentage < 50:
            return f"Your logged study pace is {adherence_percentage:g}%; let's reset this week's plan."
        return f"You have {priority_gap_count} priority gaps to address before you're on track."
    if status == "needs_attention":
        if adherence_percentage is None:
            return "Study activity hasn't been logged yet, so your pace can't be assessed."
        if adherence_percentage < 80:
            return f"Your logged study pace is {adherence_percentage:g}%; let's adjust your next step."
        return "One priority gap needs attention before you are on track."
    return f"You're on track with {adherence_percentage:g}% adherence and no priority gaps."


def build_student_summary(
    profile: StudentProfile,
    plan: Optional[dict[str, Any]],
    readiness_percentage: Optional[float],
    priority_gap_count: int,
    goal_name: Optional[str] = None,
    credit_cap: Optional[float] = None,
    adherence_percentage: Optional[float] = None,
    weekly_hours_studied: Optional[float] = None,
) -> StudentSummary:
    evidence_config = load_evidence_config()
    min_assessed_items = int(
        evidence_config.get("bkt_parameters", {}).get("min_items_required", 3)
    )
    assessment_refs = {
        event.get("item_ref") or f"event:{event.get('id')}"
        for event in StudentStore.get_evidence_for_student(profile.student_id)
        if event.get("source_type") == "assessed_diagnostic"
    }
    assessed_items_count = len(assessment_refs)

    programme = _programme_details(profile.programme)
    structure = programme.get("structure", {})
    active_credit_cap = credit_cap
    if active_credit_cap is None and structure.get("max_credits_per_semester") is not None:
        regular_cap = float(structure["max_credits_per_semester"])
        overload_cap = float(structure.get("overload_max_credits", regular_cap))
        overload_cgpa = float(structure.get("min_cgpa_for_overload", 8.5))
        active_credit_cap = overload_cap if profile.cgpa >= overload_cgpa else regular_cap

    semesters = (plan or {}).get("semesters", [])
    next_semester = semesters[0] if semesters else None
    planned_credits = (
        float(next_semester.get("total_credits", 0.0))
        if next_semester is not None
        else None
    )

    # Compute study metrics from study_sessions if not explicitly supplied
    if weekly_hours_studied is None and adherence_percentage is None:
        metrics = StudentStore.get_weekly_study_metrics(profile.student_id)
        weekly_hours_studied = metrics.get("weekly_hours_studied")
        if weekly_hours_studied is not None and profile.available_hours_per_week > 0:
            adherence_percentage = min(
                100.0,
                max(0.0, round((weekly_hours_studied / profile.available_hours_per_week) * 100.0, 1))
            )

    readiness = readiness_percentage if assessed_items_count >= min_assessed_items else None
    status = derive_student_status(
        assessed_items_count=assessed_items_count,
        min_assessed_items=min_assessed_items,
        adherence_percentage=adherence_percentage,
        priority_gap_count=priority_gap_count,
    )

    return StudentSummary(
        student_id=profile.student_id,
        programme_code=profile.programme,
        programme_name=programme["name"],
        goal_name=goal_name or profile.target_role or "Selected goal",
        year=profile.year,
        semester_index=profile.current_semester,
        cgpa=profile.cgpa,
        weekly_hours_available=profile.available_hours_per_week,
        weekly_hours_studied=weekly_hours_studied,
        credit_cap=float(active_credit_cap) if active_credit_cap is not None else None,
        planned_credits=planned_credits,
        credit_headroom=(
            float(active_credit_cap) - planned_credits
            if active_credit_cap is not None and planned_credits is not None
            else None
        ),
        adherence_percentage=adherence_percentage,
        assessed_items_count=assessed_items_count,
        min_assessed_items=min_assessed_items,
        readiness_percentage=readiness,
        priority_gap_count=priority_gap_count,
        status=status,
        status_message=_status_message(status, adherence_percentage, priority_gap_count),
    )
