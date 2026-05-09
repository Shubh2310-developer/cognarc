"""
COGNARC — Health Check Routes
apps/api/app/api/v1/health.py

T1.14: GET /health, GET /health/ready, GET /health/live
§19: /health/ready checks MongoDB connection status.
All health routes are PUBLIC — no auth required per §20.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.mongodb import get_database

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> JSONResponse:
    """
    Basic liveness check.
    Returns 200 immediately — used by Docker HEALTHCHECK and Railway.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "service": "cognarc-api"},
    )


@router.get("/health/live", summary="Kubernetes liveness probe")
async def liveness() -> JSONResponse:
    """
    Kubernetes-compatible liveness probe.
    If this returns non-200, the container is restarted.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "alive"},
    )


@router.get("/health/ready", summary="Readiness probe — checks DB")
async def readiness() -> JSONResponse:
    """
    Readiness probe.
    Checks MongoDB connection before declaring service ready.
    §19 SLO: MongoDB connection success on start must be 100%.
    """
    db_status = "disconnected"
    status_code = 503

    try:
        db = get_database()
        if db is not None:
            # Ping MongoDB to verify connection
            await db.command("ping")
            db_status = "connected"
            status_code = 200
    except Exception:
        db_status = "disconnected"
        status_code = 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if status_code == 200 else "not_ready",
            "database": db_status,
        },
    )
