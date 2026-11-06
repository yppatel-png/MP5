# Architecture & Design Decisions Log

This log tracks architectural, product, and implementation decisions made in accordance with **Rule 6** ("If something in this brief is ambiguous, choose the simplest option, note the decision in `docs/DECISIONS.md`, and continue").

---

## Decision Log

### DEC-001: Target Institute Selection
* **Date:** 2026-11-04
* **Decision:** Selected **Indian Institute of Technology Delhi (IIT Delhi)** as the primary reference institute.
* **Rationale:** IIT Delhi has publicly available, comprehensive course catalogues, explicit degree regulations (Courses of Study / Information Brochure), well-defined credit limits per semester (typically 16-24 credits), formal prerequisite chains, and a structured Minor Degree policy (20 credits of designated courses) that cleanly matches the personas in Appendix A.

### DEC-002: Target Academic Programmes
* **Date:** 2026-11-04
* **Decision:** Model the following two degree programmes in depth:
  1. **B.Tech Computer Science and Engineering (CS1)**
  2. **B.Tech Chemical Engineering (CH1)** with an optional Minor in Computer Science and Engineering.
* **Rationale:** This directly covers the Hero Persona A (Chemical Engineering student pivoting to software), while providing comprehensive coverage of core engineering mathematics, departmental core, departmental electives, and open electives.

### DEC-003: Database Strategy (Dual SQLite / PostgreSQL Support)
* **Date:** 2026-11-04
* **Decision:** Implement database models using standard SQLAlchemy 2 with dialect abstraction supporting both **PostgreSQL 16** (in Docker) and **SQLite 3** (local developer mode / CI test runs / quick start).
* **Rationale:** SQLite requires zero daemon configuration on developer laptops and allows instantaneous atomic database resets (`make reset`), while PostgreSQL with Adminer satisfies the Docker Compose packaging requirement.

### DEC-004: Default LLM Model & LiteLLM Offline Fallback
* **Date:** 2026-11-04
* **Decision:** Default `LLM_MODEL` configured as `gemini/gemini-3.5-flash-lite` in `.env.example`.
* **Rationale:** Highly capable, cost-effective, and supported natively by LiteLLM. When `LLM_API_KEY` is not provided or network access is restricted, the `LiteLLMClient` activates a deterministic rule-based template engine so that planning, validation, and diagnostics continue to function with 100% validity without crashing.

### DEC-005: Deterministic Constraint Solver & Fallback
* **Date:** 2026-11-04
* **Decision:** Use Google OR-Tools CP-SAT for multi-semester academic schedule optimization, complemented by a greedy topological sort constraint solver as a fast deterministic fallback.
* **Rationale:** Guarantees strict adherence to credit caps, prerequisite DAGs, semester offering parity (Odd/Even), and elective restrictions without relying on LLM guesswork.

### DEC-006: Skill Modeling with Bayesian Knowledge Tracing (BKT)
* **Date:** 2026-11-04
* **Decision:** Implement standard BKT (`p_init`, `p_transit`, `p_slip`, `p_guess`) implemented deterministically with NumPy.
* **Rationale:** Meets the explainability requirement ("why we believe you know X") with auditable mathematical transparency and time-decay tracking.


### DEC-007: Rule Registry & Deterministic Ordinance Clause Citations (Feature A)
* **Date:** 2026-11-05
* **Decision:** Decoupled academic constraint validation into a modular `RuleRegistry` (`backend/rules/`) with 16 accredited rules, where every rule explicitly maps to an accredited IIT Delhi ordinance clause (`ORD-X.X.X` or `student_preference`).
* **Rationale:** Moves academic validation from opaque solver constraints to visible, auditable legal proof. Ensures 100% deterministic checking without relying on generative LLM hallucination.

### DEC-008: Cryptographic Plan Certificates & SHA-256 Tamper Detection (Feature A)
* **Date:** 2026-11-05
* **Decision:** Every academic plan version receives a sealed `PlanCertificate` containing an input hash, KB version hash, rule-set version (`2024.1-IITD-ACAD`), margins, and a SHA-256 canonical JSON hash.
* **Rationale:** Guarantees that any tampering or manual modification of courses, credits, or prerequisite ordering is immediately caught by `POST /plans/{id}/certificate/verify`.

### DEC-009: Pure-Python Zero-Dependency PDF Certificate Builder (Feature A)
* **Date:** 2026-11-05
* **Decision:** Implemented a direct PDF 1.4 vector generator (`PurePDFBuilder`) in pure Python rather than requiring heavy third-party C binaries (ReportLab, Weasyprint).
* **Rationale:** Eliminates external C-library build failures in Docker/CI environments, operates 100% offline, and produces publication-quality printable A4 certificates.
