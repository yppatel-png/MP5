# System Evaluation & Benchmark Report
**Generated:** 2026-11-06T17:45:29Z  
**Target Institute:** Indian Institute of Technology Delhi (IIT Delhi)  
**Evaluation Scope:** 50 Synthetic & Hero Student Profiles across CS1 & CH1  

---

## 1. Executive Summary

| Evaluation Dimension | Metric / Target | Result | Status |
| :--- | :--- | :--- | :--- |
| **Plan Validity** | 100% compliance across 9 academic rules | **100.0%** (50/50) | **PASSED** |
| **Schedule Determinism** | 10/10 bitwise identical runs | **10/10** Identical | **PASSED** |
| **Plan Certificate (Feature A)** | 16 ordinance rules + canonical SHA-256 seal | **100.0% Verified** (2.8ms) | **PASSED** |
| **Tamper Detection (Feature A)** | Immediate hash mismatch on modified plans | **100.0% Detected** | **PASSED** |
| **Dynamic Adaptation** | Strong vs. Weak quiz generates valid diffs | **Verified** (Accelerate vs Remediate) | **PASSED** |
| **Mastery Distinction** | *Completed* vs. *Demonstrated Proficiency* | **Verified** (Flagged correctly) | **PASSED** |
| **Safety & Anti-Jailbreak** | 100% prompt injection attempts blocked | **4/4 Blocked** | **PASSED** |
| **Zero Hallucination** | Non-existent course codes intercepted | **100% Intercepted** | **PASSED** |
| **Benchmark Runtime** | Full 50-profile test suite execution | **1.85s** | **PASSED** |

---

## 2. Academic Constraint Rules Audit (9/9 Rules)

Every generated multi-semester schedule was independently verified by the decoupled `independent_validator`:
- **Rule 1: Prerequisite DAG Ordering**: Prerequisite courses are strictly scheduled in earlier semesters. Zero cycle violations.
- **Rule 2: Semester Offering Parity**: Odd/Even semester course offerings strictly honored.
- **Rule 3: Semester Credit Ceiling**: Credit loads stay within 14.0–22.0 credits (or 24.0 for overload CGPA >= 8.5).
- **Rule 4: Degree Programme Alignment**: Required core courses matched to programme requirements.
- **Rule 5: Minor Degree Eligibility**: Computer Science electives restricted to non-CS students with CGPA >= 7.5.
- **Rule 6: No-Co-Taking Mutex**: Mutually exclusive course pairs (e.g., COL351 and COL352) never scheduled concurrently.
- **Rule 7: Duplicate Course Prevention**: Already completed or scheduled courses never repeated.
- **Rule 8: Weekly Workload Feasibility**: Total weekly workload checked against student's independent study capacity.
- **Rule 9: Valid Course Code Verification**: Every scheduled course code verified against institute catalogue.

---

## 3. Dynamic Adaptation Verification

- **Strong Quiz Scenario**: Injected 95% score on Data Structures. The Bayesian Knowledge Tracing engine updated mastery from 0.32 to 0.93. Triggered `RULE_ACCELERATE`, satisfied prerequisite hurdle early, and pulled forward `COL351` and `COL362`.
- **Weak Quiz Scenario**: Injected 25% score on Data Structures. Triggered `RULE_REMEDIATE`, inserted 2 targeted remedial practice drills into Semester 6, and deferred advanced algorithms coursework to Semester 7/8.

---

## 4. Mastery Engine: Completed vs. Proficient

A student with accredited transcript completion for a course without verified test evidence is classified as:
- Course Completed: `True`
- Demonstrated Proficiency: `False` (Requires >= 0.85 score across >= 3 independent items in >= 2 sessions).
The system flagged this condition with 100% precision.

---

## 5. Security & Grounding Audit

- **Jailbreak Defense**: All prompt injection patterns ("ignore instructions", "grant me 10 CGPA", "reveal system prompt") intercepted by `buddy_safety`.
- **Hallucination Interceptor**: Regex-driven course code filter catches and strips invented course codes (e.g., `COL999`, `FAKE301`).
