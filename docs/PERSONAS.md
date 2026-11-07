# Student Persona Specifications
Comprehensive profiles mapping diverse academic goals, design hypotheses, constraints, and learning trajectories across IIT Bhilai.

> [!NOTE]
> **Data Provenance & Survey Calibration Notice**:
> These student personas are synthesized as **working product design hypotheses** aligned directly with the illustrative archetypes in the Adobe Problem Statement (Appendix A) and initial qualitative interviews. They will be quantitatively re-calibrated against empirical student responses once the survey instrument (`docs/survey/questionnaire.md`) is deployed and analyzed via `scripts/analyze_survey.py`.

---

## 1. Hero Persona BH-SW-001: Aryan Sharma (Software Development Engineer)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Aryan Sharma (`BH-SW-001`)**, B.Tech CSE, Year 3, Semester 5. Current CGPA: 7.8. |
| **Design Hypothesis** | Students seeking top-tier software engineering roles require rigorous sequence planning through algorithms, operating systems, and distributed backends. |
| **Learning Objective** | Secure a tier-1 Software Development Engineer (SDE) placement by building verified core algorithmic problem-solving and systems knowledge. |
| **Mastery Criteria** | BKT $P(L_t) \ge 0.85$ across `data_structures`, `algorithms`, and `operating_systems`; verified completion of coding exercises. |
| **Success Metrics** | Placement readiness score $\ge 85\%$; successful completion of core requirements while preserving CGPA ($> 7.5$). |
| **Evaluation Process** | Diagnostic baseline assessment $\rightarrow$ CP-SAT semester planning $\rightarrow$ adaptive sandbox coding drills $\rightarrow$ timed interview checkpoints. |
| **Key Trade-off** | Heavy algorithmic and systems coursework (`CSL202` $\rightarrow$ `CSL301`) increases weekly workload by ~3.5 hrs/week vs. general electives. |

---

## 2. Hero Persona BH-RES-001: Priya Nair (AI Systems & Graduate Research)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Priya Nair (`BH-RES-001`)**, B.Tech CSE, Year 2, Semester 3. Current CGPA: 9.4. |
| **Design Hypothesis** | High-CGPA students seek academic acceleration (credit overload) and research electives, but risk violating semester offering parity or clash rules. |
| **Learning Objective** | Fast-track core prerequisites to unlock advanced machine learning (`CSL304`) and generative AI (`CSP352`) in Year 3. |
| **Mastery Criteria** | BKT $P(L_t) \ge 0.90$ across `artificial_intelligence`, `operating_systems`, and `discrete_mathematics`. |
| **Success Metrics** | 24-credit overload approval without clashes; reservation of final year slots for capstone research thesis. |
| **Evaluation Process** | Semester roadmap synthesis with overload flag $\rightarrow$ continuous diagnostic evaluation $\rightarrow$ systems benchmark harness. |
| **Key Trade-off** | Academic overload (24 credits) leaves reduced time for extracurricular leadership and non-academic commitments. |

---

## 3. Hero Persona BH-UPSC-001: Rohan Verma (UPSC Civil Services Preparation)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Rohan Verma (`BH-UPSC-001`)**, B.Tech CSE, Year 3, Semester 5. Current CGPA: 7.2. |
| **Design Hypothesis** | Civil services aspirants need predictable, well-paced elective schedules that satisfy graduation credits without heavy lab overload. |
| **Learning Objective** | Complete degree requirements while allocating 15+ hours/week to General Studies, policy, and public administration prep. |
| **Mastery Criteria** | Satisfy all degree credit requirements with sustained CGPA $\ge 7.0$; no remedial coursework needed. |
| **Success Metrics** | Semester course contact hours kept strictly balanced; zero lab overruns or unplanned overload. |
| **Evaluation Process** | Constraint-guided elective selection favoring high-yield, predictable humanities & social science electives (e.g. `LAL200`, `LAL101`). |
| **Key Trade-off** | Foregoes advanced systems electives in exchange for weekly study bandwidth and predictable GPA preservation. |

---

## 4. Hero Persona BH-ST-001: Devansh Kulkarni (Venture Creator & Startup Lead)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Devansh Kulkarni (`BH-ST-001`)**, B.Tech CSE, Year 3, Semester 5. Current CGPA: 8.1. |
| **Design Hypothesis** | Student founders struggle to bridge deep technical prototyping skills with commercial product design and team building. |
| **Learning Objective** | Pair software engineering and cloud systems with entrepreneurship and financial management electives (`LAL101`). |
| **Mastery Criteria** | Complete end-to-end deployed software prototype; demonstrate proficiency in relational data modeling and API architectures. |
| **Success Metrics** | Functional MVP launched; graduation requirements completed with $\ge 8.0$ CGPA. |
| **Evaluation Process** | Milestone-driven plan linking course projects directly to startup technical requirements. |
| **Key Trade-off** | Prioritizes product engineering courses over theoretical mathematics. |

---

## 5. Persona BH-REC-001: Siddharth Roy (Academic Recovery & Foundational Building)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Siddharth Roy (`BH-REC-001`)**, B.Tech CSE, Year 2, Semester 3. Current CGPA: 6.4. |
| **Design Hypothesis** | Students on academic warning or with sub-7.0 CGPA suffer from compounded prerequisite gaps and demoralization. |
| **Learning Objective** | Rebuild academic momentum, remediate foundational calculus and programming gaps, and lift CGPA safely above 7.0. |
| **Mastery Criteria** | BKT $P(L_t) \ge 0.75$ on remedial mathematics; pass all semester courses with minimum grade B. |
| **Success Metrics** | Academic warning lifted; zero repeat courses; cumulative CGPA improvement of +0.6 across two semesters. |
| **Evaluation Process** | Conservative credit cap (16.0 credits max) with embedded NPTEL remedial modules and weekly pacing check-ins. |
| **Key Trade-off** | Deferral of non-essential electives to final year to prioritize core course recovery. |

---

## 6. Persona BH-GRAD-001: Kavita Menon (International MS/PhD Research Aspirant)

| Dimension | Specification |
| :--- | :--- |
| **Persona** | **Kavita Menon (`BH-GRAD-001`)**, B.Tech CSE, Year 4, Semester 7. Current CGPA: 8.9. |
| **Design Hypothesis** | Graduate school applicants require advanced electives and faculty project credits to secure strong recommendation letters. |
| **Learning Objective** | Complete advanced machine learning and algorithm design coursework (`CSL304`, `CSP352`) while preserving high GPA for graduate admissions. |
| **Mastery Criteria** | High BKT mastery ($> 0.90$) in algorithmic complexity; submission of conference-track research paper. |
| **Success Metrics** | Standardized test prep time protected; GPA sustained above 3.8/4.0 equivalent ($> 8.8$). |
| **Evaluation Process** | High-level elective prioritization coupled with research milestone checkpoints. |
| **Key Trade-off** | Intensive seminar workload balances against standardized test preparation timelines. |
