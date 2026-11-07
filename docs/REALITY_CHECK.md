# Reality Check Report: Live Visual Inspection & Screenshot Audit

**Date:** 2026-11-07  
**Build Stamp:** `Build fb38d67 · SQLITE: buddy_bhilai.db · Seed e28bdbe8b4b6 (SYNCED) · 34 courses, 112 modules, 24 skills, 240 exercises, 25 resources, 78 profiles`  
**Server Port:** `http://127.0.0.1:8000` (Single runtime process, no background collisions)  
**Screenshots Directory:** `docs/screenshots/final/` (32 full-page 1440px screenshots captured)

---

## 1. Executive Summary: What the Real App Shows Right Now

An automated Playwright capture walked all 4 target user profiles (`BH-SW-001`, `BH-HS-001`, `BH-UP-001`, and `NEW_STUDENT`) across every view of the application:
1. `Today` / Home (`01_home.png`)
2. `Personalize` / Setup (`02_setup.png`)
3. `Diagnostic` / Skill Check (`03_diagnostic.png`)
4. `Curriculum Roadmap` / Plan (`04_plan.png`)
5. `Learn & Practise` (`05_practice.png`)
6. `Skill Mastery Matrix` / Progress (`06_progress.png`)
7. `Buddy` Drawer (`07_buddy.png`)
8. `Admin Console` (`08_admin.png`)

### High-Level Reality Status
- **Resolved (Real Progress):**
  - **P6, P7, P9 (Exercises):** The placeholder prompt *"Which topic is explicitly named in the learning unit above?"* has been completely eradicated. The runtime database now serves genuine, syllabus-grounded questions from the 240-item bank (recursion output tracing, Handshaking Lemma combinatorics, C syntax rules, and engineering communication).
  - **P14 (Port & Environment Cleanliness):** Stale processes on ports 8000/8001 have been killed. The single server runs cleanly on port 8000. Build stamp (`fb38d67`, seed `e28bdbe8b4b6`, 240 exercises) is exposed in `/api/health` and verified synced in the top demo bar.
- **Critical Unresolved Deficiencies (Requiring Stabilization Sprints):**
  - **P1 (Empty Semesters):** The curriculum planner generates plans that leave major semesters completely empty (e.g. Diya Iyer has 0 courses in Semesters 6 and 8, and only 3 credits in Semester 5 and 7).
  - **P2 (Misleading Rule Badge):** The plan view states *"14 of 20 rules satisfied • verified"* in green. 14 of 20 is not satisfied, and 16 of the evaluated checks rely on Tier-2 ordinance assumptions.
  - **P3 (Goal Chip Mismatch):** For Diya Iyer, the top bar displays `"Goal: Degree Completion"` while her selected goal is Higher Studies.
  - **P4 & P11 (Leaked Raw Placeholders):** The shared student summary line visibly prints `"Not available studied · Not available adherence · Readiness Not available"`.
  - **P5 (Unexplained Skill Tags):** Course cards display raw skill tags without explaining why the course was recommended or which diagnostic gap it addresses.
  - **P8 (Mastery Delta Invisible):** Practice submissions show a score but do not show the before/after skill probability delta (e.g., `40% → 52%`).
  - **P10 (Short Diagnostic):** The diagnostic requires only 3 items rather than an adaptive 8–12 item diagnostic loop.
  - **P12 (Buddy Context Dump):** Buddy opens with a robotic memory dump (`"I remember your learning context: You are..."`) rather than an inviting, action-oriented greeting.
  - **P13 (No First-Time Welcome/Pitch):** A stranger visiting the site sees a dense internal dashboard rather than an explanation of what the product does and a 5-step guided path.

---

## 2. Screenshot-by-Screenshot Audit

