"""
COGNARC — Streak Pydantic Model
apps/api/app/models/streak.py

T1.4: Streak model for MongoDB 'streaks' collection.
§17: extra="forbid". No business logic.
§08: user_id is unique-indexed. Redis streak counter is a cache projection.
     MongoDB is the source of truth — Redis MUST NOT diverge on streak values.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Streak(BaseModel):
    """
    MongoDB 'streaks' collection document.
    One document per user. Upserted on every quest completion.
    §08: Redis streak counter is cache-only. This is the source of truth.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(description="MongoDB user ObjectId as string. Unique index.")
    current_streak: int = Field(
        default=0, ge=0, description="Consecutive active days."
    )
    longest_streak: int = Field(
        default=0, ge=0, description="Historical maximum streak."
    )
    last_completion_date: Optional[date] = Field(
        default=None,
        description="Calendar date (UTC) of the most recent quest completion.",
    )
    shield_count: int = Field(
        default=0,
        ge=0,
        description="Streak shield tokens. Phase 3 feature — scaffold only.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
