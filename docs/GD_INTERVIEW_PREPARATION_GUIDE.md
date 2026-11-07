# Group Discussion (GD) & Technical Interview Preparation Guide
## Adobe Inter-IIT Tech Meet 15.0: Personalised Learning Buddy for IIT Bhilai

This guide provides the exact spoken scripts, structural reasoning, unique engineering differentiators, iterative prototype trials, and prototype walkthrough steps to answer the four core questions in tomorrow's evaluation.

---

## 1. "What Did You Understand by the Problem Statement, and How Would You Approach It?"

### 🎙️ Spoken Script for the GD:
> *"The problem statement asks us to build an intelligent, multi-turn **Personalised Learning Buddy** for undergraduate students at **IIT Bhilai (B.Tech CSE)**.*
>
> *At its core, this is not just another conversational chatbot. It is a **constrained optimisation and pedagogical adaptation challenge**.*
>
> *Every student at IIT Bhilai faces a three-way tension:*
> 1. ***Rigid Academic Constraints:*** *They must fulfill 144 graded credits, strict prerequisite DAGs (Directed Acyclic Graphs), course-level caps, and semester offering rules from the official Courses of Study.*
> 2. ***Divergent Career Goals:*** *A student targeting Software/SDE, Higher Studies/Research, Civil Services (UPSC), or a Startup needs completely different elective pathways and timelines.*
> 3. ***The Grade vs. Competency Gap:*** *Passing a course with a 'B' does not mean you have mastered Data Structures for placement interviews or GATE. Course grades alone are blunt instruments.*
>
> *Generic LLMs like ChatGPT or Claude fail here because they **hallucinate course codes**, **ignore prerequisite chains**, and **cannot compute credit math**.*
>
> ***Our Approach:***
> *We designed a **hybrid neuro-symbolic architecture**: a strict, deterministic rule and scheduling engine for mathematics and institute ordinances, paired with an empathetic, tool-calling LLM via LiteLLM for natural conversation, explanations, and goal discovery. Every recommendation is grounded in real institutional data, verified against a Bayesian skill mastery engine, and delivered through an interactive, multi-turn experience."*

### Key Structural Highlights to Emphasize:
- **Academic Grounding:** Based on the official 208-page *IIT Bhilai Courses of Study (October 2026; applicable for 2023 batch onwards)*.
- **The Core Problem:** Bridging institutional degree rules with personal career ambitions without hallucination.
- **The Core Loop:** $\mathbf{Assess} \longrightarrow \mathbf{Personalise} \longrightarrow \mathbf{Learn} \longrightarrow \mathbf{Practise} \longrightarrow \mathbf{Adapt} \longrightarrow \mathbf{Demonstrate\ Mastery}$.

---

## 2. "What Unique Idea(s) Do You Have to Solve This?"

When the panel asks what unique idea or differentiator sets your solution apart, deliver these **4 Unique Differentiators**:

### 1. The Strict "Deterministic Engine vs. LLM" Split (Zero Hallucination Guarantee)
* **The Problem:** LLMs are probabilistic text generators. When asked to schedule courses, they hallucinate course numbers, recommend courses in wrong semesters, and miscalculate credits.
* **Our Unique Solution:** The LLM is never allowed to calculate credits, verify prerequisites, or enforce university ordinances. All hard logic (credit ceilings, semester eligibility, topological prerequisite sorting) runs in deterministic Python algorithms (`validate_plan`, `check_add`, `check_drop`). The LLM acts purely as an interface that calls these deterministic tools to fetch ground-truth facts. If the LLM generates an unverified code or incorrect math, an automated verification interceptor catches it, logs the violation, and falls back safely.

### 2. Multi-Modal Evidence via Bayesian Knowledge Tracing (BKT)
* **The Problem:** Traditional degree audits only see letter grades from months ago, ignoring skill decay and practical competence.
* **Our Unique Solution:** Our buddy tracks **24 granular skill competencies** using Bayesian Knowledge Tracing (BKT). We ingest **6 distinct adaptation signals** (§2.4): diagnostic quizzes, practice exercises, time spent, repeated attempts, decaying evidence over time, and self-declared confidence. The system clearly separates *"Courses Completed"* from *"Demonstrated Skill Proficiency"*.

