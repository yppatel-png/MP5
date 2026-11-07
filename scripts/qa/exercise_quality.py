#!/usr/bin/env python3
"""
Exercise Quality & Anti-Template QA Audit (§2.1, §2.4)
Audits the entire exercise bank for:
1. Exact or near-duplicate prompts (similarity > 0.85).
2. Missing correct answer, missing explanation, or missing skill tag.
3. MCQs with fewer than 3 plausible distractors (options < 4).
4. Skills with fewer than 3 distinct exercises.

Exits with non-zero code on any violation.
"""

import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
EXERCISES_FILE = ROOT_DIR / "data" / "seed_bhilai" / "exercises.json"


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def audit_exercises() -> int:
    print("=" * 70)
    print(" QA AUDIT: EXERCISE QUALITY, RIGOR & DIVERSITY CHECK")
    print("=" * 70)

    if not EXERCISES_FILE.exists():
        print(f"[ERROR] Exercises file not found at: {EXERCISES_FILE}")
        return 1

    with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    total_exercises = len(exercises)
    print(f"Auditing {total_exercises} exercise(s) in {EXERCISES_FILE.name}...\n")

    errors = []
    warnings = []

    skill_counts = defaultdict(list)
    normalized_prompts = []

    # 1. Individual exercise integrity check
    for idx, ex in enumerate(exercises):
        eid = ex.get("exercise_id") or f"index_{idx}"
        skill_id = ex.get("skill_id", "").strip()
        ex_type = ex.get("type", "").strip()
        prompt = ex.get("prompt", "").strip()
        ans_key = ex.get("answer_key", {})

        # Skill tag check
        if not skill_id:
            errors.append(f"[{eid}] Missing 'skill_id' tag.")
        else:
            skill_counts[skill_id].append(eid)

        # Prompt presence and minimum length
        if not prompt or len(prompt) < 20:
            errors.append(f"[{eid}] Prompt too short or empty (len {len(prompt)} < 20 chars).")

        # Anti-placeholder pattern check
        placeholder_patterns = [
            "explicitly named in",
            "learning unit above",
            "lorem ipsum",
            "todo",
            "placeholder",
        ]
        for pattern in placeholder_patterns:
            if pattern in prompt.lower():
                errors.append(f"[{eid}] Prompt contains forbidden placeholder pattern: '{pattern}'.")

        # Explanation check
        explanation = ans_key.get("explanation", "").strip()
        if not explanation or len(explanation) < 15:
            errors.append(f"[{eid}] Missing or insufficient 'answer_key.explanation' (len < 15 chars).")

        # Correct answer check
        if ex_type == "mcq":
            correct = str(ans_key.get("correct", "")).strip()
            options = ans_key.get("options", [])
            if not correct:
                errors.append(f"[{eid}] MCQ lacks 'correct' answer in answer_key.")
            if len(options) < 4:
                errors.append(f"[{eid}] MCQ has fewer than 3 distractors (total options {len(options)} < 4).")
            if len(set(options)) != len(options):
                errors.append(f"[{eid}] MCQ contains duplicate options: {options}")
            if correct not in options and not any(str(correct).strip() == str(opt).strip() for opt in options):
                errors.append(f"[{eid}] MCQ correct answer '{correct}' not found in options: {options}")

        elif ex_type in ("short", "project", "case"):
            rubric = ans_key.get("rubric", "").strip()
            correct = str(ans_key.get("correct", "")).strip()
            if not rubric and not correct:
                errors.append(f"[{eid}] {ex_type} exercise lacks both 'rubric' and 'correct' answer key.")

        elif ex_type == "code":
            starter = ex.get("starter_code", "").strip()
            test_cases = ans_key.get("test_cases", [])
            if not starter:
                warnings.append(f"[{eid}] Code exercise has empty 'starter_code'.")
            if not test_cases:
                errors.append(f"[{eid}] Code exercise lacks automated 'test_cases'.")

        norm = normalize_text(prompt)
        normalized_prompts.append((eid, prompt, norm))

    # 2. Duplicate / Near-duplicate check (O(N^2) pairwise similarity)
    print("Checking for duplicate and near-duplicate prompts (similarity > 0.85)...")
    duplicate_pairs = 0
    num_prompts = len(normalized_prompts)
    for i in range(num_prompts):
        id_i, orig_i, norm_i = normalized_prompts[i]
        for j in range(i + 1, num_prompts):
            id_j, orig_j, norm_j = normalized_prompts[j]
            # Fast length filter: if lengths differ by more than 20%, similarity cannot exceed 0.85
            len_i, len_j = len(norm_i), len(norm_j)
            if max(len_i, len_j) == 0:
                continue
            if min(len_i, len_j) / max(len_i, len_j) < 0.75:
                continue

            sim = SequenceMatcher(None, norm_i, norm_j).ratio()
            if sim > 0.85:
                errors.append(
                    f"Near-duplicate prompts detected (similarity {sim:.2f}):\n"
                    f"  1. [{id_i}]: {orig_i[:80]}...\n"
                    f"  2. [{id_j}]: {orig_j[:80]}..."
                )
                duplicate_pairs += 1

    # 3. Minimum exercise count per skill and difficulty spread (1-4)
    skill_difficulties = defaultdict(set)
    for ex in exercises:
        sid = ex.get("skill_id", "")
        diff = ex.get("difficulty")
        if sid and diff is not None:
            skill_difficulties[sid].add(diff)

    for skill_id, ex_list in skill_counts.items():
        if len(ex_list) < 8:
            errors.append(f"Skill '{skill_id}' has only {len(ex_list)} exercises (minimum required: 8).")
        diffs = skill_difficulties.get(skill_id, set())
        for required_diff in (1, 2, 3, 4):
            if required_diff not in diffs:
                errors.append(f"Skill '{skill_id}' is missing difficulty {required_diff} (present: {sorted(diffs)}).")

    # Output Summary
    print("-" * 70)
    print(f"Total exercises checked:     {total_exercises}")
    print(f"Unique skills covered:       {len(skill_counts)}")
    print(f"Near-duplicate pairs flagged: {duplicate_pairs}")
    print(f"Integrity Warnings:          {len(warnings)}")
    print(f"Integrity Errors:            {len(errors)}")
    print("-" * 70)

    if errors:
        print("\n[FAILED] Exercise quality audit found violations:")
        for err in errors[:20]:
            print(f"  • {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
        return 1

    print("\n[PASSED] 100% of exercises meet quality, distinctness, and distractor requirements.")
    return 0


if __name__ == "__main__":
    sys.exit(audit_exercises())

