"""
Domain and Pydantic models for the Knowledge Base and Student system.
Provides type safety across API endpoints, planner, and evaluators.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ----------------- KNOWLEDGE BASE SCHEMAS -----------------

class CourseBase(BaseModel):
    code: str
    title: str
    department: str
    credits: float
    semester_offered: str  # 'odd', 'even', 'both'
    course_type: str       # 'core', 'elective', 'open', 'humanities', 'minor'
    mode: str = "offline"  # 'offline', 'online'
    level: str = "undergraduate"
    workload_hours_per_week: float = 10.0
    syllabus: str
    learning_objectives: str
    source: str
    last_verified: str

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    pass

class Prerequisite(BaseModel):
    course_code: str
    requires_code: str
    type: str = "hard"  # 'hard', 'soft', 'coreq'
    source: str

class Skill(BaseModel):
    skill_id: str
    name: str
    domain: str
    description: str
    parent_skill_id: Optional[str] = None
    source: str
    last_verified: str

class CourseSkill(BaseModel):
    course_code: str
    skill_id: str
    depth: str  # 'intro', 'intermediate', 'advanced'
    weight: float = 1.0

class Module(BaseModel):
    module_id: str
    course_code: str
    order: int
    title: str
    text: str
    est_minutes: int = 60
    skill_ids: List[str] = Field(default_factory=list)
    source: str

class Resource(BaseModel):
    resource_id: str
    title: str
    provider: str  # 'NPTEL', 'SWAYAM', 'MIT OCW', 'NCERT', 'Coursera'
    url: str
    license: str = "Open Access / CC-BY"
    format: str = "video"  # 'video', 'notes', 'problem_set'
    difficulty: str = "intermediate"
    est_minutes: int = 45
    credit_eligible: bool = False
    skill_ids: List[str] = Field(default_factory=list)
    source: str
    last_verified: str

class Exercise(BaseModel):
    exercise_id: str
    skill_id: str
    module_id: str
    type: str  # 'mcq', 'short', 'code', 'project', 'case'
    difficulty: int = 3  # 1 to 5
    prompt: str
    answer_key: Dict[str, Any] = Field(default_factory=dict)
    source: str

class AcademicRule(BaseModel):
    rule_id: str
    name: str
    type: str  # 'credit_cap_min', 'credit_cap_max', 'minor_eligibility', 'online_credit_limit', 'prereq_policy'
    parameters: Dict[str, Any]
    source_text: str
    source_url: str

class GoalTemplate(BaseModel):
    goal_id: str
    name: str
    target_role: str
    typical_duration_semesters: int = 4
    required_skills: List[Dict[str, Any]] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    source: str

class Programme(BaseModel):
    code: str
    name: str
    department: str
    total_credits: int
    semesters: int = 8
    core_credits: int
    elective_credits: int
    open_credits: int
    structure: Dict[str, Any] = Field(default_factory=dict)
    source: str
    last_verified: str

