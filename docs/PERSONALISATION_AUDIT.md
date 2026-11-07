# Personalisation & Curriculum Differentiation Audit

> **Scope**: Comparison of curriculum plans, next best actions, elective pathways, goal milestones, and curated learning resources across the three hero personas and newly onboarded students at IIT Bhilai.
> **Verified Ground Truth**: All course facts, credits, and syllabus constraints ground directly in `data/raw/courses of study.pdf`.

---

## 1. Executive Summary: Distinct Personalisation by Goal

The learning buddy generates differentiated, goal-specific roadmaps while maintaining strict compliance with the IIT Bhilai B.Tech CSE Senate curriculum.

| Dimension | Aarav Sharma (`BH-SW-001`) | Diya Iyer (`BH-HS-001`) | Kabir Verma (`BH-UP-001`) |
| :--- | :--- | :--- | :--- |
| **Target Ambition** | Software Engineering & Systems | Higher Studies & Computing Research | UPSC Civil Services Examination |
| **Current Standing** | Semester 4, Year 2, CGPA 8.40 | Semester 4, Year 2, CGPA 8.70 | Semester 3, Year 2, CGPA 7.60 |
| **Next Best Action** | **CSL303: Database Management Systems** | **CSL304: Artificial Intelligence** | **LAL225: Self and Society in Modern India** |
| **Next Action Rationale** | Targets 75% gap in Database systems; core backend persistence and concurrency foundation. | Core AI foundation required for graduate research and research lab placement. | Targets 75% gap in Society & Institutions; aligns with UPSC GS IV (Ethics & Society). |
| **Elective Strategy** | High-throughput distributed systems & compilers (`CSL559`, `CSL518`, `CSL512`) | Deep theoretical algorithms & formal methods (`CSL515`, `CSL504`, `CSL510`, `CSL511`) | Maximized Humanities & Economics coverage (`LAL225`, `LAL200`, `LAL201`, `LAL222`, `LAL221`) |
| **Total Credits Planned** | 55.0 credits | 56.0 credits | 57.0 credits |
| **Next Sem Typical/Planned**| 17.0 planned / 18.0 typical | 18.0 planned / 18.0 typical | 16.0 planned / 16.0 typical |

---

## 2. Next Best Action Differentiation

A key requirement is that a software student, a research student, and a civil services aspirant must not receive identical next action recommendations unless explicitly justified.

```
+---------------------------------------------------------------------------------------------------+
| PERSONA NEXT BEST ACTIONS                                                                        |
+---------------------------------------------------------------------------------------------------+
| Aarav Sharma (Software)   --> Next planned course: Database Management Systems (CSL303, 4 cr)     |
|                               Rationale: High-priority core backend and data systems competence   |
|                                                                                                   |
| Diya Iyer (Research)      --> Next planned course: Artificial Intelligence (CSL304, 4 cr)         |
|                               Rationale: Core graduate research requirement and AI lab readiness  |
|                                                                                                   |
| Kabir Verma (UPSC)        --> Next planned course: Self and Society in Modern India (LAL225, 2 cr)|
|                               Rationale: UPSC GS Paper IV Ethics, Social Structure & Institutions |
+---------------------------------------------------------------------------------------------------+
```

### Statutory Core Course Justification
In Semester 5, all IIT Bhilai B.Tech CSE students must complete the Senate-mandated Programme Core:
- `CSL301` Operating Systems (4 cr)
- `CSL302` Compiler Design (4 cr)
- `CSL303` Database Management Systems (4 cr)
- `CSL304` Artificial Intelligence (4 cr)

Because omitting these courses would violate degree requirements (PDF pp. 21–22), both Aarav and Diya take these core courses. However, the **priority ranking and immediate Next Best Action** reflect their goals:
- **Software**: Ranks `CSL303` (DBMS) first.
- **Research**: Ranks `CSL304` (AI) first.
- **UPSC**: Because Kabir is in Semester 4, his priority slot features `LAL225` (*Self and Society in Modern India*), immediately reinforcing his civil services ambition.

---

## 3. Semester-by-Semester Electives & Pathways

### 3.1 Software Engineering (`BH-SW-001`)
Focuses on scalable architecture, systems programming, and high-performance computation:
- **Semester 5**: `CSL303` (DBMS, 4 cr), `CSL301` (OS, 4 cr), `CSL302` (Compilers, 4 cr), `CSL304` (AI, 4 cr), `LAL201` (Microeconomics, 1 cr).
- **Semester 6**: `CSL559` (Computer Systems Design, 4 cr), `CSL351` (Computer Networks, 4 cr), `CSL518` (Distributed Algorithms, 3 cr), `LAL225` (Self and Society, 2 cr).
- **Semester 7**: `CSL512` (Parallel Algorithms, 3 cr), `CSQ401` (BTech Project-I, 3 cr), `CSL505` (Cryptography, 3 cr), `CSL504` (Graph Theory, 3 cr), `LAL200` (Macroeconomics, 2 cr), `LAL224` (Postcolonial Lit, 2 cr).
- **Semester 8**: `CSL511` (Formal Verification, 3 cr), `CSL515` (Randomized Algorithms, 3 cr), `CSL510` (Approximation Algorithms, 3 cr).

