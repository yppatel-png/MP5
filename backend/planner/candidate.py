"""
Candidate Course & Learning Resource Retriever.
Retrieves candidate courses that cover student skill gaps using
the course_skills relational index and BM25 syllabus matching.
"""

import json
from typing import List, Dict, Any, Set
from pathlib import Path
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_seed_dir

SEED_DIR = get_seed_dir()

def load_seed(name: str):
    with open(SEED_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

class CandidateRetriever:
    def __init__(self):
        self.courses = {c["code"]: c for c in load_seed("courses.json")}
        self.course_skills = load_seed("course_skills.json")
        self.resources = load_seed("resources.json")
        self.skills = {s["skill_id"]: s for s in load_seed("skills.json")}
        rules = {rule["rule_id"]: rule for rule in load_seed("academic_rules.json")}
        self.hours_per_credit = float(
            rules.get("rule_workload_hours", {}).get("parameters", {}).get("hours_per_credit_week", 2)
        )

        # Build reverse index: skill_id -> list of (course_code, depth, weight)
        self.skill_to_courses: Dict[str, List[Dict[str, Any]]] = {}
        for cs in self.course_skills:
            self.skill_to_courses.setdefault(cs["skill_id"], []).append(cs)

    def retrieve_candidates_for_gaps(
        self,
        skill_gaps: List[Dict[str, Any]],
        completed_course_codes: Set[str],
        programme_code: str = "iit_bhilai_btech_cse_2023",
        cgpa: float = 8.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves and ranks candidate courses based on skill gap coverage.
        Filters out already completed courses and checks preliminary eligibility.
        """
        scored_courses: Dict[str, Dict[str, Any]] = {}

        # Prioritize gaps with high magnitude and critical flag
        for gap in skill_gaps:
            sk_id = gap["skill_id"]
            gap_weight = gap.get("gap", 0.5) * (1.5 if gap.get("critical") else 1.0)
            
            matching_courses = self.skill_to_courses.get(sk_id, [])
            for match in matching_courses:
                code = match["course_code"]
                if code in completed_course_codes:
                    continue  # already taken

                course_meta = self.courses.get(code)
                if not course_meta:
                    continue

                if code not in scored_courses:
                    scored_courses[code] = {
                        "code": code,
                        "title": course_meta["title"],
                        "credits": course_meta["credits"],
                        "semester_offered": course_meta["semester_offered"],
                        "course_type": course_meta["course_type"],
                        "department": course_meta["department"],
                        "level": course_meta.get("level", "undergraduate"),
                        "workload_hours_per_week": (
                            course_meta.get("workload_hours_per_week")
                            or float(course_meta["credits"]) * self.hours_per_credit
                        ),
                        "source_page": course_meta.get("source_page"),
                        "provenance": course_meta.get("provenance", "verified"),
                        "mode": course_meta.get("mode", "offline"),
                        "skills_targeted": [],
                        "score": 0.0,
                        "reasons": []
                    }

                depth_weight = {"intro": 0.7, "intermediate": 1.0, "advanced": 1.2}.get(match.get("depth", "intermediate"), 1.0)
                contribution = gap_weight * match.get("weight", 1.0) * depth_weight
                
                scored_courses[code]["score"] += contribution
                scored_courses[code]["skills_targeted"].append(sk_id)
                scored_courses[code]["reasons"].append(
                    f"Targets {round(gap.get('gap', 0.5)*100)}% gap in {self.skills.get(sk_id, {}).get('name', sk_id)}; mapping confidence {match.get('confidence', 0.5):.0%}."
                )

        # Sort candidates deterministically by score descending, then course code
        ranked = list(scored_courses.values())
        ranked.sort(key=lambda x: (x["score"], -x["credits"], x["code"]), reverse=True)
        return ranked

    def retrieve_resources_for_gaps(self, skill_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retrieves supplementary open learning resources (NPTEL, MIT OCW) covering skill gaps."""
        gap_skill_ids = {g["skill_id"] for g in skill_gaps}
        matched_resources = []
        for r in self.resources:
            # Strictly exclude any resources marked needs_verification or missing verified license
            if r.get("status") == "needs_verification" or not r.get("license_verified", True):
                continue
            common = set(r.get("skill_ids", [])).intersection(gap_skill_ids)
            if common:
                matched_resources.append({
                    "resource_id": r["resource_id"],
                    "title": r["title"],
                    "provider": r["provider"],
                    "url": r["url"],
                    "format": r["format"],
                    "est_minutes": r["est_minutes"],
                    "credit_eligible": bool(r.get("credit_eligible")),
                    "skills_covered": list(common)
                })
        return matched_resources

candidate_retriever = CandidateRetriever()
