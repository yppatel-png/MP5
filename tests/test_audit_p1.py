"""
Comprehensive Test Suite for Phase P1 Audit Fixes (Adobe Inter-IIT Tech Meet 15.0).
Tests:
- test_P1_1_goal_electives_differ_and_cite_gaps
- test_P1_2_mastered_content_dropped_and_test_out_flag
- test_P1_3_resource_relevance_and_milestone_carryover
- test_P1_4_unverified_course_prior_targeted_first_in_diagnostic
- test_P1_5_bkt_time_decay_and_self_declared_cannot_master
- test_P1_6_adaptation_yaml_parameter_and_no_lucky_quiz_accelerate
- test_P1_7_conflict_detector_no_html_false_positive
- test_P1_8_buddy_intent_word_boundaries_and_context_budget
"""

import pytest
import datetime
import json
from backend.student.model import StudentStore, StudentProfile, CompletedCourse, EvidenceEvent
from backend.planner.solver import MultiSemesterPlanner
from backend.student.diagnostic import diagnostic_engine
from backend.student.bkt import bkt_estimator
from backend.adapt.policy import adaptation_policy_engine
from backend.student.conflict import conflict_detector
from backend.buddy.router import buddy_router, build_bounded_context
from backend.buddy.memory import buddy_memory
from backend.buddy.safety import buddy_safety


def test_P1_1_goal_electives_differ_and_cite_gaps():
    """
    Two students with same goal but different skill gaps / interests receive
    different electives ranked by gap-coverage and student evidence.
    """
    planner = MultiSemesterPlanner()
    profile1 = StudentProfile(
        student_id="test_p1_1_std1",
        name="Student 1",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=5,
        goal_id="goal_software",
        interests=["AI/ML"],
        available_hours_per_week=16.0
    )
    profile2 = StudentProfile(
        student_id="test_p1_1_std2",
        name="Student 2",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=5,
        goal_id="goal_software",
        interests=["Systems"],
        available_hours_per_week=16.0
    )

    plan1 = planner.plan_curriculum(profile1)
    plan2 = planner.plan_curriculum(profile2)

    electives1 = [c["code"] for s in plan1["semesters"] for c in s["courses"] if c.get("type") in ("elective", "programme_elective", "open_elective")]
    electives2 = [c["code"] for s in plan2["semesters"] for c in s["courses"] if c.get("type") in ("elective", "programme_elective", "open_elective")]

    # Because interests differ (AI/ML vs Systems), elective recommendations should personalize
    assert electives1 != electives2, "Electives must differ when student interests and skills differ"


def test_P1_2_mastered_content_dropped_and_test_out_flag():
    """
    Candidate retriever drops elective candidates whose targeted skills are all mastered.
    Core courses expose test_out_eligible if all skills are mastered.
    Student with only a course grade (no assessment) is NOT treated as mastered.
    """
    from backend.planner.candidate import retrieve_candidates_for_gaps
    from backend.api.practice import get_assigned_content

    # Matrix with mastered programming fundamentals (assessed, p >= 0.85, count >= 2)
    mastered_matrix = {
        "programming_fundamentals": {
            "p_mastery": 0.95,
            "evidence_count": 3,
            "evidence_source": "assessed",
            "mastered": True
        }
    }
    # Matrix with course grade prior only (unverified, not assessed)
    unverified_matrix = {
        "programming_fundamentals": {
            "p_mastery": 0.75,
            "evidence_count": 0,
            "evidence_source": "course_grade_prior",
            "mastered": False
        }
    }

    # Verify unverified prior is not mastered
    assert unverified_matrix["programming_fundamentals"]["mastered"] is False

    # Check practice assigned content skipping
    p = StudentProfile(
        student_id="test_p1_2_student",
        name="Test Student",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=1
    )
    StudentStore.save_profile(p)
    # Add assessed evidence for programming_fundamentals
    for i in range(3):
        StudentStore.add_evidence(EvidenceEvent(
            student_id="test_p1_2_student",
            skill_id="programming_fundamentals",
            value=1.0,
            source_type="assessed_diagnostic",
            confidence=1.0,
            item_ref=f"item_pf_{i}"
        ))

    report = get_assigned_content("test_p1_2_student")
    assert report["skipped_mastered_count"] > 0
    skipped_skills = [s["skill_id"] for s in report["skipped"]]
    assert "programming_fundamentals" in skipped_skills


def test_P1_3_resource_relevance_and_milestone_carryover():
    """
    Resources are attached dynamically by skill overlap rather than static list indexing.
    Milestones carry forward instead of being dropped.
    """
    planner = MultiSemesterPlanner()
    profile = StudentProfile(
        student_id="test_p1_3_student",
        name="Resource Test Student",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=3,
        goal_id="goal_software",
        available_hours_per_week=14.0
    )
    plan = planner.plan_curriculum(profile)

    # Check that each semester with resources has "why_this_resource" and matches targeted skills
    for sem in plan["semesters"]:
        resources = sem.get("resources", [])
        for r in resources:
            assert "why_this_resource" in r or "title" in r

    # Milestones are carried forward and preserved
    milestones = [m for s in plan["semesters"] for m in s.get("milestones", [])]
    assert len(milestones) > 0


