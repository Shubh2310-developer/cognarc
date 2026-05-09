"""
COGNARC — FastAPI Application Entry Point
apps/api/app/main.py

MVP Architecture: Single monolith, port 8000.
§03: No microservices, no Go gateway, no LangGraph.
§19: Sentry + structured logging wired at startup.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.mongodb import close_db, connect_db
from app.middleware.logging import RequestLoggingMiddleware


# ── Sentry Initialisation ─────────────────────────────────────
def _init_sentry() -> None:
    """Wire Sentry error tracking. No-op if DSN not configured."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
            environment=settings.APP_ENV,
            traces_sample_rate=0.1,  # 10% trace sampling for free tier
            send_default_pii=False,  # Never send PII
        )


# ── Lifespan Manager ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown lifecycle."""
    # Startup
    _init_sentry()
    await connect_db()
    yield
    # Shutdown
    await close_db()


# ── App Factory ───────────────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="COGNARC API",
        description="AI-powered gamified skill development platform",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    # §20: Restrict to known origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # ── Request Logging ───────────────────────────────────────
    # §19: Log method, path, status, latency, user_id on every request
    app.add_middleware(RequestLoggingMiddleware)

    # ── Routes ────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # Include health routes directly at root (no /api/v1 prefix)
    from app.api.v1.health import router as health_router
    app.include_router(health_router)

    # ── Global Exception Handler ──────────────────────────────
    # IMPORTANT: Only catch non-HTTP exceptions here.
    # HTTPException (401, 403, 404, 422) is handled by FastAPI natively.
    from fastapi.exceptions import HTTPException as FastAPIHTTPException
    from fastapi.responses import JSONResponse
    import sentry_sdk as _sentry

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception) -> JSONResponse:
        # Never intercept HTTPException — let FastAPI handle it
        if isinstance(exc, FastAPIHTTPException):
            raise exc
        _sentry.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app


app = create_app()
