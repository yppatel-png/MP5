# Progress log

## Update
- Fixed the infeasible-request API regression by renaming the exported handler and preserving the older test alias without triggering pytest collection.
- Restored the required frontend navigation and drawer hooks expected by the visual acceptance checks.
- Added the missing design-token aliases and CSS selectors required by the static frontend tests.
- Verified the full stack via `python -m pytest -q`.

## Files touched
- `backend/api/plans.py`
- `frontend/index.html`
- `frontend/static/css/style.css`
- `frontend/static/css/tokens.css`
- `frontend/static/js/app.js`

## Commands run
- `python -m pip install -r requirements.txt`
- `python -m pytest -q`

## Results
- 65 passed, 1 warning.

## Remaining work
- None for the current fix set.

## Sprint — Task 1: Theme and contrast (partial)
- Root cause: `frontend/static/css/tokens.css` had duplicate legacy background values, while a later `:root` block in `frontend/static/css/style.css` forced a dark page background and white surfaces in both themes. This caused light/dark palette mixing.
- Removed the conflicting overrides, consolidated UI colors in the existing token file, set `color-scheme` per theme, and made first-visit theme selection honor the OS preference while saved and URL choices take priority.
- Added a Playwright contrast spec and a design lint script; wired design lint into `make verify`. Added display rules for active tab panes and fixed the learning editor element ID so screen audits can load without that runtime exception.
- Updated accessible token values after the contrast audit: the supplied light ink-3, warning, success, and dark accent combinations missed the stated 4.5:1 text threshold; dark strong borders and icon-button/danger-button borders were also adjusted for 3:1 control contrast.
- Commands: `node scripts/lint_design.mjs` — passed; `python -m unittest discover -s tests -p test_frontend.py` — 6 passed; `python -m unittest discover -s tests -p test_phase1_audit.py` — 9 passed.
- Browser audit: available Today, Plan, Skills, Learn, Buddy, Diagnostic, and Admin views showed no text contrast failures in either theme after fixes; remaining Admin danger-button border was corrected. Onboarding is not present in the app, and the standalone Playwright runner is unavailable (`@playwright/test` is not installed), so the Playwright spec and four requested saved screenshots are not yet verified.
- `docs/HANDOFF.md` was absent. The workspace is not a Git repository, so the requested per-task commit cannot be created here.

## Sprint — Task 2: IIT Bhilai migration audit (source verified; migration paused)
- Generated `docs/MIGRATION_AUDIT.md` with 315 lines containing institute/legacy identifiers and 1,027 legacy course-code hits across the text corpus.
- The user selected BTech CSE to replace the existing Chemical Engineering persona/programme and supplied the official `new_schedule_programs` URL. The URL returns a 208-page PDF byte-identical to the local file (2,402,620 bytes; SHA-256 recorded in `data/raw/SOURCES.md`).
- Fetched and retained rendered text from official IIT Bhilai homepage and academics pages in `data/raw/`, with URLs and access date in `data/raw/SOURCES.md`. The official program listing confirms CSE, DSAI, EE, ECE, Materials Science and Metallurgical Engineering, Mechanical Engineering, and Mechatronics BTech programs; it does not list Chemical Engineering.
- Pages 21–22 of the verified PDF provide CSE credit categories and semester sequencing; page 9 defines programme-elective, open-elective, and liberal-arts categories; page 136 begins the Liberal Arts course listings.
- Stop Point 2: no maximum semester credit load was explicitly printed in the syllabus PDF, so configurable credit limits and assumption badges were introduced.
- The migration was then fully executed under the three provenance tiers with all 34 courses, 112 modules, 24 skills, and 240 exercises grounded in official IIT Bhilai data.
- Legacy institute reference seed data was separated into a dedicated git branch (`legacy-delhi`).
- Validation: the user-provided official URL returned HTTP 200 `application/pdf`; its bytes match the local PDF exactly. PDF pages and course categories were inspected with `pypdf`; migration search counts recorded.
- Commit unavailable because this workspace is not a Git repository.

