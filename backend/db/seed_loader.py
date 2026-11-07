"""
Seed Data Loader & Database Reset Utility.
Loads seed JSON datasets into SQLite / PostgreSQL database tables.
Provides idempotent state loading and full reset capability.
"""

import sys
import json
import logging
from pathlib import Path
from backend.db.database import get_db_cursor, init_db, get_db_path
from backend.db.seed_profile import get_seed_dir

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("learning_buddy.seed")

SEED_DIR = get_seed_dir()

def load_json(filename: str):
    path = SEED_DIR / filename
    if not path.exists():
        logger.error(f"Seed file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def reset_database():
    """Drops existing user and knowledge base data for a clean reset."""
    logger.info("Resetting database state...")
    try:
        with get_db_cursor() as cur:
            tables = [
                "chat_memory", "adaptation_events", "exercise_attempts",
                "plan_versions", "evidence_events", "study_sessions", "student_profiles",
                "exercises", "modules", "resources", "course_skills", "prerequisites",
                "skills", "courses", "programmes", "academic_rules", "goal_templates",
                "seed_provenance",
            ]
            # Drop view if exists
            try:
                cur.execute("DROP VIEW IF EXISTS students;")
            except Exception:
                pass
            for tbl in tables:
                cur.execute(f"DROP TABLE IF EXISTS {tbl};")
        logger.info("All existing tables dropped.")
    except Exception as e:
        logger.warning(f"Could not drop tables cleanly: {e}")
            
    # Re-initialize clean schema
    init_db()
    logger.info("Clean schema re-initialized.")

def load_seed_data(reset: bool = False):
    """Loads all seed datasets into database."""
    if reset:
        reset_database()
    else:
        init_db()

    counts = {}

    with get_db_cursor() as cur:
        # 1. Programmes
        programmes = load_json("programmes.json")
        for p in programmes:
            cur.execute("""
            INSERT OR REPLACE INTO programmes (code, name, department, total_credits, semesters, core_credits, elective_credits, open_credits, structure_json, source, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (p["code"], p["name"], p["department"], p["total_credits"], p["semesters"], p["core_credits"], p["elective_credits"], p["open_credits"], json.dumps(p.get("structure", {})), p["source"], p["last_verified"]))
        counts["programmes"] = len(programmes)

        # 2. Courses
        courses = load_json("courses.json")
        for c in courses:
            cur.execute("""
            INSERT OR REPLACE INTO courses (code, title, department, credits, semester_offered, course_type, mode, level, workload_hours_per_week, syllabus, learning_objectives, source, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (c["code"], c["title"], c["department"], c["credits"], c["semester_offered"], c["course_type"], c.get("mode", "offline"), c.get("level", "undergraduate"), c.get("workload_hours_per_week"), c.get("syllabus"), c.get("learning_objectives"), c["source"], c["last_verified"]))
        counts["courses"] = len(courses)

        # 3. Prerequisites
        prereqs = load_json("prerequisites.json")
        known_course_codes = {course["code"].upper() for course in courses}
        loaded_prerequisites = 0
        for pr in prereqs:
            if (
                pr["course_code"].upper() not in known_course_codes
                or pr["requires_code"].upper() not in known_course_codes
            ):
                logger.warning(
                    "Retaining unresolved prerequisite %s -> %s in seed provenance only.",
                    pr["requires_code"],
                    pr["course_code"],
                )
                continue
            cur.execute("""
            INSERT OR REPLACE INTO prerequisites (course_code, requires_code, type, source)
            VALUES (?, ?, ?, ?);
            """, (pr["course_code"], pr["requires_code"], pr.get("type", "hard"), pr["source"]))
            loaded_prerequisites += 1
        counts["prerequisites"] = loaded_prerequisites

        # 4. Skills
        skills = load_json("skills.json")
        for s in skills:
            cur.execute("""
            INSERT OR REPLACE INTO skills (skill_id, name, domain, description, parent_skill_id, source, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (s["skill_id"], s["name"], s["domain"], s["description"], s.get("parent_skill_id"), s["source"], s["last_verified"]))
        counts["skills"] = len(skills)

        # 5. Course Skills
        course_skills = load_json("course_skills.json")
        for cs in course_skills:
            cur.execute("""
            INSERT OR REPLACE INTO course_skills (course_code, skill_id, depth, weight)
            VALUES (?, ?, ?, ?);
            """, (cs["course_code"], cs["skill_id"], cs["depth"], cs.get("weight", 1.0)))
        counts["course_skills"] = len(course_skills)

        # 6. Modules
        modules = load_json("modules.json")
        for m in modules:
            cur.execute("""
            INSERT OR REPLACE INTO modules (module_id, course_code, module_order, title, text, est_minutes, skill_ids_json, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (m["module_id"], m["course_code"], m["order"], m["title"], m["text"], m.get("est_minutes", 60), json.dumps(m.get("skill_ids", [])), m["source"]))
        counts["modules"] = len(modules)

        # 7. Resources
        resources = load_json("resources.json")
        for r in resources:
            cur.execute("""
            INSERT OR REPLACE INTO resources (resource_id, title, provider, url, license, format, difficulty, est_minutes, credit_eligible, skill_ids_json, source, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (r["resource_id"], r["title"], r["provider"], r["url"], r.get("license", "Open Access"), r["format"], r.get("difficulty", "intermediate"), r.get("est_minutes", 60), 1 if r.get("credit_eligible") else 0, json.dumps(r.get("skill_ids", [])), r["source"], r["last_verified"]))
        counts["resources"] = len(resources)

        # 8. Exercises
        exercises = load_json("exercises.json")
        for ex in exercises:
            cur.execute("""
            INSERT OR REPLACE INTO exercises (exercise_id, skill_id, module_id, type, difficulty, prompt, answer_key_json, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (ex["exercise_id"], ex["skill_id"], ex["module_id"], ex["type"], ex.get("difficulty", 3), ex["prompt"], json.dumps(ex.get("answer_key", {})), ex["source"]))
        counts["exercises"] = len(exercises)

        # 9. Academic Rules
        rules = load_json("academic_rules.json")
        for ru in rules:
            cur.execute("""
            INSERT OR REPLACE INTO academic_rules (rule_id, name, type, parameters_json, source_text, source_url)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (ru["rule_id"], ru["name"], ru["type"], json.dumps(ru.get("parameters", {})), ru["source_text"], ru["source_url"]))
        counts["academic_rules"] = len(rules)

        # 10. Goal Templates
        goals = load_json("goal_templates.json")
        for g in goals:
            cur.execute("""
            INSERT OR REPLACE INTO goal_templates (goal_id, name, target_role, typical_duration_semesters, required_skills_json, milestones_json, source)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (g["goal_id"], g["name"], g["target_role"], g.get("typical_duration_semesters", 4), json.dumps(g.get("required_skills", [])), json.dumps(g.get("milestones", [])), g["source"]))
        counts["goal_templates"] = len(goals)

        # 11. Student Profiles & Initial Diagnostic Evidence (Hero + Synthetic Distribution)
        profiles = load_json("student_profiles.json")
        synth_profiles = load_json("synthetic_profiles.json")
        all_profiles = profiles + synth_profiles
        evidence_count = 0
        for p in all_profiles:
            cur.execute("""
            INSERT OR REPLACE INTO student_profiles (
                student_id, name, programme, year, current_semester, cgpa,
                goal_id, target_role, available_hours_per_week, remaining_elective_slots,
                completed_courses_json, constraints_json, preferences_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                p["student_id"],
                p["name"],
                p["programme"],
                p["year"],
                p["current_semester"],
                p["cgpa"],
                p["goal_id"],
                p.get("target_role", ""),
                p.get("available_hours_per_week", 10.0),
                p.get("remaining_elective_slots", 4),
                json.dumps(p.get("completed_courses", [])),
                json.dumps(p.get("constraints", {})),
                json.dumps({
                    "interests": p.get("interests", []),
                    **p.get("preferences", {})
                })
            ))
            
            # Insert initial diagnostic evidence idempotently
            cur.execute("DELETE FROM evidence_events WHERE student_id = ? AND item_ref = 'initial_seed_diagnostic';", (p["student_id"],))
            for ev in p.get("diagnostic_evidence", []):
                cur.execute("""
                INSERT INTO evidence_events (student_id, skill_id, value, source_type, confidence, item_ref)
                VALUES (?, ?, ?, ?, ?, ?);
                """, (p["student_id"], ev["skill_id"], ev["value"], ev.get("source_type", "assessed_diagnostic"), 1.0, "initial_seed_diagnostic"))
                evidence_count += 1

        counts["student_profiles"] = len(all_profiles)
        counts["seed_evidence_events"] = evidence_count

        provenance_groups = [
            ("programme", "programmes.json", "code"),
            ("course", "courses.json", "code"),
            ("prerequisite", "prerequisites.json", None),
            ("skill", "skills.json", "skill_id"),
            ("course_skill", "course_skills.json", None),
            ("module", "modules.json", "module_id"),
            ("resource", "resources.json", "resource_id"),
            ("exercise", "exercises.json", "exercise_id"),
            ("academic_rule", "academic_rules.json", "rule_id"),
            ("goal", "goal_templates.json", "goal_id"),
        ]
        cur.execute("DELETE FROM seed_provenance")
        provenance_count = 0
        for entity_type, filename, id_field in provenance_groups:
            rows = load_json(filename)
            for row in rows:
                if id_field:
                    entity_id = str(row[id_field])
                elif entity_type == "prerequisite":
                    entity_id = f"{row['course_code']}:{row['requires_code']}"
                else:
                    entity_id = f"{row['course_code']}:{row['skill_id']}"
                provenance = row.get("provenance", "verified")
                source_page = row.get("source_page")
                confidence = row.get("confidence")
                reason = row.get("reason")
                metadata = {
                    key: value for key, value in row.items()
                    if key not in {"provenance", "source_page", "confidence", "reason"}
                }
                cur.execute("""
                INSERT OR REPLACE INTO seed_provenance (
                    entity_type, entity_id, provenance, source_page,
                    confidence, reason, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_type,
                    entity_id,
                    provenance,
                    json.dumps(source_page) if isinstance(source_page, (list, dict)) else source_page,
                    confidence,
                    reason,
                    json.dumps(metadata, ensure_ascii=False),
                ))
                provenance_count += 1
        counts["provenance_records"] = provenance_count

    logger.info("Seed data loaded successfully.")
    for k, v in counts.items():
        logger.info(f" - {k}: {v} records")
    return counts

if __name__ == "__main__":
    should_reset = "--reset" in sys.argv
    load_seed_data(reset=should_reset)
