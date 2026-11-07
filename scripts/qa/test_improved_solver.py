import json
from pathlib import Path
from collections import defaultdict

SEED_DIR = Path("data/seed_bhilai")

courses = {c["code"]: c for c in json.load(open(SEED_DIR / "courses.json", encoding="utf-8"))}
prereqs = json.load(open(SEED_DIR / "prerequisites.json", encoding="utf-8"))
prereq_map = defaultdict(list)
for p in prereqs:
    prereq_map[p["course_code"]].append(p["requires_code"])

curricula = json.load(open(SEED_DIR / "iit_bhilai_cse_curricula.json", encoding="utf-8"))
btech = next(p for p in curricula["programmes"] if p["id"] == "iit_bhilai_btech_cse_2023")
sem_templates = {s["semester"]: s for s in btech["semesters"]}

goal_templates = {g["goal_id"]: g for g in json.load(open(SEED_DIR / "goal_templates.json", encoding="utf-8"))}

# Goal elective preferences
GOAL_ELECTIVE_PREFS = {
    "goal_higher_studies": ["CSL515", "CSL510", "CSL518", "CSL511", "CSL504", "CSL512", "CSL559", "CSL505"],
    "goal_research": ["CSL515", "CSL510", "CSL518", "CSL511", "CSL504", "CSL512", "CSL559", "CSL505"],
    "goal_software": ["CSL559", "CSL518", "CSL512", "CSL505", "CSL504", "CSL515", "CSL510", "CSL511"],
    "goal_upsc": ["CSL505", "CSL504", "CSL510", "CSL518", "CSL515", "CSL511", "CSL512", "CSL559"],
    "goal_startup": ["CSL559", "CSL518", "CSL505", "CSL504", "CSL512", "CSL515", "CSL510", "CSL511"]
}

GOAL_LA_PREFS = {
    "goal_higher_studies": [
        ("LAL225", "Liberal Arts requirement: recommended for research ethics, data privacy, and academic integrity."),
        ("LAL224", "Liberal Arts requirement: fosters cognitive resilience and graduate research productivity."),
        ("LAL202", "Liberal Arts requirement: quantitative econometric modeling supporting empirical research."),
        ("LAL223", "Liberal Arts requirement: social development frameworks for technology impact analysis.")
    ],
    "goal_software": [
        ("LAL201", "Liberal Arts requirement: microeconomic principles of market dynamics, tech pricing, and cost structures."),
        ("LAL225", "Liberal Arts requirement: engineering ethics, algorithmic accountability, and public policy."),
        ("LAL200", "Liberal Arts requirement: macroeconomic perspectives on technological shifts and industrial growth."),
        ("LAL224", "Liberal Arts requirement: workplace psychology and engineering team collaboration.")
    ],
    "goal_upsc": [
        ("LAL222", "Liberal Arts requirement: directly maps to UPSC General Studies Paper I (Modern Indian History)."),
        ("LAL225", "Liberal Arts requirement: directly maps to UPSC General Studies Paper IV (Ethics, Integrity & Aptitude)."),
        ("LAL200", "Liberal Arts requirement: directly maps to UPSC General Studies Paper III (Indian Economy)."),
        ("LAL221", "Liberal Arts requirement: covers World History for UPSC Civil Services Mains General Studies.")
    ],
    "goal_startup": [
        ("LAL200", "Liberal Arts requirement: macroeconomic analysis for venture market assessment and macro trends."),
        ("LAL201", "Liberal Arts requirement: microeconomics of consumer pricing, elasticity, and platform scaling."),
        ("LAL225", "Liberal Arts requirement: tech governance, regulatory compliance, and venture ethics."),
        ("LAL224", "Liberal Arts requirement: founder mental resilience and organizational culture building.")
    ]
}

