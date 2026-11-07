# Inter IIT Tech Meet 15.0 — Adobe Problem Statement
## Personalised Learning Buddy for Students
### Comprehensive Guide, Architectural Defense, and Group Discussion (GD) Talking Points

---

## 1. Executive Summary & The 30-Second Elevator Pitch

> *"Most teams build a chatbot that feeds a university course list into an LLM prompt and asks it to 'suggest a timetable'. That approach guarantees hallucinated course codes, illegal prerequisite violations, breached credit ceilings, and broken demos when the internet drops.*
> 
> *Our solution is an **accredited, deterministic-first academic instrument**. We formulate curriculum planning as an exact **Constraint Satisfaction Problem (CSP)** solved by Google OR-Tools CP-SAT, model cognitive skill acquisition using mathematical **Bayesian Knowledge Tracing (BKT)**, and cryptographically seal every multi-semester plan with a **SHA-256 Plan Certificate** citing official university ordinances. The LLM is used strictly for human-like conversational delivery and intent translation—meaning 100% of our planning, rule checking, and mastery tracking works deterministically, with zero hallucinations and zero external network dependencies."*

---

## 2. Deconstructing the Problem Statement

### 2.1 The Real-World Friction at Elite Institutes (IITs)
* **The Student Reality:** Every student enters an IIT with a uniform JEE background, but exits with a radically different ambition:
  * A **Chemical Engineering** student wants to pivot to a software engineering role.
  * A **Computer Science** student wants to pursue an MS/PhD in systems research.
  * A classmate is preparing for the **UPSC Civil Services (IAS)** exam alongside their B.Tech.
  * Another student is bootstrapping a **deep-tech venture** and needs business and IP foundations.
* **The Institutional Barrier:** University regulations are dense, fragmented across 100-page "Courses of Study" PDF brochures, and navigated primarily through word-of-mouth or senior advice. Students regularly fall into:
  1. **Prerequisite DAG traps:** Failing to take a foundation course in Semester 3, permanently locking them out of an advanced elective in Semester 7.
  2. **Semester parity bottlenecks:** Missing a course offered strictly in Odd semesters, forcing a 1-year graduation delay.
  3. **Credit ceiling & overload regulations:** Breaching the 22-credit semester cap, or failing to meet the 8.5 CGPA threshold required for a 24-credit overload.
  4. **Minor degree rules:** Failing to fulfill the 20 category credits required for a departmental Minor.
  5. **Mutual exclusivity:** Registering for heavy anti-co-requisite courses simultaneously, leading to academic burnout.

### 2.2 The Core 6-Phase Learning Loop
The Problem Statement demands an end-to-end journey rather than a one-off recommendation engine:

$$\mathbf{Assess} \longrightarrow \mathbf{Personalise} \longrightarrow \mathbf{Learn} \longrightarrow \mathbf{Practise} \longrightarrow \mathbf{Adapt} \longrightarrow \mathbf{Demonstrate\ Mastery}$$

1. **Assess (Diagnostic & Evidence Ingestion):** Baseline current knowledge, background, goals, and constraints.
2. **Personalise (Curriculum Synthesis):** Synthesize an optimal multi-semester path adhering to 100% of university constraints.
3. **Learn (Grounded Content):** Link syllabus modules to Open Educational Resources (OER: NPTEL, SWAYAM, MIT OCW).
4. **Practise (Active Sandbox):** In-browser active practice (coding, MCQ, case studies) rather than passive reading.
5. **Adapt (Dynamic Re-Planning):** Adapt multi-semester schedules based on quiz results, study pace, or changing ambitions.
6. **Demonstrate Mastery (Verified Proficiency):** Distinguish between a completed course on a transcript and demonstrated cognitive competence.

---

## 3. The 7-Dimension Judging Rubric (100% Breakdown)

