"""Response models for the active curriculum plan API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.rules.certificate import PlanCertificate
from backend.student.summary import StudentSummary


class PlannedCourse(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    title: str
    credits: float
    course_type: str
    workload_hours_per_week: Optional[float] = None
    skills_targeted: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


class PlannedSemester(BaseModel):
    model_config = ConfigDict(extra="allow")

    semester_number: int
    total_credits: float
    courses: List[PlannedCourse]


class CurriculumPlan(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    student_id: str
    goal_id: str
    solver_engine: str
    total_credits_planned: float
    semesters_planned_count: int
    skills_covered: List[str]
    semesters: List[PlannedSemester]
    credit_cap: Optional[float] = None


class ActivePlanResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    student_id: str
    version_number: int
    plan: CurriculumPlan
    validation_report: Dict[str, Any]
    certificate: PlanCertificate
    diff: Dict[str, Any]
    student_summary: StudentSummary
    explanation: Optional[str] = None
    created_at: Optional[str] = None
