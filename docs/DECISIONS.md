# Architecture & Design Decisions Log

This log tracks architectural, product, and implementation decisions made in accordance with the project requirements.

---

## Decision Log

### DEC-001: Target Institute Selection & Three Provenance Tiers
* **Date:** 2026-11-04 (Updated 2026-11-07)
* **Decision:** Selected **Indian Institute of Technology Bhilai (IIT Bhilai)** as the official reference institute, governed by THREE PROVENANCE TIERS:
  - **Tier 1 (Verified Institutional Facts)**: Extracted verbatim from official raw documents (`Courses of Study 2023-24`): course codes, titles, L-T-P-C credits, semesters offered, and syllabi.
  - **Tier 2 (Labelled Assumptions)**: For facts unstated in the catalog (semester credit bounds, overload eligibility, online-credit cap), store configurable rules with `provenance="assumption"`, a visible rationale, and `pending ordinance` status.
  - **Tier 3 (Team-Authored Learning Layer)**: Derived skills, module breakdowns, 240 original assessment exercises with misconceptions, goal templates, and OER resources.
* **Rationale:** Completely eliminates ungrounded assumptions while delivering the full learning loop.

### DEC-002: Target Academic Programme
* **Date:** 2026-11-04 (Updated 2026-11-07)
* **Decision:** Model the **B.Tech Computer Science and Engineering (`iit_bhilai_btech_cse_2023`)** programme in depth, including CSE core, electives, and cross-departmental open electives (EE, ME, Liberal Arts).
* **Rationale:** Fully addresses student personas (Software Engineer, Higher Studies / Research, UPSC Civil Services, Startup Founder).

### DEC-003: Database Strategy (PostgreSQL as Single Primary Database)
* **Date:** 2026-11-04 (Updated 2026-11-07)
* **Decision:** Standardize on **PostgreSQL 16** via SQLAlchemy 2 and psycopg2 as the single primary production database, with Docker Compose, Adminer `students` view, and atomic reset support (`make reset`). Transparent SQLite fallback is provided only for offline developer environments.
* **Rationale:** Provides production-grade ACID compliance, connection pooling, and live admin UI editing.

### DEC-004: LiteLLM Decoupled Configuration & Ephemeral Security Token
* **Date:** 2026-11-04 (Updated 2026-11-07)
* **Decision:** Decoupled LLM settings: `LLM_MODEL` and `ADMIN_API_TOKEN` have zero hardcoded defaults in code and compose. If model or key is unset, the system runs safely in offline mode with deterministic grounded fallbacks. If `ADMIN_API_TOKEN` is unset, an ephemeral token is generated at startup.
* **Rationale:** Defense-in-depth against hardcoded credentials and token leakage.

### DEC-005: Deterministic Constraint Solver & Fallback
* **Date:** 2026-11-04
* **Decision:** Use Google OR-Tools CP-SAT for multi-semester academic schedule optimization, complemented by a greedy topological sort constraint solver as a fast deterministic fallback.
* **Rationale:** Guarantees strict adherence to credit caps, prerequisite DAGs, semester offering parity (Odd/Even), and elective restrictions without relying on LLM guesswork.

### DEC-006: Skill Modeling with Difficulty-Weighted BKT
* **Date:** 2026-11-04 (Updated 2026-11-07)
* **Decision:** Implement difficulty-weighted Bayesian Knowledge Tracing with NumPy. Slip $p_s$, guess $p_g$, and transition learning rates scale with item difficulty (tiers 1-4).
* **Rationale:** Meets the explainability requirement with auditable mathematical transparency and psychometric rigor.

### DEC-007: Rule Registry & Deterministic Ordinance Transparency (Feature A)
* **Date:** 2026-11-05 (Updated 2026-11-07)
* **Decision:** Decoupled academic constraint validation into a modular `RuleRegistry` (`backend/rules/`), explicitly displaying Verified vs Assumed status and pending ordinance documentation.
* **Rationale:** Transparent auditability for academic planning.

### DEC-008: Cryptographic Plan Certificates & SHA-256 Tamper Detection (Feature A)
* **Date:** 2026-11-05
* **Decision:** Every academic plan version receives a sealed `PlanCertificate` containing an input hash, KB version hash, rule-set version (`2024.1-BHILAI-ACAD`), margins, and a SHA-256 canonical JSON hash.
* **Rationale:** Guarantees that any tampering or manual modification of courses, credits, or prerequisite ordering is immediately caught by `POST /plans/{id}/certificate/verify`.

### DEC-009: Pure-Python Zero-Dependency PDF Certificate Builder (Feature A)
* **Date:** 2026-11-05
* **Decision:** Implemented a direct PDF 1.4 vector generator (`PurePDFBuilder`) in pure Python rather than requiring heavy third-party C binaries (ReportLab, Weasyprint).
* **Rationale:** Eliminates external C-library build failures in Docker/CI environments, operates 100% offline, and produces publication-quality printable A4 certificates.
