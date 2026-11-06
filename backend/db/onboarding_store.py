"""Persistence for the separate, source-backed IIT Bhilai onboarding flow."""

import json
from typing import Any, Dict, Optional

from backend.db.database import get_db_cursor


def init_onboarding_store() -> None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS onboarding_profiles (
                student_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_onboarding_profile(profile: Dict[str, Any]) -> None:
    with get_db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO onboarding_profiles (student_id, profile_json)
            VALUES (?, ?)
            """,
            (profile["student_id"], json.dumps(profile)),
        )


def update_onboarding_profile(profile: Dict[str, Any]) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            """
            UPDATE onboarding_profiles
            SET profile_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE student_id = ?
            """,
            (json.dumps(profile), profile["student_id"]),
        )
        return cur.rowcount == 1


def get_onboarding_profile(student_id: str) -> Optional[Dict[str, Any]]:
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT profile_json FROM onboarding_profiles WHERE student_id = ?",
            (student_id,),
        )
        row = cur.fetchone()
    return json.loads(row["profile_json"]) if row else None
