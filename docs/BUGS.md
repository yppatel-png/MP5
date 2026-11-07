# Quality Assurance Bug Registry (docs/BUGS.md)

This log records every defect, security issue, reliability flaw, or packaging vulnerability discovered during the hostile QA and hardening process.

## Severity Classification
* **P0**: Blocks demo or violates hard requirements (won't start, secret leaked, unauthorized outbound call, invalid plan presented, data loss).
* **P1**: Incorrect or misleading output, server crash, security hole (IDOR, injection, unhandled error).
* **P2**: Rough edge, graceful degradation failure, performance bottleneck, missing validation guard.
* **P3**: Cosmetic irregularity, minor log noise, styling or typographic discrepancy.

---

## Defects Table

| ID | Severity | Area | Summary | Repro | Root Cause | Fix | Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | P1 | Frontend / Offline | Missing visible offline mode indicator when API key is blank | Start app without `LLM_API_KEY` | UI had no banner alerting user that offline deterministic fallbacks are active | Added offline status banner in `frontend/index.html` and dynamic health ping in `app.js` | `test_04_offline_mode_fallback_and_notice` | **RESOLVED** |
| **BUG-002** | P0 | Database / Seed | Repeated `load_seed_data(reset=False)` duplicated diagnostic evidence events | Call `load_seed_data(reset=False)` twice | Missing unique constraint/cleanup on diagnostic evidence items | Cleared `item_ref = 'initial_seed_diagnostic'` per student before re-inserting | `test_01_seed_idempotency_double_run` | **RESOLVED** |
| **BUG-003** | P1 | Admin API / Security | Missing token-protected admin endpoints for live parameter mutations | Attempt admin mutation without auth | Administrative endpoints lacked unified routing, IDOR guards, and live solver sync | Authored `backend/api/admin.py` with `verify_admin_token` & solver memory sync | `test_05_admin_token_authorization`, `test_07_admin_course_edit_and_prerequisite_sync` | **RESOLVED** |
| **BUG-004** | P2 | Packaging / Docker | Build context bloat from `Adobe.pdf` and local database files | Run `docker build .` without `.dockerignore` | Missing `.dockerignore` file in repository root | Authored `.dockerignore` excluding `.git`, `*.pdf`, `data/*.db`, and `reports/` | `test_09_packaging_and_docker_configuration` | **RESOLVED** |
| **BUG-005** | P1 | Admin Engine | `CompletedCourse` model has no `credits` field, throwing AttributeError during grade edit | Call `edit_student_grade` on student | Code assumed `c.credits` existed on pydantic model | Resolved credit lookup from `multi_semester_planner.courses` dictionary | `test_06_admin_grade_edit_triggers_recomputation` | **RESOLVED** |

---

## Detailed Bug Reports

### BUG-001: Missing Offline Mode Notice in UI
* **Severity**: P1
* **Component**: `frontend/index.html`, `frontend/static/js/app.js`
* **Reproduction**: Start backend with empty `LLM_API_KEY` in `.env`. Open `http://localhost:8000`. The UI rendered normally without visibly informing evaluators that deterministic template engines were serving requests.
* **Root Cause**: The frontend header lacked an offline indicator badge and did not bind to `/api/health` status data.
* **Fix**: Added `<div id="offline-banner" class="offline-banner">` with quiet academic styling in `index.html`. Updated `app.js` to poll `/api/health` and display "Offline Deterministic Mode Active (100% Hermetic)" when `is_live=False`.
* **Verification Test**: `tests/test_phase1_audit.py::test_04_offline_mode_fallback_and_notice`.

### BUG-002: Seed Data Loading Non-Idempotency
* **Severity**: P0
* **Component**: `backend/db/seed_loader.py`
* **Reproduction**: Execute `python -m backend.db.seed_loader` twice consecutively without `--reset`. Count records in `evidence_events`. The row count jumped from 162 to 324.
* **Root Cause**: `evidence_events` table relies on an auto-incrementing integer primary key and has no unique constraint across `(student_id, skill_id, timestamp)`. Re-running the seed loader caused raw `INSERT` operations to duplicate rows.
* **Fix**: Modified `backend/db/seed_loader.py` to delete existing initial diagnostic evidence rows (`item_ref = 'initial_seed_diagnostic'`) for each seeded student prior to loading.
* **Verification Test**: `tests/test_phase1_audit.py::test_01_seed_idempotency_double_run`.

### BUG-003: Missing Token-Protected Administrative Mutation Endpoints
* **Severity**: P1
* **Component**: `backend/api/admin.py`
* **Reproduction**: Prior to Phase 1, there were no dedicated REST endpoints for live modification of grades, courses, prerequisites, rules, and student constraints with immediate solver cache synchronization.
* **Root Cause**: Omission of admin controller specification for runtime recomputation.
* **Fix**: Authored `backend/api/admin.py` with endpoints `/api/admin/grade`, `/api/admin/course`, `/api/admin/prerequisite`, `/api/admin/rule`, `/api/admin/constraint`, and `/api/admin/reset`. Enforced header-based authentication (`X-Admin-Token` or Bearer) matching `settings.ADMIN_API_TOKEN`. Updated in-memory structures in `multi_semester_planner`, `independent_validator`, and `rule_registry`.
* **Verification Test**: `tests/test_phase1_audit.py::test_05_admin_token_authorization`, `test_07_admin_course_edit_and_prerequisite_sync`, `test_08_admin_rule_and_constraint_mutation`.

### BUG-004: Docker Packaging Bloat from Unexcluded Large Files
* **Severity**: P2
* **Component**: `.dockerignore`
* **Reproduction**: Run docker build context inspection. The 10 MB `Adobe.pdf`, SQLite databases, and transient caches were transferred into the build context.
* **Root Cause**: Missing `.dockerignore` file.
* **Fix**: Authored root `.dockerignore` filtering out `.git`, `__pycache__`, `*.pyc`, `data/*.db`, `*.sqlite`, `*.pdf`, `reports/`, and `node_modules/`. Kept Docker image layer slim and hermetic.
* **Verification Test**: `tests/test_phase1_audit.py::test_09_packaging_and_docker_configuration`.

### BUG-005: AttributeError on `c.credits` during Admin Grade Modification
* **Severity**: P1
* **Component**: `backend/api/admin.py`
* **Reproduction**: Call `edit_student_grade(EditGradeRequest(student_id="BH-SW-001", course_code="CSL202", new_grade="A"))`. Raised `AttributeError: 'CompletedCourse' object has no attribute 'credits'`.
* **Root Cause**: `CompletedCourse` model in `backend/student/model.py` only defines `course_code`, `grade`, and `semester_completed`. Course credit weightings belong to the course catalogue schema.
* **Fix**: In `backend/api/admin.py`, queried credit weights from `multi_semester_planner.courses[c.course_code]["credits"]` with a safe default of 4.0.
* **Verification Test**: `tests/test_phase1_audit.py::test_06_admin_grade_edit_triggers_recomputation`.
