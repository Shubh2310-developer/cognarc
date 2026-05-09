"""
COGNARC — Quest Pydantic Model
apps/api/app/models/quest.py

T1.2: EvaluationCriteria and Quest models.
§17: extra="forbid" on primary domain model. No business logic.
§08: MongoDB collection 'quests'.
     embedding field scaffolded (empty) — BGE-small populated in Phase 2.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Sub-models ────────────────────────────────────────────────


class EvaluationCriteria(BaseModel):
    """Criteria used to evaluate a quest submission."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["code_submission", "self_report", "theory_qa"] = Field(
        description="Evaluation method for this quest."
    )
    test_cases: int = Field(
        default=0,
        ge=0,
        description="Number of test cases for code_submission type.",
    )
    pass_threshold: float = Field(
        default=0.67,
        ge=0.0,
        le=1.0,
        description="Minimum pass fraction (e.g. 0.67 = 2/3 tests must pass).",
    )


# ── Primary Domain Model ──────────────────────────────────────


class Quest(BaseModel):
    """
    MongoDB 'quests' collection document.
    §17: extra="forbid" — reject any undeclared fields.
    §08: Indexes — (user_id, date) compound + status + created_at TTL 30d.
    quest_id: q_<uuid4_short> — human-readable unique identifier.
    embedding: scaffolded empty list — BGE-small 384-dim populated Phase 2.
    """

    model_config = ConfigDict(extra="forbid")

    quest_id: str = Field(description="Human-readable ID: q_<uuid4_short>.")
    user_id: str = Field(description="MongoDB user ObjectId as string.")
    date: datetime = Field(description="The date this quest was assigned (UTC midnight).")
    title: str = Field(description="Short quest title.")
    description: str = Field(default="", description="Detailed quest description.")
    type: Literal["theory", "coding", "debug", "research", "build"] = Field(
        description="Quest category."
    )
    difficulty: Literal["easy", "medium", "hard", "boss"] = Field(
        description="Difficulty tier."
    )
    estimated_minutes: int = Field(
        default=30, ge=5, le=480, description="Estimated completion time in minutes."
    )
    xp_reward: int = Field(ge=0, description="XP granted on completion.")
    skill_node: str = Field(description="Skill tree node this quest maps to.")
    skill_tree: str = Field(description="Skill tree ID (e.g. 'AI Engineering').")
    evaluation_criteria: EvaluationCriteria = Field(
        description="How submissions are evaluated."
    )
    hints: List[str] = Field(default_factory=list, description="Optional hints.")
    embedding: List[float] = Field(
        default_factory=list,
        description="BGE-small-en-v1.5 384-dim embedding. Populated Phase 2. Empty in MVP.",
    )
    status: Literal["pending", "completed", "skipped", "failed"] = Field(
        default="pending"
    )
    generated_by: Literal["groq", "phi2", "cached"] = Field(
        default="groq", description="Which provider generated this quest."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = Field(
        default=None, description="UTC timestamp when quest was completed."
    )
