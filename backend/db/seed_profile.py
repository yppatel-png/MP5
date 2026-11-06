"""Select the seed bundle for the configured institute demo."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SEED_DIRECTORIES = {
    "legacy": PROJECT_ROOT / "data" / "seed",
    "iit_bhilai": PROJECT_ROOT / "data" / "seed_bhilai",
}


def get_institute_profile() -> str:
    profile = os.getenv("INSTITUTE_PROFILE", "iit_bhilai").strip().lower()
    if profile not in _SEED_DIRECTORIES:
        raise ValueError(f"Unsupported INSTITUTE_PROFILE: {profile}")
    return profile


def get_seed_dir() -> Path:
    return _SEED_DIRECTORIES[get_institute_profile()]
