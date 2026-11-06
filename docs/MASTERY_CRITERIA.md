# Mastery Criteria & Goal Readiness Framework
Establishes the empirical criteria distinguishing course completion from demonstrated proficiency, and details the composite formula for goal readiness.

---

## 1. The Core Distinction: Completed vs. Proficient

Traditional university learning management systems equate **course completion** (a passing grade on a transcript) with **skill mastery**. In practice:
- A student may pass a course with a Grade C or cram for an exam without achieving durable operational competence.
- Skills decay over time if not reinforced through active problem solving.

The Adobe Personalised Learning Buddy strictly decouples these two concepts:

```
[Course Completed on Transcript] 
           ≠ 
[Demonstrated Operational Proficiency]
```

---

## 2. Granular Skill Mastery Standard

For any discrete competence (e.g. `skill_dsa_trees` or `skill_db_relational`), a student is certified as **Mastered** if and only if they meet all four empirical criteria:

1. **Posterior Probability Threshold**:
   $$\text{BKT } P(L_t \mid O_{1..t}) \ge 0.85$$
   Calculated using standard Bayesian Knowledge Tracing with slip ($s = 0.10$), guess ($g = 0.20$), and transition ($t = 0.20$).

2. **Independent Item Volume ($K \ge 3$)**:
   The student must successfully solve at least **3 independent assessment items** (quizzes, coding exercises, or rubric-scored problems) with a score $\ge 70\%$.

3. **Multi-Session Verification ($S \ge 2$)**:
   Passed items must span at least **2 distinct sessions separated in time**, verifying retention and ruling out single-session cramming or lucky guesses.

4. **Capstone / Project Verification (for Goal-Critical Skills)**:
   For core skills mapped to the student's primary career goal, mastery additionally requires passing at least **1 timed project checkpoint or comprehensive sandbox coding challenge**.

---

## 3. Four-Tier Skill Classification

Every skill in the student's 30-skill matrix is classified into one of four states:

| Status Code | Display Label | Description & Prerequisites |
| :--- | :--- | :--- |
| `demonstrated_proficiency` | **Demonstrated Proficiency** | Passed $\ge 3$ independent items across $\ge 2$ sessions; BKT $\ge 0.85$. Verified operational competence. |
| `course_completed_only` | **Course Completed (Pending Verification)** | Accredited passing grade on transcript, but lacks recent independent active test evidence. |
| `in_progress` | **In Progress** | Formative practice attempts recorded, but below threshold ($\text{BKT } < 0.85$). |
| `not_started` | **Not Started** | Zero transcript coursework and zero active practice logged. |

---

## 4. Goal-Level Composite Readiness Metric

Goal-level readiness (e.g., *Placement Readiness for Software Engineering*) is a multi-dimensional composite score reflecting total preparation:

$$\text{Readiness \%} = w_{\text{skills}} \cdot \left(\frac{N_{\text{mastered}}}{N_{\text{required}}}\right) + w_{\text{projects}} \cdot \left(\frac{P_{\text{completed}}}{P_{\text{required}}}\right) + w_{\text{mocks}} \cdot \left(\frac{M_{\text{completed}}}{M_{\text{required}}}\right)$$

Where default component weights are:
- **Skill Mastery Weight ($w_{\text{skills}}$)**: $50\%$ (Core theoretical and algorithmic competence)
- **Project Completion Weight ($w_{\text{projects}}$)**: $30\%$ (End-to-end practical system development)
- **Timed Mock Tests ($w_{\text{mocks}}$)**: $20\%$ (Performance under timed placement exam constraints)

### "What's Missing" Actionable Checklist
The dashboard surfaces a transparent checklist indicating the exact steps required to reach $100\%$ readiness:
- `[Skill Drill]`: Complete 2 remaining binary tree coding exercises to lock in `skill_dsa_trees`.
- `[Project]`: Submit Project Milestone 1 for `COP290` (Design Practices).
- `[Timed Mock]`: Complete 1 full-length timed diagnostic exam in Semester 7.

