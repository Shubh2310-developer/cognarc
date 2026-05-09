"""
COGNARC — FastAPI Dependencies
apps/api/app/core/dependencies.py

T2.4: get_current_user() and require_admin() FastAPI dependencies.
§06: Used via Depends() in route handlers. Never inline auth logic.
§20: Role check for admin via JWT claims (role field in Supabase JWT).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.middleware.auth import (
    decode_supabase_jwt,
    extract_bearer_token,
    get_user_id_from_payload,
)


class AuthenticatedUser:
    """Container for the authenticated user context extracted from JWT."""

    def __init__(self, user_id: str, email: str, role: str = "authenticated") -> None:
        self.user_id = user_id
        self.email = email
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    FastAPI dependency: validate JWT and return AuthenticatedUser.

    Usage:
        @router.get("/me")
        async def me(user: AuthenticatedUser = Depends(get_current_user)):
            return user.user_id

    Raises:
        HTTPException 401 — if token absent, expired, or invalid.
    """
    authorization = request.headers.get("Authorization")
    token = extract_bearer_token(authorization)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_supabase_jwt(token)
    user_id = get_user_id_from_payload(payload)

    # Inject user_id into request state for logging middleware
    request.state.user_id = user_id

    return AuthenticatedUser(
        user_id=user_id,
        email=payload.get("email", ""),
        role=payload.get("role", "authenticated"),
    )


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """
    FastAPI dependency: require admin role.

    Usage:
        @router.delete("/users/{id}")
        async def delete_user(admin: AuthenticatedUser = Depends(require_admin)):
            ...

    Raises:
        HTTPException 403 — if user is not admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
