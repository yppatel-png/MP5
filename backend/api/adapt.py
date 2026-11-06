"""
Adaptation & Simulation API Endpoints.
Enables real-time simulation of student performance signals, policy evaluation,
course overrides, and live before/after plan diffing for evaluators and students.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
from backend.adapt.policy import adaptation_policy_engine
from backend.adapt.simulator import adaptation_simulator, SCRIPTED_SCENARIOS
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_institute_profile

router = APIRouter(prefix="/adapt", tags=["Dynamic Adaptation & Simulation"])

class SimulateScenarioRequest(BaseModel):
    scenario_id: str
    student_id: Optional[str] = "S1024"
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CourseOverrideRequest(BaseModel):
    student_id: str = "S1024"
    rejected_course: str = "COL362"
    reason: Optional[str] = "Student preference"

class SignalEvaluationRequest(BaseModel):
    student_id: str = "S1024"
    signals: Dict[str, Any]

@router.get("/scenarios")
def list_simulation_scenarios() -> Dict[str, Any]:
    """Returns the catalog of one-click scripted demo scenarios for evaluators."""
    if get_institute_profile() == "iit_bhilai":
        return {
            "count": 0,
            "scenarios": [],
            "message": "Legacy academic-plan simulations are disabled for the IIT Bhilai curriculum profile.",
        }
    return {
        "count": len(SCRIPTED_SCENARIOS),
        "scenarios": SCRIPTED_SCENARIOS
    }

@router.post("/simulate")
def simulate_scenario(req: SimulateScenarioRequest) -> Dict[str, Any]:
    """
    Executes a scripted simulation scenario, injects synthetic activity,
    evaluates policy, and returns before/after plan diffs and explanations.
    """
    if get_institute_profile() == "iit_bhilai":
        raise HTTPException(
            status_code=409,
            detail="Academic-plan simulations are not verified for the IIT Bhilai curriculum profile.",
        )
    try:
        result = adaptation_simulator.execute_scenario(
            scenario_id=req.scenario_id,
            student_id=req.student_id or "S1024",
            params=req.params
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/override")
def submit_course_override(req: CourseOverrideRequest) -> Dict[str, Any]:
    """
    Handles a student course rejection override.
    Re-solves the multi-semester plan with the exclusion constraint and details trade-offs.
    """
    if get_institute_profile() == "iit_bhilai":
        raise HTTPException(
            status_code=409,
            detail="Course overrides are not verified for the IIT Bhilai curriculum profile.",
        )
    try:
        return adaptation_simulator.run_course_override(
            student_id=req.student_id,
            rejected_course=req.rejected_course
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override re-solve failed: {str(e)}")

@router.post("/evaluate")
def evaluate_adaptation_signals(req: SignalEvaluationRequest) -> Dict[str, Any]:
    """
    Evaluates raw student performance/behavioral signals against active adaptation rules
    and returns recommended policy actions.
    """
    actions = adaptation_policy_engine.evaluate_signals(
        student_id=req.student_id,
        signals=req.signals
    )
    return {
        "student_id": req.student_id,
        "actions_triggered_count": len(actions),
        "actions": [a.model_dump() for a in actions]
    }

@router.get("/history/{student_id}")
def get_adaptation_audit_log(student_id: str) -> Dict[str, Any]:
    """Returns historical adaptation decisions and audit trail for a student."""
    with get_db_cursor() as cur:
        cur.execute("""
        SELECT id, trigger_signal, action_type, plan_diff_json, explanation, created_at
        FROM adaptation_events
        WHERE student_id = ?
        ORDER BY created_at DESC;
        """, (student_id,))
        rows = cur.fetchall()

    records = []
    for r in rows:
        records.append({
            "id": r["id"],
            "trigger_signal": r["trigger_signal"],
            "action_type": r["action_type"],
            "plan_diff": json.loads(r["plan_diff_json"]) if r["plan_diff_json"] else {},
            "explanation": r["explanation"],
            "created_at": str(r["created_at"])
        })

    return {
        "student_id": student_id,
        "total_events": len(records),
        "events": records
    }
