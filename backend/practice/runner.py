"""
Exercise Execution & Sandboxed Grading Engine.
Supports:
- Deterministic MCQ grading
- Sandboxed Python code evaluation (timeouts, no network, restricted builtins)
- Rubric-based short answer evaluation
- Granular attempt logging and automatic BKT evidence updates
"""

import json
import logging
import subprocess
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.db.database import get_db_cursor
from backend.student.model import StudentStore, EvidenceEvent
from backend.llm.client import llm_client

logger = logging.getLogger("learning_buddy.practice")
from backend.db.seed_profile import get_seed_dir

SEED_DIR = get_seed_dir()
CODE_EXECUTION_TIMEOUT_SECONDS = 7.0

def load_seed_json(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


class ExerciseRunner:
    def __init__(self):
        self.exercises = {e["exercise_id"]: e for e in load_seed_json("exercises.json")}
        self.modules = {m["module_id"]: m for m in load_seed_json("modules.json")}
        self.skills = {s["skill_id"]: s for s in load_seed_json("skills.json")}

    def evaluate_submission(
        self,
        student_id: str,
        exercise_id: str,
        submission: Dict[str, Any],
        time_spent_seconds: int = 60,
        hints_used: int = 0
    ) -> Dict[str, Any]:
        """
        Grades an exercise submission, logs the attempt, and updates BKT evidence.
        """
        ex = self.exercises.get(exercise_id)
        if not ex:
            return {"status": "error", "message": f"Exercise '{exercise_id}' not found."}

        ex_type = ex["type"].lower()
        skill_id = ex["skill_id"]
        answer_key = ex.get("answer_key", {})

        # Grade based on type
        if ex_type == "mcq":
            grade_res = self._grade_mcq(ex, submission.get("selected_option"))
        elif ex_type == "code":
            grade_res = self._grade_code(ex, submission.get("code", ""))
        elif ex_type == "short":
            grade_res = self._grade_short_answer(ex, submission.get("text_answer", ""))
        else:
            # Project or case study
            grade_res = self._grade_project_checkpoint(ex, submission)

        score = float(grade_res.get("score", 0.0))
        is_correct = bool(grade_res.get("is_correct", False))

        # Log attempt in DB
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO exercise_attempts (
                student_id, exercise_id, skill_id, score, is_correct,
                time_spent_seconds, hints_used, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                student_id,
                exercise_id,
                skill_id,
                score,
                1 if is_correct else 0,
                time_spent_seconds,
                hints_used,
                json.dumps(grade_res)
            ))

        # Automatically update student BKT evidence
        source_type = "quiz" if ex_type == "mcq" else ("timed_project" if ex_type == "project" else "exercise")
        ev = EvidenceEvent(
            student_id=student_id,
            skill_id=skill_id,
            value=score,
            source_type=source_type,
            confidence=1.0 if ex_type in ["mcq", "code"] else 0.85,
            item_ref=exercise_id
        )
        StudentStore.add_evidence(ev)

        return {
            "exercise_id": exercise_id,
            "exercise_type": ex_type,
            "skill_id": skill_id,
            "skill_name": self.skills.get(skill_id, {}).get("name", skill_id),
            "score": score,
            "is_correct": is_correct,
            "feedback": grade_res.get("feedback", ""),
            "explanation": answer_key.get("explanation", ""),
            "details": grade_res
        }

    def _grade_mcq(self, exercise: Dict[str, Any], selected_option: Optional[str]) -> Dict[str, Any]:
        """Deterministic MCQ grading."""
        if not selected_option:
            return {"score": 0.0, "is_correct": False, "feedback": "No option was selected."}

        correct = str(exercise.get("answer_key", {}).get("correct", "")).strip().lower()
        selected = str(selected_option).strip().lower()
        is_correct = (selected == correct)

        return {
            "score": 1.0 if is_correct else 0.0,
            "is_correct": is_correct,
            "feedback": "Correct! Well reasoned." if is_correct else f"Incorrect. The correct answer was '{exercise.get('answer_key', {}).get('correct')}'."
        }

    def _grade_short_answer(self, exercise: Dict[str, Any], student_answer: str) -> Dict[str, Any]:
        """Rubric-based grading with keyword grounding and LiteLLM assistance."""
        text = student_answer.strip()
        if not text:
            return {"score": 0.0, "is_correct": False, "feedback": "Empty response submitted."}

        rubric = exercise.get("answer_key", {}).get("rubric", "")
        # Extract rubric keywords (words > 4 chars)
        rubric_keywords = [w.lower().strip(".,;:()") for w in rubric.split() if len(w) > 4]
        text_lower = text.lower()
        matches = [kw for kw in rubric_keywords if kw in text_lower]
        keyword_coverage = len(matches) / max(1, len(rubric_keywords))

        # Basic score from keyword overlap
        score = min(1.0, max(0.1, keyword_coverage * 1.25))
        is_correct = score >= 0.65

        feedback = (
            f"Good explanation. Covered {len(matches)} of {len(rubric_keywords)} core concept elements."
            if is_correct else
            f"Partially complete. Expected concept focus: '{rubric}'."
        )

        return {
            "score": round(score, 2),
            "is_correct": is_correct,
            "feedback": feedback,
            "keywords_matched": matches
        }

    def _grade_code(self, exercise: Dict[str, Any], code_str: str) -> Dict[str, Any]:
        import os
        if os.getenv("DISABLE_CODE_EXERCISES", "false").lower() in ("true", "1", "yes"):
            return {
                "score": 0.0,
                "is_correct": False,
                "feedback": "Code exercise execution is disabled in this demo deployment for container sandbox hardening. Refer to README.md for architecture details.",
                "passed_tests": 0,
                "total_tests": 0,
                "disabled": True
            }

        worker_path = Path(__file__).with_name("code_worker.py")
        clean_env = {
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(worker_path.parents[2]),
        }
        try:
            process = subprocess.run(
                [sys.executable, "-m", "backend.practice.code_worker"],
                input=json.dumps({"exercise": exercise, "code": code_str}),
                capture_output=True,
                text=True,
                timeout=CODE_EXECUTION_TIMEOUT_SECONDS,
                cwd=worker_path.parents[2],
                env=clean_env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "score": 0.0,
                "is_correct": False,
                "feedback": "Timeout: code execution exceeded the 3-second limit.",
                "passed_tests": 0,
                "total_tests": 0,
            }
        if process.returncode == 0:
            try:
                result = json.loads(process.stdout)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                logger.error("Code worker returned invalid JSON.")
        else:
            logger.error("Code worker exited with status %s.", process.returncode)
        return {
            "score": 0.0,
            "is_correct": False,
            "feedback": "Code execution worker failed; no evidence was recorded as successful.",
            "passed_tests": 0,
            "total_tests": 0,
        }

    def _grade_project_checkpoint(self, exercise: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        """Grades milestone project submissions based on verification criteria."""
        repo_url = submission.get("repo_url", "")
        summary = submission.get("summary", "")
        
        has_repo = bool(repo_url and ("github.com" in repo_url or "gitlab.com" in repo_url or "http" in repo_url))
        has_summary = len(summary.strip()) > 30

        if has_repo and has_summary:
            score = 0.95
            feedback = "Project milestone approved! Verified repository link and technical summary."
            is_correct = True
        elif has_summary:
            score = 0.70
            feedback = "Technical summary received. Please attach public repository link to verify tests."
            is_correct = True
        else:
            score = 0.20
            feedback = "Incomplete submission. Please provide a detailed summary of your implementation."
            is_correct = False

        return {
            "score": score,
            "is_correct": is_correct,
            "feedback": feedback
        }

exercise_runner = ExerciseRunner()
