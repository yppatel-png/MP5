"""Select the seed bundle for the configured institute demo."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SEED_DIRECTORIES = {
    "iit_bhilai": PROJECT_ROOT / "data" / "seed_bhilai",
}


def get_institute_profile() -> str:
    return "iit_bhilai"


def get_seed_dir() -> Path:
    return _SEED_DIRECTORIES["iit_bhilai"]