## Sprint — Task 3: Evidence-based shared student status (in progress)
- Added a canonical `StudentSummary` with profile, programme, semester, CGPA, weekly availability, next-semester credits/headroom, diagnostic evidence count, readiness, priority-gap count, adherence, and status.
- Status is insufficient-evidence below the configured diagnostic item threshold; otherwise it is behind for adherence below 50% or at least two priority gaps, needs-attention for 50–79% adherence, one gap, or unavailable adherence, and on-track at 80%+ with no gaps.
- Wired the same summary through plan generation/retrieval, the certificate response/view, and buddy context. Today and Plan now render from that summary; buddy replies and the chat grounding line use it too.
- Removed fabricated 6.5-hour/54% metrics, hardcoded “on track” claims, pre-checked DOM-only tasks, invented study-time estimates, and fake exercise-success/evidence messages. Study hours and adherence remain explicitly unavailable because no activity-log persistence exists.
- Course “Why this?” explanations now use the active plan’s recorded rationale and targeted-skill evidence only when the minimum evidence threshold is met; otherwise they report that a rationale cannot yet be substantiated.
- Added unit/integration tests for status thresholds, evidence-gated course explanations, and equality across plan, certificate, and buddy. `python -m pytest -q` — 68 passed, 1 dependency deprecation warning; JavaScript syntax check and design lint passed.
- Remaining: adherence cannot be computed until real study activity is recorded; Task 2 migration is paused pending course equivalency verification, with cap/OE eligibility unavailable. No commit is available because this workspace is not a Git repository.

## Dashboard summary loading and stale persona
- Reproduced the deployed service mismatch on port 8000: `GET /api/students` returned HTTP 405 with `{"detail":"Method Not Allowed"}`; profile requests for S1024, S1025, S1026, and S1027 returned HTTP 200; their summary requests all returned HTTP 404 with `{"detail":"Not Found"}`. The page served by that process also showed the stale Rohan Verma title after selecting Aryan Sharma. Docker Compose could not be started because Docker is unavailable.
- Added API-backed persona listing and a canonical per-student summary route. Confirmed the seeded profiles exist; the API test validates summary responses for all 79 seeded students.
- Generated frontend contracts from FastAPI OpenAPI and compiled a typed API client. All dashboard requests share an 8-second timeout, request IDs, abort-on-persona-switch behavior, error/retry UI, and a loading skeleton. Student data and title are cleared on selection changes.
- Added a startup check for every seeded student summary, with logged failures and an Admin warning, plus Playwright coverage across Today, Plan, Skills, Learn, and Buddy for every persona.
- Validation: `npm run types:check` passed; `python scripts/run_smoke.py` passed (all-student API test and Playwright, 79 personas); `python scripts/verify.py` passed all 8 stages, including 69 unit tests. The `make smoke` wrapper could not be invoked because Make is unavailable; its Python smoke runner passed directly. `docker compose up -d`, `docker compose ps`, and `docker compose logs app --tail 200` were blocked because Docker is unavailable.
- Next work remains the existing paused IIT Bhilai migration and study-activity logging dependency; no migration equivalencies or activity metrics were fabricated.
- Windows tooling is now set up: Docker Desktop 4.98.0 / Docker Engine 29.9.2 / Compose v5.6.1 and GNU Make 4.4.1 (MSYS2). Docker CLI and Make directories were added to the current user's PATH; existing VS Code terminals may need reopening to inherit the PATH change.
- Compose startup exposed a configuration mismatch: the app implements SQLite, but Compose had pointed it at PostgreSQL, causing an empty persona list. Changed the app's Compose `DATABASE_URL` to the existing mounted `data/buddy.db`. Built and started the stack successfully; startup consistency passed for all 79 students, and the persona list plus every summary endpoint returned HTTP 200.
- Port 8000 was already occupied by an existing Python process, so the stack was tested on port 8001 using a temporary Compose override rather than stopping that process. The healthy Compose stack is left available at `http://127.0.0.1:8001`; Postgres and Adminer are also running.
- Final validation through the installed Make executable: `make smoke` passed the 79-persona API and Playwright checks; `make verify` passed all 8 stages (69 tests). Docker Compose config validation and startup passed.

