# Ideas Note: Operationalising the IIT Bhilai Knowledge Base

**Scope**: 1-Page Architectural Note on Knowledge Base Utilisation & Capability Boundaries  
**Target Domain**: Personalised Academic Advising for B.Tech CSE (IIT Bhilai)

---

## 1. System Vision & Data Utilization Strategy

This source-traced knowledge base is designed to power a **hybrid, verifiable academic advising buddy**. Rather than relying on unconstrained LLM generation (which hallucinates non-existent course codes or invents institute ordinances), the system operates on a **dual-layer architecture**:

1. **Deterministic Constraint & Graph Layer (Code Decides)**:
   - Uses `prerequisites.json` as a Directed Acyclic Graph (DAG) for valid topological course scheduling.
   - Enforces credit floors, caps, overload ceilings, and minor eligibility directly through `academic_rules.json`.
   - Computes Bayesian Knowledge Tracing (BKT) and skill gap vectors by traversing `course_skills.json`.
2. **Grounded Retrieval & Explanatory Layer (LLM Explains)**:
   - Queries `chunks.jsonl` using vector search to retrieve official ordinance clauses, course objectives, and learning resources.
   - Synthesizes student-facing explanations that cite exact syllabus page numbers and official source URLs.

---

## 2. Three Student Questions the Buddy Can Answer Well

### Question 1: Prerequisite Traversal & Schedule Feasibility
> *"Can I take Operating Systems (CSL301) in Semester 4, and what prerequisites must I clear first?"*
- **Why the data supports it**: The prerequisite graph (`prerequisites.json`) explicitly defines `CSL201` (Computer Organization) and `CSL202` (Data Structures) as hard prerequisites, while `courses.json` records that `CSL301` is standardly scheduled in Semester 5 (an odd semester).
- **Buddy Execution**: The solver verifies whether the student passed `CSL201` and `CSL202`, checks offering parity (odd vs. even term), and either confirms eligibility or proposes a valid rescheduling, citing *Courses of Study, p. 83*.

### Question 2: Workload, Credit Overload & Minor Eligibility Audits
> *"I have a 7.8 CGPA and want to take 22 credits next semester to complete an AI minor. Am I eligible?"*
- **Why the data supports it**: `academic_rules.json` contains quotable rules (`rule_sem_max_credits`, `rule_credit_overload_cap`, `rule_minor_cse_eligibility`).
- **Buddy Execution**: The rule engine checks the student's 7.8 CGPA against the institute threshold ($\ge 7.5$), confirms that overloading up to 22 credits is permitted for strong students, and verifies that the selected minor courses fit within the weekly workload ceiling without prerequisite conflicts.

### Question 3: Personalized Skill-Gap Remediation with Open Resources
> *"I want to pursue Machine Learning, but my diagnostic assessment in Linear Algebra and Probability was low. What open resources and courses should I take?"*
- **Why the data supports it**: The bipartite mapping between `skills.json`, `course_skills.json`, and `resources.json` connects `probability_statistics` to `MAL201`/`MAL403` and curated open content (MIT OCW 18.06 Gilbert Strang, NPTEL).
- **Buddy Execution**: The buddy generates a concrete, 3-week remediation plan with direct links, license terms (CC BY-NC-SA 4.0), and estimated hours before the student registers for advanced AI electives.

---

## 3. Three Student Questions the Buddy CANNOT Answer (and Boundaries)

### Question 1: Instructor Identity & Subjective Pedagogical Leniency
> *"Who is teaching CSL202 next semester, and does that professor have a strict attendance policy?"*
- **Why the data cannot answer it**: The Courses of Study and institute curricula define static academic objectives, syllabus topics, and credit distributions—not dynamic faculty semester assignments or individual grading reputations.
- **System Guardrail**: The buddy intercepts non-curricular inquiries and replies honestly: *"Faculty allocations and attendance policies are set on a per-semester basis by the department and are not part of the static course curriculum."*

### Question 2: Speculative Grade Predictions & GPA Guarantees
> *"If I register for Computer Networks and Distributed Systems together, can you guarantee I will get an A grade and reach an 8.5 CGPA?"*
- **Why the data cannot answer it**: Academic performance depends on relative grading curves, cohort variance, and individual examination execution. 
- **System Guardrail**: The buddy computes total weekly workload ($48\text{h}$ contact + self-study load) and flags workload strain honestly, but explicitly disclaims grade predictions: *"I can evaluate your workload feasibility, but grading outcomes depend on relative course assessments and cannot be guaranteed."*

### Question 3: Discretionary Senate Waivers & Administrative Exceptions
> *"Can you waive the prerequisite for CSL302 so I can graduate one semester early?"*
- **Why the data cannot answer it**: Automated academic systems must never violate institute governance. Prerequisite waivers require formal petition to the Senate and the Dean of Academic Affairs (DoAA).
- **System Guardrail**: The buddy blocks illegal schedule states and guides the student through official institute protocol: *"Automated systems cannot waive senate-mandated prerequisites. You must consult your Faculty Advisor and submit a formal petition to the Academic Office."*

