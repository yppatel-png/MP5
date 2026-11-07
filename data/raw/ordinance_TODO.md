# IIT Bhilai Academic Ordinances & Regulations Upgrade Roadmap

This document specifies the exact official documents, sections, clauses, and upgrade procedures required to transition each **Tier 2 (Labelled Assumption)** rule in `data/seed_bhilai/academic_rules.json` to **Tier 1 (Verified Institutional Fact)**.

Under our three-tier provenance architecture:
- **Tier 1 (Verified)**: Directly grounded in official documents located in `data/raw/` with verified source pages and ordinance clause references.
- **Tier 2 (Assumption)**: Transparent planning parameters used for demo parity when official institutional texts are silent. These must never be hidden or masqueraded as official facts; they carry explicit `provenance="assumption"` flags and are surfaced in plan certificates and UI badges.
- **Tier 3 (Derived / Learning Layer)**: Team-authored skill mappings, modules, exercises, and diagnostic items grounded in syllabus descriptions.

---

## Current Status Overview

| Rule ID | Rule Title | Current Provenance | Assumed Parameter | Required Institutional Document |
| :--- | :--- | :---: | :--- | :--- |
| `rule_sem_min_credits` | Minimum Recommended Semester Credits | **Assumption** | 12.0 credits | B.Tech Ordinances & Regulations (Section on Course Registration) |
| `rule_sem_max_credits` | Standard Semester Credit Cap | **Assumption** | 24.0 credits | B.Tech Ordinances & Regulations (Section on Registration Limits) |
| `rule_credit_overload_cap` | Overload Credit Cap | **Assumption** | 27.0 credits (CGPA &ge; 8.0) | Academic Senate Overload / Honors Policy |
| `rule_minor_cse_eligibility` | CS Minor Eligibility | **Assumption** | CGPA &ge; 7.0 | Senate Guidelines for Minor Degree Programs |
| `rule_online_credit_transfer_limit` | Online Credit Transfer Cap | **Assumption** | 25 credits total | MOOCs / NPTEL / SWAYAM Credit Transfer Framework |
| `rule_semester_parity` | Annual Catalogue Offering Parity | **Assumption** | Autumn / Spring Slotting | Department Course Offering & Slot Timetable Matrix |
| `rule_workload_hours` | Independent Study Workload Estimate | **Assumption** | 2.0 hrs/credit/week | Curriculum Structure & Student Workload Framework |

---

## Detailed Upgrade Specifications

### 1. `rule_sem_min_credits`
- **Rule ID**: `rule_sem_min_credits`
- **Current Parameters**: `{"min_credits": 12.0}`
- **Current Reason**: Demo planning floor; no semester minimum was found in the supplied PDF.
- **Target Official Document**: `data/raw/ordinances_and_regulations_btech.pdf` (IIT Bhilai B.Tech Ordinances & Regulations).
- **Target Clause / Section**: Section on Course Registration and Academic Load &mdash; Subsection "Minimum Registered Credits per Regular Semester".
- **Upgrade Steps**:
  1. Add the official B.Tech Ordinances PDF to `data/raw/`.
  2. Locate the clause specifying the minimum permissible registration load for full-time undergraduate students (typically 12 or 14 credits).
  3. In `data/seed_bhilai/academic_rules.json`, set:
     ```json
     {
       "rule_id": "rule_sem_min_credits",
       "parameters": { "min_credits": <verified_val> },
       "provenance": "verified",
       "clause_id": "ORD-BTECH-4.2",
       "source_page": <page_num>,
       "reason": null
     }
     ```
  4. Run `python scripts/verify.py` to reload database seeds.

---

### 2. `rule_sem_max_credits`
- **Rule ID**: `rule_sem_max_credits`
- **Current Parameters**: `{"max_credits": 24.0}`
- **Current Reason**: Demo planning cap; no semester maximum was found in the supplied PDF.
- **Target Official Document**: `data/raw/ordinances_and_regulations_btech.pdf`.
- **Target Clause / Section**: Section on Course Registration &mdash; Subsection "Maximum Regular Semester Credit Limit".
- **Upgrade Steps**:
  1. Verify the regular semester ceiling (typically 22 or 24 credits per semester).
  2. In `data/seed_bhilai/academic_rules.json`, update `parameters["max_credits"]`, set `provenance: "verified"`, and record the official clause and page citation.

---

### 3. `rule_credit_overload_cap`
- **Rule ID**: `rule_credit_overload_cap`
- **Current Parameters**: `{"max_overload_credits": 27.0, "min_cgpa_required": 8.0}`
- **Current Reason**: Demo overload threshold approved by project owner; pending institutional ordinance.
- **Target Official Document**: `data/raw/academic_senate_policy_overload.pdf` or Section 4.5 of B.Tech Ordinances.
- **Target Clause / Section**: Academic Senate Policy on Course Overload, Accelerated Graduation, or Honors Track.
- **Upgrade Steps**:
  1. Extract the Senate-approved minimum CGPA requirement (e.g., 8.0 or 8.5) and permitted overload credits (e.g., up to 26 or 28 credits).
  2. Update `data/seed_bhilai/academic_rules.json`: set `provenance: "verified"` with the senate resolution number.

