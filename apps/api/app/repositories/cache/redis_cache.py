"""
COGNARC — Redis Cache Repository
apps/api/app/repositories/cache/redis_cache.py

T4.5: Quest caching + streak counter operations via Upstash Redis.
§08: Redis is cache-ONLY. MongoDB is source of truth.
     Redis MUST NOT diverge from MongoDB on critical fields (XP, streak).
§08: Use upstash-redis REST client for HTTP-based async access.

Key patterns:
    quests:{user_id}            → JSON list of Quest objects (TTL 24h)
    streak:{user_id}            → int streak counter (TTL 48h)

Public API:
    cache_quests(user_id, quests, ttl)    → None
    get_cached_quests(user_id)            → list[Quest] | None
    get_streak_counter(user_id)           → int
    set_streak_counter(user_id, count)    → None
    invalidate_quest_cache(user_id)       → None
"""
from __future__ import annotations

import json
import time
from typing import List, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.models.quest import Quest

_logger = get_logger("repository.cache.redis")

# ── Key Helpers ───────────────────────────────────────────────

_QUEST_KEY_PREFIX = "quests"
_STREAK_KEY_PREFIX = "streak"
_DEFAULT_QUEST_TTL = 86_400    # 24 hours
_DEFAULT_STREAK_TTL = 172_800  # 48 hours


def _quest_key(user_id: str) -> str:
    return f"{_QUEST_KEY_PREFIX}:{user_id}"


def _streak_key(user_id: str) -> str:
    return f"{_STREAK_KEY_PREFIX}:{user_id}"


# ── Client Factory ────────────────────────────────────────────


def _get_client():  # type: ignore[no-untyped-def]
    """
    Return an Upstash Redis async HTTP client.
    Uses REST API — no persistent connection, works in serverless.
    Falls back to None if not configured (dev environments without Redis).
    """
    try:
        from upstash_redis import AsyncRedis  # type: ignore[import]

        url = settings.UPSTASH_REDIS_REST_URL
        token = settings.UPSTASH_REDIS_REST_TOKEN

        if not url or not token:
            _logger.warning("Upstash Redis not configured — cache operations will be no-ops.")
            return None

        return AsyncRedis(url=url, token=token)
    except ImportError:
        _logger.warning("upstash-redis not installed — cache operations will be no-ops.")
        return None


def _log_op(op: str, duration_ms: float, extra: dict | None = None) -> None:
    payload: dict = {
        "store": "redis",
        "operation": op,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        payload.update(extra)
    _logger.info(f"cache.{op}", context=payload)


# ── Quest Cache ───────────────────────────────────────────────


async def cache_quests(
    user_id: str,
    quests: List[Quest],
    ttl: int = _DEFAULT_QUEST_TTL,
) -> None:
    """
    Store a list of Quest objects in Redis as JSON.
    Key: quests:{user_id}, TTL: 24h by default.
    §08: Quest generation result is cached after MongoDB write.
          Cache must be invalidated on quest status change.
    """
    redis = _get_client()
    if redis is None:
        return

    t0 = time.monotonic()
    key = _quest_key(user_id)

    serialized = json.dumps(
        [q.model_dump(mode="json") for q in quests],
        default=str,
    )

    await redis.set(key, serialized, ex=ttl)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("cache_quests", duration_ms, {"user_id": user_id, "count": len(quests), "ttl": ttl})


async def get_cached_quests(user_id: str) -> Optional[List[Quest]]:
    """
    Retrieve cached quests for a user from Redis.
    Returns None if cache miss or Redis unavailable.
    Target: <80ms (warm Redis hit per §08 performance target).
    """
    redis = _get_client()
    if redis is None:
        return None

    t0 = time.monotonic()
    key = _quest_key(user_id)

    raw = await redis.get(key)

    duration_ms = (time.monotonic() - t0) * 1000
    hit = raw is not None

    _log_op("get_cached_quests", duration_ms, {"user_id": user_id, "hit": hit})

    if not hit or raw is None:
        return None

    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return [Quest(**item) for item in data]
    except Exception as exc:
        _logger.warning(
            "Failed to deserialize cached quests — treating as cache miss.",
            context={"user_id": user_id, "error": str(exc)},
        )
        return None


async def invalidate_quest_cache(user_id: str) -> None:
    """
    Delete the quest cache for a user.
    Call after quest status change or new generation.
    """
    redis = _get_client()
    if redis is None:
        return

    t0 = time.monotonic()
    key = _quest_key(user_id)
    await redis.delete(key)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("invalidate_quest_cache", duration_ms, {"user_id": user_id})


# ── Streak Counter ────────────────────────────────────────────


async def get_streak_counter(user_id: str) -> int:
    """
    Retrieve the cached streak counter for a user.
    Returns 0 on cache miss (caller should fall back to MongoDB).
    §08: This is a cache projection. MongoDB is the source of truth.
    """
    redis = _get_client()
    if redis is None:
        return 0

    t0 = time.monotonic()
    key = _streak_key(user_id)
    value = await redis.get(key)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("get_streak_counter", duration_ms, {"user_id": user_id, "hit": value is not None})

    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


async def set_streak_counter(user_id: str, count: int) -> None:
    """
    Cache the streak counter for a user.
    TTL: 48h. Counter is refreshed on every quest completion.
    §08: Call this AFTER upserting MongoDB streak document.
    """
    redis = _get_client()
    if redis is None:
        return

    t0 = time.monotonic()
    key = _streak_key(user_id)
    await redis.set(key, count, ex=_DEFAULT_STREAK_TTL)

    duration_ms = (time.monotonic() - t0) * 1000
    _log_op("set_streak_counter", duration_ms, {"user_id": user_id, "count": count})