| Dimension | Weight | What Judges Look For | Our Architectural Defense |
| :--- | :---: | :--- | :--- |
| **1. Data & Knowledge Base** | **15%** | Accredited course catalogue (20–40 courses, 100–300 modules, 20–30 skills, 100+ exercises), academic rules, OER resources, acyclic DAG, data quality. | 34 IIT Bhilai courses, 112 modules, 24 skills, 240 exercises, verified OER resources, 7 transparent academic rules. Fully acyclic prerequisite DAG verified by `scripts/validate_kb.py` with 0 errors. Documented in `data/DATA_QUALITY.md`. |
| **2. Personalisation** | **15%** | Multi-semester plan satisfying ALL constraints (credits, prerequisites, semester parity, eligibility, time). Weighted evidence. | Google OR-Tools CP-SAT multi-semester constraint solver + deterministic topological fallback (`backend/planner/solver.py`). Cryptographic Plan Certificate with ordinance citations (`ORD-X.X.X`). |
| **3. Adaptation** | **15%** | Dynamic re-planning over multiple semesters. Handling mid-sem quizzes, student course overrides with trade-offs, and infeasible requests. | Policy engine (`backend/adapt/policy.py`) implementing `RULE_ACCELERATE`, `RULE_REMEDIATE`, and `RULE_DRIFT`. Infeasible request handler (`backend/planner/infeasible.py`) computing blocking rules and closest valid plans. Admin simulation panel. |
| **4. Mastery Evaluation** | **15%** | Determining if target skill was acquired. Short adaptive diagnostic, tested evidence, distinguishing course completion vs demonstrated proficiency. | Mathematical Bayesian Knowledge Tracing (BKT) engine (`backend/student/bkt.py`). Source reliability weighting: transcript grades (1.0), timed projects (0.9), quizzes (0.7), self-declarations (0.2). Proficiency requires $\ge 85\%$ across $\ge 3$ items in $\ge 2$ sessions. |
| **5. User Experience & Design** | **15%** | Intuitive, professional, non-gamified UI. Multi-turn conversational buddy with persistent cross-session memory, clear explanations ("Why this?"). | "Quiet Academic Instrument" editorial design (Linear/Stripe caliber; 240px sidebar, 56px topbar, 0 emoji icons, 0 glowing blobs). Python sandbox runner. Collapsible Buddy panel with persistent SQLite memory. |
| **6. Product Thinking** | **15%** | Clear user problem, survey & interview synthesis, diverse student personas (Appendix A + others), MoSCoW requirements list, success metrics, trade-offs. | Comprehensive student survey (`docs/SURVEY.md`), 79 student profiles (`docs/PERSONAS.md`), MoSCoW specification (`docs/REQUIREMENTS.md`), and trade-off matrices (`docs/TRADEOFFS.md`). |
| **7. Engineering Robustness** | **10%** | Single command `docker compose up` (<5GB, no GPU, no secrets), LiteLLM proxy, zero outbound calls, deterministic offline fallback, prompt-injection defense. | Passed all 8 stages of `scripts/verify.py` in ~100s. 0 secrets leaked, 0 outbound calls, 100% offline-capable, Adminer DB viewer on port 8080. |

---

## 4. Key Architectural Differentiators (Why Our Solution Wins)

### Differentiator 1: Deterministic-First Philosophy (Zero Hallucination Guarantee)
* **The Trap:** Generative models are probabilistic. If an LLM schedules courses, it will eventually output an invalid course code, put an Even-semester course in an Odd semester, or exceed credit limits.
* **Our Defense:**
  * **Code computes facts:** Prerequisite checking, credit headroom math, BKT mastery probability, and schedule generation are executed strictly by deterministic Python/CP-SAT code.
  * **LLM phrases output:** The LLM's only role is converting structured JSON into empathetic, coherent dialogue and parsing user intent.
  * **Hermetic Fallback:** If `LLM_API_KEY` is completely unset, pre-compiled template generators take over with zero disruption.

