# Learning Buddy — IIT Bhilai BTech CSE demo

This prototype now defaults to a compact, source-backed IIT Bhilai BTech Computer Science and Engineering curriculum snapshot. It is designed to let students explore the supplied curriculum and let judges try the supported flows without presenting unverified IIT Delhi rules as IIT Bhilai policy.

## What is supported

- The main demo contains 14 named CSE courses from the BTech schedule and catalogue, with source-cited credits and semester slots.
- The **New Student** flow lets a student enter profile details, review the supplied semester schedule, search the 44-course CSE catalogue, shortlist courses, and ask Buddy questions. It is a planning aid, not course registration.
- Three clearly labeled sample personas can be selected from the API-backed selector.
- Today shows the selected student's profile and evidence-aware status. Buddy can answer questions about courses in the compact seed using the cited course and semester information.
- The supplied source states 144 graded BTech credits plus 12 non-graded core units. A source discrepancy for `SL302`/`CSL302` is preserved in the data notes.

## Explicitly not claimed

The supplied source does not establish prerequisites, co-requisites, elective eligibility, course offerings, semester credit limits, workload estimates, or course-to-skill mappings. Consequently, the main Plan view is a **source schedule reference**, not a personalized plan or degree audit. Credit/prerequisite checks, academic certificates, skill-readiness claims, and course substitutions are disabled or marked unavailable. No learning modules or diagnostic exercises are included in this compact dataset yet.

See [data/DATA_QUALITY.md](data/DATA_QUALITY.md) and [data/seed_bhilai/dataset.json](data/seed_bhilai/dataset.json) for provenance and limitations. The historic IIT Delhi bundle remains under `data/seed/` for the separate legacy profile; it is not the default demo. The Bhilai demo uses `data/buddy_bhilai.db`, leaving an existing `data/buddy.db` untouched.

## Run the app

### Docker

```powershell
docker compose up --build
```

Open `http://localhost:8000/`. Swagger is at `http://localhost:8000/docs`. On first startup, the app initializes the isolated Bhilai database and checks every seeded persona's summary. Docker Compose behavior depends on Docker being installed.

### Local Python

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The default `INSTITUTE_PROFILE` is `iit_bhilai`; the app seeds the new database on first startup. To run the legacy dataset for regression testing, set `INSTITUTE_PROFILE=legacy` and use a separate database URL.

## Gemini Buddy (optional)

Set `LLM_API_KEY` in a private `.env` file and restart the app. Do not commit the key or paste it into source files. Without a key, Buddy uses deterministic responses. Live Gemini requests can include the student's question and relevant profile/curriculum context; do not enable live mode for data you are not allowed to share with the configured provider.

## Validation

```powershell
python scripts/run_tests.py
python scripts/run_smoke.py
```

The test runner executes legacy regressions and Bhilai seed/API checks in separate temporary databases. The smoke runner also exercises the browser flows. `make smoke` and `make verify` are available where GNU Make and their other dependencies are installed.
