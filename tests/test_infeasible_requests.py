"""
Tests for Infeasible Request Handling (§2.3).
Verifies that mathematically or regulatorily impossible requests:
1. Clearly say 'not possible'.
2. Name the exact blocking constraint / rule.
3. Offer a valid alternative plan or sequential bridge.
"""

import pytest
from backend.planner.infeasible import infeasible_handler
from backend.student.model import StudentStore, StudentProfile, CompletedCourse
from backend.db.seed_loader import load_seed_data


@pytest.fixture(scope="module", autouse=True)
def setup_students():
    load_seed_data(reset=True)
    # Ensure synthetic low-CGPA students exist
    StudentStore.save_profile(StudentProfile(
        student_id="BH-TEST-LOWCGPA-1",
        name="Test Ineligible Minor Student 1",
        programme="BH-CSE-BTECH",
        year=2,
        current_semester=3,
        cgpa=6.2,
        goal_id="goal_software",
        completed_courses=[CompletedCourse(course_code="CSL100", grade="B", semester=1, credits=4.5)],
        available_hours_per_week=15.0
    ))
    StudentStore.save_profile(StudentProfile(
        student_id="BH-TEST-LOWCGPA-2",
        name="Test Ineligible Minor Student 2",
        programme="BH-CSE-BTECH",
        year=2,
        current_semester=3,
        cgpa=5.8,
        goal_id="goal_higher_studies",
        completed_courses=[CompletedCourse(course_code="CSL100", grade="C", semester=1, credits=4.5)],
        available_hours_per_week=12.0
    ))


INFEASIBLE_SCENARIOS = [
    # 1. Excessive credits (32 credits requested by BH-SW-001)
    {
        "student_id": "BH-SW-001",
        "request_type": "excessive_credits",
        "kwargs": {"credits": 32.0},
        "expected_rule_id": "rule_sem_max_credits",
        "desc": "32 credits requested (exceeds semester cap)"
    },
    # 2. Excessive credits (30 credits requested by BH-HS-001)
    {
        "student_id": "BH-HS-001",
        "request_type": "excessive_credits",
        "kwargs": {"credits": 30.0},
        "expected_rule_id": "rule_sem_max_credits",
        "desc": "30 credits requested (exceeds semester cap)"
    },
    # 3. Missing prerequisite (CSL252 requires CSL100, CSL201, CSL202)
    {
        "student_id": "BH-TEST-LOWCGPA-1",
        "request_type": "missing_prerequisite",
        "kwargs": {"course_code": "CSL252"},
        "expected_rule_id": "rule_prereq_strict_enforcement",
        "desc": "CSL252 requested without CSL201/CSL202 prerequisites"
    },
    # 4. Missing prerequisite (CSL510 requires CSL252)
    {
        "student_id": "BH-TEST-LOWCGPA-2",
        "request_type": "missing_prerequisite",
        "kwargs": {"course_code": "CSL510"},
        "expected_rule_id": "rule_prereq_strict_enforcement",
        "desc": "CSL510 requested without CSL252 prerequisite"
    },
    # 5. Ineligible CS minor (CGPA 6.2 < 7.0 cutoff)
    {
        "student_id": "BH-TEST-LOWCGPA-1",
        "request_type": "ineligible_minor",
        "kwargs": {"discipline": "Computer Science"},
        "expected_rule_id": "rule_minor_cse_eligibility",
        "desc": "CS minor requested with CGPA 6.2 (< 7.0)"
    },
    # 6. Ineligible CS minor (CGPA 5.8 < 7.0 cutoff)
    {
        "student_id": "BH-TEST-LOWCGPA-2",
        "request_type": "ineligible_minor",
        "kwargs": {"discipline": "Computer Science"},
        "expected_rule_id": "rule_minor_cse_eligibility",
        "desc": "CS minor requested with CGPA 5.8 (< 7.0)"
    },
    # 7. Semester parity mismatch (Spring course CSL252 in Autumn Semester 5)
    {
        "student_id": "BH-SW-001",
        "request_type": "semester_parity",
        "kwargs": {"course_code": "CSL252", "target_semester": 5},
        "expected_rule_id": "rule_semester_parity",
        "desc": "Even-semester course requested in odd semester"
    },
    # 8. Semester parity mismatch (Autumn course CSL304 in Spring Semester 6)
    {
        "student_id": "BH-SW-001",
        "request_type": "semester_parity",
        "kwargs": {"course_code": "CSL304", "target_semester": 6},
        "expected_rule_id": "rule_semester_parity",
        "desc": "Odd-semester course requested in even semester"
    },
    # 9. Disallowed overload (CGPA 6.2 requesting 26 credits)
    {
        "student_id": "BH-TEST-LOWCGPA-1",
        "request_type": "disallowed_overload",
        "kwargs": {"credits": 26.0},
        "expected_rule_id": "rule_credit_overload_cap",
        "desc": "Credit overload requested with CGPA below 8.0"
    },
    # 10. Credit underload (6 credits requested, floor is 12)
    {
        "student_id": "BH-SW-001",
        "request_type": "credit_underload",
        "kwargs": {"credits": 6.0},
        "expected_rule_id": "rule_sem_min_credits",
        "desc": "6 credits requested (below 12 credit floor)"
    }
]


@pytest.mark.parametrize("scenario", INFEASIBLE_SCENARIOS, ids=[s["desc"] for s in INFEASIBLE_SCENARIOS])
def test_infeasible_request_detection_and_resolution(scenario):
    student_id = scenario["student_id"]
    req_type = scenario["request_type"]
    kwargs = scenario["kwargs"]
    expected_rule = scenario["expected_rule_id"]

    res = infeasible_handler.evaluate_request(student_id, req_type, **kwargs)

    # 1. System must return status infeasible
    assert res["status"] == "infeasible", f"Expected infeasible status for: {scenario['desc']}"

    # 2. System must explicitly say 'not possible'
    verdict = res.get("verdict", "").lower()
    explanation = res.get("explanation", "").lower()
    assert (verdict == "not possible" or "not possible" in explanation), (
        f"Response did not clearly state 'not possible': {res.get('explanation')}"
    )

    # 3. System must name the violated constraint / blocking rule
    blocking = res.get("blocking_rule", {})
    assert blocking.get("rule_id") == expected_rule, (
        f"Expected blocking rule {expected_rule}, got {blocking.get('rule_id')}"
    )
    assert blocking.get("rule_name"), "Blocking rule must have a human-readable name"

    # 4. System must offer a valid alternative
    alt = res.get("valid_alternative") or res.get("closest_valid_plan")
    assert alt is not None, f"System failed to provide a valid alternative for: {scenario['desc']}"
    if isinstance(alt, dict) and "summary" in alt:
        assert len(alt["summary"]) > 10, "Alternative summary must be descriptive"