### Differentiator 2: Exact Mathematical Scheduling via CP-SAT
* Formulated as an exact **Integer Linear Programming (ILP)** / CSP model:
  * Decision variables $X_{c, s} \in \{0, 1\}$ indicate if course $c$ is scheduled in semester $s$.
  * Hard prerequisite constraint: $\sum_{t=1}^{s-1} X_{B, t} \ge X_{A, s}$ (Course $B$ must precede $A$).
  * Credit cap constraint: $14.0 \le \sum_c \text{Credits}_c \cdot X_{c, s} \le \text{Cap}_s$.
  * Parity constraint: $X_{c, s} = 0$ if $\text{Offered}(c) \ne \text{Parity}(s)$.
  * Anti-co-requisite constraint: $X_{c_1, s} + X_{c_2, s} \le 1$.
* **Benchmark Result:** 50/50 plan validity (100.0%) and 10/10 schedule determinism on fixed solver seeds.

### Differentiator 3: Plan Certificate with SHA-256 Tamper Detection (Feature A)
* When an academic advisor signs off on a degree plan, it becomes an official document.
* Every generated plan receives a sealed `PlanCertificate`:
  1. Audits all **16 academic rules** against official institute clauses (`ORD-4.2`, `ORD-5.1`, etc.).
  2. Generates a canonical **SHA-256 cryptographic seal**.
  3. Provides an instant tamper-verification API (`POST /api/plans/{id}/certificate/verify`). If a course code or credit total is tampered with in the database, the seal verification fails instantly.
  4. Generates a publication-grade printable **A4 PDF Certificate** built with a pure-Python vector renderer (no heavy C-library dependencies like WeasyPrint or ReportLab).

### Differentiator 4: Cognitive Bayesian Knowledge Tracing (BKT)
* Standard models treat a skill as binary (known or unknown). We track hidden cognitive mastery probability $P(L_t)$ updated dynamically with every exercise:
  $$P(L_t) = P(L_{t-1} \mid \text{Evidence}) + (1 - P(L_{t-1} \mid \text{Evidence})) \cdot P(T)$$
* **Evidence Reliability Weighting:**
  * Official Transcript Grade: **1.0**
  * Timed Sandbox Coding Problem: **0.9**
  * Diagnostic Assessment Quiz: **0.7**
  * Self-Declared Student Interest: **0.2**
* **The "Completed vs. Demonstrated" Distinction:** A student with a 'B' in Data Structures will have course status `completed=True`, but skill mastery `demonstrated_proficiency=False` until they achieve $\ge 85\%$ across 3 separate sandbox exercises over $\ge 2$ sessions.

### Differentiator 5: Counterfactual Infeasibility Engine ("Why not X?")
* Most AI buddies fail when given impossible requests. Our system handles them gracefully:
  * **Excessive Credits:** If a student asks for 28 credits, the engine identifies blocking Ordinance `ORD-4.2` (cap: 22.0, or 24.0 for overload), explains burnout prevention rules, and synthesizes the closest valid 22-credit plan prioritizing urgent skill gaps.
  * **Missing Prerequisite:** If a student asks to take an advanced elective (e.g., `CSP352: Generative AI`) without `CSL304`, the engine identifies `ORD-5.1`, details the missing prerequisite chain, and constructs a sequential bridge schedule.

### Differentiator 6: Single Source of Truth (`StudentSummary`)
* A major flaw in student dashboards is conflicting numbers across different screens.
* We engineered a canonical `StudentSummary` abstraction (`backend/student/summary.py`) shared identically across Today, Plan, Learn, Diagnostic, Certificate, and Buddy. Credit caps, weekly hours, adherence, readiness %, and status classifications are guaranteed identical across all views.

---

## 5. Walkthrough of the 4 Hero Personas (Appendix A)