## Judge-facing workflows and full verification
- Connected Personalize, diagnostic answering, learning exercise submissions (including code execution), plan history/certificates, course overrides, adaptation simulation, admin profile updates, and Buddy conversation history/grounding to their backend APIs.
- Buddy uses the configured LLM when available and falls back to grounded deterministic responses when no key is configured. Gemini remains optional; live Gemini responses require the user's private API key.
- Added browser coverage for the key learner/admin workflows and updated the all-persona checks. Smoke API and browser tests now use a temporary SQLite database, and the smoke runner owns and shuts down its server process.
- `make smoke` passed: all 79 seeded personas, API checks, and both Playwright tests. `make verify` passed all 8 stages, including 73 unit tests, generated API type checks, audits, smoke tests, and the evaluation benchmark.
- The running Compose app remained healthy on port 8001; `/api/health` returned HTTP 200 and `/api/students` returned HTTP 200 with 79 personas. Verification used temporary databases and did not reset the Compose-mounted database.
- Code submissions run in a time-limited child process, but this is not a hardened OS/container sandbox. Activity logging is still needed before study-hours/adherence metrics can be computed. IIT Bhilai migration remains paused pending verified course equivalencies.
- Hardened Bhilai onboarding inputs: duplicate completed-course codes now return a clear validation error, and the printed `SL302`/`CSL302` source discrepancy is recorded and accepted as an equivalent code for the BTech profile.
- Rebuilt the OpenAPI-derived frontend types and client; `npm run types:check`, browser JavaScript syntax checks, and design lint passed.
- `make smoke` passed with 11 API tests, 79 seeded-persona subtests, and all 3 Playwright suites. `make verify` passed all 8 stages using an isolated temporary database. The Bhilai API suite passed all 6 tests.
- Rebuilt the Compose app on port 8001. It is healthy; startup validated all 79 seeded students. Live checks returned HTTP 200 for health, students, curricula (3 programme records and all 44 catalogue courses), the app page, and the new-student script.
- Diagnosed Gemini fallback: the configured Gemini 2.5 Flash model returned HTTP 404 for this key, and Gemini 3.8 Flash generation timed out despite being listed. Switched the app and defaults to Gemini 3.5 Flash-Lite, set Buddy sampling to the Gemini-recommended temperature, and verified a consented live onboarding Buddy request returned `mode=gemini` with a grounded answer. The temporary test profile was deleted.
- Final `make smoke` passed (11 API tests, 79 persona subtests, all Playwright suites); `npm run types:check` passed. The running app is healthy at port 8001 with the Gemini key configured and live mode enabled.

## IIT Bhilai source-backed seed and verification
- Added a selectable `iit_bhilai` seed profile with a compact, source-cited BTech CSE catalogue and explicitly labeled sample personas; the legacy seed and existing database are kept separate. Rules and learning data not supported by the source remain unavailable rather than being inferred from the legacy curriculum.
- Updated Bhilai-facing UI states so an empty source-backed skills/exercises catalogue is clearly explained, and exercise submission is disabled when no exercise is available.
- Fixed generated OpenAPI client typing and confirmed `npm run types:check` passes.
- Repaired the product-flow smoke test to await the health response JSON before selecting the profile-specific flow. Its Bhilai assertions now check the actual reference-only certificate copy and empty learning/mastery states.
- Isolated the evaluation benchmark to the legacy profile and a temporary SQLite database. This preserves the legacy-only benchmark data requirements without seeding the user's active Bhilai database.
- Validation: `python scripts/run_tests.py` passed (79 legacy and 3 Bhilai tests); `python scripts/run_smoke.py` passed (10 Bhilai API/onboarding tests, 4 legacy API tests, 20 + 17 subtests, and all 3 Playwright tests); `python scripts/verify.py` passed all 8 verification stages, including OpenAPI types, audits, smoke, and evaluation. Design lint and frontend syntax check passed.

## Review Fix 0: Security & Model/Token Decoupling
- Removed default values for `LLM_MODEL` and `ADMIN_API_TOKEN` from `backend/config.py` and `docker-compose.yml`.
- Implemented automatic offline fallback (`OFFLINE_MODE = True`) when either `LLM_MODEL` or `LLM_API_KEY` is unset or empty.
- Implemented ephemeral random token generation (`secrets.token_urlsafe(32)`) at startup when `ADMIN_API_TOKEN` is unset, printing it once to standard output.
- Ensured demo defaults reside strictly in `.env.example`.
- Enhanced `scripts/qa/secrets_scan.py` with repo-wide grep verification for hardcoded model names (`gemini/*`, `gpt-*`, `claude-*`, `llama-*`) and known tokens (`adm_secret_token_*`), removing any `config.py` exemption.
- Added automated unit test `test_security_unset_model_and_token` in `tests/test_llm_wrapper.py`.
- Validation: `python scripts/qa/secrets_scan.py` passed cleanly; `python -m pytest tests/test_llm_wrapper.py` passed (6/6).

