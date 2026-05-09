"""
COGNARC — Streak Repository (MongoDB)
apps/api/app/repositories/mongo/streak_repository.py

T4.4: Get + upsert operations for MongoDB 'streaks' collection.
§06: DB access ONLY. No business logic.
§08: Motor async driver. One document per user. user_id unique index.
     MongoDB is source of truth. Redis is cache-only projection.

Public API:
    get_streak(user_id)            → Streak | None
    upsert_streak(user_id, streak) → Streak
    ensure_indexes()               → None
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from app.core.logger import get_logger
from app.db.mongodb import get_collection
from app.models.streak import Streak

_logger = get_logger("repository.streak")

COLLECTION_NAME = "streaks"

# ── Helpers ───────────────────────────────────────────────────


def _get_col():  # type: ignore[no-untyped-def]
    return get_collection(COLLECTION_NAME)


def _doc_to_streak(doc: dict) -> Streak:
    doc_copy = {k: v for k, v in doc.items() if k != "_id"}
    return Streak(**doc_copy)


def _log_op(op: str, duration_ms: float, extra: dict | None = None) -> None:
    payload: dict = {
        "collection": COLLECTION_NAME,
        "operation": op,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        payload.update(extra)
    _logger.info(f"repo.{op}", context=payload)


# ── Read Operations ───────────────────────────────────────────


async def get_streak(user_id: str) -> Optional[Streak]:
    """
    Fetch the streak document for a user.
    Returns None if no streak document exists (user has never completed a quest).
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = await col.find_one({"user_id": user_id})

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("get_streak", duration_ms, {"user_id": user_id, "found": doc is not None})

    if doc is None:
        return None
    return _doc_to_streak(doc)


# ── Write Operations ──────────────────────────────────────────


async def upsert_streak(user_id: str, streak: Streak) -> Streak:
    """
    Insert or replace the streak document for a user.
    Uses upsert=True with the user_id unique index.
    Returns the stored Streak model.
    §08: After upserting here, caller MUST also update Redis streak counter.
    """
    col = _get_col()
    t0 = time.monotonic()

    streak_doc = streak.model_dump()
    streak_doc["updated_at"] = datetime.now(timezone.utc)
    streak_doc["user_id"] = user_id

    result = await col.find_one_and_update(
        {"user_id": user_id},
        {"$set": streak_doc},
        upsert=True,
        return_document=True,
    )

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op(
        "upsert_streak",
        duration_ms,
        {
            "user_id": user_id,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
        },
    )

    # find_one_and_update with upsert=True returns the new doc
    if result is None:
        # This shouldn't happen with upsert=True but handle defensively
        stored = await col.find_one({"user_id": user_id})
        if stored is None:
            raise RuntimeError("Streak document not found after upsert.")
        return _doc_to_streak(stored)

    return _doc_to_streak(result)


# ── Infrastructure ────────────────────────────────────────────


async def ensure_indexes() -> None:
    """
    Apply MongoDB indexes for the 'streaks' collection.
    Idempotent — safe to call on every app startup.
    §08: user_id unique index (one streak doc per user).
    """
    col = _get_col()
    await col.create_index("user_id", unique=True, name="user_id_unique")
    _logger.info("MongoDB indexes ensured", context={"collection": COLLECTION_NAME})
