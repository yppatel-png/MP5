# Adobe Learning Buddy - Executive Headline Numbers

**Institution:** Indian Institute of Technology Bhilai (IIT Bhilai)  
**Curriculum Track:** B.Tech in Computer Science and Engineering (`BH-CSE-BTECH`)  
**Evaluation Date:** 2026-11-07T10:18:59Z  
**Architecture:** 3 Provenance Tiers | Single PostgreSQL 16 DB | Zero Invented Institutional Facts | Offline Deterministic Solver  

---

## Key Performance Indicators

| Evaluation Dimension | Target Metric | Verified Benchmark Result | Status |
| :--- | :--- | :--- | :---: |
| **Plan Validity (All Profiles)** | 100% compliance across academic rules | **100.0%** (78/78 profiles) | **PASS** |
| **Bitwise Determinism** | 100% identical outputs on re-run | **100.0%** (10/10 identical schedules) | **PASS** |
| **Offline Mode Planning Parity** | 100% valid plans without LLM | **100.0%** (10/10 valid) | **PASS** |
| **Fault-Injection Interception** | 100% mutated invalid plans rejected | **100.0%** (5/5 caught) | **PASS** |
| **Safety & Anti-Jailbreak Defense** | &ge;40 attack vectors neutralized | **100.0%** (42/42 blocked) | **PASS** |
| **Zero Course Hallucination** | 0 invented course codes permitted | **100.0% Intercepted** (zero leakage) | **PASS** |
| **Plan Certificate Sealing** | Canonical SHA-256 cryptographic seal | **100.0% Verified** (2.01 ms/cert) | **PASS** |
| **Tamper Detection Sensitivity** | Immediate hash mismatch on change | **100.0% Detected** (20/20) | **PASS** |
| **Assessment Item Bank** | &ge;10 items/skill across 24 skills | **240 Real Items** (difficulties 1–4, 100% grounded) | **PASS** |
| **Verified Open Resources** | &ge;90% official skill coverage | **100.0%** (24/24 skills covered, NPTEL/SWAYAM/MIT/NCERT) | **PASS** |
| **Solver Speed (p50 / p95)** | < 100 ms per multi-semester plan | **p50 = 0.23 ms / p95 = 0.33 ms** | **PASS** |
| **Validator Speed (Average)** | < 50 ms per plan verification | **2.71 ms / plan** | **PASS** |
| **Total Evaluation Duration** | Full 78-profile test suite execution | **2.5 seconds** | **PASS** |

---

## 3 Provenance Tiers Integrity Breakdown

### Tier 1 — Verified Institutional Facts (`provenance="verified"`)
- **Source**: Directly grounded in official IIT Bhilai Courses of Study PDF in `data/raw/courses of study.pdf`.
- **Catalogue**: 34 verified courses with official course codes, titles, L-T-P-C credits, and source page citations.
- **Prerequisites**: 17 verified prerequisite relations extracted with source page numbers (e.g. `CSL202` &rarr; `CSL252`, p. 11).
- **Degree Structure**: B.Tech CSE 156 graded credit structure (p. 21).

### Tier 2 — Labelled Assumptions (`provenance="assumption"`)
- **Transparency**: Stored with explicit `provenance="assumption"`, visible rationales, and `"pending ordinance"` citations in `academic_rules.json`.
- **Active Rules**: 7 rules evaluated with live badges on certificates (minimum semester credits, credit cap, overload ceiling, CS minor eligibility, online credit limits, offering parity, workload hours).
- **Roadmap**: Documented in `data/raw/ordinance_TODO.md` detailing the target ordinance document, expected clause, and automated upgrade path.

### Tier 3 — Team-Authored Learning Layer (`provenance="team_authored" / "derived"`)
- **Taxonomy**: 24 granular skills across Computer Science, Mathematics, and Humanities domains.
- **Relational Mappings**: 39 course-to-skill mappings derived from official syllabus topics.
- **Syllabus Units**: 112 modules derived from course syllabi topics.
- **Assessment Items**: 240 original assessment items (MCQ with misconceptions, trace-the-output, rubrics, code).
- **Educational Resources**: 24 verified open resources from NPTEL, SWAYAM, MIT OpenCourseWare, and NCERT with validated licenses.
- **Goal Templates**: 4 career pathways (`goal_software`, `goal_research`, `goal_upsc`, `goal_startup`).
