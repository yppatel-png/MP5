# Learning Buddy — IIT Bhilai BTech CSE Personalised Learning System

A personalized learning and degree planning system for the IIT Bhilai BTech Computer Science & Engineering curriculum (`iit_bhilai_btech_cse_2023`). Built on a strict **Three-Tier Provenance Architecture**, the platform delivers the complete Adobe learning loop (**Assess, Personalise, Learn, Practise, Adapt, Demonstrate Mastery**) without conflating official institutional facts with pedagogical assumptions or team-authored content.

---

## Three-Tier Provenance Architecture

To maintain uncompromising academic integrity while delivering a complete learning experience, all data in the platform is partitioned into three transparent tiers:

### Tier 1 — Verified Institutional Facts (`provenance="verified"`)
- **Official Source**: Extracted directly from official institute documents (`data/raw/courses of study.pdf`).
- **Includes**: 34 verified courses across CSE core, departmental electives, CS minor path, and humanities/open electives, complete with course codes, titles, credits, L-T-P-C breakdowns, semester slots, official programme structure (144 graded credits + 12 non-graded core units), and explicitly printed course prerequisites with cited `source_page` numbers.
- **Ambiguity Queue**: Ambiguities or discrepancies (e.g. `SL302`/`CSL302`) are recorded in `data/review_queue.csv`.

### Tier 2 — Labelled Assumptions (`provenance="assumption"`)
- **Ordinance Gaps**: For policies not explicitly published in the syllabus document (e.g., semester credit minimums/maximums, minor eligibility CGPA, overload thresholds, online-credit caps, offering parity, weekly workload hours).
- **Transparency**: Stored as configurable academic rules marked with `provenance="assumption"`, a visible reason, and a `"pending ordinance"` note. Documented in `data/raw/ordinance_TODO.md`.
- **Badging**: The solver, validator, and cryptographic plan certificate run on these rules and prominently display an **"Assumed"** badge next to them (contrasted with **"Verified"** badges for Tier 1 rules), ensuring students and advisors never mistake an assumption for an official institute decree.

### Tier 3 — Team-Authored Learning Layer (`provenance="team_authored" / "derived"`)
- **Pedagogical Taxonomy**: 24 granular skills mapped across Computer Science, Mathematics, and Humanities domains.
- **Course-to-Skill Mappings**: 39 mappings grounded in course syllabus topics with confidence scores and source page citations.
- **Learning Modules**: 112 modules derived from course syllabi topics with learning objectives and concepts.
- **Real Assessment Items**: 240 original, validated practice and assessment items (exactly 10 per skill, difficulty 1 to 4) featuring:
  - Conceptual MCQs with distractors grounded in genuine student misconceptions.
  - Trace-the-output questions.
  - Numeric and short-answer calculation problems with clear evaluation rubrics.
  - Python coding exercises with sandboxed unit test suites.
- **Adaptive Diagnostic & BKT**: Difficulty-weighted Bayesian Knowledge Tracing scaling slip $p_s$, guess $p_g$, and transition rates by item difficulty, and computerized adaptive testing choosing items by information gain.
- **Goal Templates**: 4 career and academic tracks (`goal_software`, `goal_research`, `goal_upsc`, `goal_startup`) defining skill proficiency requirements and milestones.
- **Open Educational Resources**: Open resources (NPTEL, SWAYAM, MIT OCW, NCERT) with provider URLs, licenses, and verification timestamps.

---

## Restored Product Capabilities

- **Personalised Degree Planning**: Fast constraint solver generating valid multi-semester course roadmaps aligned to student career goals and current academic standing.
- **Cryptographic Plan Certificate**: Deterministic plan verification with SHA-256 certificate hashing, rule audit table, and live **Verified** vs **Assumed** provenance badges.
- **Why-Not & What-If Exploration**: Transparent rationales for every course recommendation, plus one-click course alternative suggestions.
- **Plan Version History**: Chronological version tracking with structural diffs (`plan_versions`).
- **Diagnostic & Exercise Sandbox**: Interactive diagnostic questions identifying student skill gaps, and a live exercise runner with automatic scoring, feedback, and evidence logging.
- **Difficulty-Weighted Bayesian Knowledge Tracing (BKT)**: Probabilistic skill mastery tracking and memory retention modeling.
- **Dynamic Adaptation Simulation**: Scenario engine demonstrating automatic curriculum remediation when students struggle with assessments.
- **Goal Reality Check**: Real-time gap analysis comparing student proficiencies against target role requirements.
- **Conversational Buddy**: Natural language advising grounded strictly in structured curriculum facts and student context.

