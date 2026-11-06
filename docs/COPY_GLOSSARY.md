# Copywriting & Terminology Glossary (docs/COPY_GLOSSARY.md)

This glossary governs all customer- and student-facing language across the Adobe Personalised Learning Buddy. All engineers and prompt templates must use the approved student-facing terminology. Technical and internal implementation jargon must be confined strictly to the administrative console and developer reports.

---

## Terminology Mapping Table

| Internal / Implementation Term | Approved Student-Facing Term | Tone & Usage Guidelines | Example in Context |
| :--- | :--- | :--- | :--- |
| **BKT (Bayesian Knowledge Tracing)** | **Skill estimate** / **Demonstrated proficiency** | Never show "BKT Monitored" to students. State the concrete mastery or estimate level. | "Your skill estimate in Linear Data Structures is 88% based on recent exercises." |
| **Mutex / Incompatibility / Conflict** | **Courses you asked to keep apart** | Calm, non-alarmist phrasing. Avoid computer science synchronization jargon. | "You asked to keep COL351 and COL352 apart so your workload remains balanced." |
| **Prerequisite DAG / Directed Graph** | **Preparation path** / **Prerequisite chain** | Emphasize academic sequence rather than graph data structures. | "Your preparation path for Operating Systems begins with Computer Architecture." |
| **CP-SAT / Solver / Constraint Engine** | **Verified roadmap** / **Degree planner** | Students care about validity and graduation, not the constraint programming library. | "Your degree roadmap satisfies all graduation and prerequisite ordinances." |
| **LiteLLM / Model Provider / Endpoint** | *Admin only* (Quiet degraded banner if offline) | Never show "LiteLLM Online" in student UI. If offline, display quiet reassurance. | *"Operating in simplified mode. Your degree plan remains fully verified."* |
| **Hero S1024 / S1025 / S1026** | **Student Name** (e.g. *Aryan Sharma*) | In Demo mode only: *"Viewing as: Aryan Sharma (Chemical Eng → Software)"*. | "Viewing as: Rohan Verma, Chemical Eng, UPSC civil services" |
| **Diagnostic Intake / Onboarding Wizard** | **Skills check** / **Initial setup** | Action-oriented verbs. Frame as a quick milestone rather than an administrative hurdle. | "Take the 8-minute skills check to personalize your recommendations." |
| **Remediation Drill / Remedial Resource** | **Focused practice** / **Foundation review** | Supportive, growth-oriented. Never make students feel penalized. | "Review foundation concepts in tree traversals before starting advanced assignments." |
| **Academic Ordinance Clauses (ORD-X.X.X)** | **Academic regulations** / **Institute rules** | Cite the specific ordinance clause in the Certificate drawer, but explain the meaning in plain prose. | "Credit headroom next semester: 4.0 credits remaining under Institute Rule 3.2.1." |
| **Adherence / Drift Policy** | **Study routine** / **Weekly progress** | Focus on weekly cadence and real learning habits. | "This week’s study routine: 6 of 10 hours completed." |

---

## Tone Guidelines
1. **Calm, specific, and editorial**: Avoid exclamation marks, hype, and gamified dopamine lures (no confetti, badges, or "You're a superstar!").
2. **Deterministic first**: Always tell the student *why* an action was suggested, backed by specific evidence: *"We suggested this reading because your last quiz showed uncertainty with parliamentary procedure."*
3. **Sentence case everywhere**: Write `"Credit headroom next semester"`, not `"CREDIT HEADROOM NEXT SEMESTER"` or `"Credit Headroom Next Semester"`.
4. **Typographic punctuation**: Always use curly quotes (`“...”`), apostrophes (`’`), and en-dashes (`–`) for ranges.

