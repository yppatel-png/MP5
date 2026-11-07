# UI & Front-End Comprehensive Audit (docs/UI_AUDIT_V2.md)

**Role**: Senior Product Designer & Front-End Reliability Engineer  
**Standard**: Quiet Academic Instrument (Linear / Stripe / Notion caliber)  
**Scope**: Complete visual, typography, copy, logic, accessibility, and architectural audit of `frontend/`.

---

## 1. Executive Summary & Defect Log

The current interface has functional parity with the underlying solvers, but suffers from severe design system fragmentation, AI-generated aesthetic tells (neon accents, glowing blobs, ubiquitous pills, heavy box borders), exposed backend implementation details, and critical persona cross-contamination bugs where Computer Science tasks leak into Humanities/UPSC student views.

Every defect below has been categorized by severity:
* **P0**: Critical data/logic bug or requirement violation (misleading advice to students, cross-persona leakage).
* **P1**: High visual or UX breakage (clipping under sticky bars, lack of system typography, WCAG AA contrast failure, exposed internals).
* **P2**: Medium rough edge (inconsistent spacing, unlabelled time horizons, generic empty states).
* **P3**: Minor cosmetic polish (straight quotes, casing irregularity).

---

## 2. Explicit Audit of the 19 Screenshot & Architectural Defects (Section 1)

### Visual Issues
| # | Issue | File & Line References | Severity | Root Cause & Violation Details | Proposed Architectural Remedy |
| :- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Overloaded & Wrapping Top Bar** | `frontend/index.html`: lines 122–152<br>`frontend/static/css/style.css`: lines 62–95 | **P1** | Top bar packs brand logo, two-line subtitle, 7-tab navigation, persona dropdown, and status pill into one flex row. On screens <1300px, it wraps to two rows, pushing down and vertically clipping page content (such as `.persona-hero-card`). | Replace with persistent 240px left sidebar (collapsing to 64px on tablet/mobile) and a clean 56px top bar with breadcrumb, goal chip, theme toggle, and avatar. |
| **2** | **Competing Saturated Colors** | `frontend/index.html`: lines 150, 157, 185, 205, 232, 260, 265, 277<br>`frontend/static/css/style.css`: lines 8–35 | **P1** | Over 7 competing saturated colors used without semantic meaning: red-orange buttons, blue "BKT MONITORED", green "ON SCHEDULE", orange "Ineligible", red "Prerequisite Path", green checkmarks. Red is overloaded for both brand action and danger. | Establish a strict single-accent system (`--accent: #C8341E`). Reserve semantic colors strictly for verified status (`--success`, `--warn`, `--danger`). All metadata uses neutral ink. |
| **3** | **Pill Buttons & Badges Everywhere** | `frontend/index.html`: lines 133–140, 150, 173–176, 749<br>`frontend/static/css/style.css`: lines 78, 120–135 | **P2** | Fully-rounded pills (`border-radius: 999px`) used indiscriminately for tabs, status tags, metadata chips, and floating buttons. | Restrain radius scale: 6px for controls, tags, and chips; 10px for panels; circles (`border-radius: 50%`) reserved exclusively for user avatars. |
| **4** | **Heavy Boxy Cards with Tinted Borders** | `frontend/index.html`: lines 169, 202, 229, 257, 283, 304<br>`frontend/static/css/style.css`: lines 140–165 | **P2** | Every container is a heavy card with tinted 1px–2px borders and dark fills, creating visual clutter and a template appearance. | Shift to quiet academic surfaces: 1px hairline borders (`--border: #E6E2DA`), ample whitespace, and table-like rows with subtle dividers. |
| **5** | **Gradients, Glows & Glassmorphism** | `frontend/index.html`: line 67<br>`frontend/static/css/style.css`: lines 170–185 | **P2** | Glow shadows (`box-shadow: 0 0 12px rgba(239, 68, 68, 0.5)`), red-brown hero gradient, and glowing status blob. | Eliminate all gradients and glowing box-shadows. Flat surfaces with crisp 1px borders and at most subtle elevation for popovers. |
| **6** | **Floating "Chat with Buddy" Button** | `frontend/index.html`: lines 748–751<br>`frontend/static/css/style.css`: lines 710–730 | **P1** | Fixed FAB pill overlaps underlying content, obscures footer text, and duplicates both the "Open Chat" button (line 286) and "Learning Buddy Dialogue" card. | Eliminate FAB. Provide a clean right-hand Buddy drawer (360px push layout on desktop, sheet on mobile) toggled directly from the top bar. |
| **7** | **Broken 0% Readiness Ring** | `frontend/index.html`: lines 208–217<br>`frontend/static/js/app.js`: lines 158–168 | **P1** | Unassessed students or fresh sessions render an empty SVG circle with "0% Readiness", alarming students and wasting screen space. | Replace with an editorial low-evidence state: em-dash `—` with quiet caption "Not enough evidence yet" and an actionable link "Take the 8-minute diagnostic". |
| **8** | **Lack of Typographic System** | `frontend/index.html`: lines 122–300<br>`frontend/static/css/style.css`: lines 45–47 | **P1** | Entire UI uses generic system-ui sans-serif at default weights with no size hierarchy. Headings, metrics, and metadata compete for attention. | Implement Source Serif 4 (600) for display headings and key metrics; Geist/Inter Tight with tabular figures (`font-feature-settings: "tnum", "cv11"`) for body; JetBrains Mono for course codes and rules. |
| **9** | **Heavy Bold on Every Label** | `frontend/index.html`: lines 111, 219, 265, 273, 277, 289<br>`frontend/static/css/style.css`: font-weight 700/800 on all spans | **P2** | Excessive font weights (`font-weight: 800` throughout HTML inline styles) desensitize the eye so nothing stands out. | Standardize on deliberate weights: 400 (regular prose), 500 (medium UI labels), 600 (semi-bold titles). Eliminate 700/800 from inline styles. |
| **10** | **Low Contrast Grey Text** | `frontend/static/css/style.css`: lines 21–23, 220–245 | **P1** | `--text-dim: #64748b` on dark background `#090d16` produces a contrast ratio of 3.1:1, failing WCAG AA (4.5:1 required). | Re-tune `--ink-3` to `#7A766C` (light) and `#8F8A7F` (dark) ensuring minimum 4.6:1 contrast ratio across all backgrounds. |

