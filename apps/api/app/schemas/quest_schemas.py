"""
COGNARC — Quest Request/Response Schemas
apps/api/app/schemas/quest_schemas.py

T2.2: QuestResponse, QuestListResponse, QuestStatusUpdateRequest.
§06: Schema layer only. No business logic.
§17: extra="forbid" on all request schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.quest import EvaluationCriteria


# ── Request Schemas ───────────────────────────────────────────


class QuestStatusUpdateRequest(BaseModel):
    """
    POST /quests/{id}/evaluate or /quests/{id}/skip.
    Used to mark a quest completed/skipped and log result.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "skipped", "failed"] = Field(
        description="New status to set on the quest."
    )
    time_taken_min: int = Field(
        default=0,
        ge=0,
        description="Time user spent on the quest (minutes).",
    )
    evaluation_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Score from evaluator (0–100). None for self-reported.",
    )
    self_reported: bool = Field(
        default=True,
        description="True if user self-reported completion (no test cases).",
    )


class QuestGenerateRequest(BaseModel):
    """POST /quests/generate — trigger AI quest generation."""

    model_config = ConfigDict(extra="forbid")

    skill_tree: Optional[str] = Field(
        default=None,
        description="Override active skill tree for generation.",
    )
    count: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Number of quests to generate.",
    )


# ── Response Schemas ──────────────────────────────────────────


class QuestResponse(BaseModel):
    """
    Single quest returned by the API.
    Maps to Quest domain model + stringified MongoDB _id.
    """

    id: str = Field(description="MongoDB _id as string.")
    quest_id: str
    user_id: str
    date: datetime
    title: str
    description: str
    type: Literal["theory", "coding", "debug", "research", "build"]
    difficulty: Literal["easy", "medium", "hard", "boss"]
    estimated_minutes: int
    xp_reward: int
    skill_node: str
    skill_tree: str
    evaluation_criteria: EvaluationCriteria
    hints: List[str]
    status: Literal["pending", "completed", "skipped", "failed"]
    generated_by: Literal["groq", "phi2", "cached"]
    created_at: datetime
    completed_at: Optional[datetime]


class QuestListResponse(BaseModel):
    """Response wrapper for a list of quests (GET /quests/today)."""

    quests: List[QuestResponse]
    total: int
    date: str = Field(description="Date these quests are assigned to (YYYY-MM-DD).")
