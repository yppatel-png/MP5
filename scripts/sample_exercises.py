#!/usr/bin/env python3
import json
import random
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EXERCISES_FILE = ROOT_DIR / "data" / "seed_bhilai" / "exercises.json"

def main():
    with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    random.seed(42)
    sampled = random.sample(exercises, 20)

    for i, ex in enumerate(sampled, 1):
        print(f"=== SAMPLE {i:02d}: {ex['exercise_id']} ({ex['skill_id']} · Diff {ex['difficulty']} · {ex['type'].upper()}) ===")
        print(f"Prompt: {ex['prompt']}")
        if ex.get("type") == "mcq":
            for opt in ex.get("answer_key", {}).get("options", []):
                mark = "[*]" if opt == ex.get("answer_key", {}).get("correct") else "[ ]"
                print(f"  {mark} {opt}")
        elif ex.get("type") == "code":
            print(f"Test cases: {ex.get('answer_key', {}).get('test_cases', [])}")
        else:
            print(f"Rubric / Correct: {ex.get('answer_key', {}).get('rubric', ex.get('answer_key', {}).get('correct'))}")
        print(f"Explanation: {ex.get('answer_key', {}).get('explanation', '')}")
        print(f"Source: {ex.get('source')} (Page {ex.get('source_page')}, {ex.get('provenance')})\n")

if __name__ == "__main__":
    main()

