# Ideas Note: Operationalising the IIT Bhilai Knowledge Base
**Part E — 1-Page Architectural Report**  
**Author**: Yug Patel (`yppatel@iitbhilai.ac.in`), IIT Bhilai  
**Target Domain**: Personalised Academic Advising for B.Tech CSE (IIT Bhilai)  

---

## 1. My Approach: Why Naive RAG Fails & The Dual-Layer Architecture

When building an academic advising assistant, the most tempting approach is to throw course PDFs into a vector database and let an LLM generate recommendations. In practice, this fails completely:
- Vector similarity does not understand topological ordering: an LLM might recommend *Distributed Systems* and *Operating Systems* in the same semester because their syllabus descriptions are semantically similar, ignoring that OS is a strict prerequisite.
- LLMs cannot reliably do cumulative multi-semester credit math across dynamic limits (12.0 min, 24.0 standard, 27.0 overload).

To solve this, I designed a **dual-layer architecture**:

1. **Layer 1: Deterministic Graph & Constraint Engine (Code Decides)**
   - Treats `prerequisites.json` as a Directed Acyclic Graph (DAG) for valid topological scheduling.
   - Enforces semester credit caps, offering parity (odd vs. even semesters), and minor eligibility directly through `academic_rules.json`.
   - Computes skill gap vectors and probabilistic mastery using Bayesian Knowledge Tracing (BKT) on `course_skills.json`.
2. **Layer 2: Grounded Explanatory Interface (LLM Explains)**
   - Uses `chunks.jsonl` to look up exact syllabus clauses and learning resource metadata.
   - The LLM only translates the pre-validated schedule into natural, empathetic student explanations with exact page citations. The model never computes eligibility or credit math on its own.

---

## 2. Three Questions My Buddy Can Answer Well

### Question 1: Prerequisite Checking and Semester Feasibility
> *"Can I take Operating Systems (CSL301) in Semester 4, and what prerequisites do I need first?"*
- **Why my data supports it**: `prerequisites.json` records that `CSL201` (Computer Organization) and `CSL202` (Data Structures) are hard prerequisites. `courses.json` records that `CSL301` is standardly offered in Semester 5 (an odd semester).
- **How the system handles it**: The solver checks whether the student has completed `CSL201` and `CSL202`, flags that Semester 4 is an even semester while `CSL301` is an odd-semester course, and recommends taking it in Semester 5 as per *Courses of Study, p. 83*.

### Question 2: Workload, Credit Overload, and Minor Eligibility Audits
> *"I have a 7.8 CGPA and want to take 22 credits next semester to start a minor in AI. Am I eligible?"*
- **Why my data supports it**: `academic_rules.json` contains quotable policies for credit caps (`rule_sem_max_credits`), overload limits (`rule_credit_overload_cap`), and minor eligibility (`rule_minor_cse_eligibility`).
- **How the system handles it**: The rule engine compares the student's 7.8 CGPA against the threshold, confirms overload eligibility up to 22 credits, and verifies that the chosen minor course fits within the student's available weekly hours without creating prerequisite clashes.

### Question 3: Targeted Skill Remediation with Open Resources
> *"I want to focus on Machine Learning, but I struggled on the Linear Algebra and Probability diagnostic. What should I study first?"*
- **Why my data supports it**: `skills.json`, `course_skills.json`, and `resources.json` link mathematical foundations to courses like `MAL201`/`MAL403` and curated open content (MIT OCW 18.06 Gilbert Strang, NPTEL).
- **How the system handles it**: The system flags the prerequisite gap and generates a structured 3-week study plan with direct resource links, open license terms (CC BY-NC-SA 4.0), and estimated hours before the student registers for advanced electives.

---

## 3. Three Questions My Buddy CANNOT Answer (and How I Guardrail Them)

### Question 1: Professor Identities and Grading Leniency
> *"Who is teaching CSL202 next semester, and does that professor have a strict attendance rule?"*
- **Why the data cannot answer it**: The *Courses of Study* document defines static curriculum content, syllabi, and credit values—not dynamic semester faculty allocations or subjective grading habits.
- **My Guardrail**: The system intercepts faculty queries and replies honestly: *"Faculty allocations and specific attendance policies are decided each semester by the department and are not part of the static course curriculum."*

### Question 2: GPA Guarantees and Predictive Grading
> *"If I take Computer Networks and Distributed Systems together, can you guarantee I will get an A grade and cross an 8.5 CGPA?"*
- **Why the data cannot answer it**: Final grades depend on relative grading curves, batch difficulty, and student examination performance, which cannot be predicted from a syllabus.
- **My Guardrail**: The system computes total weekly workload (contact hours + self-study load) and warns about academic strain, but explicitly states: *"I can help you evaluate your weekly workload, but grade outcomes depend on course evaluations and cannot be guaranteed."*

### Question 3: Prerequisite Waivers and Senate Exceptions
> *"Can you waive the prerequisite for CSL302 so I can graduate a semester early?"*
- **Why the data cannot answer it**: Academic advisors cannot override institutional governance. Prerequisite waivers require a formal petition to the Senate and the Dean of Academic Affairs.
- **My Guardrail**: The system blocks invalid course additions and directs the student to the official administrative route: *"Automated systems cannot waive senate-mandated prerequisites. You will need to speak with your Faculty Advisor and submit an official request to the Academic Office."*