---

### 4. `rule_minor_cse_eligibility`
- **Rule ID**: `rule_minor_cse_eligibility`
- **Current Parameters**: `{"min_cgpa_cutoff": 7.0}`
- **Current Reason**: Illustrative threshold only. The supplied PDF contains no CS minor pathway or eligibility policy.
- **Target Official Document**: `data/raw/minor_degree_regulations.pdf`.
- **Target Clause / Section**: Guidelines for Minor Degree Programs in Computer Science and Engineering for Non-CSE Students.
- **Upgrade Steps**:
  1. Confirm whether IIT Bhilai Senate offers a formal Minor in Computer Science and Engineering.
  2. Extract the minimum CGPA criterion (e.g., 7.5 CGPA at the end of 4th semester) and the 20-credit core/elective basket.
  3. If approved, add the minor basket to `data/seed_bhilai/programmes.json` and set `rule_minor_cse_eligibility` to `provenance: "verified"`.

---

### 5. `rule_online_credit_transfer_limit`
- **Rule ID**: `rule_online_credit_transfer_limit`
- **Current Parameters**: `{"max_online_credits_total": 25, "max_online_courses_per_semester": 1}`
- **Current Reason**: Demo planning limit approved by project owner; no online-credit policy was found in the supplied PDF.
- **Target Official Document**: `data/raw/moocs_credit_transfer_policy.pdf` (Senate Guidelines on NPTEL/SWAYAM MOOCs Credit Mobility).
- **Target Clause / Section**: Senate Resolution on Credit Transfer from Massive Open Online Courses (adhering to AICTE/UGC credit mobility regulations).
- **Upgrade Steps**:
  1. Verify the maximum percentage of curriculum credits permissible via online platforms (typically 20% of graduation credits, approx 24-25 credits).
  2. Update the rule entry in `data/seed_bhilai/academic_rules.json` to `provenance: "verified"`.

---

### 6. `rule_semester_parity`
- **Rule ID**: `rule_semester_parity`
- **Current Parameters**: `{"assume_annual_scheduled_offering": true, "catalogue_electives_selectable": true}`
- **Current Reason**: Scheduled courses are assumed to run in the semester printed in the curriculum; catalogue-only electives are assumed selectable for demo planning.
- **Target Official Document**: `data/raw/course_offering_schedule_and_timetable.pdf` (CSE Department Course Offering & Slot Timetable Matrix).
- **Target Clause / Section**: CSE Department Course Slot Schedule for Autumn (Odd) and Spring (Even) Semesters.
- **Upgrade Steps**:
  1. For each of the 34 catalogued courses in `data/seed_bhilai/courses.json`, verify its confirmed offering slot (`semester_1` through `semester_8`, or `autumn`/`spring`).
  2. Update `data/seed_bhilai/courses.json` with verified `semester_offered` fields.
  3. Set `rule_semester_parity` to `provenance: "verified"`.

---

### 7. `rule_workload_hours`
- **Rule ID**: `rule_workload_hours`
- **Current Parameters**: `{"hours_per_credit_week": 2}`
- **Current Reason**: Planning estimate approved by project owner; not an IIT Bhilai workload standard.
- **Target Official Document**: `data/raw/curriculum_design_framework.pdf`.
- **Target Clause / Section**: Curriculum Design Norms & Credit Structure (L-T-P-C Definitions and Expected Student Engagement Hours).
- **Upgrade Steps**:
  1. Confirm institutional effort multiplier (typically 1 lecture credit = 1 contact hour + 1.5 to 2.0 independent study hours per week).
  2. Update `parameters["hours_per_credit_week"]` and set `provenance: "verified"`.

---

## Dynamic Verification Impact

Once any rule is upgraded in `data/seed_bhilai/academic_rules.json`:
1. **Rule Evaluation Engine** (`backend/rules/bhilai_rules.py`): The check automatically switches from returning `provenance="assumption"` to `provenance="verified"`.
2. **Cryptographic Certificate** (`backend/rules/certificate.py`):
   - `summary.assumed_checks_count` dynamically decrements.
   - `summary.assumptions_statement` updates from `"16 of 20 rule checks use assumptions pending the ordinance"` down to `"0 of 20 rule checks use assumptions pending the ordinance"` once all rules are verified.
3. **Official PDF Certificate** (`backend/rules/pdf_builder.py`):
   - Table rows update tier badges from amber `[ASSUMED]` to green `[VERIFIED]`.
   - The summary card's amber transparency warning is automatically removed when all rules are verified.
4. **Interactive UI Drawer**:
   - The transparency notice box dynamically updates and hides when 0 checks remain assumed.
   - Rule badges in the drawer turn green `[Verified]`.

