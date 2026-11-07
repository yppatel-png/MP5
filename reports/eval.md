# System Evaluation & Benchmark Report
**Generated:** 2026-11-07T11:37:10Z  
**Target Institute:** Indian Institute of Technology Bhilai (IIT Bhilai)  
**Evaluation Scope:** All 78 Student Profiles across BTech CSE (`BH-CSE-BTECH`)  

---

## 1. Executive Summary

| Evaluation Dimension | Metric / Target | Result | Status |
| :--- | :--- | :--- | :---: |
| **Plan Validity** | 100% compliance across academic rules | **100.0%** (78/78) | **PASSED** |
| **Infeasible Request Handling** | State 'not possible' + valid alternative | **100.0%** (10/10) | **PASSED** |
| **Schedule Determinism** | 10/10 bitwise identical runs | **10/10** Identical | **PASSED** |
| **LLM-Off Offline Validity** | 100% valid plans without external LLM | **100.0%** (10/10) | **PASSED** |
| **Fault-Injection Robustness** | 100% synthetic mutations caught | **100.0%** (5/5) | **PASSED** |
| **Plan Certificate (Feature A)** | Academic rules + canonical SHA-256 seal | **100.0% Verified** (2.7ms) | **PASSED** |
| **Tamper Detection (Feature A)** | Immediate hash mismatch on modified plans | **100.0% Detected** | **PASSED** |
| **Dynamic Adaptation** | Quiz & study week signals generate valid diffs | **Verified** (Accelerate vs Remediate) | **PASSED** |
| **Mastery Distinction** | *Completed* vs. *Demonstrated Proficiency* | **Verified** (Flagged correctly) | **PASSED** |
| **Safety & Anti-Jailbreak** | &ge;40 prompt injection and off-topic cases | **100.0%** (42/42 Blocked) | **PASSED** |
| **Benign Query False-Positive Rate** | 0% over-blocking on legitimate queries | **0.0%** (0/32 Blocked) | **PASSED** |
| **Zero Hallucination** | Non-existent course codes intercepted | **100% Intercepted** (zero leakage) | **PASSED** |
| **Benchmark Runtime** | Full test suite execution | **5.96s** | **PASSED** |

---

## 2. Academic Constraint Rules Audit

Every generated multi-semester schedule was independently verified by `independent_validator`:
- **Prerequisite Ordering**: Prerequisite courses strictly scheduled in earlier semesters. Zero cycle violations.
- **Semester Parity**: Odd/Even semester course offerings strictly honored.
- **Semester Credit Bounds**: Credit loads stay within 12.0–24.0 credits (or 27.0 for overload).
- **Degree Structure**: Required core courses matched to programme requirements.
- **Duplicate Course Prevention**: Already completed or scheduled courses never repeated.
- **Weekly Workload Feasibility**: Total weekly workload checked against student study capacity.
- **Valid Course Code Verification**: Every scheduled course code verified against institute catalogue.

---

## 3. Dynamic Adaptation Verification

- **Strong Quiz Scenario**: Injected 95% score on Data Structures. Triggered `ACCELERATE`, satisfied prerequisite hurdle early, and pulled forward `CSL252` and `CSL304`.
- **Weak Quiz Scenario**: Injected 25% score on Data Structures. Triggered `REMEDIATE`, lightened next semester load to 18 credits, and scheduled remedial practice.
- **Strong Study Week**: Logged 20 hours of study (100% adherence) &rarr; Status updated to `On Track` &rarr; Full curriculum momentum maintained.
- **Weak Study Week**: Logged 4 hours of study (20% adherence) &rarr; Status updated to `Behind` &rarr; Credit cap shed to 16 credits.

---

## 4. Mastery Engine: Completed vs. Proficient

The mastery engine decouples course completion from demonstrated proficiency. A grade on a student's transcript marks a course completed, while mastery probabilities require demonstrated empirical evidence from assessment drills.

---

## 5. Security & Safety

- **Anti-Jailbreak & Off-Topic Filter**: Caught and neutralized 42 of 42 prompt injection and off-topic cases.
- **Hallucination Interceptor**: Stripped unverified course codes with 100% reliability.

---

## 6. Cryptographic Plan Certification (Feature A)

- **Execution**: Evaluated across 20 student plans.
- **Tamper Detection**: Modifications trigger canonical SHA-256 hash mismatch.
- **Printable Vector PDF**: Clean one-page printable certificate exported with cryptographic seal.