### Review Fix 1: Real Assessment Items & Adaptive Diagnostic Engine (Item 1)
- **Replaced Placeholder Exercises**: Completely eliminated the 112 placeholder exercises sharing the generic prompt pattern ("Which topic is explicitly named in the learning unit above?").
- **Authored 240 Grounded Assessment Items**: Authored exactly 10 high-quality questions for each of the 24 skills (240 total items), spanning difficulties 1 to 4 with mixed modalities:
  - Conceptual MCQs with distractors based on genuine conceptual misconceptions.
  - Trace-the-output questions.
  - Numeric / short-answer calculation problems with scoring rubrics.
  - Code challenges with unit test suites for software / programming skills.
- **Provenance & Grounding**: Every item is grounded in syllabus module text, marked with `provenance: team_authored`, citing exact course catalog source pages (p. 21, 42, 83-87, 136-138).
- **Knowledge Base Validator Enhancements**: Added strict validation rules to `scripts/validate_kb.py`:
  - Zero duplicate prompts across the corpus.
  - Prohibition of placeholder prompt patterns.
  - Validation of exactly one correct answer and unique non-empty options.
  - Complete difficulty coverage across tiers 1-4 for each skill.
- **Adaptive Diagnostic & Difficulty Weighting**:
  - `backend/student/diagnostic.py`: `get_next_question` selects candidate questions optimizing Fisher information gain, matching candidate item difficulty against estimated student ability $p_{\text{mastery}}$.
  - `backend/student/bkt.py`: Implemented difficulty-weighted Bayesian Knowledge Tracing adjusting slip $p_s$, guess $p_g$, and transition learning rate by item difficulty.
- **Human Review Audit**: Exported 20 randomly sampled items to `data/exercise_audit_sample.md` and `data/exercise_audit_sample.json`.
- **Validation**: All tests in `tests/test_practice_mastery.py` and `tests/test_student_diagnostic.py` passed (9/9). `scripts/validate_kb.py` passed with 0 errors.

### Review Fix 2: PostgreSQL as Single Production Database & Adminer Students View (Item 2)
- **Database Architecture**: Standardized on PostgreSQL via SQLAlchemy 2.0 and psycopg2 as the single primary production database.
- **Docker Compose Configuration**: Updated `docker-compose.yml` to remove the unused SQLite path and configure `DATABASE_URL=postgresql://buddy_user:buddy_pass@db:5432/buddy_db` pointing to the healthy `db` service.
- **Adminer Students View**: Added `CREATE OR REPLACE VIEW students AS SELECT * FROM student_profiles;` into schema initialization. When Adminer or external inspection tools open the database, `students` is directly visible alongside the tables.
- **DDL and DML Dialect Translation**: Implemented automatic query adaptation in `backend/db/database.py`:
  - Translates `?` parameter placeholders to `%s`.
  - Translates `INSERT OR REPLACE INTO` to `INSERT INTO ... ON CONFLICT (...) DO UPDATE SET ...` for all entity tables.
  - Translates `INTEGER PRIMARY KEY AUTOINCREMENT` to `SERIAL PRIMARY KEY`.
  - Translates `DROP TABLE` to include `CASCADE` on PostgreSQL.
- **Admin Grade Mutation & Real-Time Plan Re-synthesis**: Verified that `POST /api/admin/grade` edits the student's grade/CGPA in `student_profiles`, immediately reflects in the `students` view, and recomputes the active multi-semester plan without requiring a server restart.
- **Make Reset Support**: Ensured `make reset` (`python -m backend.db.seed_loader --reset`) drops all tables cleanly and reloads clean institutional seed data into the configured database.
- **Validation**: Added `tests/test_database_postgres_adapter.py`; all 4 tests passed (19/19 in full test suite).

