"""
COGNARC — Auth API Routes
apps/api/app/api/v1/auth.py

T2.6: POST /auth/login, POST /auth/logout, POST /auth/refresh
§06: Routes only — no business logic. Delegates to adapters.
§14: MVP auth = Supabase magic link only. No OAuth in Phase 1.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.adapters.supabase_adapter import get_supabase_adapter
from app.core.logger import get_logger

_logger = get_logger("api.auth")
router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Send magic link email",
    status_code=status.HTTP_200_OK,
)
async def login(request: LoginRequest) -> LoginResponse:
    """
    MVP auth: send Supabase magic link to the provided email.
    §14: Magic link only. No password, no OAuth in Phase 1.
    This endpoint is public — no JWT required.
    """
    try:
        adapter = get_supabase_adapter()
        await adapter.send_magic_link(request.email)
        _logger.info("Magic link sent", context={"email": request.email})
        return LoginResponse(message="Magic link sent. Check your email.")
    except Exception as exc:
        _logger.error(f"Magic link error: {exc}", context={"email": request.email})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send magic link. Please try again.",
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate session",
)
async def logout() -> dict:
    """
    Logout endpoint — client-side token deletion is primary logout.
    This endpoint can be used to signal server-side session cleanup.
    Returns 200 OK with empty body.
    """
    # MVP: stateless JWT — client deletes token
    # Phase 2+: invalidate session in Supabase
    return {}


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
)
async def refresh_token(request: RefreshRequest) -> RefreshResponse:
    """
    Exchange a refresh token for a new access token.
    Supabase handles token rotation.
    """
    try:
        adapter = get_supabase_adapter()
        result = await adapter.refresh_session(request.refresh_token)
        return RefreshResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result.get("expires_in", 3600),
        )
    except Exception as exc:
        _logger.error(f"Token refresh failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token. Please log in again.",
        ) from exc
