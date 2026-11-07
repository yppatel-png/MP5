"""
Database Connection and Session Management.
Supports native SQLite with JSON support and relational foreign keys enabled,
with transparent connection management.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from backend.config import settings

DB_PATH = Path(settings.DATABASE_URL.replace("sqlite:///", ""))

def get_db_path() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row_factory as dict and foreign keys enabled."""
    path = get_db_path()
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_cursor():
    """Context manager for transactional database operations."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes all database tables if they do not exist."""
    with get_db_cursor() as cur:
        # 1. Programmes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS programmes (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            total_credits REAL NOT NULL,
            semesters INTEGER NOT NULL,
            core_credits REAL NOT NULL,
            elective_credits REAL NOT NULL,
            open_credits REAL NOT NULL,
            structure_json TEXT NOT NULL,
            source TEXT NOT NULL,
            last_verified TEXT NOT NULL
        );
        """)

        # 2. Courses
        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            credits REAL NOT NULL,
            semester_offered TEXT NOT NULL,
            course_type TEXT NOT NULL,
            mode TEXT NOT NULL,
            level TEXT NOT NULL,
            workload_hours_per_week REAL,
            syllabus TEXT,
            learning_objectives TEXT,
            source TEXT NOT NULL,
            last_verified TEXT NOT NULL
        );
        """)

        # 3. Prerequisites
        cur.execute("""
        CREATE TABLE IF NOT EXISTS prerequisites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            requires_code TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'hard',
            source TEXT NOT NULL,
            FOREIGN KEY (course_code) REFERENCES courses (code) ON DELETE CASCADE,
            FOREIGN KEY (requires_code) REFERENCES courses (code) ON DELETE CASCADE,
            UNIQUE(course_code, requires_code)
        );
        """)

        # 4. Skills
        cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            skill_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            description TEXT NOT NULL,
            parent_skill_id TEXT,
            source TEXT NOT NULL,
            last_verified TEXT NOT NULL
        );
        """)

        # 5. Course Skills Mapping
        cur.execute("""
        CREATE TABLE IF NOT EXISTS course_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            depth TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            FOREIGN KEY (course_code) REFERENCES courses (code) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE CASCADE,
            UNIQUE(course_code, skill_id)
        );
        """)

        # 6. Modules
        cur.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            module_id TEXT PRIMARY KEY,
            course_code TEXT NOT NULL,
            module_order INTEGER NOT NULL,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            est_minutes INTEGER NOT NULL,
            skill_ids_json TEXT NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY (course_code) REFERENCES courses (code) ON DELETE CASCADE
        );
        """)

        # 7. Resources (OER: NPTEL, SWAYAM, MIT OCW, etc.)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            resource_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            provider TEXT NOT NULL,
            url TEXT NOT NULL,
            license TEXT NOT NULL,
            format TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            est_minutes INTEGER NOT NULL,
            credit_eligible INTEGER NOT NULL DEFAULT 0,
            skill_ids_json TEXT NOT NULL,
            source TEXT NOT NULL,
            last_verified TEXT NOT NULL
        );
        """)

        # 8. Exercises
        cur.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            exercise_id TEXT PRIMARY KEY,
            skill_id TEXT NOT NULL,
            module_id TEXT NOT NULL,
            type TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            answer_key_json TEXT NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE CASCADE,
            FOREIGN KEY (module_id) REFERENCES modules (module_id) ON DELETE CASCADE
        );
        """)

        # 9. Academic Rules
        cur.execute("""
        CREATE TABLE IF NOT EXISTS academic_rules (
            rule_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            source_text TEXT NOT NULL,
            source_url TEXT NOT NULL
        );
        """)

        # 10. Goal Templates
        cur.execute("""
        CREATE TABLE IF NOT EXISTS goal_templates (
            goal_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            target_role TEXT NOT NULL,
            typical_duration_semesters INTEGER NOT NULL,
            required_skills_json TEXT NOT NULL,
            milestones_json TEXT NOT NULL,
            source TEXT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS seed_provenance (
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            provenance TEXT NOT NULL,
            source_page TEXT,
            confidence REAL,
            reason TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            PRIMARY KEY (entity_type, entity_id)
        );
        """)

        # 11. Student Profiles & Evidence Tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            programme TEXT NOT NULL,
            year INTEGER NOT NULL,
            current_semester INTEGER NOT NULL,
            cgpa REAL NOT NULL,
            goal_id TEXT,
            target_role TEXT,
            available_hours_per_week REAL NOT NULL DEFAULT 10.0,
            remaining_elective_slots INTEGER DEFAULT 4,
            completed_courses_json TEXT NOT NULL DEFAULT '[]',
            constraints_json TEXT NOT NULL DEFAULT '{}',
            preferences_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS evidence_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            value REAL NOT NULL,
            source_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            item_ref TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS plan_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            plan_json TEXT NOT NULL,
            diff_from_previous_json TEXT,
            validation_report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            tools_called_json TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS exercise_attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            skill_id TEXT NOT NULL,
            score REAL NOT NULL,
            is_correct INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            time_spent_seconds INTEGER NOT NULL DEFAULT 60,
            hints_used INTEGER NOT NULL DEFAULT 0,
            details_json TEXT NOT NULL DEFAULT '{}',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS adaptation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            trigger_signal TEXT NOT NULL,
            action_type TEXT NOT NULL,
            before_state_json TEXT,
            after_state_json TEXT,
            plan_diff_json TEXT,
            explanation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE
        );
        """)

