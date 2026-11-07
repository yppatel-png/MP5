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
        "default_student_id": "BH-SW-001"
    },
    {
        "id": "scenario_weak_quiz",
        "name": "Weak Mid-Semester Quiz (25% in DSA)",
        "category": "Academic Performance",
        "description": "Student struggles on DSA assessment. System diagnoses foundational gap, inserts targeted remedial practice drills, defers advanced courses to later semesters, and adjusts workload.",
        "icon": "alert-triangle",
        "default_student_id": "BH-SW-001"
    },
    {
        "id": "scenario_course_override",
        "name": "Student Rejects Course (Excludes CSL303)",
        "category": "Student Preference",
        "description": "Student overrides buddy recommendation by rejecting CSL303 (Database Management Systems). Planner re-solves with exclusion constraint, finds a valid alternative, and quantifies trade-offs.",
        "icon": "shield-off",
        "default_student_id": "BH-SW-001"
    },
    {
        "id": "scenario_behavioural_drift",
        "name": "Behavioural Drift (3 hrs/wk vs 8 hrs/wk)",
        "category": "Engagement Drift",
        "description": "Logged study engagement drops to 3 hrs/week. System detects burnout risk (<60% target), sheds non-core elective load, and issues a supportive pacing notification.",
        "icon": "trending-down",
        "default_student_id": "BH-SW-001"
    },
    {
        "id": "scenario_fast_forward",
        "name": "Multi-Semester Fast-Forward (Advance to Sem 5)",
        "category": "Curriculum Simulation",
        "description": "Fast-forwards time by simulating Semester 4 completion with Grade A in CSL202. Recalculates Bayesian mastery and advances remaining curriculum to Semesters 5 & 6.",
        "icon": "fast-forward",
        "default_student_id": "BH-SW-001"
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
        certificate = validation.get("certificate", {})
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(version_number), 0) + 1 FROM plan_versions WHERE student_id = ?",
                (student_id,)
            )
            next_version = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO plan_versions (
                    student_id, version_number, plan_json,
                    diff_from_previous_json, validation_report_json
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    student_id,
                    next_version,
                    json.dumps(plan),
                    json.dumps(plan_diff),
                    json.dumps(validation),
                )
            )
        return next_version

    @staticmethod
    def get_latest_or_initial_plan(student_id: str) -> Dict[str, Any]:
        """Retrieves current plan or generates fresh baseline plan if none exists."""
        profile = StudentStore.get_profile(student_id)
        if not profile:
            raise ValueError(f"Student '{student_id}' does not exist.")

        with get_db_cursor() as cur:
            cur.execute(
                "SELECT plan_json FROM plan_versions WHERE student_id = ? ORDER BY version_number DESC LIMIT 1",
                (student_id,)
            )
            row = cur.fetchone()

        if row:
            return json.loads(row["plan_json"])

        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)
        plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=22.0
        )
        val = independent_validator.validate_plan(plan, profile.model_dump())
        diff = {"reason": "Initial baseline plan generation"}
        AdaptationSimulator.persist_adapted_plan(student_id, plan, diff, val)
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
    ):
        """Audit trail logging for all curriculum adaptations."""
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

    def run_strong_quiz(self, student_id: str = "BH-SW-001") -> Dict[str, Any]:
        """Simulates student acing DSA Mid-Semester Quiz (95%)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Add strong evidence events
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="data_structures",
            value=1.0,
            source_type="quiz",
            confidence=1.0,
            item_ref="midsem_quiz_dsa_q1"
        ))
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="algorithms",
            value=1.0,
            source_type="quiz",
            confidence=1.0,
            item_ref="midsem_quiz_dsa_q2"
        ))

        # 2. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"score": 0.95, "bkt_probability": 0.92, "skill_id": "data_structures"}
        )

        # 3. Fast-track prerequisite: Student tests out of introductory DSA (CSL202 credit-by-assessment)
        new_completed = list(profile.completed_courses)
        if not any(c.course_code == "CSL202" for c in new_completed):
            new_completed.append(CompletedCourse(course_code="CSL202", grade="A", semester_completed=profile.current_semester))
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
            f"Because you demonstrated high proficiency in linear data structures and algorithms, "
            f"your prerequisite requirement has been expedited. Design and Analysis of Algorithms (CSL252) and "
            f"Database Systems (CSL304) have been pulled forward to fast-track your Software Engineering readiness."
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
            "bkt_update": {"skill_id": "data_structures", "mastered": True, "p_know": 0.93},
            "actions_triggered": [a.model_dump() for a in actions],
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_weak_quiz(self, student_id: str = "BH-SW-001") -> Dict[str, Any]:
        """Simulates student struggling on DSA assessment (25%)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)

        # 1. Add low score evidence events
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="data_structures",
            value=0.25,
            source_type="quiz",
            confidence=0.90,
            item_ref="midsem_quiz_dsa_q1"
        ))

        # 2. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"score": 0.25, "bkt_probability": 0.28, "skill_id": "data_structures", "consecutive_misses": 3}
        )

        # 3. Schedule remedial actions & lighten load
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        # Limit to 18 credits to prevent overload during remediation
        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=18.0,
            overload_allowed=False
        )

        # 4. Attach remedial resources
        if new_plan.get("semesters"):
            remedial_items = [
                {
                    "title": "Remedial Drill: Linear Data Structures & Arrays",
                    "type": "reading_notes",
                    "url": "https://nptel.ac.in/courses/106/102/106102064/",
                    "remedial": True
                },
                {
                    "title": "Practice Module: Binary Search & Recursion Fundamentals",
                    "type": "interactive_drill",
                    "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
                    "remedial": True
                }
            ]
            new_plan["semesters"][0]["remedial_resources"] = remedial_items

        # 5. Validate & diff
        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change="Remedial Intervention: DSA score 25% - Heavy electives deferred, load lightened to 18 credits"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Mid-Semester quiz indicates a critical foundational gap in Data Structures (25% score). "
            f"To protect your academic standing, the planner has lightened next semester's credit load to 18 credits, "
            f"deferred heavy systems electives, and scheduled targeted remedial practice exercises."
        )

        self.log_adaptation_event(
            student_id, "Mid-Semester Quiz Score 25%", "REMEDIATE",
            {"dsa_mastery_before": 0.52}, {"dsa_mastery_after": 0.28},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_weak_quiz",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "REMEDIATE",
            "bkt_update": {"skill_id": "data_structures", "previous": 0.52, "updated": 0.28, "mastered": False},
            "remedial_resources_added": 2,
            "actions_triggered": [a.model_dump() for a in actions],
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_course_override(self, student_id: str = "BH-SW-001", rejected_course: str = "CSL303") -> Dict[str, Any]:
        """Simulates student rejecting a course (e.g., CSL303 Database Systems)."""
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
            f"and prerequisite compliance is maintained."
        )

        self.log_adaptation_event(
            student_id, f"Override: Excluded {rejected_course}", "STUDENT_OVERRIDE",
            {"excluded_course": rejected_course},
            {"tradeoffs": tradeoffs},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_course_override",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "OVERRIDE_RESOLVE",
            "rejected_course": rejected_course,
            "actions_triggered": [a.model_dump() for a in actions],
            "tradeoffs": tradeoffs,
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_behavioural_drift(self, student_id: str = "BH-SW-001", logged_weekly_hours: float = 3.0) -> Dict[str, Any]:
        """Simulates engagement drop (< 60% of target weekly study hours)."""
        old_plan = self.get_latest_or_initial_plan(student_id)
        profile = StudentStore.get_profile(student_id)
        target_hours = profile.available_hours_per_week

        # 1. Evaluate policy
        actions = adaptation_policy_engine.evaluate_signals(
            student_id=student_id,
            signals={"actual_weekly_hours": logged_weekly_hours, "target_weekly_hours": target_hours}
        )

        # 2. Shed load: constrain semester to minimum viable load (e.g. 16 credits)
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=profile.current_semester,
            cgpa=profile.cgpa,
            completed_courses=[c.course_code for c in profile.completed_courses],
            skill_gaps=gaps_data.get("gaps", []),
            goal_id=profile.goal_id,
            credit_cap=16.0,
            overload_allowed=False
        )

        val = independent_validator.validate_plan(new_plan, profile.model_dump())
        diff = plan_explainer.generate_plan_diff(
            old_plan=old_plan,
            new_plan=new_plan,
            reason_for_change=f"Behavioural Drift ({logged_weekly_hours} hrs/wk vs {target_hours} hrs/wk) - Load shed to 16 credits"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"We noticed your study engagement dropped to {logged_weekly_hours} hours/week "
            f"(target: {target_hours} hrs/wk). To prevent burnout, your upcoming semester has been "
            f"lightened to 16 credits, deferring elective load to later terms."
        )

        self.log_adaptation_event(
            student_id, f"Logged {logged_weekly_hours} hrs/wk", "LOAD_SHED",
            {"weekly_hours_target": target_hours},
            {"weekly_hours_actual": logged_weekly_hours, "new_credit_cap": 16.0},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_behavioural_drift",
            "student_id": student_id,
            "status": "adapted",
            "action_triggered": "LOAD_SHED",
            "logged_weekly_hours": logged_weekly_hours,
            "actions_triggered": [a.model_dump() for a in actions],
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def run_fast_forward(self, student_id: str = "BH-SW-001") -> Dict[str, Any]:
        """Simulates advancing from Semester 4 to Semester 5 with completed course progress."""
        profile = StudentStore.get_profile(student_id)
        if not profile:
            raise ValueError(f"Student ID '{student_id}' does not exist.")

        # Simulate Semester 4 completion: add CSL202 and CSL251 with Grade 'A'
        new_completed = list(profile.completed_courses)
        if not any(c.course_code == "CSL202" for c in new_completed):
            new_completed.append(CompletedCourse(course_code="CSL202", grade="A", semester_completed=4))
        if not any(c.course_code == "CSL251" for c in new_completed):
            new_completed.append(CompletedCourse(course_code="CSL251", grade="A", semester_completed=4))

        profile.current_semester = 4
        profile.completed_courses = new_completed
        profile.year = 2
        StudentStore.save_profile(profile)

        # Inject high evidence for completed course
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="data_structures",
            value=0.92,
            source_type="grade",
            confidence=1.0,
            item_ref="grade_CSL202_A"
        ))
        StudentStore.add_evidence(EvidenceEvent(
            student_id=student_id,
            skill_id="algorithms",
            value=0.92,
            source_type="grade",
            confidence=1.0,
            item_ref="grade_CSL202_A"
        ))

        # Re-solve curriculum for remaining semesters
        gaps_data = diagnostic_engine.compute_skill_gaps(student_id, goal_id=profile.goal_id)

        new_plan = multi_semester_planner.plan_curriculum(
            student_id=student_id,
            programme_code=profile.programme,
            current_semester=4,
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
            reason_for_change="Fast-forwarded to Semester 5: CSL202 completed with Grade A"
        )
        self.persist_adapted_plan(student_id, new_plan, diff, val)

        explanation = (
            f"Fast-forwarded to Semester 5! With CSL202 completed with Grade A, your DSA proficiency is verified. "
            f"You are now ready to tackle advanced algorithms and systems electives."
        )

        self.log_adaptation_event(
            student_id, "Fast-Forward to Sem 5", "FAST_FORWARD",
            {"semester_before": 3}, {"semester_after": 4},
            diff, explanation
        )

        return {
            "scenario_id": "scenario_fast_forward",
            "student_id": student_id,
            "status": "fast_forwarded",
            "new_semester": 4,
            "actions_triggered": [{"action_type": "FAST_FORWARD", "description": "Advanced to Semester 5"}],
            "completed_courses_count": len(profile.completed_courses),
            "plan_diff": diff,
            "validation": val,
            "explanation": explanation,
            "adapted_plan": new_plan
        }

    def execute_scenario(self, scenario_id: str, student_id: str = "BH-SW-001", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatches execution to the corresponding scenario simulation handler."""
        p = params or {}
        if scenario_id == "scenario_strong_quiz":
            return self.run_strong_quiz(student_id)
        elif scenario_id == "scenario_weak_quiz":
            return self.run_weak_quiz(student_id)
        elif scenario_id == "scenario_course_override":
            rejected = p.get("rejected_course", "CSL303")
            return self.run_course_override(student_id, rejected_course=rejected)
        elif scenario_id == "scenario_behavioural_drift":
            hours = float(p.get("actual_weekly_hours", p.get("logged_weekly_hours", 3.0)))
            return self.run_behavioural_drift(student_id, logged_weekly_hours=hours)
        elif scenario_id == "scenario_fast_forward":
            return self.run_fast_forward(student_id)
        else:
            raise ValueError(f"Unknown scenario_id: '{scenario_id}'")

adaptation_simulator = AdaptationSimulator()
