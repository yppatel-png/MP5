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
- Stop Point 2: no maximum semester credit load was identified, and the PDF does not enumerate which inter-discipline courses are eligible for the CSE open-elective category. The app still enforces IIT Delhi 22/24-credit caps and uses IIT Delhi courses and rules.
- The user selected a bounded migration with cap/OE eligibility left unavailable, then chose to wait until course equivalencies are verified. Existing synthetic profiles contain IIT Delhi course codes, grades, and diagnostic evidence; no official or user-approved IIT Bhilai equivalency mapping is available.
- No programme, course, prerequisite, elective, or rule seed data has been changed. Do not count or relabel old institute records as IIT Bhilai CSE credit.
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
