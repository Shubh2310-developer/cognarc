"""
COGNARC — Unit Tests: Redis Cache Repository
apps/api/tests/unit/test_redis_cache.py

Phase 02 validation gate:
  • cache_quests / get_cached_quests round-trip (mocked Redis)
  • Cache miss returns None
  • set_streak_counter / get_streak_counter round-trip
  • Graceful no-op when Redis not configured
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.quest import EvaluationCriteria, Quest

# ── Fixtures ──────────────────────────────────────────────────

def _make_quest(quest_id: str = "q_abc123") -> Quest:
    return Quest(
        quest_id=quest_id,
        user_id="507f1f77bcf86cd799439011",
        date=datetime.now(timezone.utc),
        title="Test Quest",
        description="A test quest description.",
        type="coding",
        difficulty="easy",
        estimated_minutes=30,
        xp_reward=75,
        skill_node="python-basics",
        skill_tree="AI Engineering",
        evaluation_criteria=EvaluationCriteria(type="self_report"),
        created_at=datetime.now(timezone.utc),
    )


def _make_mock_redis(get_return=None) -> MagicMock:
    """Return a mock Redis client with async get/set/delete."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=get_return)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    return mock


# ── cache_quests / get_cached_quests ─────────────────────────

@pytest.mark.asyncio
async def test_cache_quests_stores_json():
    """cache_quests serializes quest list to JSON and calls Redis SET."""
    quests = [_make_quest("q_001"), _make_quest("q_002")]
    mock_redis = _make_mock_redis()

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import cache_quests
        await cache_quests("user123", quests, ttl=3600)

    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    key = call_args[0][0]
    stored_json = call_args[0][1]

    assert key == "quests:user123"
    parsed = json.loads(stored_json)
    assert len(parsed) == 2
    assert parsed[0]["quest_id"] == "q_001"


@pytest.mark.asyncio
async def test_get_cached_quests_hit():
    """get_cached_quests returns deserialized Quest list on cache hit."""
    quest = _make_quest("q_hit")
    serialized = json.dumps([quest.model_dump(mode="json")], default=str)

    mock_redis = _make_mock_redis(get_return=serialized)

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import get_cached_quests
        result = await get_cached_quests("user123")

    assert result is not None
    assert len(result) == 1
    assert result[0].quest_id == "q_hit"


@pytest.mark.asyncio
async def test_get_cached_quests_miss():
    """get_cached_quests returns None on cache miss."""
    mock_redis = _make_mock_redis(get_return=None)

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import get_cached_quests
        result = await get_cached_quests("user_no_cache")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_quests_corrupt_json():
    """get_cached_quests returns None (cache miss) on corrupt JSON."""
    mock_redis = _make_mock_redis(get_return="{{bad json}}")

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import get_cached_quests
        result = await get_cached_quests("user_corrupt")

    assert result is None


@pytest.mark.asyncio
async def test_invalidate_quest_cache():
    """invalidate_quest_cache calls Redis DELETE with correct key."""
    mock_redis = _make_mock_redis()

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import invalidate_quest_cache
        await invalidate_quest_cache("user789")

    mock_redis.delete.assert_called_once_with("quests:user789")


# ── Streak Counter ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_streak_counter():
    """set_streak_counter calls Redis SET with correct key and value."""
    mock_redis = _make_mock_redis()

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import set_streak_counter
        await set_streak_counter("user123", 7)

    mock_redis.set.assert_called_once()
    args = mock_redis.set.call_args[0]
    assert args[0] == "streak:user123"
    assert args[1] == 7


@pytest.mark.asyncio
async def test_get_streak_counter_hit():
    """get_streak_counter returns int on cache hit."""
    mock_redis = _make_mock_redis(get_return="14")

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import get_streak_counter
        result = await get_streak_counter("user123")

    assert result == 14


@pytest.mark.asyncio
async def test_get_streak_counter_miss():
    """get_streak_counter returns 0 on cache miss."""
    mock_redis = _make_mock_redis(get_return=None)

    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=mock_redis,
    ):
        from app.repositories.cache.redis_cache import get_streak_counter
        result = await get_streak_counter("user_no_streak")

    assert result == 0


# ── No-op when Redis unavailable ──────────────────────────────

@pytest.mark.asyncio
async def test_cache_noop_when_redis_none():
    """All cache ops are safe no-ops when _get_client returns None."""
    with patch(
        "app.repositories.cache.redis_cache._get_client",
        return_value=None,
    ):
        from app.repositories.cache.redis_cache import (
            cache_quests,
            get_cached_quests,
            get_streak_counter,
            set_streak_counter,
        )
        # None of these should raise
        await cache_quests("u", [_make_quest()], ttl=100)
        result = await get_cached_quests("u")
        counter = await get_streak_counter("u")
        await set_streak_counter("u", 5)

    assert result is None
    assert counter == 0
