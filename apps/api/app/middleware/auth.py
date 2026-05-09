"""
COGNARC — Supabase JWT Auth Middleware
apps/api/app/middleware/auth.py

T2.3: Decode Supabase JWT via python-jose, inject user_id, return 401 on failure.
§20: JWT validation happens here ONLY — never in route handlers.
§20: All API routes require JWT except GET /health* and POST /auth/login.

Algorithm: HS256 (Supabase default for JWT Secret)
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings
from app.core.logger import get_logger

_logger = get_logger("middleware.auth")

# Routes that do NOT require authentication
PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health",
    "/health/live",
    "/health/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
})

# JWT algorithm used by Supabase
SUPABASE_JWT_ALGORITHMS = ["HS256"]


def is_public_path(path: str) -> bool:
    """Return True if the path does not require authentication."""
    return path in PUBLIC_PATHS or path.startswith("/health")


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Parse 'Bearer <token>' from Authorization header.
    Returns None if header is absent or malformed.
    """
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def decode_supabase_jwt(token: str) -> dict:
    """
    Decode and validate a Supabase JWT.

    Supabase JWTs are signed with SUPABASE_JWT_SECRET (HS256).
    Raises HTTPException 401 on any validation failure.

    Returns:
        Decoded JWT payload dict.
    """
    if not settings.SUPABASE_JWT_SECRET:
        _logger.error("SUPABASE_JWT_SECRET is not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service misconfigured",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=SUPABASE_JWT_ALGORITHMS,
            options={"verify_aud": False},  # Supabase doesn't always set aud
        )
        return payload

    except ExpiredSignatureError:
        _logger.warning("JWT expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        _logger.warning(f"JWT validation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id_from_payload(payload: dict) -> str:
    """
    Extract user ID (sub claim) from JWT payload.
    Supabase sets 'sub' to the auth.users UUID.
    Raises 401 if 'sub' is missing.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(user_id)
