# Stabilisation Sprint Progress Log

**Last Updated:** 2026-11-07  
**Build Stamp:** `Build fb38d67 · SQLITE: buddy_bhilai.db · Seed e28bdbe8b4b6 (SYNCED) · 34 courses, 112 modules, 24 skills, 240 exercises, 25 resources, 78 profiles`  
**Host Port:** `http://127.0.0.1:8000` (verified active single process)  
**Screenshots Path:** `docs/screenshots/final/`

---

## 1. Ground Rules & Current Real Status

This project is in an active **Stabilisation Sprint** focused on end-to-end reality, clarity for first-time users, and eliminating paper compliance.
- Claims without screenshots or execution evidence are disallowed.
- `docs/REQUIREMENTS_TRACE.md` is marked **STALE / UNRELIABLE** pending Phase 8 completion.
- The sole source of truth is the live application running in a clean browser.

---

## 2. Phase 0: Clean Environment & Build Stamp (Completed)

### What Was Done
1. **Process & Port Hygiene:**
   - Stopped legacy processes listening on ports 8000 and 8001.
   - Cleared stale local database files (`data/*.db`).
   - Verified single server running on port 8000 via Uvicorn (`http://127.0.0.1:8000`).
2. **Build Stamp Implementation:**
   - Created `backend/build_stamp.py` computing: Git commit (`fb38d67`), active DB type and filename (`SQLITE: buddy_bhilai.db`), deterministic seed hash (`e28bdbe8b4b6`), and live record counts (34 courses, 112 modules, 24 skills, 240 exercises, 25 resources, 78 student profiles).
   - Exposed `build_stamp` inside `GET /api/health`.
   - Wired live build stamp and stale-database detection into `frontend/index.html` and `frontend/static/js/app.js`. If DB counts diverge from the seed hash, a red warning banner appears with a one-click reset action.
3. **Execution Evidence:**
   - `GET http://127.0.0.1:8000/api/health` returns HTTP 200 `status: healthy`, `seed_match: true`.

---

## 3. Phase 1: Reality Capture & Baseline Analysis (Completed)

### What Was Done
1. **Automated Capture Script:**
   - Authored `scripts/qa/reality_capture.ts` using Playwright at 1440px viewport.
   - Captured full-page screenshots for 4 distinct personas across all 8 user screens:
     - `BH-SW-001` (Aarav Sharma, S4, Software Engineering)
     - `BH-HS-001` (Diya Iyer, S4, Higher Studies & Research)
     - `BH-UP-001` (Kabir Verma, S3, UPSC Preparation)
     - `NEW_STUDENT` (First-time visitor / Onboarding)
   - All 32 screenshots are saved under `docs/screenshots/final/`.
2. **Reality Check Document:**
   - Created `docs/REALITY_CHECK.md` auditing every screen against defects P1 through P14.

### Honest Reality Check: What Works vs What Is Broken

#### What Actually Works (Evidenced by Screenshots)
- **Authentic Exercise Bank (Fixes P6, P7, P9):**
  - All 112 placeholder items (*"Which topic is explicitly named in the learning unit above?"*) are completely gone.
  - The database serves 240 team-authored, syllabus-grounded items across 24 skills (e.g. C recursion tracing, Handshaking Lemma combinatorics, C syntax rules).
  - Screenshots: [`BH-SW-001_03_diagnostic.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-SW-001_03_diagnostic.png), [`BH-HS-001_03_diagnostic.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-HS-001_03_diagnostic.png), [`BH-SW-001_05_practice.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-SW-001_05_practice.png).
- **Environment & Build Transparency (Fixes P14):**
  - The demo bar visibly displays `Build fb38d67 · SQLITE · Synced (240 ex)` indicating that the runtime is synced with the seed.
  - Screenshots: [`BH-SW-001_01_home.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-SW-001_01_home.png).
- **Multi-Persona Profiles & Course Catalogue:**
  - 3 hero profiles and 75 synthetic profiles load cleanly from `data/seed_bhilai/`.
  - Bhilai CSE course catalogue (34 courses, 112 modules) correctly loads with verified course codes.

#### What Is Broken (Defects Confirmed from Live App)
- **Empty Plan Semesters (P1):**
  - For Diya Iyer (BH-HS-001), Semester 5 has only 3 credits (CSL515), Semester 6 is empty (0 cr), Semester 7 has only 3 credits (CSQ401), Semester 8 is empty (0 cr). Total planned: 6 credits across 4 semesters.
  - Screenshot: [`BH-HS-001_04_plan.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-HS-001_04_plan.png).
- **Misleading Rules Badge (P2):**
  - Badge says `"14 of 20 rules satisfied • verified"` in green. 14/20 is not satisfied, and 16 of the 20 checks rely on unverified assumptions pending the ordinance.
  - Screenshot: [`BH-HS-001_04_plan.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-HS-001_04_plan.png).
- **Goal Chip Mismatch (P3):**
  - For Diya Iyer, the top bar goal chip says `"Goal: Degree Completion"` while her selected goal is Higher Studies.
  - Screenshot: [`BH-HS-001_01_home.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-HS-001_01_home.png).
- **Leaked Placeholders (P4, P11):**
  - The shared summary line prints `"Not available studied · Not available adherence · Readiness Not available"` on Today, Plan, and Buddy.
  - Screenshot: [`BH-HS-001_04_plan.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-HS-001_04_plan.png).
- **Unexplained Skill Tags (P5):**
  - Course cards display skill tags without explaining why the course is there or which student gap it addresses.
- **Mastery Delta Invisible (P8):**
  - Submitting practice exercises provides score feedback but does not display before/after skill probability change (e.g. `40% → 52%`).
- **Diagnostic Too Short (P10):**
  - The diagnostic finishes after 3 items rather than an adaptive 8–12 question loop.
- **Buddy Context Dump (P12):**
  - Buddy opens with a robotic memory dump (`"I remember your learning context: You are Aarav Sharma..."`) instead of a brief, helpful greeting with 3 action buttons.
  - Screenshot: [`BH-SW-001_07_buddy.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/BH-SW-001_07_buddy.png).
- **Lack of Purpose & Onboarding (P13):**
  - No welcome pitch or 5-step roadmap on Home. First-time visitors land directly on a dense dashboard.
  - Screenshot: [`NEW_STUDENT_01_home.png`](file:///c:/Users/yp871/OneDrive/Desktop/MP5/docs/screenshots/final/NEW_STUDENT_01_home.png).

---

## 4. Next Phase Action Plan

1. **Phase 2:** Ensure runtime exercise data is 100% clean (run `scripts/qa/exercise_quality.py`, eliminate `title: null`, verify 240 items).
2. **Phase 3:** Fix Curriculum Planner (populate real required courses and explicit elective slots across all remaining semesters, resolve 144 vs 156 credit discrepancy, fix rules summary semantics, fix goal chip, eliminate `"Not available"` strings).
3. **Phase 4:** Redesign Home and Navigation (pitch, 5-step journey, rename tabs: Today, Your plan, Practise, Progress, Buddy; add UI text guard).
4. **Phase 5:** Complete Learning Loop (8–12 adaptive diagnostic questions, visible practice delta, 3-state progress).
5. **Phase 6:** Buddy Polish (clean greeting, 3 action pills, grounded citations, zero raw context dumps).
6. **Phase 7:** Clean Boundaries (hide unproven code sandbox behind feature flag, catalog limitations in `docs/KNOWN_LIMITATIONS.md`).
7. **Phase 8:** Demo check (`make demo-check`, `make demo-reset`, `docs/DEMO_WALKTHROUGH.md`, final screenshots).
