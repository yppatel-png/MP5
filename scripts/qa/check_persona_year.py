import json
import math

profiles = json.load(open("data/seed_bhilai/student_profiles.json", encoding="utf-8"))
reconcile_issues = []

for p in profiles:
    pid = p["student_id"]
    sem = p["current_semester"]
    yr = p["year"]
    cgpa = p["cgpa"]
    expected_yr = math.ceil(sem / 2.0)
    if yr != expected_yr:
        reconcile_issues.append({
            "student_id": pid,
            "name": p["name"],
            "current_semester": sem,
            "recorded_year": yr,
            "expected_year": expected_yr,
            "cgpa": cgpa
        })

print(f"Total profiles: {len(profiles)}")
print(f"Profiles with Year != ceil(sem/2): {len(reconcile_issues)}")
for issue in reconcile_issues[:10]:
    print(issue)
