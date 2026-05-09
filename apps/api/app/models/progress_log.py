"""
COGNARC — ProgressLog Pydantic Model
apps/api/app/models/progress_log.py

T1.3: ProgressLog model for MongoDB 'progress_logs' collection.
§17: extra="forbid". No business logic.
§08: Indexes — (user_id, completed_at) compound + archive TTL 90d.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProgressLog(BaseModel):
    """
    MongoDB 'progress_logs' collection document.
    Immutable record created when a quest is completed or evaluated.
    §08: Archive TTL index 90d — old records are auto-pruned.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(description="MongoDB user ObjectId as string.")
    quest_id: str = Field(description="Quest identifier (quest_id field, not _id).")
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of completion/evaluation.",
    )
    xp_earned: int = Field(ge=0, description="XP awarded after evaluation.")
    time_taken_min: int = Field(
        ge=0, description="Time taken by user to complete the quest in minutes."
    )
    evaluation_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Evaluation score 0–100. None if self-reported.",
    )
    evaluation_method: str = Field(
        default="self_report",
        description="How the quest was evaluated (self_report | test_cases | ai_review).",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
