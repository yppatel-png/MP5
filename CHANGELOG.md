# Audit Fixes & Selection Assignment Deliverables Changelog

**Project**: Learning Buddy for IIT Bhilai B.Tech CSE (Adobe Inter-IIT Tech Meet 15.0)  
**Execution Date**: 2026-11-09  
**Status**: All P0 and P1 audit fixes implemented and verified. All Day 1 Selection Assignment pipeline deliverables generated and validated. 100% test pass rate across the full test runner and end-to-end smoke suite.

---

## 1. Test Verification Matrix

| Test Suite | Command | Total Tests | Passed | Result |
| :--- | :--- | :---: | :---: | :---: |
| **Audit P0 & P1 Suites** | `python -m pytest tests/test_audit_p0.py tests/test_audit_p1.py` | 16 | 16 | **PASS (100%)** |
| **Full Repository Test Suite** | `python scripts/run_tests.py` | 133 (+45 subtests) | 133 (+45 subtests) | **PASS (100%)** |
| **E2E & Smoke Validation** | `python scripts/run_smoke.py` | 17 (3 browser + 14 API) | 17 | **PASS (100%)** |
| **Reproducible Data Pipeline** | `python run_pipeline.py` / `make pipeline` | 5 stages (DAG check, chunks) | 5 stages | **PASS (100%)** |
| **Zero Literal Grep Verification** | `grep -rn "19.0\|, 24.0)\|, 22.0)\|UPSC Civil Services'" backend/` | 0 occurrences | 0 occurrences | **PASS (Zero Literals)** |

---

## 2. Issue ID $\to$ Files Touched $\to$ Tests Added $\to$ Result

### Phase P0: Correctness & Academic Honesty

| Issue ID | Description & Changes | Files Touched | Tests Added / Extended | Result |
| :--- | :--- | :--- | :--- | :--- |
| **P0-1** | **Deferred Core Queue & Constraint Rescheduling**: Fixed topological solver silently dropping required core courses when credit/prereq limits are encountered. Implemented `deferred_core` queue with offering parity checks (odd/even) and independent validator agreement. | `backend/planner/solver.py`<br>`backend/planner/validator.py` | `test_P0_1_core_course_deferred_and_rescheduled`<br>`test_P0_1_unmet_prereq_chain_reports_infeasible_not_silent_drop` | **PASSED** |
| **P0-2** | **Independent Validator Agreement & Cryptographic Seals**: Decoupled validator from solver. Enforced strict 9-rule audit pass (DAG acyclicity, credit caps, offering parity, prerequisite satisfaction) and digital seal generation. | `backend/planner/validator.py`<br>`backend/rules/registry.py` | `test_P0_2_independent_validator_parity_on_personas`<br>`test_P0_2_validator_detects_all_mutations` | **PASSED** |
| **P0-3** | **No Fallback Literals & No UPSC Default**: Removed all hardcoded credit limits (`22.0`, `24.0`, `19.0`). Created `backend/rules/params.py` as central parameter accessor. Students without target roles now explore without default assumptions. | `backend/rules/params.py`<br>`backend/buddy/router.py`<br>`backend/planner/infeasible.py`<br>`backend/rules/credit_rules.py` | `test_P0_3_no_fallback_literals_and_no_upsc_default` | **PASSED** |
| **P0-4** | **No Swallowed Exceptions**: Replaced bare `except Exception: pass` across models, indexers, and seed loaders with structured logging (`logger.exception`) and user-facing `degraded: True` flags. Defensive handling for JSON list attributes in SQLite. | `backend/student/diagnostic.py`<br>`backend/db/seed_loader.py`<br>`backend/buddy/tools.py` | `test_P0_4_no_swallowed_exceptions_and_degraded_flag` | **PASSED** |
| **P0-5** | **Provenanced Academic Rules & Honest UI Text**: Academic rules without an explicit chapter/section in the Courses of Study PDF carry `provenance="assumption"`. UI text clearly labels rules as "assumed, pending ordinance" instead of citing false institute authority. | `data/seed_bhilai/academic_rules.json`<br>`frontend/static/js/app.js`<br>`backend/rules/bhilai_rules.py` | `test_P0_5_assumed_rules_carry_provenance_badge` | **PASSED** |
| **P0-6** | **LLM Kept Out of Eligibility Logic**: All eligibility, prerequisite validation, and credit math are computed strictly in deterministic Python code; the LLM only phrases explanations and ranks pre-approved options. | `backend/buddy/router.py`<br>`backend/buddy/tools.py`<br>`backend/buddy/safety.py` | `test_P0_6_llm_cannot_override_eligibility` | **PASSED** |
| **P0-7** | **Zero Invented Institute Facts**: Verified all course codes, credit values, prerequisites, and semester offerings against `data/raw/courses of study.pdf`. Added missing course `UGQ301` (Interdisciplinary Undergraduate Project, p. 22). | `data/seed_bhilai/courses.json`<br>`backend/buddy/safety.py` | `test_P0_7_zero_invented_courses_or_rules` | **PASSED** |
| **P0-8** | **Deterministic Code Execution & Sandboxing**: Ensured practice runner operates safely with deterministic AST checks and resource-constrained execution. | `backend/practice/runner.py`<br>`backend/practice/code_worker.py` | `test_P0_8_sandbox_determinism_and_safety` | **PASSED** |

---

### Phase P1: Pedagogical Depth & Grounding

