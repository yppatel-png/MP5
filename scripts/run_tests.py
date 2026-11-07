#!/usr/bin/env python3
"""Run test suite for IIT Bhilai against isolated temporary database."""

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
    return run_profile_tests("iit_bhilai", ["tests"])


if __name__ == "__main__":
    raise SystemExit(main())
