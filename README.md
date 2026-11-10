# Learning Buddy — IIT Bhilai B.Tech CSE Prototype
**Personalised Degree Planning & Adaptive Learning Platform**  
- **Author**: Yug Patel (`yppatel@iitbhilai.ac.in`), IIT Bhilai  
- **Target Programme**: B.Tech Computer Science and Engineering (2023 Batch Onwards), IIT Bhilai  
- **Live Website**: [https://adobe-buddy.onrender.com/](https://adobe-buddy.onrender.com/)  
- **API Documentation**: [https://adobe-buddy.onrender.com/docs](https://adobe-buddy.onrender.com/docs)  
- **Data Engineering Repository**: [https://github.com/yppatel-png/adobe-selection-assignment](https://github.com/yppatel-png/adobe-selection-assignment)  

---

## What is This?

This is my working prototype of the **Personalised Learning Buddy** built for the IIT Bhilai B.Tech CSE curriculum (`iit_bhilai_btech_cse_2023`).

Most academic advising bots are built as simple ChatGPT wrappers that search a PDF and try to guess what courses a student should take. That approach breaks immediately in real university life because LLMs hallucinate course codes, can't do cumulative multi-semester credit math, and don't understand prerequisite dependency graphs.

I took a different architectural approach: **code decides eligibility and course schedules; the LLM only translates the output into natural explanations.**

You can try the live interactive web app directly at **[adobe-buddy.onrender.com](https://adobe-buddy.onrender.com/)**.

---

## Core Features & How I Built Them

### 1. Multi-Semester Curriculum Scheduler
- **Topological Solver**: Solves course roadmaps across semesters while respecting hard prerequisite chains (DAG), offering parity (Odd/Autumn vs. Even/Spring terms), and semester credit bounds (12.0 min, 24.0 standard, 27.0 overload cap).
- **Deferred Core Queue**: If a required core course cannot fit in its template semester due to credit limits or unmet prerequisites, the solver places it in a deferred queue and reschedules it in the earliest eligible semester before any electives are scheduled.
- **Independent Plan Validator**: Candidate plans are checked by an independent 9-rule audit pass, issuing a cryptographically sealed Plan Certificate with a SHA-256 hash.

### 2. Difficulty-Weighted Bayesian Knowledge Tracing (BKT)
- **Probabilistic Mastery Tracking**: Updates latent student knowledge states ($P(L_t)$) per skill based on student response sequences. It scales slip ($P(S)$), guess ($P(G)$), and transition ($P(T)$) probabilities by question difficulty.
- **Time-Decay Retention**: Older, unpracticed competencies attenuate over a 90-day half-life window so that mastery status reflects current knowledge.
- **Evidence Hierarchy**: Self-declared skills can set initial priors, but cannot confirm mastery without verified assessment responses.

### 3. Dynamic Adaptation & Remediation
- **Automatic Pacing**: If a student demonstrates high cumulative mastery but struggles on recent prerequisite assessments, the adaptation engine prioritizes remediation over acceleration, suggesting review modules before moving forward.
- **Anti-Lucky-Quiz Protection**: A single lucky quiz score $\ge 0.85$ does not trigger acceleration unless supported by multiple assessment observations (`min_items_required = 3`).

### 4. Honest Data Provenance
To make sure institutional facts are never confused with working assumptions:
- **Verified Facts**: Sourced directly from the official IIT Bhilai *Courses of Study* PDF with exact page numbers cited.
- **Labelled Assumptions**: Institutional rules not published in the syllabus document (e.g. credit overload cutoffs) are marked as `assumption` ("pending ordinance") in the database and visibly tagged in the UI.

### 5. Sandboxed Practice Runner
- **AST Security Filter**: Python code exercises are checked using an Abstract Syntax Tree visitor (`SecurityVisitor`) that blocks unauthorized imports (`os`, `sys`, `subprocess`), dangerous builtins (`eval`, `exec`), and dunder reflection escapes.
- **Process Isolation**: Subprocess execution runs with a 7.0-second timeout, memory ceilings, and scrubbed environment variables.

---

## Live Deployment & Local Setup

### Live Demo
The application is deployed on Render:
- **Web App**: [https://adobe-buddy.onrender.com/](https://adobe-buddy.onrender.com/)
- **Swagger API Docs**: [https://adobe-buddy.onrender.com/docs](https://adobe-buddy.onrender.com/docs)
- **API Health**: [https://adobe-buddy.onrender.com/api/health](https://adobe-buddy.onrender.com/api/health)

### Running Locally

```bash
# 1. Clone the repository
git clone https://github.com/yppatel-png/MP5.git
cd MP5

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the local server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in your browser. On startup, the backend automatically initializes and seeds `data/buddy_bhilai.db`.

### Running with Docker

```bash
docker compose up --build
```
The application will run at `http://localhost:8000/`.

---

## Testing & Verification

I wrote automated test suites to verify that the scheduler, validator, BKT mathematics, and safety interceptors behave deterministically:

```bash
# Run the full automated test suite (133 tests + 45 subtests)
python scripts/run_tests.py

# Run Playwright browser and API smoke validation
python scripts/run_smoke.py

# Run audit test suites (P0 & P1)
python -m pytest tests/test_audit_p0.py tests/test_audit_p1.py

# Run the 5-stage data engineering pipeline
python run_pipeline.py
```

All 133 tests pass cleanly. A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the test runner automatically on every push.
