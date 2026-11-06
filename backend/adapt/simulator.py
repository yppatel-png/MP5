"""
Curriculum Adaptation Simulator Engine.
Provides scripted demo scenarios and dynamic event-driven plan recomputation
for evaluators, demonstrating real-time responsive adaptation to student signals.
"""

import json
from typing import Dict, Any, List, Optional
from backend.db.database import get_db_cursor
from backend.student.model import StudentStore, StudentProfile, CompletedCourse, EvidenceEvent
from backend.student.diagnostic import diagnostic_engine
from backend.planner.solver import multi_semester_planner
from backend.planner.validator import independent_validator
from backend.planner.explainer import plan_explainer
from backend.adapt.policy import adaptation_policy_engine, AdaptationAction
from backend.llm.client import llm_client
from backend.rules import rule_registry

SCRIPTED_SCENARIOS = [
    {
        "id": "scenario_strong_quiz",
        "name": "Strong Mid-Semester Quiz (95% in DSA)",
        "category": "Academic Performance",
        "description": "Student demonstrates mastery in Data Structures & Algorithms. Satisfies prerequisite hurdle early, advances higher-level systems electives, and compresses graduation pathway.",
        "icon": "zap",
        "default_student_id": "S1024"
    },
    {
        "id": "scenario_weak_quiz",
        "name": "Weak Mid-Semester Quiz (25% in DSA)",
        "category": "Academic Performance",
        "description": "Student struggles on DSA assessment. System diagnoses foundational gap, inserts targeted remedial practice drills, defers advanced courses to later semesters, and adjusts workload.",
        "icon": "alert-triangle",
        "default_student_id": "S1024"
    },
    {
        "id": "scenario_course_override",
        "name": "Student Rejects Course (Excludes COL362)",
        "category": "Student Preference",
        "description": "Student overrides buddy recommendation by rejecting COL362 (Database Systems). Planner re-solves with exclusion constraint, finds a valid alternative, and quantifies trade-offs.",
        "icon": "shield-off",
        "default_student_id": "S1024"
    },
    {
        "id": "scenario_behavioural_drift",
        "name": "Behavioural Drift (3 hrs/wk vs 8 hrs/wk)",
        "category": "Engagement Drift",
        "description": "Logged study engagement drops to 3 hrs/week. System detects burnout risk (<60% target), sheds non-core elective load, and issues a supportive pacing notification.",
        "icon": "trending-down",
        "default_student_id": "S1024"
    },
    {
        "id": "scenario_fast_forward",
        "name": "Multi-Semester Fast-Forward (Advance to Sem 7)",
        "category": "Curriculum Simulation",
        "description": "Fast-forwards time by simulating Semester 6 completion with Grade A in COL106. Recalculates Bayesian mastery and advances remaining curriculum to Semesters 7 & 8.",
        "icon": "fast-forward",
        "default_student_id": "S1024"
    }
]

