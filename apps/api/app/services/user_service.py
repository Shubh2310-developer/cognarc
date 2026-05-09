"""
COGNARC — User Service
apps/api/app/services/user_service.py

T3.6: Orchestrates user creation on first login.
§06: Services call repositories only. No direct DB access. No AI calls.
Pattern: get-or-create on first JWT validation.
"""
from __future__ import annotations

from typing import Optional

from app.core.logger import get_logger
from app.models.user_model import UserDocument, UserResponse, UserUpdateRequest
from app.repositories.mongo import user_repository

_logger = get_logger("service.user")


async def get_or_create_user(auth_id: str, email: str) -> UserResponse:
    """
    Fetch user by auth_id or create a new one on first login.

    This is called by GET /users/me after JWT validation.
    Implements the 'lazy user creation' pattern — no user row until first API call.

    Args:
        auth_id: Supabase auth.users UUID (from JWT 'sub' claim).
        email: User email from JWT claims.

    Returns:
        UserResponse: The user profile.
    """
    user = await user_repository.get_user_by_auth_id(auth_id)
    if user is not None:
        return user

    _logger.info("Creating user on first login", context={"auth_id": auth_id})
    new_user = UserDocument(
        auth_id=auth_id,
        email=email,
        display_name=_extract_name_from_email(email),
    )
    return await user_repository.create_user(new_user)


async def get_user_profile(auth_id: str) -> Optional[UserResponse]:
    """Fetch user profile by auth_id. Returns None if not found."""
    return await user_repository.get_user_by_auth_id(auth_id)


async def update_user_profile(
    auth_id: str,
    update: UserUpdateRequest,
) -> Optional[UserResponse]:
    """Update user profile fields. Returns None if user not found."""
    return await user_repository.update_user(auth_id, update)


def _extract_name_from_email(email: str) -> str:
    """Derive a default display name from email local part."""
    local = email.split("@")[0]
    return local.replace(".", " ").replace("_", " ").replace("-", " ").title()[:50]
