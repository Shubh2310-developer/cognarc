"""
COGNARC — User Pydantic Model
apps/api/app/models/user_model.py

T3.4: Pydantic model with all fields per §08 schema.
§17: One class per file. No business logic in models.
§08: MongoDB collection: 'users'.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Enums as Literals (no Enum class needed in Pydantic v2) ───

QuestType = str  # theory | coding | debug | build | research
SkillStatus = str  # locked | available | in_progress | mastered


# ── Sub-models ────────────────────────────────────────────────

class BehavioralProfile(BaseModel):
    """Adaptive difficulty signals. Updated by the Adaptation engine."""

    difficulty_modifier: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Multiplier applied to XP rewards. Range 0.5–2.0.",
    )
    completion_rate_7d: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Quest completion rate over last 7 days.",
    )
    avg_time_per_quest_min: float = Field(
        default=30.0,
        description="Rolling average time to complete a quest in minutes.",
    )
    preferred_quest_types: List[QuestType] = Field(
        default_factory=list,
        description="Quest types the user has shown preference for.",
    )
    boredom_signal: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Boredom score 0–10. High → increase difficulty.",
    )
    frustration_signal: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Frustration score 0–10. High → decrease difficulty.",
    )


class UserSettings(BaseModel):
    """User-configurable preferences."""

    timezone: str = Field(default="UTC", description="IANA timezone string.")
    daily_goal_quests: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Target quests per day.",
    )
    notifications_enabled: bool = Field(default=True)
    theme: str = Field(default="dark", pattern="^(dark|light)$")


class StreakState(BaseModel):
    """Streak counters — mirrored from Redis; MongoDB is source of truth."""

    current_streak: int = Field(default=0, ge=0)
    longest_streak: int = Field(default=0, ge=0)
    last_completion_date: Optional[str] = Field(
        default=None,
        description="ISO date YYYY-MM-DD of last quest completion.",
    )
    shield_count: int = Field(
        default=0,
        ge=0,
        description="Streak shield count. Phase 3 feature.",
    )


# ── Main User Model ───────────────────────────────────────────

class UserDocument(BaseModel):
    """
    MongoDB 'users' collection document.
    §08: auth_id is FK to Supabase auth.users UUID.
    """

    auth_id: str = Field(description="Supabase auth.users UUID. Unique index.")
    email: EmailStr = Field(description="User email address.")
    display_name: str = Field(default="", description="Public display name.")
    avatar_url: Optional[str] = Field(default=None)

    # Gamification state
    level: int = Field(default=1, ge=1)
    total_xp: int = Field(default=0, ge=0)

    # Skill tree
    active_skill_tree: str = Field(
        default="python-fundamentals",
        description="ID of the currently active skill tree.",
    )
    skill_state: Dict[str, SkillStatus] = Field(
        default_factory=dict,
        description="DAG node ID → status mapping.",
    )

    # AI adaptation
    behavioral_profile: BehavioralProfile = Field(
        default_factory=BehavioralProfile
    )

    # Streak — synced with Redis
    streak: StreakState = Field(default_factory=StreakState)

    # User preferences
    settings: UserSettings = Field(default_factory=UserSettings)

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ── Response Schemas ──────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user profile — returned from GET /users/me. No secrets."""

    id: str  # MongoDB _id as string
    auth_id: str
    email: str
    display_name: str
    avatar_url: Optional[str]
    level: int
    total_xp: int
    active_skill_tree: str
    streak: StreakState
    settings: UserSettings
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseModel):
    """PATCH /users/me request body. All fields optional."""

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    settings: Optional[UserSettings] = None