def plan_student(student_id, current_sem, cgpa, completed_courses, goal_id):
    completed_set = set(c.upper() for c in completed_courses)
    scheduled_so_far = set(completed_set)
    already_scheduled = set()
    
    start_sem = current_sem + 1
    semesters_to_plan = list(range(start_sem, 9))
    if not semesters_to_plan:
        semesters_to_plan = [current_sem]
        
    sem_plans = []
    elec_order = GOAL_ELECTIVE_PREFS.get(goal_id, GOAL_ELECTIVE_PREFS["goal_software"])
    la_order = GOAL_LA_PREFS.get(goal_id, GOAL_LA_PREFS["goal_software"])
    la_idx = 0
    
    # Calculate initial completed credits
    completed_credits = sum(courses.get(c, {}).get("credits", 4.0) for c in completed_set)
    running_credits = completed_credits

    for sem in semesters_to_plan:
        sem_courses = []
        sem_credits = 0.0
        template = sem_templates.get(sem, {})
        typical_cr = template.get("stated_credits", 18.0)
        
        # 1. Mandatory core courses from official curriculum
        for c_entry in template.get("courses", []):
            code = c_entry.get("code")
            if not code or c_entry.get("placeholder"):
                continue
            if code in scheduled_so_far or code in already_scheduled:
                continue
            if code in courses:
                # Check prereqs
                reqs = prereq_map.get(code, [])
                if all(r in scheduled_so_far for r in reqs):
                    meta = courses[code]
                    sem_courses.append({
                        "code": code,
                        "title": meta["title"],
                        "credits": meta["credits"],
                        "course_type": "programme_core",
                        "workload_hours_per_week": meta["credits"] * 2.0,
                        "skills_targeted": meta.get("skills_covered", []),
                        "reason": f"Required in Semester {sem} (Programme Core) per Courses of Study p.21-22.",
                        "provenance": "verified",
                        "source_page": meta.get("source_page", 21)
                    })
                    sem_credits += meta["credits"]
                    already_scheduled.add(code)
                    scheduled_so_far.add(code)

        # 2. Add goal-aligned Liberal Arts course if curriculum slot exists
        has_la_slot = any(c.get("category") == "LA" and c.get("placeholder") for c in template.get("courses", []))
        if has_la_slot:
            # Pick next available LA course
            while la_idx < len(la_order):
                la_code, la_reason = la_order[la_idx]
                la_idx += 1
                if la_code not in scheduled_so_far and la_code not in already_scheduled and la_code in courses:
                    meta = courses[la_code]
                    sem_courses.append({
                        "code": la_code,
                        "title": meta["title"],
                        "credits": meta["credits"],
                        "course_type": "liberal_arts",
                        "workload_hours_per_week": meta["credits"] * 2.0,
                        "skills_targeted": meta.get("skills_covered", []),
                        "reason": la_reason,
                        "provenance": "verified",
                        "source_page": meta.get("source_page", 21)
                    })
                    sem_credits += meta["credits"]
                    already_scheduled.add(la_code)
                    scheduled_so_far.add(la_code)
                    break

        # 3. Add goal-aligned Programme Electives to reach typical credit load
        has_pe_or_oe = any(c.get("category") in ("PE", "OE") and c.get("placeholder") for c in template.get("courses", []))
        if has_pe_or_oe or sem_credits < 14.0:
            target_cr = typical_cr
            for e_code in elec_order:
                if sem_credits >= target_cr or sem_credits >= 22.0:
                    break
                if e_code in scheduled_so_far or e_code in already_scheduled or e_code not in courses:
                    continue
                # Check prereqs
                reqs = prereq_map.get(e_code, [])
                if all(r in scheduled_so_far for r in reqs):
                    meta = courses[e_code]
                    if sem_credits + meta["credits"] <= 24.0:
                        sem_courses.append({
                            "code": e_code,
                            "title": meta["title"],
                            "credits": meta["credits"],
                            "course_type": "programme_elective",
                            "workload_hours_per_week": meta["credits"] * 2.0,
                            "skills_targeted": meta.get("skills_covered", []),
                            "reason": f"Programme elective ({meta['credits']} cr): recommended for your goal to strengthen specialized CS capabilities.",
                            "provenance": "verified",
                            "source_page": meta.get("source_page", 88)
                        })
                        sem_credits += meta["credits"]
                        already_scheduled.add(e_code)
                        scheduled_so_far.add(e_code)

        running_credits += sem_credits
        sem_plans.append({
            "semester_number": sem,
            "season": "Odd (Autumn)" if sem % 2 == 1 else "Even (Spring)",
            "total_credits": round(sem_credits, 1),
            "typical_credits": typical_cr,
            "credit_summary": f"planned {sem_credits:.1f} cr of {typical_cr:.1f} typical",
            "running_total_credits": round(running_credits, 1),
            "workload_hours": round(sem_credits * 2.0, 1),
            "courses": sem_courses
        })

    return sem_plans

# Test with Diya Iyer (BH-HS-001)
diya_completed = ["CSL100", "MAL100", "CYL100", "PHL101", "CYL101", "CYP102", "MAL101", "ECL101", "EEL101", "BML101", "MEP102", "PHP102", "MAL403", "CSL201", "CSL202", "CSP203", "LAL100", "LAL200", "CSL251", "CSL252", "CSL253", "LAL101", "LAL201"]
plans = plan_student("BH-HS-001", 4, 8.7, diya_completed, "goal_higher_studies")
print("=== DIYA IYER PLAN ===")
for s in plans:
    print(f"Semester {s['semester_number']} ({s['credit_summary']}), Running: {s['running_total_credits']} cr:")
    for c in s['courses']:
        print(f"  - [{c['code']}] {c['title']} ({c['credits']} cr, {c['course_type']})")
