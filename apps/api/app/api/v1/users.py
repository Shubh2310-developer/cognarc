"""
COGNARC — Users API Routes
apps/api/app/api/v1/users.py

T3.7: GET /users/me, PATCH /users/me, GET /users/{id}/profile
§06: Routes parse requests, call services, return Pydantic schemas. NO business logic.
§20: All routes require valid JWT via Depends(get_current_user).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import AuthenticatedUser, get_current_user
from app.models.user_model import UserResponse, UserUpdateRequest
from app.services import user_service

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    responses={
        200: {"description": "User profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserResponse:
    """
    Fetch the authenticated user's profile.
    Creates the user document on first call (lazy creation).
    """
    user = await user_service.get_or_create_user(
        auth_id=current_user.user_id,
        email=current_user.email,
    )
    return user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    responses={
        200: {"description": "Updated user profile"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
    },
)
async def update_me(
    update_request: UserUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserResponse:
    """
    Update editable fields of the authenticated user's profile.
    Only provided (non-null) fields are updated.
    """
    user = await user_service.update_user_profile(
        auth_id=current_user.user_id,
        update=update_request,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    return user


@router.get(
    "/{user_id}/profile",
    response_model=UserResponse,
    summary="Get public user profile by ID",
    responses={
        200: {"description": "Public user profile"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
    },
)
async def get_user_profile(
    user_id: str,
    _: AuthenticatedUser = Depends(get_current_user),  # auth required but ID unused
) -> UserResponse:
    """
    Get a specific user's public profile by their auth_id.
    Requires authentication but does not require admin role.
    """
    user = await user_service.get_user_profile(auth_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
