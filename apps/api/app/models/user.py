"""
COGNARC — User Pydantic Models
apps/api/app/models/user.py

T1.1: SkillState, BehavioralProfile, UserSettings, User models.
§17: extra="forbid" on all primary domain models. One module, one concern.
§08: MongoDB collection 'users'. auth_id FK → Supabase auth.users UUID.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Sub-models ────────────────────────────────────────────────


class SkillState(BaseModel):
    """Progress state for a single skill tree node."""

    model_config = ConfigDict(extra="forbid")

    current_node: str = Field(description="Active skill node ID.")
    node_progress: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Progress within current node (0–1)."
    )
    mastered_nodes: List[str] = Field(default_factory=list)
    unlocked_nodes: List[str] = Field(default_factory=list)
    locked_nodes: List[str] = Field(default_factory=list)


class BehavioralProfile(BaseModel):
    """Adaptive difficulty signals updated by the Adaptation engine."""

    model_config = ConfigDict(extra="forbid")

    difficulty_modifier: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="XP reward multiplier (0.5–2.0). Driven by boredom/frustration signals.",
    )
    preferred_quest_types: List[str] = Field(
        default_factory=list,
        description="Quest types the user prefers (theory/coding/debug/research/build).",
    )
    completion_rate_7d: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Rolling 7-day quest completion rate.",
    )
    mode: Literal["normal", "comeback", "boredom", "frustration"] = Field(
        default="normal",
        description="Current behavioral adaptation mode.",
    )
    avg_time_per_quest_min: float = Field(
        default=30.0,
        description="Rolling average quest completion time (minutes).",
    )
    boredom_signal: float = Field(
        default=0.0, ge=0.0, le=10.0, description="Boredom score 0–10."
    )
    frustration_signal: float = Field(
        default=0.0, ge=0.0, le=10.0, description="Frustration score 0–10."
    )


class UserSettings(BaseModel):
    """User-configurable preferences."""

    model_config = ConfigDict(extra="forbid")

    timezone: str = Field(default="UTC", description="IANA timezone string.")
    theme: Literal["dark", "light"] = Field(default="dark")
    daily_goal_quests: int = Field(default=3, ge=1, le=10)
    notifications_enabled: bool = Field(default=True)


# ── Primary Domain Model ──────────────────────────────────────


class User(BaseModel):
    """
    MongoDB 'users' collection document.
    §17: extra="forbid" — reject any undeclared fields.
    §08: auth_id is unique-indexed FK to Supabase auth.users.id.
    total_xp is cumulative and never decreases.
    """

    model_config = ConfigDict(extra="forbid")

    auth_id: str = Field(description="Supabase auth.users UUID. Unique index.")
    username: str = Field(description="Public display name.")
    email: EmailStr = Field(description="User email address.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Gamification
    level: int = Field(default=1, ge=1)
    total_xp: int = Field(default=0, ge=0, description="Cumulative XP — never decreases.")

    # Skill tree
    active_skill_tree: str = Field(
        default="AI Engineering",
        description="ID of the currently active skill tree.",
    )
    skill_state: Dict[str, SkillState] = Field(
        default_factory=dict,
        description="skill_tree_id → SkillState mapping per active tree.",
    )

    # AI adaptation
    behavioral_profile: BehavioralProfile = Field(
        default_factory=BehavioralProfile
    )

    # Preferences
    settings: UserSettings = Field(default_factory=UserSettings)

    # Optional profile extras
    avatar_url: Optional[str] = Field(default=None)
