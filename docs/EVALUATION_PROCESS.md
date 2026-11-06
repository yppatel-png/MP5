# Evaluation Process & Verification Methodology
Describes the multi-tiered testing and verification framework ensuring the Learning Buddy meets both academic integrity standards and Inter IIT Tech Meet 15.0 competition guidelines.

---

## 1. Evaluation Architecture Overview

The system is evaluated across three decoupled layers:

```
[Tier 1: Unit & Regression Suites]
     46 Automated Tests (Health, KB, Diagnostic, Solver, Mastery, Adapt, Buddy, Frontend)
                          │
                          ▼
[Tier 2: Mathematical Plan Validator]
     Decoupled 9-Rule Constraint Auditor (Runs on every generated schedule)
                          │
                          ▼
[Tier 3: End-to-End Evaluation Harness]
     scripts/evaluate.py (50-Profile Benchmark, Determinism, Adaptation Diffs, Telemetry)
```

---

## 2. Decoupled 9-Rule Independent Plan Validator

Every multi-semester schedule produced by the planning engine is independently audited by `backend/planner/validator.py` prior to presentation:

1. **Rule 1 (Prerequisite DAG Compliance)**:
   - For every course $C_i$ scheduled in Semester $S_k$, all prerequisites $\text{Req}(C_i)$ must belong to $\{C \mid \text{Semester}(C) < S_k\} \cup \text{CompletedCourses}$.
   - Co-requisites within the same semester are strictly disallowed.

2. **Rule 2 (Semester Offering Parity)**:
   - Odd semester courses are scheduled strictly in Semesters 1, 3, 5, 7.
   - Even semester courses are scheduled strictly in Semesters 2, 4, 6, 8.

3. **Rule 3 (Semester Credit Bounds)**:
   - Minimum semester load: $\ge 14.0$ credits.
   - Maximum standard load: $\le 22.0$ credits.
   - Overload maximum: $\le 24.0$ credits (strictly conditioned on CGPA $\ge 8.5$).

4. **Rule 4 (Degree Programme Alignment)**:
   - Mandatory departmental core courses cannot be omitted.

5. **Rule 5 (Minor Degree Eligibility Check)**:
   - Computer Science minor courses for non-CS students require CGPA $\ge 7.5$.

6. **Rule 6 (No-Co-Taking Mutex Pairs)**:
   - Mutually exclusive courses (e.g., `COL351` Analysis & Design of Algorithms and `COL352` Introduction to Automata) cannot be taken concurrently in the same semester.

7. **Rule 7 (Duplicate Course Prevention)**:
   - No course code may appear more than once across completed and scheduled semesters.

8. **Rule 8 (Weekly Workload Feasibility)**:
   - Estimated independent self-study hours ($\approx 35\%$ of total contact hours) must fit within the student's stated weekly study budget.

9. **Rule 9 (Valid Catalogue Grounding)**:
   - Every scheduled course code must exist in the institute catalogue; zero fabricated codes permitted.

---

## 3. Evaluation Harness Execution

The evaluation harness can be run on-demand via:
```bash
python scripts/evaluate.py
```
Or inside Docker via:
```bash
make eval
```

It outputs:
- `reports/eval.md`: Formatted markdown audit with pass/fail tables.
- `reports/eval.json`: Structured machine-readable benchmark telemetry.

