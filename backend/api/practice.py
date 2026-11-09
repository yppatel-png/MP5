"""
Practice & Mastery API Endpoints.
Handles exercise execution, sandboxed grading, dynamic question generation,
and comprehensive mastery/readiness evaluations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.practice.runner import exercise_runner
from backend.practice.generator import question_generator
from backend.practice.mastery import mastery_engine
from backend.student.model import StudentStore
from backend.config import settings

router = APIRouter(prefix="/practice", tags=["Learn, Practise & Mastery"])

class ExerciseSubmissionModel(BaseModel):
    student_id: str
    exercise_id: str
    selected_option: Optional[str] = None
    code: Optional[str] = Field(default=None, max_length=20000)
    submitted_code: Optional[str] = Field(default=None, max_length=20000)
    text_answer: Optional[str] = None
    repo_url: Optional[str] = None
    summary: Optional[str] = None
    time_spent_seconds: int = 60
    hints_used: int = 0

class QuestionGenerationRequest(BaseModel):
    module_id: str
    skill_id: Optional[str] = None
    difficulty: int = 3

class ExerciseListItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    exercise_id: str
    title: Optional[str] = None
    prompt: str
    difficulty: int = 2
    type: str
    skill_id: str
    starter_code: Optional[str] = None
    options: List[str] = Field(default_factory=list)

@router.get("/exercises", response_model=List[ExerciseListItem])
def list_exercises(
    skill_id: Optional[str] = None,
    module_id: Optional[str] = None,
    exercise_type: Optional[str] = None,
    student_id: Optional[str] = None,
    skip_mastered: bool = False
) -> List[Dict[str, Any]]:
    """Lists practice exercises with optional filters. Can skip mastered content for a student."""
    results = list(exercise_runner.exercises.values())
    if skill_id:
        results = [e for e in results if e["skill_id"] == skill_id]
    if module_id:
        results = [e for e in results if e["module_id"] == module_id]
    if exercise_type:
        results = [e for e in results if e["type"] == exercise_type]

    if student_id and skip_mastered:
        from backend.student.diagnostic import diagnostic_engine
        skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
        mastered_skills = {
            sk for sk, d in skill_matrix.items()
            if d.get("mastered", False) and d.get("evidence_source") == "assessed"
        }
        results = [e for e in results if e["skill_id"] not in mastered_skills]
    
    # Sanitize: don't reveal answer_key in exercise list!
    sanitized = []
    for ex in results:
        copy_ex = dict(ex)
        ans = copy_ex.get("answer_key", {})
        copy_ex["options"] = ans.get("options", [])
        copy_ex.pop("answer_key", None)
        copy_ex["skill_name"] = exercise_runner.skills.get(copy_ex.get("skill_id", ""), {}).get("name", copy_ex.get("skill_id", ""))
        if not copy_ex.get("title"):
            first_line = copy_ex["prompt"].split("\n")[0].strip()
            if len(first_line) > 60:
                first_line = first_line[:57] + "..."
            copy_ex["title"] = first_line
        sanitized.append(copy_ex)
    return sanitized

@router.get("/assigned-content/{student_id}")
def get_assigned_content(student_id: str) -> Dict[str, Any]:
    """Returns recommended practice exercises for student, skipping mastered skills and reporting why."""
    from backend.student.diagnostic import diagnostic_engine
    skill_matrix = diagnostic_engine.get_full_skill_matrix(student_id)
    mastered_skills = {
        sk: d for sk, d in skill_matrix.items()
        if d.get("mastered", False) and d.get("evidence_source") == "assessed"
    }

    all_exercises = list(exercise_runner.exercises.values())
    assigned = []
    skipped = []

    for ex in all_exercises:
        sk = ex.get("skill_id", "")
        if sk in mastered_skills:
            skipped.append({
                "exercise_id": ex["exercise_id"],
                "skill_id": sk,
                "reason": f"Skipped: Skill '{sk}' is already verified as mastered by student ({mastered_skills[sk].get('evidence_count', 0)} assessed items)."
            })
        else:
            assigned.append(ex)

    return {
        "student_id": student_id,
        "assigned_exercises_count": len(assigned),
        "skipped_mastered_count": len(skipped),
        "skipped": skipped[:10],
        "assigned": [
            {
                "exercise_id": e["exercise_id"],
                "skill_id": e["skill_id"],
                "title": e.get("title") or e["prompt"][:50],
                "type": e["type"],
                "difficulty": e.get("difficulty", 2)
            }
            for e in assigned[:20]
        ]
    }

@router.get("/resources")
def list_resources(skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns curated educational resources mapped to skills."""
    import json
    from backend.db.seed_profile import get_seed_dir
    seed_dir = get_seed_dir()
    with open(seed_dir / "resources.json", "r", encoding="utf-8") as f:
        all_res = json.load(f)
    if skill_id:
        return [r for r in all_res if skill_id in r.get("skill_ids", [])]
    return all_res

