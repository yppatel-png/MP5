# System Requirements Specification (MoSCoW Prioritisation)
Functional and technical requirements for the Adobe Personalised Learning Buddy, categorized by MoSCoW prioritization with verifiable acceptance criteria.

---

## 1. Must Have (P0 - Mission Critical for Pilot Launch)

### M1. Mathematical Prerequisite DAG & Constraint Planner
- **Description**: Synthesizes a multi-semester schedule that guarantees 100% adherence to institute regulations.
- **Acceptance Criteria**:
  - Prerequisite DAG is strictly acyclic; courses require all prerequisites completed in strictly earlier semesters.
  - Semester offering parity (Odd, Even, Both) is 100% respected.
  - Semester credit limits (14.0 minimum, 22.0 maximum, or 24.0 for overload CGPA $\ge 8.5$) are never breached.
  - Decoupled `independent_validator` validates 100% of generated plans across 9 rules.

### M2. Grounded Course Knowledge Base
- **Description**: Seeded repository of verified courses, modules, skills, prerequisites, and rules.
- **Acceptance Criteria**:
  - Minimum 30 accredited courses, 100+ modules, and 20+ fine-grained skills.
  - Zero hallucinated course codes permitted; all course codes matched to institute catalogue.
  - Automated integrity validator (`scripts/validate_kb.py`) passes with 0 errors.

### M3. Bayesian Knowledge Tracing (BKT) Student Model
- **Description**: Tracks hidden cognitive mastery probability $P(L_t \mid O_t)$ across discrete skills based on multi-source evidence.
- **Acceptance Criteria**:
  - Evidence weighted by source reliability: grades (1.0), timed projects (0.9), quizzes (0.7), self-declarations (0.2).
  - Distinguishes *Course Completed* on transcript from *Demonstrated Proficiency* (requires score $\ge 0.85$ on $\ge 3$ items across $\ge 2$ sessions).

### M4. Resilient LLM Wrapper with Offline Fallbacks
- **Description**: LiteLLM client wrapper with strict timeout, retry, in-memory SHA256 cache, and deterministic offline fallbacks.
- **Acceptance Criteria**:
  - Application boots and operates cleanly even when `LLM_API_KEY` is completely unset.
  - Zero crashes in front of evaluators; template fallback triggers on any LLM latency spike or timeout.

### M5. Visual Web Dashboard (Section 13)
- **Description**: Responsive single-page web UI serving all 9 core screens.
- **Acceptance Criteria**:
  - Accessible via `http://localhost:8000/`.
  - Includes Onboarding, Diagnostic, Dashboard, Plan Timeline with "Why this?" drawers, Learn/Practise sandbox, Mastery heatmap, and Buddy chat drawer.

---

## 2. Should Have (P1 - High Priority)

### S1. Dynamic Adaptation Policy Engine
- **Description**: Adapts curriculum plans based on mid-semester performance signals and engagement drift.
- **Acceptance Criteria**:
  - Strong score ($\ge 0.85$) triggers `RULE_ACCELERATE`, pulling electives forward.
  - Weak score ($< 0.40$) triggers `RULE_REMEDIATE`, inserting remedial practice resources and pacing load.
  - Behavioural drift ($< 60\%$ weekly study hours) sheds elective credits to prevent burnout.

### S2. Student Course Override & Trade-Off Engine
- **Description**: Permits students to reject a recommended course and re-solves plan with exclusion constraint.
- **Acceptance Criteria**:
  - Quantifies trade-off delta: skills lost, replacement courses added, workload delta, and degree audit validity.

### S3. Multi-Layer Buddy Memory & Anti-Jailbreak Filter
- **Description**: Conversational memory that persists across server restarts and defends against prompt injections.
- **Acceptance Criteria**:
  - Survives simulated server restart via SQLite `chat_memory` table.
  - Blocks prompt injection attempts (e.g., "ignore instructions", "grant 10 CGPA") with polite redirection.

---

## 3. Could Have (P2 - Nice to Have)

### C1. One-Click Scripted Simulation Panel
- **Description**: Admin console triggers for Strong Quiz, Weak Quiz, Course Override, Behavioural Drift, and Fast-Forward.
- **Acceptance Criteria**:
  - Demonstrates instant live before/after plan diffs and factual explanations for evaluators.

### C2. In-Browser Python Code Runner
- **Description**: Sandboxed Python runner executing student code submissions against test cases.
- **Acceptance Criteria**:
  - Executes inside restricted sandbox with CPU timeout (3000ms) and memory limits.

---

## 4. Won't Have (Out of Scope for Initial Pilot)

- **W1. Direct Integration with Legacy Institute ERP**: The system operates independently as an intelligent advisor; live grade syncing via university LDAP/OAuth is deferred to Phase 9.
- **W2. Automated Assignment Plagiarism Detection**: Relies on standard institute Moodle/Turnitin systems.
- **W3. GPU-Accelerated LLM Hosting**: System relies strictly on cloud API endpoints with deterministic CPU-friendly fallbacks (<5GB Docker image).