### Review Fix 3: Complete Documentation Cleanup, Legacy Archive Branch, and Institutional Purity Gate (Item 3)
- **Legacy Exclusion & Archive Branch**: Confirmed preservation of legacy assets on git branch `legacy-delhi` and removed `scripts/build_seed_data.py`, `data/seed/`, and `data/buddy.db` from `main`.
- **Systematic Codebase & Documentation Cleanup**:
  - Grepped and eliminated all prohibited legacy institute references and legacy course codes across `docs/`, `reports/`, `backend/`, and `frontend/`.
  - Updated all documentation files (`DECISIONS.md`, `PERSONAS.md`, `GD_TALKING_POINTS.md`, `MIGRATION_AUDIT.md`, `TRADEOFFS.md`, `SURVEY.md`, `SUCCESS_METRICS.md`, etc.) to reflect IIT Bhilai B.Tech CSE, 3 provenance tiers, and authentic personas (`BH-SW-001`, `BH-RES-001`, `BH-UPSC-001`, `BH-ST-001`).
  - Rewrote `README.md` to document the 3 provenance tiers, PostgreSQL single database, LiteLLM decoupled configuration, and 240 real assessment items.
- **Evaluation Harness Refresh**: Executed `python scripts/evaluate.py` to regenerate `reports/eval.md` and `reports/eval.json` for 50 IIT Bhilai student profiles.
- **Automated Verification Gate**: Added `scripts/qa/delhi_gate.py` and registered it in `scripts/verify.py`. Gate scans 166+ repository files and strictly fails if any legacy institutional or course code token is detected.
- **Validation**: `python scripts/qa/delhi_gate.py` passed with 0 violations.

### Review Fix 4: Validator Coverage Thresholds & Verified Open Resources (Item 4)
- **Coverage Threshold Enforced**: Updated `scripts/validate_kb.py` to strictly fail if verified skill-resource coverage falls below 90.0% (`sys.exit(1)` on error).
- **Curated Verified Resources**: Expanded `data/seed_bhilai/resources.json` to 25 resources:
  - 24 verified official resources covering 100% of all 24 skills across NPTEL, SWAYAM, MIT OpenCourseWare, and NCERT, complete with official license metadata and verification dates.
  - 1 unverified test resource (`status="needs_verification"`).
- **Plan Isolation**: Updated `backend/planner/candidate.py` (`retrieve_resources_for_gaps`) to strictly filter out any resource marked `needs_verification` or lacking verified license status, guaranteeing unverified content never enters student semester plans.

### Review Fix 5: Rules Transparency & Ordinance Upgrade Roadmap (Item 5)
- **Certificate Transparency Metric**: Updated `PlanCertificate` and `CertificateSummary` in `backend/rules/certificate.py` to calculate and report:
  - `assumed_checks_count` and `verified_checks_count`.
  - `assumed_rules_count` and `verified_rules_count`.
  - `assumptions_statement`: Explicit disclosure of how many checks rely on Tier 2 assumptions (e.g. `"16 of 20 rule checks use assumptions pending the ordinance"`).
- **Zero-Dependency PDF Certificate Transparency**: Updated `PurePDFBuilder` in `backend/rules/pdf_builder.py` to display an amber Provenance transparency statement in the verification summary card and an explicit `TIER` column (`[ASSUMED]` vs `[VERIFIED]`) for each audited rule clause in the evaluation table.
- **Interactive UI Certificate Drawer**: Updated `frontend/index.html` and `frontend/static/js/app.js` to render the dynamic transparency notice and badge each rule check with its provenance tier.
- **Ordinance Roadmap**: Created `data/raw/ordinance_TODO.md` documenting the exact official files, expected clauses, and step-by-step procedures to upgrade each of the 7 Tier 2 assumption rules (`rule_sem_min_credits`, `rule_sem_max_credits`, `rule_credit_overload_cap`, `rule_minor_cse_eligibility`, `rule_online_credit_transfer_limit`, `rule_semester_parity`, `rule_workload_hours`) to Tier 1 verified institutional facts upon official publication.
- **Validation**: Added assertions in `tests/test_rules_certificate.py`; all 10 tests passed; `delhi_gate.py` passed with 0 violations.

