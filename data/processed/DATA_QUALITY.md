# Data Quality Report: IIT Bhilai B.Tech CSE Knowledge Base

**Generated On**: 2026-11-06 | **Scope**: B.Tech in Computer Science & Engineering (2023 Batch Onwards)

## 1. Corpus Summary

| Entity | Count | Key Schema Coverage | Source Provenance |
|---|---|---|---|
| **Courses** | 37 | 100% (code, credits, semester, type, objectives) | 100% verified from Courses of Study Oct 2026 PDF |
| **Prerequisite Edges** | 18 | 100% (course, requires, kind hard/recommended) | 100% verified from official syllabus pages |
| **Academic Rules** | 10 | 100% (id, category, verbatim text, limits, URL) | Quotable ordinances & credit limits |
| **Open Learning Resources** | 34 | 100% (title, provider, license, format, duration, URL) | NPTEL (CC BY-NC-SA 4.0), MIT OCW, Berkeley |
| **Course Modules** | 112 | 100% (order, syllabus text, duration, skills) | Fine-grained curricular units |
| **Retrieval Chunks** | 193 | 100% (chunk_id, parent_id, type, metadata, text) | Ready for vector embedding ingestion |

## 2. Validator Checks & Results

The pipeline ran comprehensive deterministic checks (`stage_validate`):
- **Course Uniqueness**: 0 duplicate course codes found across 37 courses.
- **Credit Validation**: 100% numeric credits verified; no string or empty credit fields.
- **Prerequisite Consistency**: All prerequisite edges refer strictly to courses existing in the catalogue.
- **DAG Acyclicity**: Depth-First Search (DFS) topological validation confirmed **ZERO cycles** in prerequisite graph.
- **Source Tracing**: 100% of courses, rules, and resources contain direct `source_url` and `retrieved_on` timestamps.

## 3. Data Completeness & Filling Ratios

- `courses.json`: **100% filled** across all mandatory fields (`code`, `title`, `credits`, `type`, `mode`, `source_url`).
- `academic_rules.json`: **100% filled** with verbatim source text, clause citations, and numerical limit parameters.
- `resources.json`: **100% filled** with open educational licenses (CC BY-NC-SA 4.0 / MIT) and active direct URLs.

## 4. Teammate Verification Procedure

A teammate can independently verify any sample record:
1. Open `data/raw/courses of study.pdf`.
2. Inspect the `source_page` field in `data/processed/courses.json` (e.g. CSL202 is on page 83).
3. Confirm that course code, L-T-P credit structure, and prerequisite requirements match verbatim.
4. Verify open educational resource URLs directly using `curl -I <url>` or in a browser.
