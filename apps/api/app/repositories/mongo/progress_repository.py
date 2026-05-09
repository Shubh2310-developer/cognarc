"""
COGNARC — Progress Log Repository (MongoDB)
apps/api/app/repositories/mongo/progress_repository.py

T4.3: Create + read operations for MongoDB 'progress_logs' collection.
§06: DB access ONLY. No business logic.
§08: Motor async driver. Indexes: (user_id, completed_at) compound + TTL 90d.

Public API:
    create_log(log)                          → ProgressLog
    get_logs_for_user(user_id, limit)        → list[ProgressLog]
    get_completion_rate_7d(user_id)          → float
    ensure_indexes()                         → None
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.logger import get_logger
from app.db.mongodb import get_collection
from app.models.progress_log import ProgressLog

_logger = get_logger("repository.progress")

COLLECTION_NAME = "progress_logs"

# ── Helpers ───────────────────────────────────────────────────


def _get_col():  # type: ignore[no-untyped-def]
    return get_collection(COLLECTION_NAME)


def _doc_to_log(doc: dict) -> ProgressLog:
    doc_copy = {k: v for k, v in doc.items() if k != "_id"}
    return ProgressLog(**doc_copy)


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


async def create_log(log: ProgressLog) -> ProgressLog:
    """
    Insert a new progress log document.
    §08: Immutable insert. Never update or delete progress logs.
    Returns the persisted ProgressLog model.
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = log.model_dump()
    result = await col.insert_one(doc)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "create_log",
        duration_ms,
        {"user_id": log.user_id, "quest_id": log.quest_id, "xp_earned": log.xp_earned},
    )

    stored = await col.find_one({"_id": result.inserted_id})
    if stored is None:
        raise RuntimeError("ProgressLog not found immediately after insert.")
    return _doc_to_log(stored)


# ── Read Operations ───────────────────────────────────────────


async def get_logs_for_user(user_id: str, limit: int = 20) -> List[ProgressLog]:
    """
    Fetch the most recent N progress log entries for a user.
    Uses the (user_id, completed_at) compound index.
    Returns sorted newest-first.
    """
    col = _get_col()
    t0 = time.monotonic()

    cursor = (
        col.find({"user_id": user_id})
        .sort("completed_at", -1)
        .limit(limit)
    )

    logs: List[ProgressLog] = []
    async for doc in cursor:
        logs.append(_doc_to_log(doc))

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "get_logs_for_user",
        duration_ms,
        {"user_id": user_id, "limit": limit, "count": len(logs)},
    )
    return logs


async def get_completion_rate_7d(user_id: str) -> float:
    """
    Calculate the quest completion rate over the last 7 days.
    completion_rate = completed_count / total_count (excluding 'pending').
    Returns 0.0 if no quests exist in the period.

    Uses MongoDB aggregation pipeline on progress_logs.
    The compound index (user_id, completed_at) optimises this query.
    """
    col = _get_col()
    t0 = time.monotonic()

    since = datetime.now(timezone.utc) - timedelta(days=7)

    # Count completed logs in last 7 days
    completed_count = await col.count_documents(
        {
            "user_id": user_id,
            "completed_at": {"$gte": since},
        }
    )

    # Cross-reference quest collection for total assigned quests in 7d
    # (quests with status != pending would mean attempted)
    # For simplicity in MVP: completion_rate = logs / max(logs + skipped, 1)
    # Skipped quests are also logged — check evaluation_method for skip
    from app.db.mongodb import get_collection as _get_collection_raw

    quests_col = _get_collection_raw("quests")
    total_attempted = await quests_col.count_documents(
        {
            "user_id": user_id,
            "date": {"$gte": since},
            "status": {"$in": ["completed", "skipped", "failed"]},
        }
    )

    rate = completed_count / max(total_attempted, 1)
    rate = min(rate, 1.0)  # Clamp to 1.0

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "get_completion_rate_7d",
        duration_ms,
        {"user_id": user_id, "completed": completed_count, "total": total_attempted, "rate": rate},
    )
    return rate


# ── Infrastructure ────────────────────────────────────────────


async def ensure_indexes() -> None:
    """
    T3.3 + T3.4: Apply MongoDB indexes for 'progress_logs' collection.
    Idempotent — safe to call on every app startup.
    §08: (user_id, completed_at) compound + completed_at TTL 90d.
    """
    col = _get_col()
    await col.create_index(
        [("user_id", 1), ("completed_at", -1)],
        name="user_completed_at_compound",
    )
    await col.create_index(
        "completed_at",
        expireAfterSeconds=7_776_000,
        name="completed_at_ttl_90d",
    )
    _logger.info("MongoDB indexes ensured", context={"collection": COLLECTION_NAME})