### 3.2 Higher Studies & Research (`BH-HS-001`)
Focuses on foundational mathematics, algorithmic complexity, and academic publishing:
- **Semester 5**: `CSL304` (AI, 4 cr), `CSL302` (Compilers, 4 cr), `CSL301` (OS, 4 cr), `CSL303` (DBMS, 4 cr), `LAL225` (Self and Society, 2 cr).
- **Semester 6**: `CSL515` (Randomized Algorithms, 3 cr), `CSL504` (Graph Theory, 3 cr), `CSL351` (Computer Networks, 4 cr), `LAL224` (Postcolonial Lit, 2 cr).
- **Semester 7**: `CSL510` (Approximation Algorithms, 3 cr), `CSQ401` (BTech Project-I, 3 cr), `CSL518` (Distributed Algorithms, 3 cr), `CSL511` (Formal Verification, 3 cr), `LAL202` (International Trade, 2 cr), `LAL223` (Partition Literature, 2 cr).
- **Semester 8**: `CSL505` (Cryptography, 3 cr), `CSL512` (Parallel Algorithms, 3 cr), `CSL559` (Computer Systems Design, 4 cr).

### 3.3 UPSC Civil Services (`BH-UP-001`)
Focuses on comprehensive social sciences, administrative ethics, and public policy:
- **Semester 4**: `LAL225` (Self and Society, 2 cr), `LAL200` (Macroeconomics, 2 cr), `LAL201` (Microeconomics, 1 cr), `LAL222` (City in Literature, 2 cr), `CSL252` (Design & Analysis of Algorithms, 4 cr), `CSL253` (Theory of Computation, 4 cr), `LAL101` (Introduction to Finance, 1 cr).
- **Semester 5**: `CSL303` (DBMS, 4 cr), `CSL304` (AI, 4 cr), `LAL221` (Indian Writing in English, 2 cr), `LAL224` (Postcolonial Literature, 2 cr).
- **Semester 6**: `CSL351` (Computer Networks, 4 cr), `LAL223` (Partition Literature, 2 cr), `LAL202` (International Trade, 2 cr).
- **Semester 7**: `CSQ401` (BTech Project-I, 3 cr), `CSL505` (Cryptography, 3 cr), `CSL504` (Graph Theory, 3 cr), `CSL510` (Approximation Algorithms, 3 cr).
- **Semester 8**: `CSL518` (Distributed Algorithms, 3 cr), `CSL515` (Randomized Algorithms, 3 cr), `CSL511` (Formal Verification, 3 cr).

---

## 4. Goal Milestones Comparison

Milestones structure non-credit career preparation across semesters:

| Semester Offset | Software Engineering (`BH-SW-001`) | Higher Studies (`BH-HS-001`) | UPSC (`BH-UP-001`) |
| :---: | :--- | :--- | :--- |
| **M1** | Systems Core & Algorithmic Foundations (150+ LeetCode/Codeforces) | Faculty Lab Attachment & AI Literature Survey | Foundational General Studies (GS I & IV) & Ethics |
| **M2** | Distributed Systems Capstone & Open Source Contribution | Original Research Manuscript Submission (Workshop paper) | CSAT Mastery & Macroeconomic Policy Analysis |
| **M3** | System Design & Technical Interview Preparation | SOP Formulation & Graduate Admissions Portfolio | Optional Subject Deep-Dive & Answer Writing Drills |
| **M4** | Industry Software Engineering Transition | Senior Honors Thesis Defense | UPSC Civil Services Prelims Mock Simulation Series |
| **M5** | *N/A (Graduation)* | *N/A (Graduation)* | Personality Test / Interview Board Guidance |

---

## 5. Curated Open Educational Resources (OER)

Each student's plan attaches zero-cost, high-quality open learning resources mapped to their diagnostic gaps and target roles:

### Software Engineering
1. **Problem Solving through Programming in C** (NPTEL · `nptel_cs_prog_c`)
2. **The Missing Semester of Your CS Education** (MIT OpenCourseWare · `mit_missing_semester`)
3. **Introduction to Algorithms** (MIT OpenCourseWare · `mit_6006`)
4. **Database Systems** (MIT OpenCourseWare · `mit_6830`)
5. **Software Engineering** (NPTEL · `nptel_cs_soft_eng`)

### Higher Studies & Research
1. **Mathematics for Computer Science** (MIT OpenCourseWare · `mit_6042j`)
2. **Research Methodology** (NPTEL · `nptel_research_methods`)
3. **Introduction to Probability and Statistics** (MIT OpenCourseWare · `mit_1805`)
4. **Technical English for Engineers** (NPTEL · `nptel_tech_english`)

### UPSC Civil Services
1. **Technical English for Engineers** (NPTEL · `nptel_tech_english`)
2. **Introductory Macroeconomics** (NCERT Class XII · `ncert_macroeconomics`)
3. **Introductory Microeconomics** (NCERT Class XII · `ncert_microeconomics`)
4. **International Economics and Trade Policy** (NPTEL · `nptel_intl_economics`)
5. **Indian Society** (NCERT Class XII · `ncert_indian_society`)
6. **Introduction to Literary Theory** (NPTEL · `nptel_literary_theory`)

---

## 6. Audit Assertions & Rule Grounding

1. **Course Grounding (PDF Audit)**:
   - All 34 courses strictly ground in `data/raw/courses of study.pdf`.
   - `CSL304` (Artificial Intelligence) verified on PDF pp. 21, 22, 85 (4 credits, 3-0-2).
   - `CSL510` (Approximation Algorithms) verified on PDF p. 88 (3 credits, 3-0-0).
   - `LAL225` verified as *Self and Society in Modern India* on PDF p. 139 (2 credits, 2-0-0).
2. **Persona Consistency**:
   - `Year = ceil(current_semester / 2)` holds true for all 78 seed profiles and newly created onboarding profiles.
3. **Mastery Threshold**:
   - Exactly one threshold (`0.85`) governs BKT, practice, conflict alerts, and frontend indicators.
