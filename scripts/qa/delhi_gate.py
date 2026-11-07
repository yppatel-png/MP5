#!/usr/bin/env python3
"""
Automated Verification Gate: Institutional Grounding & Delhi String Check.
Ensures that zero un-migrated references to Delhi, IITD, or legacy course codes exist
in any active documentation, configuration, scripts, or application source files.
Exits with non-zero status code if any violation is discovered.
"""

import os
import sys
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DELHI_PATTERN = re.compile(r"\b(delhi|iitd)\b", re.IGNORECASE)
LEGACY_CODE_PATTERN = re.compile(r"\b(COL\d+|HUL\d+|CS1|CH1)\b")

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "playwright-report",
    "test-results"
}

EXCLUDED_EXTS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3"
}

def check_delhi_and_legacy_strings():
    print("=" * 70)
    print(" QA VERIFICATION GATE: INSTITUTIONAL PURITY AUDIT")
    print("=" * 70)

    violations = []
    scanned_files = 0

    for root, dirs, files in os.walk(str(ROOT_DIR)):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if file == "delhi_gate.py" or any(file.endswith(ext) for ext in EXCLUDED_EXTS):
                continue

            filepath = Path(root) / file
            rel_path = filepath.relative_to(ROOT_DIR)
            scanned_files += 1

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        # Permit explicit references to the legacy archive branch name
                        sanitized = line.replace("legacy-delhi", "")
                        if DELHI_PATTERN.search(sanitized):
                            violations.append((str(rel_path), line_num, "DELHI_REFERENCE", line.strip()))
                        elif LEGACY_CODE_PATTERN.search(line):
                            violations.append((str(rel_path), line_num, "LEGACY_COURSE_CODE", line.strip()))
            except Exception as e:
                pass

    if violations:
        print(f"\n[FAILED] Found {len(violations)} prohibited legacy references across {scanned_files} files:")
        for file, line, kind, text in violations:
            print(f"  {file}:{line} [{kind}]: {text}")
        print("\nFix all occurrences above before committing or merging into main.")
        sys.exit(1)
    else:
        print(f"\n[PASSED] 0 legacy institutional references found across {scanned_files} active files.")
        print(" Institutional Purity: 100% Grounded in IIT Bhilai.")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    check_delhi_and_legacy_strings()
