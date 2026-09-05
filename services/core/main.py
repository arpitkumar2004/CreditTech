"""Main FastAPI application entry point."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from services.core.config import get_settings
from services.core.admin.router import router as admin_router
from services.core.consent.router import router as consent_router
from services.core.database import close_db, init_db
from services.core.dashboard.router import report_router
from services.core.dashboard.router import router as dashboard_router
from services.core.decisioning.router import router as decisioning_router
from services.core.grievance.router import router as grievance_router
from services.core.handoff.router import router as handoff_router
from services.core.ingestion.mocks.server import router as mock_router
from services.core.ingestion.router import router as ingestion_router
from services.core.monitoring.router import router as monitoring_router
from services.core.ops.router import router as ops_router
from services.core.scoring.router import router as scoring_router
from services.core.shared.logging import get_logger, setup_logging
from services.core.shared.security_middleware import (
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from services.core.simulation.router import router as simulation_router

settings = get_settings()
logger = get_logger("core.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown lifecycle events."""
    # 1. Initialize logging
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger.info("application_starting", env=settings.app_env, version=settings.app_version)

    # 2. Database initialization (in dev, automatically create tables if not exists)
    if settings.is_development:
        logger.info("initializing_database_tables")
        await init_db()

    yield

    # 3. Clean up connections on shutdown
    logger.info("application_shutting_down")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="Alternative Credit Scoring System for Rural Financial Inclusion",
    version=settings.app_version,
    debug=settings.app_debug,
    lifespan=lifespan,
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# P6 security hardening (order matters: outer wraps first-declared last)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please contact support."},
    )


# Basic health check endpoint
@app.get("/health", tags=["Health"], summary="System health check")
async def health_check() -> dict:
    """Returns application status metadata."""
    return {
        "status": "healthy",
        "env": settings.app_env,
        "version": settings.app_version,
    }


# Register routers
app.include_router(consent_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(mock_router, prefix="/api/v1")
app.include_router(scoring_router, prefix="/api/v1")
app.include_router(handoff_router, prefix="/api/v1")
app.include_router(decisioning_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(grievance_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(report_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(ops_router, prefix="/api/v1")



@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def serve_dashboard() -> HTMLResponse:
    """Serves the visual analytics operations dashboard HTML page."""
    filepath = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    if os.path.exists(filepath):
        with open(filepath, encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>Dashboard Template Not Found</h1>", status_code=404)





