"""
COGNARC — Request Logging Middleware
apps/api/app/middleware/logging.py

§19: Log method, path, status code, latency_ms, user_id on every request.
Per §17: no print(). Outputs structured JSON log.
"""
from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logger import get_logger

_logger = get_logger("api.requests", level=settings.LOG_LEVEL)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every HTTP request with latency and user context."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Extract user_id from request state (set by auth middleware if present)
        user_id: str | None = getattr(request.state, "user_id", None)

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        _logger.info(
            f"{request.method} {request.url.path} → {response.status_code}",
            context={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "user_id": user_id,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