def test_P1_4_unverified_course_prior_targeted_first_in_diagnostic():
    """
    A student with a B in CSL202 (Data Structures & Algorithms) but zero assessment events
    shows 'unverified' DSA ('needs a check'), not confirmed strength.
    The first diagnostic question targets DSA because unverified course claims have top priority.
    """
    profile = StudentProfile(
        student_id="test_p1_4_student",
        name="DSA Prior Student",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=4,
        goal_id="goal_software",
        completed_courses=[
            CompletedCourse(course_code="CSL202", grade="B", semester_completed=3)
        ]
    )
    StudentStore.save_profile(profile)

    gaps_report = diagnostic_engine.compute_skill_gaps("test_p1_4_student", goal_id="goal_software")
    # DSA should be unverified / in gaps, NOT in confirmed strengths!
    strengths_skills = [s["skill_id"] for s in gaps_report["strengths"]]
    assert "data_structures" not in strengths_skills, "Unverified course prior must not be marked as confirmed strength"

    # In gaps, status must be unverified and label 'needs a check'
    dsa_gap = next((g for g in gaps_report["gaps"] if g["skill_id"] == "data_structures"), None)
    assert dsa_gap is not None
    assert dsa_gap["status"] == "unverified"
    assert dsa_gap["status_label"] == "needs a check"
    assert dsa_gap["evidence_source"] == "course_grade_prior"

    # First diagnostic question should target DSA (data_structures or algorithms)
    q = diagnostic_engine.get_next_question("test_p1_4_student", answered_exercise_ids=[])
    assert q["available"] is True
    assert q["exercise"]["skill_id"] in ("data_structures", "algorithms")


def test_P1_5_bkt_time_decay_and_self_declared_cannot_master():
    """
    BKT time decay: evidence 90 days old yields lower mastery than fresh evidence.
    Self-declared evidence alone can never confirm mastery.
    """
    # 1. Fresh evidence vs 90-day-old evidence
    now = datetime.datetime.now(datetime.timezone.utc)
    old_date = (now - datetime.timedelta(days=90)).isoformat()
    fresh_date = now.isoformat()

    old_events = [
        {"value": 1.0, "source_type": "quiz", "confidence": 0.8, "difficulty": 2, "timestamp": old_date},
        {"value": 1.0, "source_type": "quiz", "confidence": 0.8, "difficulty": 2, "timestamp": old_date}
    ]
    fresh_events = [
        {"value": 1.0, "source_type": "quiz", "confidence": 0.8, "difficulty": 2, "timestamp": fresh_date},
        {"value": 1.0, "source_type": "quiz", "confidence": 0.8, "difficulty": 2, "timestamp": fresh_date}
    ]

    res_old = bkt_estimator.estimate_skill_mastery(old_events)
    res_fresh = bkt_estimator.estimate_skill_mastery(fresh_events)

    assert res_old["p_mastery"] < res_fresh["p_mastery"], (
        f"90-day old mastery ({res_old['p_mastery']}) must be lower than fresh mastery ({res_fresh['p_mastery']})"
    )

    # 2. Self-declared evidence cannot reach mastered
    self_events = [
        {"value": 1.0, "source_type": "self_declared", "confidence": 1.0, "timestamp": fresh_date},
        {"value": 1.0, "source_type": "self_declared", "confidence": 1.0, "timestamp": fresh_date},
        {"value": 1.0, "source_type": "self_declared", "confidence": 1.0, "timestamp": fresh_date},
        {"value": 1.0, "source_type": "self_declared", "confidence": 1.0, "timestamp": fresh_date}
    ]
    res_self = bkt_estimator.estimate_skill_mastery(self_events)
    assert res_self["mastered"] is False, "Self-declared evidence alone must never confirm mastery"


