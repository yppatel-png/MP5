# Academic Trade-Offs & Multi-Objective Balancing
Analyzes the fundamental trade-offs inherent in curriculum planning and details how the Learning Buddy algorithmically balances competing academic objectives.

---

## 1. The Core Trade-Off Frontier

Every engineering student at IIT Delhi navigates four competing forces:

```
                  Learning Depth & Skill Mastery
                                ▲
                                │
                                │
    Workload / Burnout ─────────┼───────── CGPA Protection
                                │
                                │
                                ▼
                     Graduation Timeline
```

---

## 2. Specific Dimension Trade-Offs

### Trade-Off 1: Ambitious Electives vs. CGPA Protection
- **The Dilemma**: Non-CS students targeting software roles frequently want to take advanced electives (`COL351` Algorithm Design, `COL362` Database Systems). However, high-difficulty computer science courses are graded against competitive CSE cohorts, creating risk of a grade drop that could jeopardize overall CGPA.
- **System Balancing**:
  - The buddy imposes the institute's **CGPA $\ge 7.5$** threshold before permitting registration in CS Minor electives.
  - When baseline skill gaps are wide (e.g. DSA mastery $< 40\%$), the planner schedules foundational prerequisites (`COL106`) first and reserves advanced courses for later semesters.
  - Credit ceilings are capped at 18.0 credits during semesters with heavy programming components to ensure adequate time for assignment submission.

### Trade-Off 2: Total Contact Hours vs. Independent Self-Study Budget
- **The Dilemma**: A 22-credit semester demands ~35–42 hours/week of lectures, tutorials, and scheduled labs. A student with ambitious outside-class goals (e.g. competitive programming, open source projects, or UPSC GS reading) cannot sustain 15+ hours/week of independent study on top of full course loads without experiencing severe burnout.
- **System Balancing**:
  - The planner treats student weekly study budget as a hard constraint.
  - If a student reports $\le 8.0$ hours/week available study time, elective courses with heavy uncredited lab components are flagged.
  - If behavioural drift is detected ($< 60\%$ of target study hours logged), the system triggers `RULE_BEHAVIOURAL_DRIFT` and sheds 4.0 elective credits.

### Trade-Off 3: Speed of Acceleration vs. Depth of Mastery
- **The Dilemma**: High-performing students (e.g., Hero Persona Priya S1025) want to fast-track prerequisites to take graduate seminars early. However, compressing the sequence risks shallow retention.
- **System Balancing**:
  - Acceleration is granted only upon **empirical evidence** ($\text{BKT } P(L_t) \ge 0.85$ across $\ge 3$ independent items in $\ge 2$ sessions), never on stated ambition alone.
  - Even when accelerated, mandatory DAG dependencies (`COL100` $\rightarrow$ `COL106` $\rightarrow$ `COL351`) are preserved chronologically across distinct semesters.