| Issue ID | Description & Changes | Files Touched | Tests Added / Extended | Result |
| :--- | :--- | :--- | :--- | :--- |
| **P1-1** | **Personalized Electives via Diagnostic Gaps**: Candidate retriever customizes elective recommendations by matching student interests (`interests`) and priority skill gaps even when no gaps are pre-cached, surfacing differentiated choices for AI/ML vs Systems. | `backend/planner/candidate.py`<br>`backend/planner/solver.py` | `test_P1_1_goal_electives_differ_and_cite_gaps` | **PASSED** |
| **P1-2** | **Mastered Content Dropped & Test-Out Flagging**: Content with demonstrated proficiency ($p \ge 0.85$ over multiple items) is excluded from remedial recommendations; core courses expose a test-out eligible indicator. Grade alone without assessment does not trigger mastery. | `backend/planner/candidate.py`<br>`backend/api/practice.py` | `test_P1_2_mastered_content_dropped_and_test_out_flag` | **PASSED** |
| **P1-3** | **Relevance-Based Resources & Milestone Carryover**: Open educational resources matched to course skills and format preferences (reading, video, interactive). Uncompleted milestones carry forward sequentially across semesters. | `backend/planner/solver.py`<br>`data/seed_bhilai/resources.json` | `test_P1_3_resource_relevance_and_milestone_carryover` | **PASSED** |
| **P1-4** | **Unverified Prior Courses Targeted First**: Students with prior unassessed courses are directed to baseline diagnostic questions first to verify background knowledge. | `backend/student/diagnostic.py` | `test_P1_4_unverified_course_prior_targeted_first_in_diagnostic` | **PASSED** |
| **P1-5** | **BKT Time-Decay & Anti-Self-Declared Mastery**: Bayesian Knowledge Tracing applies half-life decay to older evidence. Self-declared competencies can contribute prior signals but can never unilaterally confirm mastery. | `backend/student/bkt.py` | `test_P1_5_bkt_time_decay_and_self_declared_cannot_master` | **PASSED** |
| **P1-6** | **Adaptation Policy Configuration & Anti-Lucky Quiz**: Rule parameters read from `config/adaptation_policy.yaml`. Single quiz score $\ge 0.85$ does not trigger `ACCELERATE` unless `min_items_required` (3) is satisfied. Conflicting signals prioritize `REMEDIATE` with explicit explanation. | `backend/adapt/policy.py`<br>`config/adaptation_policy.yaml` | `test_P1_6_adaptation_yaml_parameter_and_no_lucky_quiz_accelerate` | **PASSED** |
| **P1-7** | **Conflict Detector HTML False-Positive Fix**: Replaced naive substring matching in conflict detector with HTML token parsing and word boundaries, eliminating false positive alerts on normal coursework. | `backend/student/conflict.py` | `test_P1_7_conflict_detector_no_html_false_positive` | **PASSED** |
| **P1-8** | **Buddy Intent Boundaries & Proposal TTL**: Hybrid intent classifier uses word boundaries and negative lookahead (`"prefer not to drop"` does not trigger `CHECK_DROP`). Bounded context builder enforces 1500-token budget. Ephemeral proposals stored in DB with 30-min TTL. Hard code verifier catches unverified codes. | `backend/buddy/router.py`<br>`backend/buddy/memory.py`<br>`backend/buddy/safety.py`<br>`backend/db/database.py` | `test_P1_8_buddy_intent_word_boundaries_and_context_budget` | **PASSED** |

---

## 3. Adobe Selection Assignment Deliverables (Day 1 Brief)

All 5 core deliverables mandated by `Adobe_PS_1-Day_Selection_Assignment.pdf` have been synthesized and verified:

1. **`run_pipeline.py` & `Makefile` (`make pipeline`)**:
   - 5-stage automated data engineering pipeline:
     - **Stage 1 (Ingest)**: Verifies `data/raw/courses of study.pdf` (2.29 MB) and pre-extracted page cache.
     - **Stage 2 (Parse & Normalise)**: Standardizes schema across courses, prerequisites, skills, rules, resources, modules, and exercises.
     - **Stage 3 (Validate)**: Enforces hard consistency checks: DFS acyclic DAG verification (zero cycles), numeric credit assertions, foreign key course code validation.
     - **Stage 4 (Chunk)**: Emits 193 retrieval-ready vector chunks.
     - **Stage 5 (Export)**: Generates 8 CSVs and 8 JSONs under `data/processed/` and `chunks.jsonl`.
2. **`data/processed/`**:
   - Contains clean CSV and JSON exports for: `courses`, `prerequisites`, `skills`, `course_skills`, `academic_rules`, `resources`, `modules`, and `exercises`.
3. **`chunks.jsonl`**:
   - 193 semantic chunks (128 KB) formatted with entity metadata, text content, and official source citations.
4. **`SOURCES.md`**:
   - Complete audit trail with official URLs, document retrieval dates, SHA-256 hash for raw PDF, 34 external open resources with open licenses, and data ethics statement.
5. **`IDEAS.md`**:
   - 1-page analysis detailing 3 questions the buddy answers well with this dataset, 3 questions it cannot answer (and safety guardrails), and the dual-layer deterministic + neural architecture.

---

## 4. Deliberate Invariants & Non-Changes

1. **IIT Bhilai Ordinance Baseline**:
   - Rules not explicitly codified in the Courses of Study PDF (such as maximum semester overload limits or specific attendance policies) were deliberately left with `provenance="assumption"` rather than fabricating official ordinance clause numbers.
2. **Preserved Raw PDF Discrepancy**:
   - The discrepancy between `SL302` and `CSL302` noted in the source PDF is documented and preserved in `DATA_QUALITY.md` rather than silently normalized away.
3. **Sandbox Offline Default**:
   - Production settings retain deterministic offline mode by default so that the application can be evaluated completely without requiring third-party API credentials or network dependencies.