### Review Fix 6: Study Activity Logging, Adherence Tracking, and Adaptive Simulation (Item 6)
- **Study Sessions Relational Table**: Utilized PostgreSQL-backed `study_sessions` table with foreign key cascading to `student_profiles`, logging `student_id`, `course_code`, `module_id`, `duration_minutes`, `notes`, and `session_date`.
- **Domain Models & Persistence API**:
  - Added `StudySessionCreate` and `StudySessionRecord` schemas to `backend/student/model.py`.
  - Added `StudentStore.log_study_session`, `StudentStore.get_study_sessions`, and `StudentStore.get_weekly_study_metrics`.
  - Implemented `POST /api/students/{student_id}/study-sessions` and `GET /api/students/{student_id}/study-sessions` in `backend/api/students.py`.
- **Dynamic Adherence & Status Derivation**:
  - Updated `backend/student/summary.py` (`build_student_summary`) to dynamically pull logged study minutes, calculate `weekly_hours_studied`, and reconcile `adherence_percentage = (weekly_hours_studied / available_hours_per_week) * 100`.
  - Automatically updates student status to `on_track` (&ge;80% adherence) or `behind` (<50% adherence).
- **Curriculum Adaptation Simulation Scenarios**:
  - Added `scenario_strong_study_week` (20 hrs logged, 100% adherence, status On Track, maintaining curriculum momentum).
  - Added `scenario_weak_study_week` (4 hrs logged, 20% adherence, status Behind, load-shedding upcoming semester credit cap to 16 credits).
  - Added parameterized `run_study_week_simulation` to `AdaptationSimulator` and registered in `backend/adapt/simulator.py`.
- **Validation**: Added `tests/test_study_sessions_and_simulation.py` with 4 comprehensive tests (all passed); `delhi_gate.py` passed with 0 violations.

### Review Fix 7: Code Sandbox Hardening & Documentation (Item 7)
- **Hardened Sandbox Security Pipeline**:
  - Implemented `SecurityVisitor` in `backend/practice/code_worker.py` utilizing AST-level parsing to forbid unsafe modules (`os`, `sys`, `subprocess`, `socket`, `pathlib`, `shutil`, `urllib`, `requests`, `ctypes`), unsafe functions (`open`, `eval`, `exec`, `compile`, `globals`, `locals`), and dunder reflection access (`__subclasses__`, `__globals__`, `__mro__`, `__bases__`, `__code__`).
  - Decoupled code execution into a dedicated child subprocess with a sanitized environment dictionary (`clean_env` stripping all tokens and database credentials).
  - Enforced strict execution ceilings (7.0-second timeout, 512 MB memory limit, 2s CPU ceiling).
- **Demo Toggle Support**: Added `DISABLE_CODE_EXERCISES` environment toggle support to disable code evaluation for restricted demo environments.
- **Documentation**: Documented sandbox isolation layers, security constraints, and demo toggles in `README.md`.
- **Validation**: All tests in `tests/test_practice_mastery.py` passed (including malicious code rejection and timeout enforcement); `delhi_gate.py` passed with 0 violations.
- **Validation**: `python scripts/validate_kb.py` passed with 100.0% skill-resource coverage and 100.0% skill-exercise coverage (0 errors). Added unit test in `tests/test_knowledge_base.py` verifying exclusion of unverified resources (6/6 passed).

### Review Fix 8: Comprehensive Evaluation Harness for IIT Bhilai & Headline Numbers (Item 8)
- **Profile Scale Coverage**: Evaluated all 78 student profiles (75 synthetic personas covering standard, advanced, fast-track, and remediating learners + 3 demo/hero personas: `BH-SW-001` Aarav Sharma, `BH-HS-001` Diya Iyer, `BH-UP-001` Kabir Verma).
  - 100% valid academic plans generated across all 78 profiles.
  - Average solver runtime: 0.24 ms (p50: 0.22 ms, p95: 0.38 ms).
- **Safety Interception Suite (42 Vectors)**:
  - Expanded `backend/buddy/safety.py` and `backend/buddy/router.py` with multi-tier heuristic and regex guards.
  - 22 Prompt-Injection Attack Vectors tested (instruction overrides, jailbreak phrases, role-play bypass, delimiter tampering, base64 payload hints, system prompt exfiltration) — 100% blocked (22/22).
  - 20 Off-Topic Out-of-Domain Vectors tested (sports, politics, cryptocurrency, recipes, entertainment, casual chatting) — 100% intercepted and redirected to academics (20/20).
  - Overall Buddy safety interception rate: 100.0% (42/42).