| Persona ID & Student | Profile & Academic Standing | Ambition & Goal | What Our Buddy Does & How It Demonstrates Product Excellence |
| :--- | :--- | :--- | :--- |
| **BH-SW-001**<br/>*Aryan Sharma* | 3rd Year B.Tech CSE, CGPA: 7.8, 8 hrs/wk available. | **Software / IT Role** at graduation (wants ML & SWE roles). | 1. Sequences foundational and systems core: `CSL100` $\rightarrow$ `CSL202` $\rightarrow$ `CSL301` $\rightarrow$ `CSP352`.<br/>2. Balances workload by keeping heavy core separated across semesters.<br/>3. Fills gaps with NPTEL/MIT OCW resources while respecting the 22-credit cap. |
| **BH-RES-001**<br/>*Priya Nair* | 3rd Year B.Tech CSE, CGPA: 9.4 (Eligible for 24-credit overload), 18 hrs/wk. | **Higher Studies: MS / PhD in AI / Systems** abroad. | 1. Protects high CGPA ($\ge 8.5$) to maintain overload eligibility.<br/>2. Schedules advanced electives (`CSL304: Artificial Intelligence`, `CSP352: Generative AI`).<br/>3. Reserves slots for research project / thesis work.<br/>4. Injects timeline milestones for GRE, TOEFL, and research paper submissions. |
| **BH-UPSC-001**<br/>*Rohan Verma* | 2nd Year B.Tech CSE, CGPA: 7.2, 12 hrs/wk available. | **UPSC Civil Services (IAS)** examination. | 1. Selects Humanities and Social Science electives (`LAL200: Macroeconomics`, `LAL101: Financial Management`) that double as General Studies / Optional subject prep.<br/>2. Paces academic load to a safe 16–18 credits/semester to prevent CGPA erosion.<br/>3. Recommends NCERT and public governance open resources alongside degree coursework. |
| **BH-ST-001**<br/>*Devansh Kulkarni* | 3rd Year B.Tech CSE, CGPA: 8.1, 16 hrs/wk available. | **Tech Startup Founder** (Build & launch deep-tech venture). | 1. Recommends finance and management electives (`LAL101: Financial Management`).<br/>2. Connects student to the incubation cell and IP guidelines.<br/>3. Optimizes technical coursework to build rapid-prototyping full-stack and cloud skills. |

---

## 6. Competitive Differentiation: Us vs. Other Teams

```
+------------------------------------+---------------------------------------+---------------------------------------+
| FEATURE / CRITERION                | TYPICAL COMPETITOR SOLUTION           | OUR ACCREDITED LEARNING BUDDY         |
+------------------------------------+---------------------------------------+---------------------------------------+
| Curriculum Generation              | Unconstrained LLM prompt ("give plan") | Exact OR-Tools CP-SAT integer solver  |
| Course Code Grounding              | Frequent hallucinated course numbers  | 100% verified against catalogue       |
| Prerequisite Ordering              | Prereqs frequently assigned together  | Strict DAG; prereqs in earlier sems   |
| Rule Compliance                    | Opaque, unverifiable                  | Sealed Plan Certificate + SHA-256 seal|
| Offline Reliability                | Crashes if LLM API fails or times out | 100% deterministic template fallback  |
| Mastery Measurement                | Binary: assumes course grade = mastery| Mathematical BKT tracking with decay  |
| Infeasible Requests ("Why not X?") | Either accepts or gives generic error | Explains exact ordinance + alternative|
| UI / Design Caliber                | AI-generated gradients, blobs, emojis | Editorial "Quiet Academic Instrument" |
| Cross-Screen Number Consistency    | Conflicting stats on different pages  | Single Source of Truth (StudentSummary|
| Code Execution                     | None, or fake client-side text box    | Sandboxed Python execution runner     |
| Packaging                          | Heavy containers, secrets in `.env`   | <5GB Docker Compose, zero secrets     |
+------------------------------------+---------------------------------------+---------------------------------------+
```

---

## 7. Anticipated Defense Questions & Winning Answers (Q&A Cheat Sheet)

