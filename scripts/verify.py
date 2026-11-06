#!/usr/bin/env python3
"""
Master Verification Suite Runner (make verify / python scripts/verify.py)
Executes all QA audits, integrity tests, unit/security test suites, and evaluation benchmarks.
Exits with non-zero status code on any failure.
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
NPM = "npm.cmd" if sys.platform == "win32" else "npm"

VERIFICATION_STEPS = [
    {
        "name": "Frontend Design Lint",
        "command": ["node", str(ROOT_DIR / "scripts" / "lint_design.mjs")]
    },
    {
        "name": "Generated Frontend API Types",
        "command": [NPM, "run", "types:check"]
    },
    {
        "name": "Knowledge Base Integrity Validation",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "validate_kb.py")]
    },
    {
        "name": "Secrets & Leak Audit",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "qa" / "secrets_scan.py")]
    },
    {
        "name": "Zero-Egress Outbound Call Audit",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "qa" / "outbound_audit.py")]
    },
    {
        "name": "Automated Unit, Parity & Security Tests",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "run_tests.py")]
    },
    {
        "name": "Seeded-Student API & Browser Smoke Tests",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "run_smoke.py")]
    },
    {
        "name": "End-to-End Evaluation Harness Benchmark",
        "command": [sys.executable, str(ROOT_DIR / "scripts" / "evaluate.py")],
        "environment": {
            "INSTITUTE_PROFILE": "legacy",
            "OFFLINE_MODE": "true",
        },
    }
]

def run_master_verification():
    print("=" * 70)
    print(" ADOBE LEARNING BUDDY - MASTER QA VERIFICATION SUITE")
    print("=" * 70)
    start_time = time.time()
    evaluation_database = Path(tempfile.gettempdir()) / f"learning-buddy-verify-eval-{os.getpid()}.db"

    total_steps = len(VERIFICATION_STEPS)
    for idx, step in enumerate(VERIFICATION_STEPS, 1):
        print(f"\n[{idx}/{total_steps}] Running: {step['name']}...")
        step_start = time.time()
        environment = os.environ.copy()
        environment.update(step.get("environment", {}))
        is_evaluation = step["name"] == "End-to-End Evaluation Harness Benchmark"
        if is_evaluation:
            environment["DATABASE_URL"] = f"sqlite:///{evaluation_database.as_posix()}"
        try:
            res = subprocess.run(step["command"], cwd=str(ROOT_DIR), env=environment)
        finally:
            if is_evaluation:
                for path in (
                    evaluation_database,
                    Path(f"{evaluation_database}-shm"),
                    Path(f"{evaluation_database}-wal"),
                ):
                    path.unlink(missing_ok=True)
        duration = time.time() - step_start
        if res.returncode != 0:
            print(f"\n[FAILED] {step['name']} exited with non-zero code {res.returncode} ({duration:.2f}s)!")
            sys.exit(res.returncode)
        else:
            print(f"[PASSED] {step['name']} completed successfully in {duration:.2f}s.")

    total_duration = time.time() - start_time
    print("\n" + "=" * 70)
    print(f" ALL {total_steps} VERIFICATION STAGES PASSED CLEANLY in {total_duration:.2f}s.")
    print(" Status: PRODUCTION READY / EVALUATION ACCREDITED")
    print("=" * 70)
    sys.exit(0)

if __name__ == "__main__":
    run_master_verification()
