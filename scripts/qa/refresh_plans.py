import json
from backend.db.database import get_db_cursor
from backend.db.seed_loader import load_seed_data
from backend.api.plans import generate_student_plan, PlanGenerateRequest
from backend.student.model import StudentStore

print("Reloading seed data and regenerating student plans...")
load_seed_data(reset=True)

# Regenerate plans for hero personas
personas = ["BH-SW-001", "BH-HS-001", "BH-UP-001"]
for pid in personas:
    res = generate_student_plan(PlanGenerateRequest(
        student_id=pid,
        reason_for_change="Curriculum alignment update"
    ))
    plan = res["plan"]
    print(f"\n[{pid}] Plan Version {res['version_number']}: Total credits = {plan['total_credits_planned']}")
    for s in plan["semesters"]:
        c_codes = [c["code"] for c in s.get("courses", [])]
        print(f"  Sem {s['semester_number']} ({s['total_credits']} cr): {c_codes}")

print("\nAll plans refreshed and stored in database!")
