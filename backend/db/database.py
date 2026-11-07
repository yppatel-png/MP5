"""
Database Connection and Session Management.
Supports PostgreSQL as the single primary production database (via SQLAlchemy and psycopg2)
with full DDL/query translation and seed management, plus transparent local SQLite fallback.
"""

import os
import re
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, List, Dict
from backend.config import settings

logger = logging.getLogger("learning_buddy.database")

TABLE_CONFLICT_KEYS = {
    "programmes": ["code"],
    "courses": ["code"],
    "prerequisites": ["course_code", "requires_code"],
    "skills": ["skill_id"],
    "course_skills": ["course_code", "skill_id"],
    "modules": ["module_id"],
    "resources": ["resource_id"],
    "exercises": ["exercise_id"],
    "academic_rules": ["rule_id"],
    "goal_templates": ["goal_id"],
    "student_profiles": ["student_id"],
    "seed_provenance": ["entity_type", "entity_id"],
}

_engine = None
_engine_initialized = False
_is_postgres = False

def get_db_path() -> Path:
    raw_url = settings.DATABASE_URL
    if raw_url.startswith("sqlite:///"):
        path_str = raw_url.replace("sqlite:///", "", 1)
    else:
        from backend.config import BASE_DIR, DEFAULT_DATABASE_NAME
        path_str = str(BASE_DIR / "data" / DEFAULT_DATABASE_NAME)
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

DB_PATH: Optional[Path] = get_db_path()

def _get_engine():
    global _engine, _engine_initialized, _is_postgres
    if _engine_initialized:
        return _engine

    url = (settings.DATABASE_URL or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql://") or url.startswith("postgresql+psycopg2://"):
        try:
            from sqlalchemy import create_engine
            engine = create_engine(url, pool_pre_ping=True, future=True)
            with engine.connect() as test_conn:
                pass
            _engine = engine
            _is_postgres = True
            logger.info("Connected to PostgreSQL database at %s", url.split("@")[-1])
        except Exception as exc:
            logger.warning(
                "PostgreSQL database not reachable (%s); using local SQLite fallback for development/testing.",
                exc
            )
            _engine = None
            _is_postgres = False
    else:
        _engine = None
        _is_postgres = False

    _engine_initialized = True
    return _engine

def is_postgres() -> bool:
    _get_engine()
    return _is_postgres

def adapt_sql_for_postgres(sql: str) -> str:
    cleaned = sql.strip()

    # Adapt DROP TABLE IF EXISTS <tbl> [CASCADE]
    m_drop = re.match(r"^DROP\s+TABLE\s+IF\s+EXISTS\s+([a-zA-Z0-9_]+)\s*;?$", cleaned, re.IGNORECASE)
    if m_drop:
        tbl = m_drop.group(1)
        return f"DROP TABLE IF EXISTS {tbl} CASCADE;"

    # Adapt INSERT OR REPLACE INTO <tbl> (<cols>) VALUES (...)
    m_insert = re.match(r"^\s*INSERT\s+OR\s+REPLACE\s+INTO\s+([a-zA-Z0-9_]+)\s*\(([^)]+)\)", cleaned, re.IGNORECASE)
    if m_insert:
        tbl = m_insert.group(1).lower()
        cols = [c.strip() for c in m_insert.group(2).split(",")]
        keys = TABLE_CONFLICT_KEYS.get(tbl, [])
        update_cols = [c for c in cols if c not in keys]
        sql_base = re.sub(r"^\s*INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", cleaned, flags=re.IGNORECASE)
        sql_base = sql_base.rstrip().rstrip(";")
        if keys and update_cols:
            conflict_clause = f" ON CONFLICT ({', '.join(keys)}) DO UPDATE SET " + ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
            sql_base += conflict_clause
        elif keys:
            sql_base += f" ON CONFLICT ({', '.join(keys)}) DO NOTHING"
        cleaned = sql_base + ";"

    # Adapt CREATE TABLE auto-increment
    cleaned = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", cleaned, flags=re.IGNORECASE)
    # Adapt CREATE VIEW
    cleaned = re.sub(r"CREATE\s+VIEW\s+IF\s+NOT\s+EXISTS", "CREATE OR REPLACE VIEW", cleaned, flags=re.IGNORECASE)

    # Convert parameter placeholders from ? to %s
    return cleaned.replace("?", "%s")

class PostgresCursorWrapper:
    """Wraps a psycopg2 DictCursor to provide seamless parameter conversion and dict row mapping."""
    def __init__(self, raw_cursor):
        self._cur = raw_cursor

    def execute(self, query: str, params: Optional[Any] = None):
        adapted = adapt_sql_for_postgres(query)
        if params is not None:
            if isinstance(params, (list, tuple)):
                return self._cur.execute(adapted, params)
            elif isinstance(params, dict):
                return self._cur.execute(adapted, params)
            else:
                return self._cur.execute(adapted, (params,))
        return self._cur.execute(adapted)

    def executemany(self, query: str, seq_of_params):
        adapted = adapt_sql_for_postgres(query)
        return self._cur.executemany(adapted, seq_of_params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size) if size else self._cur.fetchmany()

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def __iter__(self):
        return iter(self._cur)

def get_connection():
    """Returns a database connection (PostgreSQL raw connection or SQLite connection)."""
    global DB_PATH
    default_path = get_db_path()
    if DB_PATH is not None and DB_PATH != default_path:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    engine = _get_engine()
    if _is_postgres and engine is not None:
        return engine.raw_connection()
    path = DB_PATH or default_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db_cursor():
    """Context manager for transactional database operations across PostgreSQL and SQLite."""
    conn = get_connection()
    if _is_postgres:
        import psycopg2.extras
        raw_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor = PostgresCursorWrapper(raw_cur)
    else:
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
    """Initializes all database tables and views if they do not exist."""
    _get_engine()
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

        # 12. Students View (ensures Adminer and external tooling view seeded students directly)
        cur.execute("CREATE VIEW IF NOT EXISTS students AS SELECT * FROM student_profiles;")

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

        # 13. Study Sessions Table (Item 6 activity log)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            module_id TEXT,
            duration_minutes INTEGER NOT NULL,
            notes TEXT,
            session_date DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE
        );
        """)
