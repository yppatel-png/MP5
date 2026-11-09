# Learning Buddy: IIT Bhilai B.Tech CSE

### Personalised Degree Planning, Diagnostic Assessment & Adaptive Learning System
- **Institution & Cohort**: Indian Institute of Technology Bhilai — B.Tech Computer Science and Engineering (2023 Batch Onwards)
- **Live Application**: [https://adobe-buddy.onrender.com/](https://adobe-buddy.onrender.com/)
- **API Documentation**: [https://adobe-buddy.onrender.com/docs](https://adobe-buddy.onrender.com/docs)
- **Data Engineering Repository**: [https://github.com/yppatel-png/adobe-selection-assignment](https://github.com/yppatel-png/adobe-selection-assignment)
- **Developer**: Yug Patel (`yppatel@iitbhilai.ac.in`), IIT Bhilai

---

## System Overview

Learning Buddy is a full-stack personalised academic advising and diagnostic learning platform built for the IIT Bhilai B.Tech Computer Science and Engineering curriculum (`iit_bhilai_btech_cse_2023`).

The system implements the complete Adobe educational loop: **Assess $\to$ Personalise $\to$ Learn $\to$ Practise $\to$ Adapt $\to$ Demonstrate Mastery**. It pairs deterministic constraint optimization for degree scheduling with probabilistic cognitive modeling for student skill mastery, preventing the hallucinations and arithmetic errors inherent to pure LLM-based academic advisors.

---

## Core Engineering Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Core                        │
│                                                                        │
│   ┌───────────────────────────┐     ┌──────────────────────────────┐   │
│   │  Multi-Semester Planner   │     │  Bayesian Knowledge Tracing  │   │
│   │  • Topological DAG Solver │     │  • Probabilistic Mastery Pt  │   │
│   │  • Offering Parity (O/E)  │     │  • Time-Decay Half-Life      │   │
│   │  • Deferred Core Queue    │     │  • Anti-Self-Declared Gate   │   │
│   │  • Independent Validator  │     │  • Granular Skill Mapping    │   │
│   └─────────────┬─────────────┘     └──────────────┬───────────────┘   │
│                 │                                  │                   │
│   ┌─────────────┴─────────────┐     ┌──────────────┴───────────────┐   │
│   │ Dynamic Adaptation Policy │     │ Grounded Conversational Buddy│   │
│   │ • Remediation on Struggle │     │ • Intent Word-Boundary Parser│   │
│   │ • Pacing & Deferral Rules │     │ • 1500-Token Bounded Context │   │
│   │ • Anti-Lucky-Quiz Barrier │     │ • Hard Code Interceptor      │   │
│   └───────────────────────────┘     └──────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Deterministic Multi-Semester Curriculum Solver
- **Constraint Scheduling**: Solves multi-semester academic schedules subject to semester offering parity (Odd/Autumn vs. Even/Spring), hard prerequisite chains, and semester credit bounds (12.0 min, 24.0 standard, 27.0 overload ceiling).
- **Deferred Core Queue**: Core courses that cannot be scheduled in a given semester due to prerequisites or credit limits are placed into a deferred queue and re-evaluated in the earliest eligible semester before electives are scheduled.
- **Decoupled Independent Validator**: Candidate schedules are verified by an independent 9-rule audit pass, issuing cryptographically sealed Plan Certificates with SHA-256 hashes.

### 2. Difficulty-Weighted Bayesian Knowledge Tracing (BKT)
- **Probabilistic Mastery**: Tracks latent student knowledge states ($P(L_t)$) per skill based on assessment response sequences, weighting slip ($P(S)$), guess ($P(G)$), and transition ($P(T)$) probabilities by item difficulty.
- **Evidence Decay**: Incorporates time-decay modeling where older unpracticed competencies attenuate over a 90-day half-life window.
- **Strict Evidence Hierarchy**: Self-declared competencies can contribute prior signals ($P(L_0)$) but can never confirm mastery without verified assessment items.

### 3. Dynamic Adaptation Policy
- **Automated Pacing**: Monitors continuous performance signals (quiz scores, diagnostic struggle, study adherence).
- **Remediation Priority**: When a student demonstrates high cumulative mastery but struggles on recent prerequisite assessments, the adaptation policy prioritizes remediation over acceleration, inserting foundational modules and pacing adjustments.
- **Anti-Lucky-Quiz Protection**: Single quiz scores $\ge 0.85$ cannot trigger acceleration unless supported by multiple assessment observations (`min_items_required = 3`).

### 4. Three-Tier Provenance System
To ensure academic honesty, all information in the platform carries transparent provenance:
- **Tier 1 (Verified Institutional Facts)**: Directly transcribed from official institute documents (`data/raw/courses of study.pdf`) with cited page numbers.
- **Tier 2 (Labelled Assumptions)**: Institutional policies not published in the syllabus document (e.g., credit caps, overload thresholds) are explicitly designated as `provenance="assumption"` and labeled "pending ordinance" in the UI.
- **Tier 3 (Pedagogical Content)**: Formative exercises, learning modules, and skill mappings authored by the team to deliver an interactive experience.

### 5. Sandboxed Code Execution
- **AST Security Filter**: Python code exercises undergo Abstract Syntax Tree validation via `SecurityVisitor`, strictly blocking unauthorized module imports (`os`, `sys`, `subprocess`, `socket`), unsafe builtins (`open`, `eval`, `exec`), and reflection escapes.
- **Resource Constraints**: Subprocess workers run with strict timeouts (7.0 seconds), memory ceilings (512 MB), and sanitized environment variables.

---

## Live Deployment & Local Setup

### Live Deployment
The web application is live and accessible at:
- **Production URL**: [https://adobe-buddy.onrender.com/](https://adobe-buddy.onrender.com/)
- **Swagger API Docs**: [https://adobe-buddy.onrender.com/docs](https://adobe-buddy.onrender.com/docs)
- **Health & Telemetry**: [https://adobe-buddy.onrender.com/api/health](https://adobe-buddy.onrender.com/api/health)

### Running Locally with Python

```bash
# 1. Clone repository
git clone https://github.com/yppatel-png/MP5.git
cd MP5

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start local development server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/` in your browser. The application seeds `data/buddy_bhilai.db` automatically on first launch.

### Running with Docker

```bash
docker compose up --build
```
The application will be available at `http://localhost:8000/`.

---

## Verification & Automated Test Suites

The codebase includes comprehensive automated test suites enforcing curriculum correctness, solver determinism, BKT accuracy, and security boundaries.

```bash
# 1. Run full test runner (133 tests + 45 subtests)
python scripts/run_tests.py

# 2. Run Playwright browser and API smoke validation
python scripts/run_smoke.py

# 3. Run core audit test suites (P0 & P1)
python -m pytest tests/test_audit_p0.py tests/test_audit_p1.py

# 4. Run reproducible data engineering pipeline
python run_pipeline.py
```

### Continuous Integration
Automated CI workflows (`.github/workflows/ci.yml`) execute on every push, ensuring all test suites, DAG verification checks, and smoke tests pass.

---

## License

Developed for the Adobe Inter-IIT Tech Meet 15.0 competition. All curriculum data is sourced from Indian Institute of Technology Bhilai documentation.
