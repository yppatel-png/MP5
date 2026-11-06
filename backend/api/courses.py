"""
Knowledge Base API Endpoints.
Exposes courses, prerequisite graphs, skills, academic rules, and goal templates.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from backend.db.database import get_db_cursor

router = APIRouter(prefix="/courses", tags=["Knowledge Base"])

@router.get("")
def list_courses(
    department: Optional[str] = None,
    course_type: Optional[str] = None,
    semester_offered: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists courses with optional filtering."""
    query = "SELECT * FROM courses WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if course_type:
        query += " AND course_type = ?"
        params.append(course_type)
    if semester_offered:
        query += " AND (semester_offered = ? OR semester_offered = 'both')"
        params.append(semester_offered)

    with get_db_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

@router.get("/{code}")
def get_course_detail(code: str) -> Dict[str, Any]:
    """Retrieves full course detail including prerequisites, modules, and taught skills."""
    code_norm = code.upper().replace(" ", "")
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM courses WHERE code = ?", (code_norm,))
        course_row = cur.fetchone()
        if not course_row:
            raise HTTPException(status_code=404, detail=f"Course code '{code}' not found in catalogue.")

        course_data = dict(course_row)

        # Fetch prerequisites
        cur.execute("SELECT requires_code, type FROM prerequisites WHERE course_code = ?", (code_norm,))
        course_data["prerequisites"] = [dict(r) for r in cur.fetchall()]

        # Fetch skills
        cur.execute("""
        SELECT cs.skill_id, s.name, cs.depth, cs.weight 
        FROM course_skills cs
        JOIN skills s ON cs.skill_id = s.skill_id
        WHERE cs.course_code = ?
        """, (code_norm,))
        course_data["skills"] = [dict(r) for r in cur.fetchall()]

        # Fetch modules
        cur.execute("SELECT module_id, module_order, title, text, est_minutes, skill_ids_json FROM modules WHERE course_code = ? ORDER BY module_order ASC", (code_norm,))
        mods = []
        for r in cur.fetchall():
            m_dict = dict(r)
            m_dict["skill_ids"] = json.loads(m_dict.pop("skill_ids_json"))
            mods.append(m_dict)
        course_data["modules"] = mods

        return course_data

# Additional endpoints for skills, rules, and goal templates
kb_router = APIRouter(prefix="", tags=["Knowledge Base"])

@kb_router.get("/skills")
def list_skills() -> List[Dict[str, Any]]:
    """Returns all verified skill nodes."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM skills ORDER BY domain, name")
        return [dict(r) for r in cur.fetchall()]

@kb_router.get("/rules")
def list_academic_rules() -> List[Dict[str, Any]]:
    """Returns all active academic policy rules."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM academic_rules")
        res = []
        for r in cur.fetchall():
            d = dict(r)
            d["parameters"] = json.loads(d.pop("parameters_json"))
            res.append(d)
        return res

@kb_router.get("/goals")
def list_goal_templates() -> List[Dict[str, Any]]:
    """Returns predefined goal templates for career and post-graduation pathways."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM goal_templates")
        res = []
        for r in cur.fetchall():
            d = dict(r)
            d["required_skills"] = json.loads(d.pop("required_skills_json"))
            d["milestones"] = json.loads(d.pop("milestones_json"))
            res.append(d)
        return res

@kb_router.get("/programmes")
def list_programmes() -> List[Dict[str, Any]]:
    """Returns degree structures and credit requirement rules."""
    with get_db_cursor() as cur:
        cur.execute("SELECT * FROM programmes")
        res = []
        for r in cur.fetchall():
            d = dict(r)
            d["structure"] = json.loads(d.pop("structure_json"))
            res.append(d)
        return res