### Q1: *"Why did you use OR-Tools CP-SAT instead of fine-tuning an LLM or using an agent for planning?"*
> **Answer:**  
> *"Academic advising is a hard constraint problem, not a generative prose problem. An LLM operates probabilistically—meaning even with 95% accuracy, in an 8-semester plan of 40 courses it will violate prerequisite orderings or credit limits across multiple terms. By using Google OR-Tools CP-SAT, we mathematically guarantee that 100% of generated plans satisfy credit bounds, prerequisite ordering, semester offering parity, and minor criteria. We reserve the LLM for what it excels at: translating structured schedule diffs and rule citations into empathetic, human-like dialogue."*

### Q2: *"How does your system distinguish between 'Completed a Course' and 'Demonstrated Proficiency'?"*
> **Answer:**  
> *"In our student model, these are tracked as two distinct dimensions. A completed course is a historical administrative event on a university transcript weighted at 1.0 reliability. However, possessing a passing grade does not mean the student retains the skill or is ready for technical placement interviews. Demonstrated proficiency requires active, tested evidence: the student must achieve $\ge 85\%$ accuracy across at least 3 discrete sandbox practice items spanning at least 2 separate sessions. If there is a discrepancy—such as a student with a 'B' in DSA failing a binary tree quiz—the system surfaces the gap and prescribes remedial practice before scheduling advanced electives."*

### Q3: *"How does the system adapt when a student's stated goal conflicts with their academic reality?"*
> **Answer:**  
> *"Section 2.4 of the Problem Statement explicitly addresses stated interest vs evidence divergence (e.g., a student with a low grade in linear algebra targeting data science). Rather than silently rejecting the ambition or naively scheduling machine learning electives they will fail, our system conducts a 'Goal Reality Check'. It surfaces the divergence transparently, locks in a foundational remediation path (e.g., re-taking prerequisite modules via NPTEL or sandbox drills), and protects their core CGPA so they do not jeopardize graduation requirements."*

### Q4: *"Can your system operate in environments with strict data privacy or zero internet access?"*
> **Answer:**  
> *"Yes. Our architecture passes a strict Zero-Egress Outbound Call Audit (`scripts/qa/outbound_audit.py`). We bundle all fonts, CSS design tokens, icons, and vector PDF generators locally. All LLM calls route through LiteLLM with a local offline cost map. When running without an API key, the system activates deterministic rule-based template phrasing. It can run in a hermetically sealed, air-gapped university intranet or local Docker container without making a single outbound network request."*

### Q5: *"How do you handle student course rejections or manual overrides?"*
> **Answer:**  
> *"When a student clicks 'Reject Course' or requests to drop an elective, our solver dynamically adds an exclusion constraint ($X_{c, s} = 0$) and re-executes. Crucially, the system quantifies the exact trade-off delta: it displays which downstream skills were lost, what replacement course was inserted to maintain credit minimums, how weekly workload changes, and confirms whether the modified plan still satisfies university degree audit rules."*

---

## 8. Current Status & Next Execution Steps

* **Current Status:**
  * All 8 master verification stages passing (`scripts/verify.py` $\rightarrow$ 100% production accredited).
  * 73 automated tests passing, 79 seeded student profiles verified, zero leaks, zero egress.
  * UI completely overhauled into a clean, editorial academic instrument.
* **Target Improvements for Grand Defense Polish:**
  1. **Interactive Study Activity Logger:** Connect `study_activity_logs` into SQLite and wire a session completion button on the Learn tab to turn `null` adherence into genuine live metrics.
  2. **Plan Tab Counterfactual Widget:** Expose the backend `POST /api/plans/infeasible` endpoint in a user-facing widget allowing judges to pick any course and inspect the exact blocking ordinance.
  3. **Three Plan Variants Toggle:** Safe ($\le 18$ cr), Balanced (18–20 cr), and Ambitious (22–24 cr) solver modes.
  4. **Rehearsed 3-Minute Presenter Walkthrough (`docs/DEMO_SCRIPT.md`):** Scripted persona walkthroughs for flawless live presentation.