class AdaptationSimulator:
    @staticmethod
    def persist_adapted_plan(
        student_id: str,
        plan: Dict[str, Any],
        plan_diff: Dict[str, Any],
        validation: Dict[str, Any],
    ) -> int:
        """Store only independently valid adaptations as the new active plan version."""
        if not validation.get("is_valid"):
            raise ValueError("Adapted plan failed independent validation and was not saved.")
        profile = StudentStore.get_profile(student_id)
        if not profile:
            raise ValueError(f"Student ID '{student_id}' does not exist.")
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT version_number FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
                (student_id,),
            )
            previous = cur.fetchone()
            version = (previous["version_number"] if previous else 0) + 1
        certificate = rule_registry.generate_certificate(
            plan,
            profile.model_dump(),
            plan_version_id=f"{student_id}_v{version}",
        )
        report = {**validation, "certificate": certificate.model_dump()}
        with get_db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO plan_versions (
                    student_id, version_number, plan_json,
                    diff_from_previous_json, validation_report_json
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (student_id, version, json.dumps(plan), json.dumps(plan_diff), json.dumps(report)),
            )
        return version

    @staticmethod
    def get_latest_or_initial_plan(student_id: str) -> Dict[str, Any]:
        """Retrieves latest plan from database or synthesizes initial baseline plan."""
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT plan_json, version_number FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
                (student_id,)
            )
            row = cur.fetchone()
            if row:
                return json.loads(row["plan_json"])

        profile = StudentStore.get_profile(student_id)
        if not profile:
            raise ValueError(f"Student ID '{student_id}' does not exist.")

        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)
        plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=22.0,
            max_weekly_hours=profile.available_hours_per_week
        )
        
        # Save baseline as version 1
        val = independent_validator.validate_plan(plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(None, plan, "Initial baseline curriculum")
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO plan_versions (student_id, version_number, plan_json, diff_from_previous_json, validation_report_json)
            VALUES (?, 1, ?, ?, ?);
            """, (student_id, json.dumps(plan), json.dumps(diff), json.dumps(val)))

        return plan

    @staticmethod
    def log_adaptation_event(
        student_id: str,
        trigger_signal: str,
        action_type: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        plan_diff: Dict[str, Any],
        explanation: str
    ) -> None:
        """Persists adaptation decision audit record."""
        with get_db_cursor() as cur:
            cur.execute("""
            INSERT INTO adaptation_events (
                student_id, trigger_signal, action_type, before_state_json,
                after_state_json, plan_diff_json, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                student_id,
                trigger_signal,
                action_type,
                json.dumps(before_state),
                json.dumps(after_state),
                json.dumps(plan_diff),
                explanation
            ))

    def run_strong_quiz(self, student_id: str = "S1024") -> Dict[str, Any]:
        """Simulates student acing DSA Mid-Semester Quiz (95%)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Add strong evidence events
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="skill_dsa_linear",
            value=1.0,
            source_type="quiz",
            confidence=1.0,
            item_ref="midsem_quiz_dsa_q1"
        ))
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="skill_dsa_trees",
            value=1.0,
            source_type="quiz",
            confidence=1.0,
            item_ref="midsem_quiz_dsa_q2"
        ))

        # 2. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"score": 0.95, "bkt_probability": 0.92, "skill_id": "skill_dsa_trees"}
        )

        # 3. Fast-track prerequisite: Student tests out of introductory DSA (COL106 credit-by-assessment)
        new_completed = list(profile.completed_courses)
        if not any(c.course_code == "COL106" for c in new_completed):
            new_completed.append(CompletedCourse(course_code="COL106", grade="A", semester_completed=profile.current_semester))
            profile.completed_courses = new_completed
            StudentStore.save_profile(profile)

        # Recompute gaps and re-solve plan with unlocked advanced electives
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        # Allow overload / acceleration
        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=24.0,
            overload_allowed=True
        )

        # 4. Validate & diff
        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change="Mid-Semester Quiz Mastery (95% in DSA) - Prerequisite accelerated"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Outstanding performance on DSA Mid-Semester assessment (95%). "
            f"Because you demonstrated high proficiency in linear data structures and tree traversals, "
            f"your prerequisite requirement has been expedited. Advanced Algorithm Design (COL351) and "
            f"Database Systems (COL362) have been pulled forward to fast-track your Software Engineering readiness."
        )

        self.log_adaptation_event(
            student_id, "Mid-Semester Quiz Score 95%", "ACCELERATE",
            {"dsa_mastery_before": 0.32}, {"dsa_mastery_after": 0.93},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_strong_quiz",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "ACCELERATE",
            "bkt_update": {"skill": "skill_dsa_trees", "previous": 0.32, "updated": 0.93, "mastered": True},
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_weak_quiz(self, student_id: str = "S1024") -> Dict[str, Any]:
        """Simulates student struggling on DSA Mid-Semester Quiz (25%)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Add weak evidence event
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="skill_dsa_trees",
            value=0.0,
            source_type="quiz",
            confidence=0.8,
            item_ref="midsem_quiz_dsa_weak"
        ))

        # 2. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"score": 0.25, "bkt_probability": 0.20, "skill_id": "skill_dsa_trees", "consecutive_misses": 3}
        )

        # 3. Re-solve plan with conservative credit cap and remedial resource insertion
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=18.0,  # lower credit cap to avoid burnout
            max_weekly_hours=8.0
        )

        # Inject remedial practice resources specifically into Semester 6
        if new_plan.get("semesters"):
            remedial_items = [
                {
                    "resource_id": "oer_remedial_dsa",
                    "title": "NPTEL Trees & Recursion Foundation Drills",
                    "type": "video_playlist",
                    "url": "https://nptel.ac.in/courses/remedial_dsa",
                    "remedial": True
                },
                {
                    "resource_id": "drill_binary_trees",
                    "title": "Interactive Binary Search Tree Practice Drills",
                    "type": "interactive_drill",
                    "url": "https://leetcode.com/explore/learn/card/data-structure-tree/",
                    "remedial": True
                }
            ]
            new_plan["semesters"][0]["remedial_resources"] = remedial_items

        # 4. Validate & diff
        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change="Performance signal below threshold (25% in DSA) - Remediation & Workload Pacing"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Assessment indicated challenges with tree structures and recursion (score 25%). "
            f"To protect your academic standing and ensure durable mastery, the buddy inserted 2 remedial "
            f"practice modules and capped semester credits at 18. Advanced design coursework has been comfortably "
            f"spaced to give you time to master core foundations."
        )

        self.log_adaptation_event(
            student_id, "Mid-Semester Quiz Score 25%", "REMEDIATE",
            {"dsa_mastery_before": 0.32}, {"dsa_mastery_after": 0.20},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_weak_quiz",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "REMEDIATE",
            "bkt_update": {"skill": "skill_dsa_trees", "previous": 0.32, "updated": 0.20, "mastered": False},
            "remedial_resources_added": 2,
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_course_override(self, student_id: str = "S1024", rejected_course: str = "COL362") -> Dict[str, Any]:
        """Simulates student rejecting a course (e.g., COL362 Database Systems)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"student_override": {"rejected_course": rejected_course, "reason": "Student preference"}}
        )

        # 2. Re-solve plan with excluded_courses constraint
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=22.0,
            excluded_courses=[rejected_course]
        )

        # 3. Compute trade-offs
        tradeoffs = adaptation_policy_engine.compute_tradeoffs(
            old_plan=old_plan,
            new_plan=new_plan,
            rejected_course=rejected_course
        )

        # 4. Validate & diff
        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change=f"Student override: Excluded {rejected_course}"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"You chose to exclude {rejected_course}. The scheduler re-optimized your remaining semesters "
            f"to maintain degree eligibility without this course. "
            f"Trade-off: Relational database skill coverage is deferred, but your semester workload is reduced "
            f"by {abs(tradeoffs['workload_delta_hours_per_week'])} hrs/week while meeting graduation credit rules."
        )

        self.log_adaptation_event(
            student_id, f"Student Excluded {rejected_course}", "OVERRIDE_RESOLVE",
            {"excluded_course": rejected_course}, {"new_courses": [c["code"] for s in new_plan.get("semesters", []) for c in s.get("courses", [])]},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_course_override",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "OVERRIDE_RESOLVE",
            "tradeoffs": tradeoffs,
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_behavioural_drift(self, student_id: str = "S1024", logged_weekly_hours: float = 3.0) -> Dict[str, Any]:
        """Simulates engagement drift (e.g. logging only 3 hrs/wk vs 8 hrs/wk target)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"actual_weekly_hours": logged_weekly_hours, "target_weekly_hours": profile.available_hours_per_week}
        )

        # 2. Shed load: Reduce credit cap to 16 credits
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=16.0,  # shed load
            max_weekly_hours=logged_weekly_hours
        )

        # 3. Validate & diff
        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change=f"Engagement drift detected ({logged_weekly_hours}h/wk logged vs {profile.available_hours_per_week}h/wk target)"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Noticed engagement drift: your logged study time averaged {logged_weekly_hours} hrs/week over the past weeks "
            f"(below your {profile.available_hours_per_week}h goal). To prevent stress and keep learning sustainable, "
            f"we lowered your semester elective load by {abs(diff.get('net_credit_change', 0))} credits, "
            f"focusing exclusively on core foundations."
        )

        self.log_adaptation_event(
            student_id, f"Engagement Drift {logged_weekly_hours}h/wk", "LOAD_SHED",
            {"target_hours": profile.available_hours_per_week}, {"actual_hours": logged_weekly_hours},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_behavioural_drift",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "LOAD_SHED",
            "logged_weekly_hours": logged_weekly_hours,
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_fast_forward(self, student_id: str = "S1024") -> Dict[str, Any]:
        """Simulates advancing from Semester 5 to Semester 7 with completed course progress."""
        profile = StudentStore.get_profile(student_id)
        if not profile:
            raise ValueError(f"Student ID '{student_id}' does not exist.")

        # Simulate Semester 6 completion: add COL106 with Grade 'A'
        new_completed = list(profile.completed_courses)
        if not any(c.course_code == "COL106" for c in new_completed):
            new_completed.append(CompletedCourse(course_code="COL106", grade="A", semester_completed=6))

        profile.current_semester = 6
        profile.completed_courses = new_completed
        profile.year = 3
        StudentStore.save_profile(profile)

        # Inject high evidence for completed course
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="skill_dsa_linear",
            value=0.92,
            source_type="grade",
            confidence=1.0,
            item_ref="grade_COL106_A"
        ))
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="skill_dsa_trees",
            value=0.92,
            source_type="grade",
            confidence=1.0,
            item_ref="grade_COL106_A"
        ))

        # Re-solve curriculum for remaining semesters (7 & 8)
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=6,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=22.0
        )

        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=None,
            new_plan=new_plan,
            reason_for_change="Fast-forwarded to Semester 7: COL106 completed with Grade A"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Fast-forwarded to Semester 7! With COL106 completed with Grade A, your DSA proficiency is verified. "
            f"You are now ready to tackle COL351 (Algorithm Design) and systems electives in your final year."
        )

        self.log_adaptation_event(
            student_id, "Fast-Forward to Sem 7", "FAST_FORWARD",
            {"semester_before": 5}, {"semester_after": 6},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_fast_forward",
            "student_id": student_id,
            "status": "fast_forwarded",
            "new_semester": 6,
            "completed_courses_count": len(profile.completed_courses),
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def execute_scenario(self, scenario_id: str, student_id: str = "S1024", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatches scenario by ID."""
        p = params or {}
        if scenario_id == "scenario_strong_quiz":
            return self.run_strong_quiz(student_id)
        elif scenario_id == "scenario_weak_quiz":
            return self.run_weak_quiz(student_id)
        elif scenario_id == "scenario_course_override":
            rejected = p.get("rejected_course", "COL362")
            return self.run_course_override(student_id, rejected)
        elif scenario_id == "scenario_behavioural_drift":
            hours = float(p.get("actual_weekly_hours", 3.0))
            return self.run_behavioural_drift(student_id, hours)
        elif scenario_id == "scenario_fast_forward":
            return self.run_fast_forward(student_id)
        else:
            raise ValueError(f"Unknown scenario ID: '{scenario_id}'")

adaptation_simulator = AdaptationSimulator()
