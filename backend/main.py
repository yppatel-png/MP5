"""
Main FastAPI Application Entrypoint.
Initializes routes, middleware, and lifecycle hooks.
Mounts responsive single-page web UI at root and static assets,
and serves Swagger OpenAPI interactive documentation at /docs.
"""

from pathlib import Path
import logging
import uuid
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.config import settings
from backend.api.health import router as health_router
from backend.api.courses import router as courses_router, kb_router
from backend.api.students import router as students_router
from backend.api.plans import router as plans_router
from backend.api.practice import router as practice_router
from backend.api.adapt import router as adapt_router
from backend.api.buddy import router as buddy_router
from backend.api.admin import router as admin_router
from backend.api.programmes import load_programme_catalog, router as programmes_router
from backend.api.onboarding import router as onboarding_router
from backend.db.database import init_db
from backend.db.database import get_db_cursor
from backend.db.seed_profile import get_institute_profile
from backend.db.seed_loader import load_seed_data
from backend.db.onboarding_store import init_onboarding_store
from backend.student.diagnostic import diagnostic_engine
from backend.student.model import StudentStore
from backend.student.summary import build_student_summary

logger = logging.getLogger("learning_buddy.startup")
seed_consistency_report = {
    "checked": 0,
    "failures": [{"student_id": None, "message": "Startup check has not run."}],
}

class SeedConsistencyFailure(BaseModel):
    student_id: Optional[str]
    message: str

class SeedConsistencyReport(BaseModel):
    checked: int
    failures: List[SeedConsistencyFailure]
    healthy: bool

app = FastAPI(
    title="Adobe Personalised Learning Buddy API",
    description="Intelligent, constraint-respecting academic learning buddy and curriculum planner for Inter IIT Tech Meet 15.0.",
    version="1.0.0"
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(kb_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(plans_router, prefix="/api")
app.include_router(practice_router, prefix="/api")
app.include_router(adapt_router, prefix="/api")
app.include_router(buddy_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(programmes_router, prefix="/api")
app.include_router(onboarding_router, prefix="/api")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.on_event("startup")
def verify_seeded_student_summaries() -> None:
    """Verify every persisted student profile can produce the shared summary."""
    global seed_consistency_report
    init_db()
    init_onboarding_store()
    if get_institute_profile() == "iit_bhilai":
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM programmes), "
                "(SELECT COUNT(*) FROM courses), "
                "(SELECT COUNT(*) FROM student_profiles)"
            )
            seed_counts = tuple(cur.fetchone())
        if not any(seed_counts):
            logger.info("Initializing the isolated IIT Bhilai demo database from its seed bundle.")
            load_seed_data()
        elif not all(seed_counts):
            logger.error(
                "IIT Bhilai database is only partially seeded (programmes=%s, courses=%s, students=%s). "
                "No automatic reset was performed.",
                *seed_counts
            )
    load_programme_catalog()
    profiles = StudentStore.get_all_profiles()
    failures = []
    for profile in profiles:
        try:
            gaps = diagnostic_engine.compute_skill_gaps(profile.student_id)
            build_student_summary(
                profile=profile,
                plan=None,
                readiness_percentage=gaps.get("readiness_percentage"),
                priority_gap_count=gaps.get("critical_gap_count", 0),
                goal_name=gaps.get("goal_name"),
            )
        except Exception as exc:
            logger.exception(
                "Seeded student summary check failed for student_id=%s",
                profile.student_id
            )
            failures.append({
                "student_id": profile.student_id,
                "message": f"{type(exc).__name__}: {exc}",
            })
    if not profiles:
        failures.append({"student_id": None, "message": "No seeded student profiles were found."})
    seed_consistency_report = {"checked": len(profiles), "failures": failures}
    if failures:
        logger.error(
            "Seed consistency check completed with %s failure(s) across %s student(s).",
            len(failures),
            len(profiles)
        )
    else:
        logger.info("Seed consistency check passed for %s student(s).", len(profiles))

@app.get("/api/admin/seed-consistency", response_model=SeedConsistencyReport)
def get_seed_consistency_report():
    return {
        **seed_consistency_report,
        "healthy": not seed_consistency_report["failures"],
    }

# Static frontend assets mount
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_model=None)
@app.get("/index.html", response_model=None)
def root(request: Request = None):
    # If a programmatic client explicitly asks for JSON, return JSON
    if request is not None and hasattr(request, "headers"):
        accept = request.headers.get("accept", "")
        if "application/json" in accept and "text/html" not in accept:
            return JSONResponse({
                "message": "Welcome to Adobe Personalised Learning Buddy API",
                "health_check": "/api/health",
                "docs": "/docs",
                "courses": "/api/courses",
                "skills": "/api/skills",
                "rules": "/api/rules",
                "goals": "/api/goals"
            })

    # Serve the visual web application
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    return JSONResponse({
        "message": "Welcome to Adobe Personalised Learning Buddy API",
        "health_check": "/api/health",
        "docs": "/docs"
    })

@app.get("/styleguide", response_model=None)
def styleguide():
    """Hidden design system styleguide route for visual verification."""
    guide_file = FRONTEND_DIR / "styleguide.html"
    if guide_file.exists():
        return FileResponse(str(guide_file))
    return JSONResponse({"error": "styleguide.html not found"}, status_code=404)
