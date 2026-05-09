"""
COGNARC — Quest Repository (MongoDB)
apps/api/app/repositories/mongo/quest_repository.py

T4.2: Full CRUD for MongoDB 'quests' collection.
§06: DB access ONLY. No business logic.
§08: Motor async driver. Indexes: (user_id, date) compound, status, created_at TTL.

Public API:
    create_quest(quest)                         → Quest
    get_quests_for_user_today(user_id, date)    → list[Quest]
    get_quest_by_id(quest_id)                   → Quest | None
    update_quest_status(quest_id, status)       → None
    get_recent_quests(user_id, days)            → list[Quest]
    ensure_indexes()                            → None
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.logger import get_logger
from app.db.mongodb import get_collection
from app.models.quest import Quest

_logger = get_logger("repository.quest")

COLLECTION_NAME = "quests"

# ── Helpers ───────────────────────────────────────────────────


def _get_col() -> AsyncIOMotorCollection:  # type: ignore[type-arg]
    return get_collection(COLLECTION_NAME)


def _doc_to_quest(doc: dict) -> Quest:
    """Convert a raw MongoDB document into a Quest domain model."""
    doc_copy = {k: v for k, v in doc.items() if k != "_id"}
    return Quest(**doc_copy)


def _log_op(op: str, duration_ms: float, extra: dict | None = None) -> None:
    payload: dict = {
        "collection": COLLECTION_NAME,
        "operation": op,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        payload.update(extra)
    _logger.info(f"repo.{op}", context=payload)


# ── Write Operations ──────────────────────────────────────────


async def create_quest(quest: Quest) -> Quest:
    """
    Insert a new quest document into MongoDB.
    Returns the persisted Quest domain model.
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = quest.model_dump()
    result = await col.insert_one(doc)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("create_quest", duration_ms, {"quest_id": quest.quest_id, "user_id": quest.user_id})

    stored = await col.find_one({"_id": result.inserted_id})
    if stored is None:
        raise RuntimeError("Quest document not found immediately after insert.")
    return _doc_to_quest(stored)


async def update_quest_status(quest_id: str, status: str) -> None:
    """
    Set the status field on a quest by its quest_id string.
    Sets completed_at if status = 'completed'.
    §06: Write-only. No return — caller owns the state machine.
    """
    col = _get_col()
    t0 = time.monotonic()

    update_fields: dict = {"status": status}
    if status == "completed":
        update_fields["completed_at"] = datetime.now(timezone.utc)

    await col.update_one(
        {"quest_id": quest_id},
        {"$set": update_fields},
    )

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("update_quest_status", duration_ms, {"quest_id": quest_id, "status": status})


# ── Read Operations ───────────────────────────────────────────


async def get_quests_for_user_today(user_id: str, target_date: date) -> List[Quest]:
    """
    Fetch all quests assigned to a user for a given calendar date.
    Uses the (user_id, date) compound index.
    Filters: date >= midnight UTC of target_date, < midnight UTC of next day.
    """
    col = _get_col()
    t0 = time.monotonic()

    day_start = datetime(
        target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc
    )
    day_end = day_start + timedelta(days=1)

    cursor = col.find(
        {
            "user_id": user_id,
            "date": {"$gte": day_start, "$lt": day_end},
        }
    ).sort("created_at", 1)

    quests: List[Quest] = []
    async for doc in cursor:
        quests.append(_doc_to_quest(doc))

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "get_quests_for_user_today",
        duration_ms,
        {"user_id": user_id, "date": str(target_date), "count": len(quests)},
    )
    return quests


async def get_quest_by_id(quest_id: str) -> Optional[Quest]:
    """
    Fetch a single quest by its quest_id string field (not MongoDB _id).
    Returns None if not found.
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = await col.find_one({"quest_id": quest_id})

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("get_quest_by_id", duration_ms, {"quest_id": quest_id, "found": doc is not None})

    if doc is None:
        return None
    return _doc_to_quest(doc)


async def get_recent_quests(user_id: str, days: int = 7) -> List[Quest]:
    """
    Fetch all quests for a user within the last N days.
    Used by quest generation service for dedup context (Phase 2+).
    """
    col = _get_col()
    t0 = time.monotonic()

    since = datetime.now(timezone.utc) - timedelta(days=days)

    cursor = col.find(
        {
            "user_id": user_id,
            "date": {"$gte": since},
        }
    ).sort("date", -1)

    quests: List[Quest] = []
    async for doc in cursor:
        quests.append(_doc_to_quest(doc))

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "get_recent_quests",
        duration_ms,
        {"user_id": user_id, "days": days, "count": len(quests)},
    )
    return quests


# ── Infrastructure ────────────────────────────────────────────


async def ensure_indexes() -> None:
    """
    T3.2: Apply MongoDB indexes for the 'quests' collection.
    Idempotent — safe to call on every app startup.
    §08: (user_id, date) compound, status, created_at TTL 30d.
    """
    col = _get_col()
    await col.create_index(
        [("user_id", 1), ("date", -1)],
        name="user_date_compound",
    )
    await col.create_index("status", name="status_idx")
    await col.create_index(
        "created_at",
        expireAfterSeconds=2_592_000,
        name="created_at_ttl_30d",
    )
    _logger.info("MongoDB indexes ensured", context={"collection": COLLECTION_NAME})
