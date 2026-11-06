"""
Application configuration management.
Reads environment variables with validation and fallback defaults.
Implemented cleanly using standard Pydantic and os.environ.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# The Bhilai demo uses an isolated database so switching profiles never
# overwrites the existing legacy demo database.
INSTITUTE_PROFILE = os.getenv("INSTITUTE_PROFILE", "iit_bhilai").strip().lower()
DEFAULT_DATABASE_NAME = (
    "buddy_bhilai.db" if INSTITUTE_PROFILE == "iit_bhilai" else "buddy.db"
)
_configured_database_url = os.getenv("DATABASE_URL")
if (
    INSTITUTE_PROFILE == "iit_bhilai"
    and _configured_database_url
    and _configured_database_url.startswith("sqlite:///")
    and Path(_configured_database_url.replace("sqlite:///", "", 1)).name == "buddy.db"
):
    _configured_database_url = None

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # LLM Settings (via LiteLLM)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-3.5-flash-lite")
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
    LLM_API_BASE: Optional[str] = os.getenv("LLM_API_BASE")
    EMBEDDING_MODEL: Optional[str] = os.getenv("EMBEDDING_MODEL")
    
    # Offline toggle: when true, forces deterministic fallback with no network calls
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "false").lower() in ("true", "1", "yes")

    # Admin Security Token
    ADMIN_API_TOKEN: str = os.getenv("ADMIN_API_TOKEN", "adm_secret_token_15")

    # Feature Flags (defaulting to True for competitive completeness)
    FEATURE_CERTIFICATE: bool = os.getenv("FEATURE_CERTIFICATE", "true").lower() in ("true", "1", "yes")
    FEATURE_COUNTERFACTUAL: bool = os.getenv("FEATURE_COUNTERFACTUAL", "true").lower() in ("true", "1", "yes")
    FEATURE_VARIANTS: bool = os.getenv("FEATURE_VARIANTS", "true").lower() in ("true", "1", "yes")
    FEATURE_RETENTION: bool = os.getenv("FEATURE_RETENTION", "true").lower() in ("true", "1", "yes")
    FEATURE_REALITY_CHECK: bool = os.getenv("FEATURE_REALITY_CHECK", "true").lower() in ("true", "1", "yes")
    
    # Database URL: defaults to SQLite for local development
    DATABASE_URL: str = _configured_database_url or (
        f"sqlite:///{BASE_DIR / 'data' / DEFAULT_DATABASE_NAME}"
    )
    
    # Evidence weights file path
    EVIDENCE_WEIGHTS_PATH: Path = BASE_DIR / "config" / "evidence_weights.yaml"

settings = Settings()

def load_evidence_config() -> Dict[str, Any]:
    """Loads evidence weighting and BKT default hyperparameters from YAML."""
    if settings.EVIDENCE_WEIGHTS_PATH.exists():
        with open(settings.EVIDENCE_WEIGHTS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "evidence_weights": {
            "grade": 1.0,
            "assessed_diagnostic": 1.0,
            "timed_project": 0.9,
            "mock_exam": 0.9,
            "quiz": 0.7,
            "exercise": 0.7,
            "inferred_course": 0.5,
            "self_declared": 0.2
        },
        "bkt_parameters": {
            "p_init_default": 0.1,
            "p_transit_default": 0.2,
            "p_slip_default": 0.1,
            "p_guess_default": 0.2,
            "mastery_threshold": 0.85,
            "min_items_required": 3,
            "min_sessions_required": 2
        }
    }
