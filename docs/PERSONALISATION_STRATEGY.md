# Personalisation & Signal Resolution Strategy
Defines the mathematical framework for resolving conflicting student signals, weighing heterogeneous evidence sources, and balancing student ambitions against academic safety.

---

## 1. Evidence Reliability Hierarchy

Student competence is evaluated through multiple heterogeneous channels, each carrying a calibrated reliability coefficient ($w_i \in [0.1, 1.0]$) that scales the effective confidence of Bayesian Knowledge Tracing updates:

| Evidence Source | Reliability Weight ($w_i$) | Description & Rationale |
| :--- | :--- | :--- |
| **Accredited Course Grade** | **1.00** | Formal university transcript grade (A, B, C, D). High-stakes, invigilated summative evaluation. |
| **Assessed Diagnostic Test** | **1.00** | Structured information-gain diagnostic administered under timed baseline conditions. |
| **Timed Coding Project** | **0.90** | Automated test suite execution on end-to-end coding assignments with hidden test cases. |
| **Mock Placement Exam** | **0.90** | Rigorous timed simulation under realistic placement exam constraints. |
| **Interactive Quiz / Practice Drill** | **0.70** | Formative practice exercises solved with immediate feedback and optional hints. |
| **Inferred Course Prerequisite** | **0.50** | Derived from passing a higher-level course that presumes foundational knowledge. |
| **Self-Declared Student Interest** | **0.20** | Unverified stated interest in onboarding wizard. Used strictly as a low-confidence prior. |

```
P(Evidence | Mastered) is updated using:
P*(E) = P(E) * w_i
```

---

## 2. Resolving Conflicting Signals

### Conflict Scenario A: High Interest vs. Low Baseline Grade
- **Context**: A student self-declares high passion for "Machine Learning" (interest prior = 0.8), but earned a Grade D in prerequisite Linear Algebra (`MTL101`).
- **Resolution Policy**:
  1. The system **never dismisses** the student's career aspiration.
  2. The system **never immediately schedules** advanced machine learning (`COL770`), as doing so violates prerequisite readiness and risks a failing grade.
  3. Action: The planner inserts a foundational bridge module (e.g., NPTEL Linear Algebra refresher) and schedules the core mathematics prerequisite before advancing to the elective.
  4. Explanation: *"We honored your goal for Machine Learning by scheduling the exact sequence needed to master foundational Linear Algebra first, ensuring your CGPA is protected."*

### Conflict Scenario B: Accredited Course Completed vs. Weak Diagnostic Test
- **Context**: Student passed `COL106` (Data Structures) with Grade B- two semesters ago, but scored 25% on the diagnostic tree traversal drill.
- **Resolution Policy**:
  1. Distinguish *Accredited Completion* from *Current Operational Proficiency*.
  2. Course completion satisfies the formal administrative prerequisite check (the student is not barred from taking advanced electives).
  3. However, BKT mastery probability decays and flags a cognitive gap.
  4. Action: The system flags a `GapAlert` and inserts 2 high-yield remedial drills into the active weekly checklist without requiring the student to re-take the entire course.

---

## 3. Student Override & Agency Framework

A fundamental design tenet of the Adobe Learning Buddy is **Student Agency**: the student is the ultimate pilot of their academic journey. The AI buddy advises; the student decides.

When a student rejects a course recommendation or overrides the credit schedule:
1. **Exclusion Constraint**: The rejected course code is added as a hard exclusion in the constraint solver (`excluded_courses = [course_code]`).
2. **Re-Solve with Active Constraints**: The mathematical solver re-runs, exploring alternative courses in the institute catalogue that satisfy remaining credit requirements.
3. **Transparent Trade-off Presentation**: The system immediately generates a factual trade-off breakdown:
   - **What is lost**: Specific skills deferred or missed.
   - **What is gained**: Alternative skill coverage, workload reduction (hrs/week), or elective flexibility.
   - **Degree Audit Compliance**: Confirmation that core degree requirements and graduation credit minimums remain 100% satisfied.

