#!/usr/bin/env python3
"""Run legacy regression tests and IIT Bhilai tests against isolated databases."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_profile_tests(profile: str, arguments: list[str]) -> int:
    with tempfile.TemporaryDirectory(prefix=f"learning-buddy-{profile}-tests-") as temp_dir:
        environment = os.environ.copy()
        environment["INSTITUTE_PROFILE"] = profile
        environment["OFFLINE_MODE"] = "true"
        environment["DATABASE_URL"] = f"sqlite:///{(Path(temp_dir) / 'tests.db').as_posix()}"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *arguments],
            cwd=ROOT_DIR,
            env=environment,
        )
        return result.returncode


def main() -> int:
    legacy_result = run_profile_tests(
        "legacy",
        ["tests", "--ignore=tests/test_bhilai_seed.py"],
    )
    if legacy_result:
        return legacy_result
    return run_profile_tests("iit_bhilai", ["tests/test_bhilai_seed.py"])


if __name__ == "__main__":
    raise SystemExit(main())
