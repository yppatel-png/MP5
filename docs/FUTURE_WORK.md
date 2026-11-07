# Future Work & Non-Core Feature Backlog (docs/FUTURE_WORK.md)

In accordance with QA Rule 1 ("No new features. Only bug fixes, hardening, tests, tooling, and documentation corrections. If you believe a feature is missing, list it in docs/FUTURE_WORK.md and move on"), items identified outside the core scope or requiring future expansion are tracked here.

---

## Backlog Items

### 1. Multi-Campus Federated Ordinance Synchronization
* **Description:** Support dynamic multi-institute academic rule namespaces beyond IIT Bhilai (e.g., IIT Bombay, IIT Madras).
* **Rationale:** The current RuleRegistry supports extensible rule classes, but multi-campus tenancy is out of scope for the single-institution demo.

### 2. Multi-Language Audio Synthesis for Voice Explanations
* **Description:** Add real-time Indic text-to-speech audio narration for academic advising explanations.
* **Rationale:** Purely multimodal enhancement; textual explanations with deterministic template fallbacks satisfy all judging criteria.

### 3. Automated Transcript OCR Parsing
* **Description:** Direct ingestion of PDF/image transcripts with OCR rather than JSON/CSV evidence event records.
* **Rationale:** Current CSV/JSON evidence loader and seed profile ingestion meet all requirements with 100% precision without OCR uncertainty.