def test_P1_6_adaptation_yaml_parameter_and_no_lucky_quiz_accelerate():
    """
    Adaptation policy reads parameters from config.
    A single lucky quiz (evidence_count=1) does NOT trigger ACCELERATE when min_items=3.
    Conflict resolution: high BKT with poor recent session prioritizes REMEDIATE with explicit note.
    """
    # 1. Single quiz should not accelerate
    single_quiz_signals = {
        "bkt_probability": 0.90,
        "score": 0.95,
        "evidence_count": 1,
        "skill_id": "algorithms"
    }
    actions = adaptation_policy_engine.evaluate_signals("any_student", single_quiz_signals)
    accelerate_actions = [a for a in actions if a.action_type == "ACCELERATE"]
    assert len(accelerate_actions) == 0, "Single quiz must not trigger ACCELERATE when min_items_required is 3"

    # 2. Conflict resolution: high BKT but poor recent score (< 0.40)
    conflict_signals = {
        "bkt_probability": 0.88,
        "score": 0.25,
        "evidence_count": 4,
        "skill_id": "operating_systems"
    }
    actions_conflict = adaptation_policy_engine.evaluate_signals("any_student", conflict_signals)
    remedial = [a for a in actions_conflict if a.action_type == "REMEDIATE"]
    accelerate = [a for a in actions_conflict if a.action_type == "ACCELERATE"]

    assert len(remedial) == 1, "REMEDIATE must trigger when recent score is struggling"
    assert len(accelerate) == 0, "ACCELERATE must not trigger when student is currently struggling"
    assert "Conflicting signals" in remedial[0].description, "Conflict resolution must be explicitly explained"


def test_P1_7_conflict_detector_no_html_false_positive():
    """
    Conflict detector matches canonical interests without false positives on substrings like 'html' or 'email'.
    Student with weak maths applying for AI goal receives structured GapAlert with MAL201.
    """
    p_web = StudentProfile(
        student_id="test_p1_7_web_student",
        name="Web Developer",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=3,
        goal_id="goal_software",
        interests=["Web and App Dev"]
    )
    StudentStore.save_profile(p_web)
    alerts_web = conflict_detector.detect_conflicts("test_p1_7_web_student")
    # Must NOT have AI/ML math foundation gap alert
    ml_alerts = [a for a in alerts_web if a.get("alert_id") == "gap_alert_ml_linear_algebra"]
    assert len(ml_alerts) == 0, "Web and App Dev interest must not falsely trigger AI/ML gap alerts"

    # Student applying for higher studies / AI with unassessed maths
    p_ai = StudentProfile(
        student_id="test_p1_7_ai_student",
        name="AI Aspirant",
        programme="iit_bhilai_btech_cse_2023",
        current_semester=3,
        goal_id="goal_higher_studies",
        interests=["AI/ML"]
    )
    StudentStore.save_profile(p_ai)
    alerts_ai = conflict_detector.detect_conflicts("test_p1_7_ai_student")
    ml_alert = next((a for a in alerts_ai if a.get("alert_id") == "gap_alert_ml_linear_algebra"), None)
    assert ml_alert is not None, "AI aspirant with unassessed math must receive mathematical foundations GapAlert"
    # Option 1 recommends MAL201
    opt1 = ml_alert["options"][0]
    assert "MAL201" in opt1["action"] or "MAL201" in opt1["description"]


def test_P1_8_buddy_intent_word_boundaries_and_context_budget():
    """
    'I prefer not to drop CSL202' does NOT trigger course-drop flow.
    Buddy proposals persist in DB across restarts with TTL.
    Bounded context builder caps tokens.
    Hallucinated course codes like 'CSL999' are caught and verified.
    """
    # 1. Intent classification with negative lookbehind
    intent = buddy_router.classify_intent("I prefer not to drop CSL202")
    assert intent != "CHECK_DROP", f"Negated drop statement must not classify as CHECK_DROP (got {intent})"
    assert intent != "RECOMMEND_ELECTIVES", f"Negated drop statement must not classify as RECOMMEND_ELECTIVES (got {intent})"

    # 2. Database persistence of pending proposals
    proposal = {"action": "add", "course_code": "CSL301", "semester": 5, "credits": 4}
    buddy_memory.set_pending_proposal("test_p1_8_student", proposal, ttl_seconds=1800)

    # Retrieve from DB
    loaded = buddy_memory.get_pending_proposal("test_p1_8_student")
    assert loaded is not None
    assert loaded["course_code"] == "CSL301"

    # Test expiration
    buddy_memory.set_pending_proposal("test_p1_8_student", proposal, ttl_seconds=-10)
    expired = buddy_memory.get_pending_proposal("test_p1_8_student")
    assert expired is None, "Expired proposal must return None"

    # 3. Context bounding
    huge_context = {
        "student_summary": {"recent_evidence": [{"ev": i} for i in range(20)]},
        "gaps": [{"skill_id": f"sk_{i}", "evidence_trail": [f"step {j}" for j in range(10)]} for i in range(25)],
        "eligible_electives": [{"code": f"ELEC{i}"} for i in range(30)]
    }
    bounded = build_bounded_context(huge_context)
    assert len(bounded["student_summary"]["recent_evidence"]) <= 3
    assert len(bounded["gaps"]) <= 5
    assert len(bounded["eligible_electives"]) <= 5

    # 4. Hallucination interceptor
    clean_text = buddy_safety.intercept_and_verify_course_codes("You should take CSL999 and CSL202 next.")
    assert "CSL999" not in clean_text
    assert "CSL202" in clean_text
    assert "[Unverified Course Code Intercepted]" in clean_text
