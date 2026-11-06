#!/usr/bin/env python3
"""Seed the configured smoke database and serve the app for browser tests."""

import os
import sys
import tempfile
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.db.seed_loader import load_seed_data


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url or not database_url.startswith("sqlite:///"):
        raise RuntimeError("DATABASE_URL must point to an isolated smoke database.")
    load_seed_data(reset=True)
    try:
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8765, log_level="warning")
    finally:
        database_path = Path(database_url.removeprefix("sqlite:///"))
        if (
            database_path.parent == Path(tempfile.gettempdir())
            and database_path.name.startswith("learning-buddy-smoke-")
        ):
            for path in (
                database_path,
                Path(f"{database_path}-shm"),
                Path(f"{database_path}-wal"),
            ):
                path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
