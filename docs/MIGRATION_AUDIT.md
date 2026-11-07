# IIT Bhilai Curriculum Migration Audit

## Executive Summary
This document records the completed institutional curriculum migration to **Indian Institute of Technology Bhilai (IIT Bhilai)** for the B.Tech Computer Science and Engineering programme (`iit_bhilai_btech_cse_2023`).

The architecture adopts a strict **Three-Tier Provenance Model**:
1. **Tier 1 - Verified Institutional Facts**:
   - Source: Official IIT Bhilai `Courses of Study 2023-24` (`data/raw/`).
   - 34 accredited courses (CSE core, electives, EE/ME foundations, Liberal Arts, Mathematics).
   - Verbatim course titles, codes, L-T-P-C credit structures, and official syllabi with catalog page citations.
2. **Tier 2 - Labelled Assumptions**:
   - 7 transparently labelled rules for facts not explicitly defined in the course catalog (semester credit bounds, overload criteria, workload estimates, online credit cap).
   - Displayed with visible "Assumed" badges and documented in `data/raw/ordinance_TODO.md` pending ordinance publication.
3. **Tier 3 - Team-Authored Learning Layer**:
   - 24 derived technical and general skills.
   - 112 curriculum modules structured directly from syllabus topics.
   - 240 original assessment exercises (10 per skill across difficulties 1 to 4) with authentic conceptual distractors.
   - 4 calibrated career goal templates (Software Engineer, Higher Studies / Research, UPSC Civil Services, Startup Founder).

## Clean-Up & Legacy Segregation
- All legacy reference bundles, seed data, and builder scripts have been permanently preserved on the `legacy-delhi` git branch and completely excised from `main`.
- All documentation, reports, and code enforce an automated QA gate failing on any legacy institutional references.
