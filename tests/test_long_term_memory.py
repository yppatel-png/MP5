"""
Integration Test for Long-Term Memory and Cross-Session Persistence (§2.5).
Verifies that:
1. Student profile attributes (goal, CGPA, completed courses) persist.
2. Multi-turn Buddy conversations are stored in DB and survive session restart.
3. Plan version history (baseline and adapted plans with diffs) persists.
4. Buddy memory synthesis ('What I remember about you') retains past decisions.
5. Operates across SQLite and PostgreSQL databases.
"""

import os
import json
import pytest
from pathlib import Path

from backend.db.database import get_db_cursor, is_postgres
from backend.db.seed_loader import load_seed_data
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.buddy.memory import buddy_memory
from backend.buddy.router import buddy_router
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.llm.client import llm_client


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    load_seed_data(reset=True)
    # Ensure offline mode for fast, deterministic LLM calls during tests
    llm_client.offline = True


def test_long_term_memory_and_session_restart():
    test_student_id = "BH-TEST-MEM-001"

    # Step 1: Create student profile with explicit career goal
    profile = StudentProfile(
        student_id=test_student_id,
        name="Ananya Sharma",
        programme="BH-CSE-BTECH",
        year=3,
        current_semester=5,
        cgpa=8.45,
        goal_id="goal_software",
        target_role="Full Stack & Systems Engineer",
        available_hours_per_week=16.0,
        completed_courses=[
            CompletedCourse(course_code="CSL100", grade="A", semester=1, credits=4.5),
            CompletedCourse(course_code="CSL201", grade="A-", semester=3, credits=4.0),
            CompletedCourse(course_code="CSL202", grade="B", semester=3, credits=4.0),
            CompletedCourse(course_code="CSL251", grade="A", semester=4, credits=4.0),
            CompletedCourse(course_code="CSL252", grade="B+", semester=4, credits=4.0),
        ]
    )
    StudentStore.save_profile(profile)

    # Step 2: Generate baseline plan (Version 1) and record in DB
    plan_v1 = multi_semester_planner.plan_curriculum(
        student_id=test_student_id,
        programme_code=profile.programme,
        current_semester=profile.current_semester,
        cgpa=profile.cgpa,
        completed_courses=[c.course_code for c in profile.completed_courses],
        skill_gaps=[],
        goal_id=profile.goal_id,
        credit_cap=22.0
    )
    val_v1 = independent_validator.validate_plan(plan_v1, profile.model_dump())
    assert val_v1["is_valid"], f"Baseline plan validation failed: {val_v1.get('errors')}"

    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_student_id,
            1,
            json.dumps(plan_v1),
            None,
            json.dumps(val_v1)
        ))

    # Step 3: Hold multi-turn Buddy conversation
    # Turn 1: Goal inquiry
    turn1 = buddy_router.handle_message(
        test_student_id,
        "What are my priority skill gaps for my software engineering goal?"
    )
    assert turn1["intent"] == "SKILL_GAPS"
    assert turn1["facts_used"]

    # Turn 2: Course decision & override discussion
    turn2 = buddy_router.handle_message(
        test_student_id,
        "I don't want to take CSL301 next semester, what are the trade-offs?"
    )
    assert turn2["intent"] == "OVERRIDE_COURSE"

    # Turn 3: Plan adaptation (Version 2) with recorded diff
    plan_v2 = dict(plan_v1)
    plan_v2["version"] = 2
    plan_diff = {
        "reason": "Student requested course override for CSL301; deferred to semester 7",
        "courses_added": ["CSL304"],
        "courses_removed": ["CSL301"],
        "credit_delta": 0.0
    }
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_student_id,
            2,
            json.dumps(plan_v2),
            json.dumps(plan_diff),
            json.dumps(val_v1)
        ))

    # Turn 4: Asking why the plan changed
    turn4 = buddy_router.handle_message(
        test_student_id,
        "Why did my plan change?"
    )
    assert turn4["intent"] == "PLAN_DIFF"

    # Step 4: Simulate Application / Session Restart
    # By querying purely from clean DB cursors, bypassing any in-memory references
    persisted_profile = StudentStore.get_profile(test_student_id)
    assert persisted_profile is not None
    assert persisted_profile.name == "Ananya Sharma"
    assert persisted_profile.goal_id == "goal_software"
    assert persisted_profile.cgpa == 8.45
    assert len(persisted_profile.completed_courses) == 5

    # Step 5: Verify Plan Version History cross-session
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT version_number, plan_json, diff_from_previous_json
            FROM plan_versions
            WHERE student_id = ?
            ORDER BY version_number ASC
        """, (test_student_id,))
        rows = cur.fetchall()

    assert len(rows) == 2, f"Expected 2 plan versions, found {len(rows)}"
    assert rows[0]["version_number"] == 1
    assert rows[0]["diff_from_previous_json"] is None
    assert rows[1]["version_number"] == 2
    assert "deferred to semester 7" in rows[1]["diff_from_previous_json"]

    # Step 6: Verify Conversational History in chat_memory
    recent_history = buddy_memory.get_recent_history(test_student_id, limit=20)
    assert len(recent_history) >= 6, f"Expected at least 6 turns (user+assistant), got {len(recent_history)}"

    user_messages = [t["content"] for t in recent_history if t["role"] == "user"]
    assert any("priority skill gaps" in m for m in user_messages)
    assert any("trade-offs" in m for m in user_messages)
    assert any("Why did my plan change" in m for m in user_messages)

    # Step 7: Verify 'What I remember about you' memory facts synthesis
    memory_facts = buddy_memory.get_student_memory_facts(test_student_id)
    assert memory_facts["known"] is True
    assert memory_facts["student_name"] == "Ananya Sharma"
    assert memory_facts["goal"] == "goal_software"
    # Past decisions must be reflected
    facts_str = " ".join(memory_facts["facts"])
    assert "Software" in facts_str
    assert "Has explored course overrides and trade-off comparisons." in memory_facts["facts"]

    print("\n[SUCCESS] Long-term memory integration test passed:")
    print(f"  - Database engine: {'PostgreSQL' if is_postgres() else 'SQLite'}")
    print(f"  - Profile persisted: {persisted_profile.student_id} ({persisted_profile.name})")
    print(f"  - Plan versions persisted: {len(rows)} versions with diff history")
    print(f"  - Chat memory turns: {len(recent_history)} turns persisted")
    print(f"  - Memory facts synthesized: {len(memory_facts['facts'])} facts including past decisions")
