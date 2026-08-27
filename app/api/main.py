from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


# ============================================================
# NEXUS AI FASTAPI APPLICATION
# ============================================================

APP_NAME = "NEXUS AI"

APP_VERSION = "4.0"

APP_DESCRIPTION = (
    "Autonomous Enterprise Intelligence API"
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["System"],
)
def root() -> dict:
    """
    FastAPI root endpoint.
    """

    return {
        "name": APP_NAME,
        "description": APP_DESCRIPTION,
        "version": APP_VERSION,
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "health": "/api/health",
    }


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    router
)


# ============================================================
# HEALTH ALIAS
# ============================================================

@app.get(
    "/health",
    tags=["System"],
)
def health_alias() -> dict:
    """
    Simple health endpoint.

    This alias makes health checks convenient for
    load balancers, Docker, deployment platforms,
    and monitoring systems.
    """

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# APPLICATION EXPORT
# ============================================================

__all__ = [
    "app",
]