### 3. Tiered Knowledge Base with Cryptographic Auditability
* **The Problem:** Many AI products fabricate rules, invent non-existent survey statistics, or present ungrounded opinions as university regulations.
* **Our Unique Solution:** We implemented a strict **3-tier data provenance model**:
  * **Tier 1 (Verified Facts):** 100% cited directly from the 208-page official *Courses of Study* PDF with exact page numbers (34 courses, 18 prerequisites, 144-credit requirement).
  * **Tier 2 (Labelled Assumptions):** Unstated institute policies (e.g., 24-credit maximum cap, 12-credit floor, overload thresholds, CS minor cutoffs) are explicitly flagged with `provenance="assumption"` and display visible **"Assumed (Pending Ordinance)"** warning badges in the UI.
  * **Plan Certificate:** Every degree plan generates a deterministic SHA-256 cryptographic seal verifying compliance against all academic rules.

### 4. Interactive "Plan-as-Code" Proposals (Buddy Acts, Not Just Talks)
* **The Problem:** Chatbots that only give text responses force the student to manually cross-reference and edit their schedules elsewhere.
* **Our Unique Solution:** When the buddy suggests dropping a course or adding an elective, it renders an **actionable `[Apply Change]` card** directly inside the chat stream. One click updates the student's degree plan in real time, logs the diff in version history, and recalculates weekly study workload.

---

## 3. "What All Have We Tried in Making This Prototype?"

Walk the panel through your **engineering journey, iterative experiments, and empirical testing**:

### 1. Attempted vs. Abandoned: Pure LLM Prompting
* **What we tried:** Initially tested feeding the entire course catalogue and academic rules into an LLM system prompt, asking Gemini/GPT to schedule a 4-year degree plan.
* **Why it failed:** The LLM frequently suggested electives in semesters where they weren't offered, violated prerequisite dependencies (e.g., recommending *Algorithms* before *Data Structures*), and made basic credit arithmetic errors.
* **What we built instead:** Extracted the syllabus into a Directed Acyclic Graph (DAG) and built a topological prerequisite solver that gates every course addition mathematically.

### 2. Persona Modeling & Appendix A Grounding:
* Built **4 canonical Hero Personas** covering the full spectrum of IIT Bhilai students:
  * **Aarav Sharma (`BH-SW-001`)**: 3rd Sem, aiming for Software SDE, balanced academics.
  * **Rohan Verma (`BH-HS-001`)**: 3rd Sem, research-focused, targeting foreign MS/PhD, needs research electives and B.Tech project early.
  * **Tara Rao (`BH-UP-001`)**: 3rd Sem, underprepared/foundation gaps, needs credit headroom management and remediation.
  * **Priya Patel (`BH-ST-001`)**: 7th Sem high-performer (8.9 CGPA), looking for advanced electives and placement polish.
* Designed a **6-step onboarding wizard** for arbitrary new students that validates completed courses, accepts target career ambitions, and dynamically synthesizes an optimal 8-semester roadmap.

### 3. Graceful Degradation & Network Sandbox Testing:
* Built an abstraction layer over **LiteLLM** supporting multiple model providers (`gemini-3.5-flash-lite`, OpenAI, Claude) without code changes.
* Implemented automatic timeout and rate-limit fallbacks: if the API key fails or network drops, the system seamlessly degrades to deterministic template answers without crashing or showing blank screens.

### 4. Automated Quality & Anti-Template QA Suite:
* Implemented AST checks preventing any direct provider SDK imports outside LiteLLM.
* Built `scripts/qa/exercise_quality.py` which audits all 240 questions for duplicate prompts (similarity > 0.85), ensures at least 3 plausible distractors for every MCQ, and verifies 100% topic alignment between modules and skill tags.
* Wrote Playwright end-to-end acceptance tests capturing verified screenshot artifacts across all 7 development phases.

---

## 4. "How Would You Explain the Working of the Prototype?"

