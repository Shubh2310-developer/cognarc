"""
COGNARC — Progress Request/Response Schemas
apps/api/app/schemas/progress_schemas.py

T2.3: ProgressLogRequest, ProgressLogResponse, StreakResponse.
§06: Schema layer only. No business logic.
§17: extra="forbid" on request schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request Schemas ───────────────────────────────────────────


class ProgressLogRequest(BaseModel):
    """
    Internal schema used by services to record quest completion.
    NOT directly exposed as an HTTP endpoint — used by evaluation_service.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str
    quest_id: str
    xp_earned: int = Field(ge=0)
    time_taken_min: int = Field(ge=0)
    evaluation_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    evaluation_method: str = Field(default="self_report")


# ── Response Schemas ──────────────────────────────────────────


class ProgressLogResponse(BaseModel):
    """Serialized progress log entry returned from API."""

    id: str = Field(description="MongoDB _id as string.")
    user_id: str
    quest_id: str
    completed_at: datetime
    xp_earned: int
    time_taken_min: int
    evaluation_score: Optional[float]
    evaluation_method: str
    created_at: datetime


class StreakResponse(BaseModel):
    """
    Current streak state — returned alongside user or gamification responses.
    Mirrors Streak domain model for API consumption.
    """

    user_id: str
    current_streak: int
    longest_streak: int
    last_completion_date: Optional[str] = Field(
        description="ISO date string YYYY-MM-DD or null."
    )
    shield_count: int


class CompletionRateResponse(BaseModel):
    """Response for 7-day completion rate analytics."""

    user_id: str
    completion_rate_7d: float = Field(ge=0.0, le=1.0)
    quests_completed: int
    quests_total: int
    period_days: int = 7
