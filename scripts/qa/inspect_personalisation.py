import json
import urllib.request

personas = ['BH-SW-001', 'BH-HS-001', 'BH-UP-001']
for pid in personas:
    url = f'http://127.0.0.1:8000/api/plans/{pid}'
    data = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
    plan = data['plan']
    print(f"==================================================")
    print(f"PERSONA: {pid} | Goal: {plan.get('goal_id')}")
    print(f"Total Credits Planned: {plan.get('total_credits_planned')}")
    first_sem = plan['semesters'][0]
    first_course = first_sem['courses'][0]
    print(f"Next Action: {first_course['code']} — {first_course['title']}")
    print(f"Next Action Reason: {first_course.get('reason')}")
    
    print("\nPlanned Semesters & Courses:")
    for s in plan['semesters']:
        sem_num = s['semester_number']
        courses = [f"{c['code']} ({c['title']}, {c['credits']} cr, {c['course_type']})" for c in s['courses']]
        print(f"  Sem {sem_num} ({s['total_credits']} cr):")
        for c in courses:
            print(f"    - {c}")
        milestones = [m['title'] for m in s.get('milestones', [])]
        if milestones:
            print(f"    * Milestones: {', '.join(milestones)}")
        resources = [r['title'] for r in s.get('resources', [])]
        if resources:
            print(f"    * Resources: {', '.join(resources)}")
    print()
