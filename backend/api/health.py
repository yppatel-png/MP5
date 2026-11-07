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

router = APIRouter(tags=["Health"])

class HealthLLMStatus(BaseModel):
    model: Optional[str] = None
    key_configured: bool
    is_live: bool
    offline_mode: bool

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

@router.get("/health")
def health_check() -> HealthResponse:
    return {
        "status": "healthy",
        "service": "Adobe Personalised Learning Buddy",
        "app_env": settings.APP_ENV,
        "llm": {
            "model": settings.LLM_MODEL,
            "key_configured": bool(settings.LLM_API_KEY),
            "is_live": llm_client.is_live(),
            "offline_mode": settings.OFFLINE_MODE
        },
        "database": {
            "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql"
        },
        "institute_profile": get_institute_profile(),
        "telemetry": call_logger.get_summary()
    }