---

### Information & Copywriting Issues
| # | Issue | File & Line References | Severity | Root Cause & Violation Details | Proposed Architectural Remedy |
| :- | :--- | :--- | :--- | :--- | :--- |
| **11** | **Implementation Details Leaked to Students** | `frontend/index.html`: lines 127, 145–148, 150, 205, 272 | **P1** | Internal engineering terms ("LiteLLM Online", "BKT Monitored", "No-Co-Taking Mutex", "Hero S1024", "IIT Bhilai Pilot", "Inter IIT Tech Meet 15.0") exposed to students. | Relocate system health, persona switching, and event metadata to a separate 32px Demo bar and Admin console. Use student-friendly language. |
| **12** | **Nav Labels Describe Technical Flows, Not Tasks** | `frontend/index.html`: lines 133–140 | **P2** | Nav tabs labeled "Adaptive Diagnostic" and "Onboarding Wizard" reflect engineering subsystems rather than student daily tasks. | Reorganize into purposeful destinations: `Today`, `Plan`, `Learn`, `Skills`, `Buddy`, with `Settings` and `Admin` in the footer. |
| **13** | **Unnatural "Learning Buddy Dialogue" Card** | `frontend/index.html`: lines 285–296 | **P2** | Section title reads like a technical spec; insight string uses straight quotes and sounds like a generic canned message. | Rename to "From your buddy" using editorial typographic quotes and evidence-grounded dynamic student insights. |
| **14** | **Status Words Contradict Data** | `frontend/index.html`: line 232<br>`frontend/static/js/app.js`: lines 158–174 | **P1** | Dashboard badge proudly states "ON SCHEDULE" even when the student has 0% readiness and an active unaddressed gap. | Derive status text strictly from data: `on_track`, `needs_attention`, `at_risk`, or `insufficient_evidence`. "On track" only when verified. |
| **15** | **Straight Quotes, Inconsistent Casing & Filler Words** | `frontend/index.html`: lines 231, 259, 289 | **P3** | Title-cased hyphenated strings ("This-Week Academic Checklist"), straight quotes (`""`), and marketing filler ("Unlock your potential"). | Enforce sentence case across all UI, curly typographic quotes (`“...”`), en-dashes for ranges, and concise factual phrasing. |

---

### Critical Logic & Consistency Issues (P0 Bugs)
| # | Issue | File & Line References | Severity | Root Cause & Violation Details | Proposed Architectural Remedy |
| :- | :--- | :--- | :--- | :--- | :--- |
| **16** | **Goal & Content Contradiction (P0)** | `frontend/index.html`: lines 234–250<br>`frontend/static/js/app.js`: lines 170–174 | **P0** | When student is targeting UPSC Civil Services, next action should display goal-aligned humanities and public policy prerequisites, not software tree traversals. | Root cause: legacy UI hardcoded CS checklist rows for all students. Must synthesize goal-aware next actions and checklists from the student's active goal template (`goal_upsc` vs `goal_software`). |
| **17** | **Unlabelled Time Horizons** | `frontend/index.html`: line 245, 289 | **P1** | Profile indicates student is in Year 2, Semester 3, but checklist refers to "18 credits planned in Sem 6" and buddy refers to "Semesters 6 through 8" without distinction. | Explicitly tag time horizons: separate "This semester (Sem 3)" tasks from "Future semesters (Planned: Sem 6)". |
| **18** | **Conflicting Credit Arithmetic** | `frontend/index.html`: lines 245, 269, 289 | **P1** | Screen presents "22 credit ceiling", "8 credits headroom", and "18 credits planned" without a unified breakdown. | Compute a single `StudentSummary` object (Cap, Planned, Headroom, Completed) and bind it identically across Dashboard, Plan, Certificate, and Buddy. |
| **19** | **Irrelevant Prerequisite DAG Path Displayed** | `frontend/index.html`: line 277 | **P1** | Hardcoded legacy DAG path displayed for UPSC and Research students who have no intention of taking Algorithms or OS. | Dynamically render the prerequisite chain strictly for the course or skill currently in focus. |

---

## 3. Plan of Action

1. **Step 2 (Foundations)**:
   - Authored unified design tokens (`tokens.css`) supporting crisp Light (default) and Dark modes.
   - Built complete component library (`components.css`) adhering to the 6px/10px radius scale and strict 4px spacing grid.
   - Rebuilt modern layout shell (`layout.css`) with 240px sidebar, 56px top bar, 32px demo bar, and 360px push buddy panel.
   - Upgraded `/styleguide` with complete interactive showcase across all components and states.
2. **Step 3 (Dashboard Rebuild)**:
   - Implement goal-aware dynamic dashboard engine resolving P0 bug #16.
   - Unify arithmetic via single source of truth (`StudentSummary`).
3. **Step 4 to 7**:
   - Rebuild Plan, Skills, Learn, and Buddy panels; verify via Playwright across 1440px and 390px in both themes.

