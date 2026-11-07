# Student Academic Journey & Needs Survey

**Status:** Survey instrument ready, responses **PENDING**  
**Target Population:** Undergraduate students across engineering disciplines at IIT Bhilai (B.Tech Years 1–4).  
**Data Provenance Note:** As of this audit, no raw survey responses (CSV/form export) exist in the repository. The questionnaire and analysis pipeline are fully designed and instrumented (`docs/survey/questionnaire.md`, `scripts/analyze_survey.py`). All findings below represent **working product hypotheses** derived from problem statement specifications and preliminary student interviews, pending empirical data collection.

---

## 1. Survey Methodology & Questionnaire

The survey instrument is designed to understand academic navigation bottlenecks, elective discovery hurdles, self-study capacity, and student pain points in course sequencing.

### Questionnaire Structure (18 Questions)
1. **Academic Standing & Programme**: Year (1–4), Department (CSE, EE, DSAI, ME, MECH, etc.), Current CGPA bracket.
2. **Post-Graduation Ambitions**: Primary goal (Industry Software, Higher Studies / MS-PhD, UPSC / Civil Services, Startup Founder, Undecided).
3. **Elective Discovery & Scheduling**:
   - How do you currently discover non-departmental electives? (Word of mouth, senior advice, department circulars, portal browsing).
   - Have you ever faced prerequisite clash or semester offering mismatches?
   - How do you balance CGPA safety vs. ambitious skill acquisition?
4. **Time & Workload Budget**:
   - Realistic independent study hours outside scheduled lectures/labs (hrs/week).
   - Frequency of academic burnout or overload.
5. **Tools Used Today**: ERP portal, unofficial spreadsheets, senior roadmaps, ChatGPT / generic LLMs.
6. **Expectations from a Personalised Learning Buddy**: Critical feature priorities, privacy expectations, and explanation requirements.

*The full 18-question instrument with options, branching, and informed consent statement is available at [`docs/survey/questionnaire.md`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/survey/questionnaire.md).*

---

## 2. Working Hypotheses (Not Survey Data)

> [!IMPORTANT]
> The figures and insights below are **working hypotheses** formulated during product scoping to guide initial architecture. They are **not empirical survey responses** and must be re-calibrated once `data/survey/responses.csv` is populated via `scripts/analyze_survey.py`.

### Hypothesized Bottlenecks & Product Implications

| Dimension | Working Hypothesis (Unverified) | Product Implication |
| :--- | :--- | :--- |
| **Prerequisite Blindspots** | ~75% of students discover a required prerequisite too late to take a target elective. | Hard mathematical prerequisite DAG solver with forward-scheduling. |
| **Generic AI Hallucinations** | ~65% of students who used generic AI chatbots encountered hallucinated course codes or unfeasible schedules. | 100% cited institute course catalogue with zero-hallucination code interceptor. |
| **Workload Underestimation** | ~70% of students who overload credits in Year 2/3 experience a drop in core course performance. | Dynamic weekly workload meters and strict credit headroom ceilings. |
| **Non-CS Minor Confusion** | ~80% of non-CS students find minor eligibility and offering parity rules confusing or poorly documented. | Independent validation rule enforcing institute Minor degree policy. |
| **Realistic Self-Study Capacity** | Typical independent study capacity is estimated at 8–10 hours/week outside lectures and labs. | System defaults self-study budget to 8–10 hrs/week, avoiding unrealistic schedules. |

### Hypothesized Career Goal Distribution

```
Industry Software / Tech Role: ~55% [███████████████████████████████]
Higher Studies (MS/PhD Research): ~20% [█████████████]
Civil Services (UPSC / Govt): ~15%     [████████]
Venture Creation / Startup: ~7%        [████]
Undecided / Exploring: ~3%             [██]
```

### Problem Archetypes (Target Student Scenarios)

The following archetypes illustrate the problem space addressed by the product design:

- **Archetype A (Core/Chemical to Software):** Student aiming for software placements who relies on fragmented senior advice, discovers prerequisite dependencies late, and risks overloading on electives.
- **Archetype B (CSE Core & AI):** Student attempting to use generic chatbots for semester roadmaps, resulting in advice recommending courses in wrong semesters or missing discrete mathematics prerequisites.
- **Archetype C (Higher Studies / Research):** Student targeting research admissions who must maintain a high CGPA while taking advanced electives and undergraduate thesis credits.
