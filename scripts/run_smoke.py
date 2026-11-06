#!/usr/bin/env python3
"""Run the all-seeded-students API and browser smoke checks."""

import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
NPM = "npm.cmd" if sys.platform == "win32" else "npm"

def main() -> int:
    smoke_database = Path(tempfile.gettempdir()) / f"learning-buddy-smoke-{os.getpid()}.db"
    environment = os.environ.copy()
    environment["OFFLINE_MODE"] = "true"
    environment["DATABASE_URL"] = f"sqlite:///{smoke_database.as_posix()}"
    environment["INSTITUTE_PROFILE"] = "iit_bhilai"
    environment["LEARNING_BUDDY_SMOKE_DATABASE"] = str(smoke_database)
    legacy_database = Path(tempfile.gettempdir()) / f"learning-buddy-legacy-smoke-{os.getpid()}.db"
    legacy_environment = environment.copy()
    legacy_environment["DATABASE_URL"] = f"sqlite:///{legacy_database.as_posix()}"
    legacy_environment["INSTITUTE_PROFILE"] = "legacy"
    server = None
    try:
        bhilai_tests = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_student_summary_api.py",
                "tests/test_bhilai_onboarding.py",
                "tests/test_bhilai_seed.py",
            ],
            cwd=ROOT_DIR,
            env=environment,
        )
        if bhilai_tests.returncode:
            return bhilai_tests.returncode

        legacy_tests = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests/test_product_flows.py"],
            cwd=ROOT_DIR,
            env=legacy_environment,
        )
        if legacy_tests.returncode:
            return legacy_tests.returncode

        server_environment = environment.copy()
        server_environment["OFFLINE_MODE"] = "true"
        server = subprocess.Popen(
            [sys.executable, "scripts/smoke_server.py"],
            cwd=ROOT_DIR,
            env=server_environment,
        )
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(f"Smoke server exited with status {server.returncode}.")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise TimeoutError("Smoke server did not become healthy within 120 seconds.")

        environment["LEARNING_BUDDY_SMOKE_EXTERNAL_SERVER"] = "true"
        result = subprocess.run(
            [NPM, "run", "test:e2e:personas"],
            cwd=ROOT_DIR,
            env=environment,
        )
        if result.returncode:
            return result.returncode
        print("All seeded-student API and browser smoke checks passed.")
        return 0
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        for path in (
            smoke_database,
            Path(f"{smoke_database}-shm"),
            Path(f"{smoke_database}-wal"),
            legacy_database,
            Path(f"{legacy_database}-shm"),
            Path(f"{legacy_database}-wal"),
        ):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
