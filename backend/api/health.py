"""
Health & Diagnostic Endpoints.
Reports system status, LiteLLM connectivity, offline mode flag, and performance metrics.
"""

from fastapi import APIRouter
from typing import Dict, Any, Optional
from pydantic import BaseModel
from backend.config import settings
from backend.db.seed_profile import get_institute_profile
from backend.llm.client import llm_client, call_logger
from backend.build_stamp import get_build_stamp, get_git_commit, get_app_js_hash, _BUILD_TIMESTAMP

router = APIRouter(tags=["Health"])

class VersionResponse(BaseModel):
    git_hash: str
    build_time: str
    app_js_hash: str

@router.get("/version", response_model=VersionResponse)
def version_check() -> VersionResponse:
    """Returns the current git commit hash, server build time, and SHA-256 hash of app.js."""
    return {
        "git_hash": get_git_commit(),
        "build_time": _BUILD_TIMESTAMP,
        "app_js_hash": get_app_js_hash(),
    }

class HealthLLMStatus(BaseModel):
    model: Optional[str] = None
    key_configured: bool
    is_live: bool
    offline_mode: bool
    error_reason: Optional[str] = None

class HealthDatabaseStatus(BaseModel):
    type: str

class HealthResponse(BaseModel):
    status: str
    service: str
    app_env: str
    llm: HealthLLMStatus
    database: HealthDatabaseStatus
    institute_profile: str
    telemetry: Dict[str, Any]
    build_stamp: Dict[str, Any]

@router.get("/health")
def health_check() -> HealthResponse:
    stamp = get_build_stamp()
    status_str = "healthy" if stamp["seed_match"] else "degraded"
    probe = llm_client.probe_live_status()
    return {
        "status": status_str,
        "service": "Adobe Personalised Learning Buddy",
        "app_env": settings.APP_ENV,
        "llm": {
            "model": settings.LLM_MODEL,
            "key_configured": bool(settings.LLM_API_KEY),
            "is_live": probe.get("is_live", False),
            "offline_mode": settings.OFFLINE_MODE,
            "error_reason": probe.get("reason"),
        },
        "database": {
            "type": stamp["database_type"],
            "name": stamp["database_name"],
        },
        "institute_profile": get_institute_profile(),
        "telemetry": call_logger.get_summary(),
        "build_stamp": stamp,
    }