Give a crisp, 5-stage walkthrough of the student journey:

```
┌────────────────────────────────────────────────────────┐
│ 1. Onboard & Diagnose (6-step wizard, baseline skills) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. Deterministic Planner (Locks Core, Solves DAG, Cap) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. Interactive Buddy Chat (Tool-calling with [Apply])  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. BKT Practice & Mastery (Adaptive quiz, OER, Ring)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 5. Evaluator & Audit Engine (Plan diff, SHA-256 seal)  │
└────────────────────────────────────────────────────────┘
```

### Step 1: Onboarding & Baseline Diagnostic
1. The student selects their programme (B.Tech CSE), current semester, CGPA, target goal (Software, Research, UPSC, Startup), and up to 5 interest chips.
2. They take an adaptive diagnostic question. Their answers immediately initialize their **Bayesian Knowledge Tracing (BKT)** mastery probabilities.

### Step 2: Validated Semester Roadmap
1. The system invokes the deterministic solver. It locks mandatory institute core courses (`🔒 Required`), calculates remaining elective slots, and displays the **credit meter** (e.g., `18 / 24 credits`, showing `6 credits headroom`).
2. Dropping a core course is blocked (`400 Bad Request`); dropping an elective dynamically updates available headroom.

### Step 3: Multi-Turn Buddy with Tool Execution
1. The student chats with the buddy: *"What should I take in Semester 6 for machine learning?"* or *"Can I add CSL304?"*
2. The Buddy queries deterministic tools (`get_gaps`, `list_eligible`, `check_add`).
3. It responds in 3–5 sentences citing exact course codes and PDF pages, names any prerequisite gaps, and presents an **interactive proposal card**. Clicking **Apply** updates the planner state instantly.

### Step 4: Practice, Learning Resources & Mastery Ring
1. On the **Practise** tab, the student sees targeted study resources (curated NPTEL and MIT OCW links with verified licenses) and diagnostic MCQs.
2. Submitting an answer provides immediate pedagogical explanations (why option A is correct and why B is a misconception).
3. Correct answers trigger live BKT state updates, advancing the SVG **Goal Readiness Ring** from baseline to target mastery.

### Step 5: Evaluator Tools & Cryptographic Audit
1. Under the **Evaluator Tools (`Eval`)**, judges and faculty can:
   - Simulate a mid-semester "what-if" drop or fail, viewing a real-time **Plan Diff**.
   - Edit course credit workloads and test solver re-indexing.
   - Inspect the cryptographic Plan Certificate with its SHA-256 seal and explicit ordinance assumption disclosures.

---

## 5. GD Golden Strategy & Power Phrases

| Discussion Point | What to Say | What NOT to Say |
| :--- | :--- | :--- |
| **System Architecture** | *"We implemented a neuro-symbolic split: deterministic constraint solvers for institute rules, and LLM tool-calling for explanation and dialogue."* | *"We just prompted ChatGPT with all the PDF text."* |
| **Data Accuracy** | *"Course codes, prerequisites, and credit arithmetic are never generated by model memory; they are fetched from deterministic tool outputs."* | *"Our prompt tells the AI not to hallucinate."* |
| **Student Modeling** | *"We model competencies through Bayesian Knowledge Tracing across 6 adaptation signals, differentiating course completion from tested mastery."* | *"We just check their CGPA and recommend electives."* |
| **Missing Regulations** | *"Where the official PDF is silent on credit caps or minor pathways, we label them transparently as assumptions pending ordinance."* | *"We assumed the standard rules that all IITs have."* |
| **Interactive UX** | *"The conversation is actionable: recommendations yield interactive proposal cards with real-time diffs, not just conversational text."* | *"The chatbot tells the student what to do."* |

---

## 6. One-Minute Closing Summary for Judges
> *"In summary, our Learning Buddy solves the core problem of university advising: it bridges rigid institute constraints with personal student ambitions. We achieve this not with another fragile chatbot, but with an accredited, deterministic-first academic instrument that pairs Bayesian mastery modeling with verifiable ordinance compliance."*