@router.get("/exercises/{exercise_id}")
def get_exercise_detail(exercise_id: str) -> Dict[str, Any]:
    """Retrieves exercise prompt and metadata (without leaking answer)."""
    ex = exercise_runner.exercises.get(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail=f"Exercise '{exercise_id}' not found.")
    
    clean = dict(ex)
    clean["options"] = clean.get("answer_key", {}).get("options", [])
    clean.pop("answer_key", None)
    if not clean.get("title"):
        first_line = clean["prompt"].split("\n")[0].strip()
        if len(first_line) > 60:
            first_line = first_line[:57] + "..."
        clean["title"] = first_line
    return clean

@router.post("/submit")
@router.post("/run")
def submit_exercise(sub: ExerciseSubmissionModel) -> Dict[str, Any]:
    """
    Evaluates exercise submission via deterministic or sandboxed execution,
    logs attempt in DB, and recalibrates student BKT skill mastery.
    """
    if not StudentStore.get_profile(sub.student_id):
        raise HTTPException(status_code=404, detail=f"Student ID '{sub.student_id}' not found.")

    import os
    import backend.config
    is_disabled = (
        os.getenv("DISABLE_CODE_EXERCISES", "").lower() in ("true", "1", "yes")
        if os.getenv("DISABLE_CODE_EXERCISES") is not None
        else getattr(backend.config.settings, "DISABLE_CODE_EXERCISES", True)
    )
    ex = exercise_runner.exercises.get(sub.exercise_id)
    if ex and ex.get("type") == "code" and is_disabled:
        skill_id = ex.get("skill_id", "")
        return {
            "exercise_id": sub.exercise_id,
            "exercise_type": "code",
            "skill_id": skill_id,
            "skill_name": exercise_runner.skills.get(skill_id, {}).get("name", skill_id),
            "score": 0.0,
            "is_correct": False,
            "feedback": (
                "Code exercise execution is disabled in safe mode. "
                "Please practice via conceptual MCQs, trace-the-output, and rubric-based exercises, "
                "or set DISABLE_CODE_EXERCISES=false to enable restricted execution (AST-filtered, not a full security boundary)."
            ),
            "explanation": "To enable restricted Python execution in your environment, configure DISABLE_CODE_EXERCISES=false in .env.",
            "details": {"disabled": True, "test_cases_passed": 0, "test_cases_total": 0},
            "passed": False,
            "test_cases_passed": 0,
            "test_cases_total": 0,
            "execution_time_ms": 0.0,
        }
    code_content = sub.code or sub.submitted_code
    submission_data = {
        "selected_option": sub.selected_option,
        "code": code_content,
        "text_answer": sub.text_answer,
        "repo_url": sub.repo_url,
        "summary": sub.summary
    }

    res = exercise_runner.evaluate_submission(
        student_id=sub.student_id,
        exercise_id=sub.exercise_id,
        submission=submission_data,
        time_spent_seconds=sub.time_spent_seconds,
        hints_used=sub.hints_used
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])

    details = res.get("details", {})
    # Enrich response for frontend test-runner display
    res["passed"] = res.get("is_correct", False)
    res["test_cases_passed"] = details.get("test_cases_passed", 1 if res.get("is_correct") else 0)
    res["test_cases_total"] = details.get("test_cases_total", 1)
    res["execution_time_ms"] = details.get("execution_time_ms", 12.5)
    return res

@router.post("/generate")
def generate_practice_question(req: QuestionGenerationRequest) -> Dict[str, Any]:
    """Generates a newly validated question grounded in module syllabus text."""
    return question_generator.generate_question(
        module_id=req.module_id,
        skill_id=req.skill_id,
        difficulty=req.difficulty
    )

@router.get("/mastery/{student_id}")
def get_student_mastery_report(
    student_id: str,
    goal_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns comprehensive mastery breakdown, explicitly distinguishing
    'Completed Course' from 'Demonstrated Proficiency', with 'What's Missing' checklist.
    """
    res = mastery_engine.compute_goal_readiness(student_id, goal_id=goal_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res
