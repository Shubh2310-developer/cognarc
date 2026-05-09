"""
COGNARC — User Repository (MongoDB)
apps/api/app/repositories/mongo/user_repository.py

T4.1: Full CRUD operations on MongoDB 'users' collection.
§06: DB access ONLY. No business logic. No service calls.
§08: Motor async driver. Indexes: auth_id (unique), level.

Public API:
    create_user(user)              → User
    get_user_by_auth_id(auth_id)   → User | None
    get_user_by_id(user_id)        → User | None
    update_user(user_id, updates)  → User
    update_skill_state(user_id, tree, state) → None
    ensure_indexes()               → None
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.logger import get_logger
from app.db.mongodb import get_collection
from app.models.user import SkillState, User

_logger = get_logger("repository.user")

COLLECTION_NAME = "users"

# ── Helpers ───────────────────────────────────────────────────


def _get_col() -> AsyncIOMotorCollection:  # type: ignore[type-arg]
    return get_collection(COLLECTION_NAME)


def _doc_to_user(doc: dict) -> User:
    """
    Convert a raw MongoDB document dict into a User domain model.
    MongoDB stores _id as ObjectId; we exclude it from the model
    and return it separately when needed via the schemas layer.
    """
    doc_copy = {k: v for k, v in doc.items() if k != "_id"}
    return User(**doc_copy)


def _log_op(op: str, duration_ms: float, extra: dict | None = None) -> None:
    """Structured repository operation log per §08 observability requirement."""
    payload: dict = {
        "collection": COLLECTION_NAME,
        "operation": op,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        payload.update(extra)
    _logger.info(f"repo.{op}", context=payload)


# ── Write Operations ──────────────────────────────────────────


async def create_user(user: User) -> User:
    """
    Insert a new user document into MongoDB.
    §08: Raises pymongo.errors.DuplicateKeyError if auth_id already exists.
    Returns the created User with all default fields populated.
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = user.model_dump()
    result = await col.insert_one(doc)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("create_user", duration_ms, {"auth_id": user.auth_id})

    # Re-fetch to ensure we return exactly what was stored
    stored = await col.find_one({"_id": result.inserted_id})
    if stored is None:
        raise RuntimeError("User document not found immediately after insert.")
    return _doc_to_user(stored)


async def update_user(user_id: str, updates: dict) -> User:
    """
    Partially update a user by MongoDB _id.
    `updates` is a dict of field→value pairs to $set.
    Automatically sets `updated_at` timestamp.
    Raises ValueError if user not found.
    """
    col = _get_col()
    t0 = time.monotonic()

    updates["updated_at"] = datetime.now(timezone.utc)

    doc = await col.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
        return_document=True,  # Return updated document
    )

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("update_user", duration_ms, {"user_id": user_id})

    if doc is None:
        raise ValueError(f"User with id={user_id} not found.")
    return _doc_to_user(doc)


async def update_skill_state(user_id: str, tree: str, state: SkillState) -> None:
    """
    Update the SkillState for a specific skill tree on a user.
    Uses MongoDB dot-notation to update the nested skill_state map.
    §06: No return value — write-only. Caller owns the state machine.
    """
    col = _get_col()
    t0 = time.monotonic()

    field = f"skill_state.{tree}"
    await col.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                field: state.model_dump(),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("update_skill_state", duration_ms, {"user_id": user_id, "tree": tree})


# ── Read Operations ───────────────────────────────────────────


async def get_user_by_auth_id(auth_id: str) -> Optional[User]:
    """
    Fetch a user by Supabase auth_id (UUID).
    Uses the unique auth_id index. Returns None if not found.
    """
    col = _get_col()
    t0 = time.monotonic()

    doc = await col.find_one({"auth_id": auth_id})

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("get_user_by_auth_id", duration_ms, {"found": doc is not None})

    if doc is None:
        return None
    return _doc_to_user(doc)


async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Fetch a user by MongoDB _id.
    Returns None if not found or if user_id is an invalid ObjectId.
    """
    col = _get_col()
    t0 = time.monotonic()

    try:
        oid = ObjectId(user_id)
    except Exception:
        _logger.warning(f"Invalid ObjectId format: {user_id}")
        return None

    doc = await col.find_one({"_id": oid})

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("get_user_by_id", duration_ms, {"found": doc is not None})

    if doc is None:
        return None
    return _doc_to_user(doc)


# ── Infrastructure ────────────────────────────────────────────


async def ensure_indexes() -> None:
    """
    T3.1: Apply MongoDB indexes for the 'users' collection.
    Idempotent — safe to call on every app startup.
    §08: auth_id (unique), level.
    """
    col = _get_col()
    await col.create_index("auth_id", unique=True, name="auth_id_unique")
    await col.create_index("level", name="level_idx")
    _logger.info("MongoDB indexes ensured", context={"collection": COLLECTION_NAME})