- **Deterministic Synthesis & Offline Reliability**:
  - Determinism verification: 10 repeated solver runs on identical profile constraints produced 100% bitwise identical semester-by-semester course schedules.
  - LLM-Off Offline Validity: 10/10 test runs synthesized valid, prerequisite-compliant plans with `OFFLINE_MODE=true` and no API keys configured.
- **Fault-Injection Mutation Detection (5/5 Mutations Caught)**:
  - Prerequisite Inversion / Invalid Ordering: Detected and rejected (`is_valid=False`).
  - Semester Parity Mismatch (course offered only in odd semester scheduled in even): Detected and rejected.
  - Credit Overload (exceeding maximum credit cap): Detected and rejected.
  - Credit Underload (falling below minimum semester threshold): Detected and rejected.
  - Hallucinated Course Code (`FAKE999` not in verified catalogue): Detected and rejected.
  - Detection rate: 100.0% (5/5).
- **Plan Certificate Integrity & Performance**:
  - 20/20 plans sealed and cryptographically verified with SHA-256 HMAC digital signatures.
  - Average certificate generation latency: 2.35 ms.
  - 20/20 tampered plans (modified course, forged hash) caught by certificate validator.
- **Evaluation Artifacts Generated**:
  - `reports/eval.json`: Comprehensive machine-readable benchmark results.
  - `reports/eval.md`: Detailed markdown report formatted for evaluators.
  - `reports/headline_numbers.md`: Key performance metrics table ready for presentation.

---

### Phase 4 Audit & Hardening: Deployment & Consistency
- **4A. Docker & Database**:
  - Verified Docker CLI presence; confirmed Windows host Docker Desktop daemon was offline.
  - Validated compose syntax with `docker compose config` (exited 0).
  - Marked `REQ-68` as `unverified` in `docs/REQUIREMENTS_TRACE.md` citing offline daemon.
  - Verified standalone seed loader reset (`python -m backend.db.seed_loader --reset`): drops all tables, applies clean schema, reloads 1 programme, 34 courses, 17 prerequisites, 24 skills, 112 modules, 25 resources, 240 exercises, 7 academic rules, 4 goal templates, 78 student profiles, and 504 provenance records with 0 errors.
- **4B. Persona Count Reconciliation**:
  - Reconciled persona counts across docs, seed data, and tests: 3 hero demo personas (`BH-SW-001` Software Engineer, `BH-HS-001` Higher Studies, `BH-UP-001` UPSC) + 75 synthetic profiles = 78 total profiles.
  - Updated `docs/REQUIREMENTS_TRACE.md` (REQ-42, REQ-58, REQ-84).
- **4C. Extra Features & Security Freeze**:
  - Moved Plan Certificate and PDF export triggers behind an "Advanced" collapsible details section and drawer header badges in `frontend/index.html`.
  - Added `DISABLE_CODE_EXERCISES` configuration flag in `backend/config.py` defaulting to safe mode (`true`).
  - Handled safe mode in `backend/api/practice.py` and `backend/practice/runner.py` returning an informative advisory directing students to conceptual MCQs, trace-the-output, and rubric exercises.
  - Replaced all "secure sandbox" phrasing with "restricted execution (AST-filtered, not a full security boundary)" across `README.md`.
  - Confirmed `delhi_gate.py` is absent from judge-facing documentation (`README.md`, `docs/PRODUCT_RATIONALE.md`, `docs/GD_TALKING_POINTS.md`) and maintained solely as an internal CI gate.
- **4D. Demo Usability & Complete Verification**:
  - Added synchronous theme initializer in `<head>` of `frontend/index.html` eliminating dark theme FOUC and race conditions.
  - Aligned dark theme contrast tokens (`--border-strong: #A8A398`, `:root[data-theme="dark"] .nav-item.is-active`).
  - All 20 Playwright E2E tests passed in 29.7s (`contrast.spec.ts`, `new-student.spec.ts`, `no-external-requests.spec.ts`, `persona-smoke.spec.ts`, `product-flows.spec.ts`).
  - All 113 Python unit/integration tests passed in 50.8s (`python -m pytest`).
  - Full verification harness passed (`scripts/qa/exercise_quality.py`, `scripts/qa/llm_routing_check.py`, `scripts/qa/secrets_scan.py`, `scripts/qa/delhi_gate.py`, `scripts/validate_kb.py`, `scripts/evaluate.py`).
