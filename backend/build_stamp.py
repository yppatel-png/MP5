"""
Build stamp and seed checksum verification.
Computes Git commit, database info, deterministic seed hash, and table counts.
Exposes verification checks to detect stale builds and desynchronized databases.
"""

import json
import hashlib
import subprocess
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

from backend.config import settings, BASE_DIR
from backend.db.seed_profile import get_seed_dir
from backend.db.database import get_db_cursor

logger = logging.getLogger("learning_buddy.build_stamp")

_CACHED_SEED_HASH: str = ""
_CACHED_SEED_COUNTS: Dict[str, int] = {}
_BUILD_TIMESTAMP: str = datetime.datetime.now(datetime.timezone.utc).isoformat()

def get_git_commit() -> str:
    """Returns the short git commit hash if available, else fallback."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(BASE_DIR),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        if commit:
            return commit
    except Exception:
        pass
    return "dev-local"

def compute_seed_info() -> Tuple[str, Dict[str, int]]:
    """
    Computes deterministic SHA-256 hash across all JSON files in the seed directory
    and counts key entities.
    """
    global _CACHED_SEED_HASH, _CACHED_SEED_COUNTS
    if _CACHED_SEED_HASH and _CACHED_SEED_COUNTS:
        return _CACHED_SEED_HASH, _CACHED_SEED_COUNTS

    seed_dir = get_seed_dir()
    if not seed_dir.exists():
        return "no-seed-dir", {}

    hasher = hashlib.sha256()
    counts = {
        "courses": 0,
        "modules": 0,
        "skills": 0,
        "exercises": 0,
        "resources": 0,
        "profiles": 0,
    }

    json_files = sorted(seed_dir.glob("*.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            hasher.update(file_path.name.encode("utf-8"))
            canonical = json.dumps(data, sort_keys=True).encode("utf-8")
            hasher.update(canonical)

            if file_path.name == "courses.json":
                counts["courses"] = len(data)
            elif file_path.name == "modules.json":
                counts["modules"] = len(data)
            elif file_path.name == "skills.json":
                counts["skills"] = len(data)
            elif file_path.name == "exercises.json":
                counts["exercises"] = len(data)
            elif file_path.name == "resources.json":
                counts["resources"] = len(data)
            elif file_path.name == "student_profiles.json":
                counts["profiles"] += len(data)
            elif file_path.name == "synthetic_profiles.json":
                counts["profiles"] += len(data)
        except Exception as exc:
            logger.warning(f"Error hashing seed file {file_path.name}: {exc}")

    _CACHED_SEED_HASH = hasher.hexdigest()[:12]
    _CACHED_SEED_COUNTS = counts
    return _CACHED_SEED_HASH, _CACHED_SEED_COUNTS

def get_db_counts() -> Dict[str, int]:
    """Retrieves actual live record counts from the database."""
    counts = {
        "courses": 0,
        "modules": 0,
        "skills": 0,
        "exercises": 0,
        "resources": 0,
        "profiles": 0,
    }
    table_map = {
        "courses": "courses",
        "modules": "modules",
        "skills": "skills",
        "exercises": "exercises",
        "resources": "resources",
        "profiles": "student_profiles",
    }
    try:
        with get_db_cursor() as cur:
            for key, tbl in table_map.items():
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                    row = cur.fetchone()
                    counts[key] = int(row[0]) if row else 0
                except Exception:
                    counts[key] = -1
    except Exception as exc:
        logger.warning(f"Failed to query DB counts: {exc}")
    return counts

def get_build_stamp() -> Dict[str, Any]:
    """Generates the full build stamp dictionary."""
    git_hash = get_git_commit()
    seed_hash, seed_counts = compute_seed_info()
    db_counts = get_db_counts()

    db_type = "sqlite" if "sqlite" in settings.DATABASE_URL.lower() else "postgresql"
    db_name = (
        Path(settings.DATABASE_URL.replace("sqlite:///", "", 1)).name
        if db_type == "sqlite"
        else settings.DATABASE_URL.split("/")[-1].split("?")[0]
    )

    # Check match on critical tables
    seed_match = True
    mismatches = []
    for k in ["courses", "modules", "skills", "exercises", "resources", "profiles"]:
        exp = seed_counts.get(k, 0)
        act = db_counts.get(k, -1)
        if exp > 0 and act != exp:
            seed_match = False
            mismatches.append(f"{k}: expected {exp}, got {act}")

    summary = (
        f"Build {git_hash} · {db_type.upper()}: {db_name} · "
        f"Seed {seed_hash} ({'SYNCED' if seed_match else 'MISMATCH'}) · "
        f"{db_counts.get('courses', 0)} courses, {db_counts.get('modules', 0)} modules, "
        f"{db_counts.get('skills', 0)} skills, {db_counts.get('exercises', 0)} exercises, "
        f"{db_counts.get('resources', 0)} resources, {db_counts.get('profiles', 0)} profiles"
    )

    return {
        "git_commit": git_hash,
        "build_time": _BUILD_TIMESTAMP,
        "database_type": db_type,
        "database_name": db_name,
        "seed_hash": seed_hash,
        "seed_counts": seed_counts,
        "db_counts": db_counts,
        "seed_match": seed_match,
        "mismatches": mismatches,
        "summary_string": summary,
    }
