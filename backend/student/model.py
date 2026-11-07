"""
Student Profile & Evidence Store Domain Models.
Manages student academic records, completed courses, constraints, and granular evidence history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pydantic import BaseModel, Field
from backend.db.database import get_db_cursor
from backend.config import load_evidence_config

class CompletedCourse(BaseModel):
    course_code: str
    grade: str  # e.g. "A", "A-", "B", "B-", "C", "D", "F"
    semester_completed: int = 1

class StudentProfile(BaseModel):
    student_id: str
    name: str
    programme: str  # e.g. "iit_bhilai_btech_cse_2023"
    year: int = 2
    current_semester: int = 4
    cgpa: float = Field(default=8.0, ge=0.0, le=10.0)
    goal_id: str = "goal_software"
    target_role: Optional[str] = None
    available_hours_per_week: float = Field(default=10.0, ge=0.0, le=80.0)
    remaining_elective_slots: Optional[int] = 4
    completed_courses: List[CompletedCourse] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)

class EvidenceEvent(BaseModel):
    student_id: str
    skill_id: str
    value: float  # 0.0 to 1.0 (score or mastery signal)
    source_type: str  # grade, assessed_diagnostic, quiz, timed_project, self_declared, inferred_course
    confidence: float = 1.0
    item_ref: Optional[str] = None
    timestamp: Optional[str] = None

class StudySessionCreate(BaseModel):
    course_code: str
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    module_id: Optional[str] = None
    notes: Optional[str] = None
    session_date: Optional[str] = None

class StudySessionRecord(BaseModel):
    id: int
    student_id: str
    course_code: str
    duration_minutes: int
    module_id: Optional[str] = None
    notes: Optional[str] = None
    session_date: str
    created_at: Optional[str] = None

class StudentStore:
    """Persistence manager for student profiles and evidence events in SQLite / Postgres."""
    
    @staticmethod
    def save_profile(profile: StudentProfile) -> None:
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT OR REPLACE INTO student_profiles (
                student_id, name, programme, year, current_semester, cgpa,
                goal_id, target_role, available_hours_per_week, remaining_elective_slots,
                completed_courses_json, constraints_json, preferences_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                profile.student_id,
                profile.name,
                profile.programme,
                profile.year,
                profile.current_semester,
                profile.cgpa,
                profile.goal_id,
                profile.target_role or "",
                profile.available_hours_per_week,
                profile.remaining_elective_slots,
                json.dumps([c.model_dump() for c in profile.completed_courses]),
                json.dumps(profile.constraints),
                json.dumps({
                    "interests": profile.interests,
                    **profile.preferences
                })
            ))

    @staticmethod
    def get_profile(student_id: str) -> Optional[StudentProfile]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM student_profiles WHERE student_id = ?", (student_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            completed_raw = json.loads(data.get("completed_courses_json", "[]"))
            completed = [CompletedCourse(**c) for c in completed_raw]
            pref_data = json.loads(data.get("preferences_json", "{}"))
            interests = pref_data.pop("interests", [])
            
            return StudentProfile(
                student_id=data["student_id"],
                name=data["name"],
                programme=data["programme"],
                year=data["year"],
                current_semester=data["current_semester"],
                cgpa=data["cgpa"],
                goal_id=data["goal_id"],
                target_role=data["target_role"],
                available_hours_per_week=data["available_hours_per_week"],
                remaining_elective_slots=data["remaining_elective_slots"],
                completed_courses=completed,
                interests=interests,
                constraints=json.loads(data.get("constraints_json", "{}")),
                preferences=pref_data
            )

    @staticmethod
    def get_all_profiles() -> List[StudentProfile]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM student_profiles ORDER BY student_id")
            rows = cur.fetchall()
        profiles = []
        for row in rows:
            data = dict(row)
            completed = [
                CompletedCourse(**course)
                for course in json.loads(data.get("completed_courses_json", "[]"))
            ]
            preferences = json.loads(data.get("preferences_json", "{}"))
            interests = preferences.pop("interests", [])
            profiles.append(StudentProfile(
                student_id=data["student_id"],
                name=data["name"],
                programme=data["programme"],
                year=data["year"],
                current_semester=data["current_semester"],
                cgpa=data["cgpa"],
                goal_id=data["goal_id"],
                target_role=data["target_role"],
                available_hours_per_week=data["available_hours_per_week"],
                remaining_elective_slots=data["remaining_elective_slots"],
                completed_courses=completed,
                interests=interests,
                constraints=json.loads(data.get("constraints_json", "{}")),
                preferences=preferences
            ))
        return profiles

    @staticmethod
    def add_evidence(event: EvidenceEvent) -> None:
        cfg = load_evidence_config()
        weights = cfg.get("evidence_weights", {})
        # Scale event confidence by source type reliability weight
        rel_weight = weights.get(event.source_type, 0.5)
        effective_conf = min(1.0, event.confidence * rel_weight)

        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO evidence_events (student_id, skill_id, value, source_type, confidence, item_ref)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (event.student_id, event.skill_id, event.value, event.source_type, effective_conf, event.item_ref))

    @staticmethod
    def get_evidence_for_student(student_id: str, skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM evidence_events WHERE student_id = ?"
        params = [student_id]
        if skill_id:
            query += " AND skill_id = ?"
            params.append(skill_id)
        query += " ORDER BY timestamp ASC"

        with get_db_cursor() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def log_study_session(student_id: str, session: StudySessionCreate) -> int:
        session_date = session.session_date or datetime.now().strftime("%Y-%m-%d")
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO study_sessions (student_id, course_code, module_id, duration_minutes, notes, session_date)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (
                student_id,
                session.course_code,
                session.module_id,
                session.duration_minutes,
                session.notes,
                session_date,
            ))
            cur.execute("SELECT id FROM study_sessions WHERE student_id = ? ORDER BY id DESC LIMIT 1;", (student_id,))
            row = cur.fetchone()
            return int(row["id"] if isinstance(row, dict) else row[0])

    @staticmethod
    def get_study_sessions(student_id: str, days: Optional[int] = None) -> List[Dict[str, Any]]:
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT * FROM study_sessions WHERE student_id = ? ORDER BY session_date DESC, id DESC",
                (student_id,)
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def get_weekly_study_metrics(student_id: str) -> Dict[str, Any]:
        """Calculates total hours studied and session count from logged study sessions."""
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT duration_minutes, session_date FROM study_sessions WHERE student_id = ?",
                (student_id,)
            )
            rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return {"weekly_hours_studied": None, "session_count": 0}
        total_mins = sum(int(r["duration_minutes"]) for r in rows)
        total_hours = round(total_mins / 60.0, 1)
        return {
            "weekly_hours_studied": total_hours,
            "session_count": len(rows),
        }
