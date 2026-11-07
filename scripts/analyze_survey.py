#!/usr/bin/env python3
"""
IIT Bhilai Student Survey Analyzer (§3 Product Management)
Reads empirical survey responses from data/survey/responses.csv, computes descriptive
statistics, and generates a formatted markdown summary in docs/survey/results.md.

If responses are not yet gathered, exits with a clear 'PENDING' notice without inventing data.
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SURVEY_CSV_PATH = ROOT_DIR / "data" / "survey" / "responses.csv"
OUTPUT_MD_PATH = ROOT_DIR / "docs" / "survey" / "results.md"


def analyze_survey(csv_path: Path, output_path: Path) -> int:
    if not csv_path.exists():
        print(f"[SURVEY PENDING] Survey response file not found at: {csv_path}")
        print("Status: The survey questionnaire instrument is ready at docs/survey/questionnaire.md.")
        print("Action required: Once student responses are collected, save them as CSV at data/survey/responses.csv")
        print("and re-run this script to generate docs/survey/results.md.")
        return 0

    print(f"Loading responses from {csv_path}...")
    responses = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        lines = [line for line in f if not line.strip().startswith("#")]
        reader = csv.DictReader(lines)
        for row in reader:
            responses.append(row)

    total_responses = len(responses)
    if total_responses == 0:
        print("[SURVEY PENDING] responses.csv is empty. No responses to analyze.")
        return 0

    print(f"Processing {total_responses} student response(s)...")

    # Metrics aggregation
    years = Counter(r.get("year", "Unknown").strip() for r in responses)
    departments = Counter(r.get("department", "Unknown").strip() for r in responses)
    goals = Counter(r.get("primary_goal", "Undecided").strip() for r in responses)
    pain_points = Counter()
    for r in responses:
        points = r.get("top_pain_points", "").split(";")
        for p in points:
            cleaned = p.strip()
            if cleaned:
                pain_points[cleaned] += 1

    study_hours = []
    for r in responses:
        try:
            val = float(r.get("weekly_study_hours", "0"))
            if val > 0:
                study_hours.append(val)
        except ValueError:
            pass

    avg_study_hours = sum(study_hours) / len(study_hours) if study_hours else 0.0

    # Write markdown summary
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        rel_csv = csv_path.resolve().relative_to(ROOT_DIR.resolve())
    except ValueError:
        rel_csv = csv_path

    with open(output_path, mode="w", encoding="utf-8") as out:
        out.write("# Survey Analysis Report: IIT Bhilai Undergraduate Journey\n\n")
        out.write(f"**Total Verified Responses (N):** {total_responses}  \n")
        out.write(f"**Source Data:** `{rel_csv}`  \n")
        out.write(f"**Generated:** {Path(__file__).name}  \n\n")
        out.write("---\n\n")

        out.write("## 1. Academic Year Distribution\n\n")
        out.write("| Academic Year | Responses | Percentage |\n| :--- | :---: | :---: |\n")
        for y, count in years.most_common():
            pct = (count / total_responses) * 100
            out.write(f"| {y} | {count} | {pct:.1f}% |\n")

        out.write("\n## 2. Departmental Breakdown\n\n")
        out.write("| Discipline / Department | Count | Share |\n| :--- | :---: | :---: |\n")
        for d, count in departments.most_common():
            pct = (count / total_responses) * 100
            out.write(f"| {d} | {count} | {pct:.1f}% |\n")

        out.write("\n## 3. Career & Post-Graduation Ambitions\n\n")
        out.write("| Primary Goal Track | Responses | Share |\n| :--- | :---: | :---: |\n")
        for g, count in goals.most_common():
            pct = (count / total_responses) * 100
            out.write(f"| {g} | {count} | {pct:.1f}% |\n")

        out.write(f"\n**Average Self-Study Capacity:** {avg_study_hours:.1f} hours/week outside classes.\n\n")

        out.write("## 4. Top Reported Elective & Planning Pain Points\n\n")
        out.write("| Reported Bottleneck / Pain Point | Mentions | Frequency |\n| :--- | :---: | :---: |\n")
        for pp, count in pain_points.most_common(10):
            pct = (count / total_responses) * 100
            out.write(f"| {pp} | {count} | {pct:.1f}% |\n")

        out.write("\n---\n*End of empirical survey report.*\n")

    print(f"Successfully generated empirical report at {output_path}")
    return 0


if __name__ == "__main__":
    target_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else SURVEY_CSV_PATH
    target_out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_MD_PATH
    sys.exit(analyze_survey(target_csv, target_out))
