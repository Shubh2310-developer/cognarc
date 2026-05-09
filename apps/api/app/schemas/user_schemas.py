"""
COGNARC — User Request/Response Schemas
apps/api/app/schemas/user_schemas.py

T2.1: UserCreateRequest, UserUpdateRequest, UserResponse, UserProfileResponse.
§06: Schemas are the API boundary layer. Separate from domain models.
§17: extra="forbid" on request schemas. Never duplicate types outside shared-types.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import BehavioralProfile, SkillState, UserSettings


# ── Request Schemas ───────────────────────────────────────────


class UserCreateRequest(BaseModel):
    """POST /auth/register — create a new user profile in MongoDB."""

    model_config = ConfigDict(extra="forbid")

    auth_id: str = Field(description="Supabase auth.users UUID.")
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    active_skill_tree: str = Field(default="AI Engineering")
    timezone: str = Field(default="UTC")


class UserUpdateRequest(BaseModel):
    """PATCH /users/me — partial profile update."""

    model_config = ConfigDict(extra="forbid")

    username: Optional[str] = Field(default=None, min_length=2, max_length=50)
    avatar_url: Optional[str] = None
    settings: Optional[UserSettings] = None
    active_skill_tree: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────


class SkillStateResponse(BaseModel):
    """Serialized skill state for a single tree."""

    current_node: str
    node_progress: float
    mastered_nodes: List[str]
    unlocked_nodes: List[str]
    locked_nodes: List[str]


class UserResponse(BaseModel):
    """
    Public user profile — returned from GET /users/me.
    Includes id (MongoDB _id stringified) + all non-sensitive fields.
    """

    id: str = Field(description="MongoDB _id as string.")
    auth_id: str
    username: str
    email: str
    avatar_url: Optional[str]
    level: int
    total_xp: int
    active_skill_tree: str
    skill_state: Dict[str, SkillStateResponse] = Field(default_factory=dict)
    behavioral_profile: BehavioralProfile
    settings: UserSettings
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    """
    Minimal public-facing profile for leaderboard/social viewing.
    GET /users/{id}/profile — omits behavioral_profile and settings.
    """

    id: str
    username: str
    avatar_url: Optional[str]
    level: int
    total_xp: int
    active_skill_tree: str