| Persona | Screen | Screenshot Path | What a User Sees | Visible Defect / Note |
| :--- | :--- | :--- | :--- | :--- |
| **BH-SW-001** (Aarav Sharma, S4, Software) | Home / Today | `BH-SW-001_01_home.png` | Header with name, stats (`—`, `— / 14h`, `0`), next action card (`Computer Systems Design`), rules list | Leaked `"Not available"` in credit headroom; unhelpful empty stat indicators. |
| | Setup | `BH-SW-001_02_setup.png` | Personalize form pre-filled with name, goal, CGPA (7.8), 14h/week | Functional, but labeled as a primary sidebar navigation item rather than an onboarding step. |
| | Diagnostic | `BH-SW-001_03_diagnostic.png` | *"Question 1 · Programming fundamentals: What is the output of the recursive call f(4)..."* | **Verified Good**: Real C code question with options. Defect P9 resolved. |
| | Plan | `BH-SW-001_04_plan.png` | Sem 5: CSL559 (4cr), CSL303 (4cr). Sem 6: 0 cr. Sem 7: 0 cr. Sem 8: 0 cr. Total: 8 cr. | **Defect P1 & P2**: Semesters 6, 7, 8 are completely empty (0 cr). Badge says "13 of 20 rules satisfied • verified". |
| | Practise | `BH-SW-001_05_practice.png` | Exercise bank with C programming exercises, code box, output area | Real questions shown. Does not yet show skill delta after submit (P8). |
| | Progress | `BH-SW-001_06_progress.png` | Skill matrix showing 24 skills, proficiency %, evidence counts | All skills currently show 0 evidence until diagnostic is taken. Needs clear 3-state categorization (not started, course done, proven). |
| | Buddy | `BH-SW-001_07_buddy.png` | Chat drawer with memory dump: *"I remember your learning context: You are Aarav Sharma..."* | **Defect P12**: Robotic context dump. |
| | Admin | `BH-SW-001_08_admin.png` | Student parameter mutation, adaptation scenario runner, Adminer pointer | Functional admin controls. |
| **BH-HS-001** (Diya Iyer, S4, Higher Studies) | Home / Today | `BH-HS-001_01_home.png` | Header with Diya Iyer, CGPA 8.7, Goal chip: **Degree Completion** | **Defect P3**: Goal chip displays "Degree Completion" instead of Higher Studies. |
| | Setup | `BH-HS-001_02_setup.png` | Setup form with Diya Iyer, Higher Studies goal | Clean form state. |
| | Diagnostic | `BH-HS-001_03_diagnostic.png` | *"Question 1 · Discrete mathematics: By the Handshaking Lemma..."* | **Verified Good**: Authentic math question with options. |
| | Plan | `BH-HS-001_04_plan.png` | Sem 5: CSL515 (3 cr). Sem 6: 0 cr. Sem 7: CSQ401 (3 cr). Sem 8: 0 cr. Total: 6 cr. | **Defect P1 & P2**: Empty semesters (6 and 8). Badge says "14 of 20 rules satisfied • verified". Summary leaks `"Not available"`. |
| | Practise | `BH-HS-001_05_practice.png` | 240 exercise bank with skill filter dropdown | Exercises load properly. |
| | Progress | `BH-HS-001_06_progress.png` | Skill mastery grid | Clean grid, needs 3 distinct visual states and evidence history drawer. |
| | Buddy | `BH-HS-001_07_buddy.png` | Chat drawer showing assistant reply citing randomized algorithms and project methods | Real citations present, but context dump header is still rendered. |
| | Admin | `BH-HS-001_08_admin.png` | Admin mutation controls | Functional. |
| **BH-UP-001** (Kabir Verma, S3, UPSC) | Home / Today | `BH-UP-001_01_home.png` | Header, Next course: Macroeconomics | Summary line leaks `"Not available"` 3 times. |
| | Setup | `BH-UP-001_02_setup.png` | Setup form with UPSC goal | Functional. |
| | Diagnostic | `BH-UP-001_03_diagnostic.png` | *"Question 1 · Communication: What is the primary function of an Executive Summary..."* | **Verified Good**: Real communication question. |
| | Plan | `BH-UP-001_04_plan.png` | Sem 4: 8 Liberal Arts courses (15 cr). Sem 5: 0 cr. Sem 6: 0 cr. Sem 7: CSQ401 (3 cr). Sem 8: 0 cr. | **Defect P1**: Semesters 5, 6, and 8 have 0 courses planned. |
| | Practise | `BH-UP-001_05_practice.png` | Exercise sandbox | Functional. |
| | Progress | `BH-UP-001_06_progress.png` | Mastery matrix | Functional. |
| | Buddy | `BH-UP-001_07_buddy.png` | Chat with UPSC course advice | Cites LAL courses, but opens with robotic memory dump. |
| | Admin | `BH-UP-001_08_admin.png` | Admin console | Functional. |
| **NEW_STUDENT** (Fresh student) | Home / First visit | `NEW_STUDENT_01_home.png` | Blank student dashboard | **Defect P13**: Lands on empty dashboard without onboarding pitch or 5-step journey. |
| | Setup | `NEW_STUDENT_02_setup.png` | Empty setup form | Needs clear guidance. |
| | Diagnostic | `NEW_STUDENT_03_diagnostic.png` | Diagnostic prompt | Functional. |
| | Plan | `NEW_STUDENT_04_plan.png` | Initial plan view | Functional. |
| | Practise | `NEW_STUDENT_05_practice.png` | Practice sandbox | Functional. |
| | Progress | `NEW_STUDENT_06_progress.png` | Empty mastery matrix | Needs teaching empty state. |
| | Buddy | `NEW_STUDENT_07_buddy.png` | Fresh buddy stream | Functional. |
| | Admin | `NEW_STUDENT_08_admin.png` | Admin console | Functional. |