---

## Sandbox Security & Code Execution Architecture

Python practice exercises are evaluated through a multi-tier hardened security boundary:
- **AST Static Analysis (`backend/practice/code_worker.py`)**: Before code is executed, an abstract syntax tree visitor (`SecurityVisitor`) strictly blocks:
  - Unauthorized module imports (`os`, `sys`, `subprocess`, `socket`, `pathlib`, `shutil`, `urllib`, `requests`, `ctypes`, etc.).
  - Unsafe built-in calls (`open`, `eval`, `exec`, `compile`, `globals`, `locals`, `getattr`, `breakpoint`).
  - Dunder reflection escapes (`__subclasses__`, `__globals__`, `__bases__`, `__mro__`, `__code__`).
- **Subprocess Isolation**: Code executes in a dedicated child worker process (`python -m backend.practice.code_worker`) decoupled from the web application server, with all sensitive environment variables scrubbed from the worker's environment.
- **Resource Limits & Timeouts**: Hardened with an absolute 7.0-second process timeout, 512 MB virtual memory ceiling (`RLIMIT_AS`), and a 2-second CPU ceiling (`RLIMIT_CPU`).
- **Restricted Built-in Scope**: Code runs in a clean scope limited to pure mathematical and algorithmic primitives (e.g. `range`, `len`, `int`, `min`, `max`, `sum`, `abs`, `sorted`).
- **Demo Toggle**: Code execution can be completely disabled for demo environments by setting `DISABLE_CODE_EXERCISES=true` in `.env`. When active, code submission endpoints return an informative advisory guiding the student to conceptual MCQs and rubric-graded exercises.

---

## Single Database Architecture (PostgreSQL)

The platform standardizes on **PostgreSQL 16** via SQLAlchemy 2.0 and psycopg2 as the single primary production database:
- Configured via `DATABASE_URL=postgresql://buddy_user:buddy_pass@db:5432/buddy_db` in `docker-compose.yml`.
- `students` database view: Automatically presents student profile records so database consoles (such as Adminer on `http://localhost:8080`) can inspect student records directly.
- Admin Grade Mutation: Editing a student's grade in Adminer or via `POST /api/admin/grade` updates the record, recalculates CGPA and BKT mastery, and immediately regenerates the active multi-semester plan without server restart.
- Clean Reset: `make reset` (`python -m backend.db.seed_loader --reset`) drops all tables and reloads clean institutional seed data.

---

## Security & LiteLLM Configuration

All LLM calls route through **LiteLLM**, completely decoupling the application from specific model vendors:
- **Zero Hardcoded Secrets or Model Defaults**: `LLM_MODEL` and `ADMIN_API_TOKEN` defaults have been eliminated from application code and compose files.
- **Offline Mode**: If `LLM_MODEL` or `LLM_API_KEY` is unset, the system runs in offline mode using deterministic, grounded rule templates.
- **Ephemeral Admin Token**: If `ADMIN_API_TOKEN` is unset in the environment, a cryptographically secure random token is generated at startup and logged once.
- **Code Execution Sandbox**: Python code exercises run with strict execution timeouts (7.0s), restricted builtins, and forbidden AST inspection blocking dangerous OS/file/network access.

---

## Quick Start

### Docker Compose (Recommended)

```powershell
docker compose up --build
```
- Web Application & API: `http://localhost:8000/`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Database Adminer Console: `http://localhost:8080` (System: PostgreSQL, Server: db, User: buddy_user, Pass: buddy_pass, DB: buddy_db)

### Local Setup

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Configure environment (copy demo values from .env.example)
cp .env.example .env

# 3. Start development server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Verification & Testing

```powershell
# Run the full automated test suite
python scripts/run_tests.py

# Run knowledge base integrity validator
python scripts/validate_kb.py

# Run student profile evaluation harness
python scripts/evaluate.py

# Run full end-to-end automated verification suite
python scripts/verify.py
```
