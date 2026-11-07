# Learning Buddy — IIT Bhilai BTech CSE Personalised Learning System

A personalized learning and degree planning system for the IIT Bhilai BTech Computer Science & Engineering curriculum. Built on a strict **Three-Tier Provenance Architecture**, the platform delivers the full Adobe learning loop (**Assess, Personalise, Learn, Practise, Adapt, Demonstrate Mastery**) without conflating official institutional policy with pedagogical or assumed data.

---

## Three-Tier Provenance Architecture

To maintain strict academic integrity while providing a rich learning experience, all data in the platform is partitioned into three transparent tiers:

### Tier 1 — Verified Institutional Facts (`provenance="verified"`)
- **Official Source**: Extracted directly from official institute documents (`data/raw/courses of study.pdf`).
- **Includes**: 34 verified courses across CSE core, departmental electives, CS minor path, and humanities/open electives, complete with course codes, titles, credits, L-T-P-C breakdowns, semester slots, official programme structure (144 graded credits + 12 non-graded core units), and explicitly printed course prerequisites with cited `source_page` numbers.
- **Ambiguity Queue**: Ambiguities or discrepancies (e.g. `SL302`/`CSL302`) are recorded in `data/review_queue.csv`.

### Tier 2 — Labelled Assumptions (`provenance="assumption"`)
- **Ordinance Gaps**: For policies not explicitly published in the syllabus document (e.g., semester credit minimums/maximums, minor eligibility CGPA, overload thresholds, online-credit caps, offering parity, weekly workload hours).
- **Transparency**: Stored as configurable academic rules marked with `provenance="assumption"`, a visible reason, and a `"pending ordinance"` note.
- **Badging**: The solver, validator, and cryptographic plan certificate run on these rules and prominently display an **"Assumed"** badge next to them (contrasted with **"Verified"** badges for Tier 1 rules), ensuring students and advisors never mistake an assumption for an official institute decree.

### Tier 3 — Team-Authored Learning Layer (`provenance="team_authored" / "derived"`)
- **Pedagogical Taxonomy**: 24 granular skills mapped across Computer Science, Mathematics, and Humanities domains.
- **Course-to-Skill Mappings**: 39 mappings grounded in course syllabus topics with confidence scores and source page citations.
- **Learning Modules**: 112 modules derived from course syllabi topics with learning objectives and concepts.
- **Original Exercises**: 112 original practice and assessment questions (MCQ, code, short answer, project) with validated correct answer keys grounded directly in module texts.
- **Goal Templates**: 4 career and academic tracks (`goal_software`, `goal_higher_studies`, `goal_upsc`, `goal_startup`) defining skill proficiency requirements and milestones.
- **Open Educational Resources**: Open resources (NPTEL, SWAYAM, MIT OCW, NCERT) with provider URLs, licenses, and verification timestamps.

---

## Restored Product Capabilities

- **Personalised Degree Planning**: Fast constraint solver generating valid multi-semester course roadmaps aligned to student career goals and current academic standing.
- **Cryptographic Plan Certificate**: Deterministic plan verification with SHA-256 certificate hashing, rule audit table, and live **Verified** vs **Assumed** provenance badges.
- **Why-Not & What-If Exploration**: Transparent rationales for every course recommendation, plus one-click course alternative suggestions.
- **Plan Version History**: Chronological version tracking with structural diffs (`plan_versions`).
- **Diagnostic & Exercise Sandbox**: Interactive diagnostic questions identifying student skill gaps, and a live exercise runner with automatic scoring, feedback, and evidence logging.
- **Bayesian Knowledge Tracing (BKT)**: Probabilistic skill mastery tracking and memory retention modeling.
- **Dynamic Adaptation Simulation**: Scenario engine demonstrating automatic curriculum remediation when students struggle with assessments.
- **Goal Reality Check**: Real-time gap analysis comparing student proficiencies against target role requirements.
- **Conversational Buddy**: Natural language advising grounded strictly in structured curriculum facts and student context.

---

## LiteLLM Configuration

All LLM calls route through **LiteLLM**, decoupling the application from specific model vendors and enabling seamless switches between local and cloud providers:

- Environment Variables:
  - `LLM_MODEL`: Model identifier (tested default: `gemini/gemini-3.5-flash-lite`; supports `gemini/*`, `openai/*`, `azure/*`, `ollama/*`).
  - `LLM_API_KEY`: API key for the chosen provider.
  - `LLM_API_BASE`: (Optional) Custom endpoint base URL for self-hosted or proxy deployments.
- **Offline Resilience**: When no API key is supplied or when network calls fail, the system falls back gracefully to deterministic, grounded template responses without breaking the user experience.

---

## Quick Start

### Local Setup

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Configure environment (optional: add LLM_API_KEY for live LLM)
cp .env.example .env

# 3. Start development server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/`. API documentation is available at `http://localhost:8000/docs`.

### Docker

```powershell
docker compose up --build
```

---

## Verification & Testing

```powershell
# Run the full test suite (82 tests, 122 subtests)
python scripts/run_tests.py

# Run the end-to-end smoke tests (pytest + Playwright browser flows)
python scripts/run_smoke.py

# Run knowledge base validation
python scripts/validate_kb.py
```
