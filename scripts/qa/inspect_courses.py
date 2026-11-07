import json

courses = json.load(open("data/seed_bhilai/courses.json", encoding="utf-8"))
prereqs = json.load(open("data/seed_bhilai/prerequisites.json", encoding="utf-8"))
prereq_map = {}
for p in prereqs:
    prereq_map.setdefault(p["course_code"], []).append(p["requires_code"])

print(f"Total courses: {len(courses)}")
for c in courses:
    code = c["code"]
    reqs = prereq_map.get(code, [])
    print(f"{code:7s} | {c['credits']} cr | slot: {c.get('semester_offered', 'None'):21s} | type: {c.get('course_type', 'None'):10s} | prereqs: {reqs}")