---

## 3. Detailed Comparison: Defects P1 to P14

| Defect ID | Description from Prompt | Status Today | Exact Evidence from Live App |
| :--- | :--- | :--- | :--- |
| **P1** | Empty Plan Semesters (Sem 5, 6, 8 have 0 credits) | **STILL PRESENT** | Live API `/api/plans/BH-HS-001`: Sem 5 has 3 cr, Sem 6 has 0 cr, Sem 7 has 3 cr, Sem 8 has 0 cr. Total planned: 6 cr of 144 required for graduation. |
| **P2** | Misleading badge "14 of 20 rules satisfied • verified" | **STILL PRESENT** | Badge rendered on plan view says `14 of 20 rules satisfied • verified` in green. 14/20 is a failure, and 16 rules are unverified assumptions. |
| **P3** | Goal chip mismatch ("Degree Completion" instead of Higher Studies) | **STILL PRESENT** | For Diya Iyer, `#topbar-goal-text` displays `Goal: Degree Completion` despite profile goal being Higher Studies. |
| **P4** | Leaked placeholders (`Not available`, `null`, `undefined`) | **STILL PRESENT** | `#plan-student-summary` contains: `Not available studied · Not available adherence · Readiness Not available`. |
| **P5** | Unexplained skill tags & "Suggest alternative" button | **STILL PRESENT** | Course cards display raw tags like `core`, `research_methods` without a plain-language explanation of why the course was chosen. |
| **P6** | Stale placeholder exercise prompt ("Which topic is explicitly named...") | **FIXED** | Database seeded with 240 distinct items. Top prompts include recursion tracing, Handshaking lemma, and C identifier rules. |
| **P7** | Question refers to "learning unit above" with no unit displayed | **FIXED** | All 240 questions in `data/seed_bhilai/exercises.json` are self-contained with complete stems and code snippets. |
| **P8** | Practice feedback does not show skill change | **STILL PRESENT** | Feedback displays `Score: 100%. Evidence has been added...` but does not show the skill percentage delta (`40% → 52%`). |
| **P9** | Diagnostic serves placeholder question | **FIXED** | Diagnostic pulls real questions from the active skill pool. |
| **P10** | "1 of 3 diagnostic items assessed" (diagnostic too short) | **STILL PRESENT** | Diagnostic engine considers assessment complete after 3 questions rather than an adaptive 8–12 question loop. |
| **P11** | Shared summary line prints `0 / null credits planned` and `Not available` | **STILL PRESENT** | Formatted string in `app.js` and `summary.py` emits `Not available` 3-5 times when fields are unpopulated. |
| **P12** | Buddy opens with context dump instead of friendly greeting | **STILL PRESENT** | Chat stream begins with `I remember your learning context: You are Aarav Sharma...` with raw CGPA and student ID. |
| **P13** | Nothing on screen explains what the product is for | **STILL PRESENT** | No landing welcome hero, no 5-step roadmap visualization, no purpose lines under screen headers. |
| **P14** | Port & process stale state (port 8000/8001 confusion) | **FIXED** | Single server on port 8000; build stamp `fb38d67` (seed `e28bdbe8b4b6`, 240 exercises) visible in demo bar and `/api/health`. |

---

## 4. Phase-by-Phase Roadmap to Stabilization

Based on this reality check, the path forward is unambiguous:
1. **Phase 2 (Runtime Data Parity):** Verify exercise quality gate script and ensure all 240 items are exposed cleanly without `null` titles.
2. **Phase 3 (Curriculum Planner Reality):** Resolve the credit structure from the Bhilai PDF (144 vs 156), populate all remaining semesters with required courses, programme electives, and open electives, fix rule summary semantics, and eliminate all `null`/`Not available` leaks.
3. **Phase 4 (Understandable UI):** Introduce the Home screen pitch, 5-step journey, rename navigation (Today, Your plan, Practise, Progress, Buddy), and implement UI text guard.
4. **Phase 5 (Learning Loop):** Expand diagnostic to 8–12 adaptive questions, render visible before-and-after skill delta in practice, and group progress into 3 clear states.
5. **Phase 6 (Buddy Polish):** Replace context dump with short greeting and 3 action pills; cite course codes and PDF pages.
6. **Phase 7 (Hide Unproven Features):** Move incomplete features behind Advanced and catalog them in `docs/KNOWN_LIMITATIONS.md`.
7. **Phase 8 (Demo Check):** `make demo-check`, `make demo-reset`, `docs/DEMO_WALKTHROUGH.md`, and final verified report.
