"""
COGNARC — Quest Generation Service
apps/api/app/services/quest_service.py

T5.1: Full quest generation pipeline — context → AI → parse → validate → store → cache.
T5.2: get_today_quests(), skip_quest() — cache-first read and skip recording.

§06: Service layer. Calls repositories + AI adapter. No direct DB access.
§07: AI called ONLY through the ai_services adapter interface (generate_quests()).
     Never import ai_services modules directly in the service layer.
§16: AI failure is non-fatal. Fallback returns yesterday's cache cleanly.
§21: Quest generation rate-limited to 5/day at the router layer.

Pipeline (T5.1):
    1. Check Redis cache → return if HIT
    2. Build context (quest_context_builder)
    3. Call generate_quests() from ai_services
    4. Build Quest domain models from ParsedQuest
    5. Persist to MongoDB (quest_repository.create_many)
    6. Cache in Redis (redis_cache.cache_quests, TTL 24h)
    7. Return quest list

Error handling:
    - ValueError/Exception from AI pipeline → log → return fallback quests
    - Fallback = yesterday's cached quests from Redis or MongoDB
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, date as date_type
from typing import List, Optional

from app.core.logger import get_logger
from app.models.quest import Quest, EvaluationCriteria
from app.models.user import User
from app.models.progress_log import ProgressLog
from app.repositories.mongo import quest_repository, progress_repository, user_repository
from app.repositories.cache import redis_cache
from app.services.quest_context_builder import build_quest_context

_logger = get_logger("service.quest")

# ── AI Adapter Interface ──────────────────────────────────────
# §07: Import ai_services at function-call time to avoid circular imports
# and to ensure ai-services remains strictly isolated.


def _call_ai_generate(context: dict) -> list:
    """
    Thin adapter call to ai_services.generate_quests().
    §07: This is the ONLY place quest service touches ai_services.
    Raises ValueError on parse/validation failure.
    """
    from ai_services import generate_quests  # §07: isolated import
    return generate_quests(context)


# ── Quest Document Builder ────────────────────────────────────


def _build_quest_doc(parsed, user: User, target_date: datetime) -> Quest:
    """
    Convert a ParsedQuest (from ai_services) into a Quest domain model
    suitable for MongoDB insertion.

    §16: xp_reward from AI output is ADVISORY — it's been validated by
         quest_validator.py to be in the allowed range for the difficulty.
         The deterministic XP engine (calculate_xp) is used on evaluation.
    """
    from ai_services.parsers.quest_output_parser import ParsedQuest

    # Determine evaluation criteria from quest type
    eval_type_map = {
        "coding": "code_submission",
        "debug": "code_submission",
        "theory": "self_report",
        "research": "self_report",
        "build": "code_submission",
    }
    eval_method = eval_type_map.get(parsed.type, "self_report")

    criteria = EvaluationCriteria(
        type=eval_method,
        test_cases=0,       # Phase 2: test cases populated by evaluator
        pass_threshold=0.67,
    )

    quest_id = f"q_{uuid.uuid4().hex[:12]}"

    return Quest(
        quest_id=quest_id,
        user_id=str(user.auth_id),  # Use auth_id as user ref in quests
        date=target_date,
        title=parsed.title,
        description="",         # Phase 2: expanded description
        type=parsed.type,
        difficulty=parsed.difficulty,
        estimated_minutes=parsed.estimated_minutes,
        xp_reward=parsed.xp_reward,
        skill_node=parsed.skill_node,
        skill_tree=user.active_skill_tree,
        evaluation_criteria=criteria,
        hints=parsed.hints,
        embedding=[],           # Phase 2: BGE-small embedding
        status="pending",
        generated_by="groq",
    )


# ── Fallback ──────────────────────────────────────────────────


async def _get_fallback_quests(user_id: str) -> List[Quest]:
    """
    §16: AI failure is non-fatal. Return yesterday's cached quests if available.
    Falls back to an empty list — route handler returns a graceful 503.
    """
    _logger.warning(
        "Quest generation failed — attempting cache fallback",
        context={"user_id": user_id},
    )
    # Try Redis yesterday cache (same key, may still be warm)
    cached = await redis_cache.get_cached_quests(user_id)
    if cached:
        _logger.info(
            "Fallback: returning cached quests",
            context={"user_id": user_id, "count": len(cached)},
        )
        return cached

    # Try MongoDB today's quests (idempotency guard)
    today = datetime.now(timezone.utc).date()
    stored = await quest_repository.get_quests_for_user_today(user_id, today)
    if stored:
        _logger.info(
            "Fallback: returning MongoDB today quests",
            context={"user_id": user_id, "count": len(stored)},
        )
        return stored

    return []


# ── Rate Limiting Helper ──────────────────────────────────────

_RATE_LIMIT_KEY = "rate_limit:quest_generate:{user_id}"
_MAX_GENERATIONS_PER_DAY = 5


async def check_rate_limit(user_id: str) -> bool:
    """
    §20: Rate limit quest generation to MAX_GENERATIONS_PER_DAY per user per day.
    Uses Redis counter keyed by user_id + UTC date.
    Returns True if request is allowed, False if rate limit exceeded.
    """
    try:
        from upstash_redis import AsyncRedis  # type: ignore[import]
        from app.core.config import settings

        if not settings.UPSTASH_REDIS_REST_URL or not settings.UPSTASH_REDIS_REST_TOKEN:
            return True  # No Redis → allow (dev mode)

        redis = AsyncRedis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN,
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"rate_limit:quest_generate:{user_id}:{today}"

        count = await redis.incr(key)
        if count == 1:
            # First request today — set TTL to 25h (covers timezone edge cases)
            await redis.expire(key, 90_000)

        return int(count) <= _MAX_GENERATIONS_PER_DAY

    except Exception as exc:
        _logger.warning(
            f"Rate limit check failed (non-fatal, allowing request): {exc}",
            context={"user_id": user_id},
        )
        return True  # Fail open — allow on Redis error


# ── Public API ────────────────────────────────────────────────


async def generate_quests_for_user(user_id: str) -> List[Quest]:
    """
    T5.1: Full quest generation pipeline.

    Args:
        user_id: Supabase auth_id (UUID string).

    Returns:
        List of 3 Quest domain models (generated or cached).

    §07: All AI access via _call_ai_generate() — never direct import.
    §16: AI failure returns fallback quests — never raises to the route handler.
    """
    import time as _time

    t0 = _time.monotonic()

    # Step 1: Check cache first (idempotency + performance)
    cached = await redis_cache.get_cached_quests(user_id)
    if cached:
        _logger.info(
            "Quest cache HIT",
            context={"user_id": user_id, "count": len(cached)},
        )
        return cached

    # Step 2: Load user from MongoDB
    user = await user_repository.get_user_by_auth_id(user_id)
    if user is None:
        _logger.error("User not found for quest generation", context={"user_id": user_id})
        return []

    # Step 3: Load streak + recent progress logs
    streak_count = await redis_cache.get_streak_counter(user_id)
    if streak_count == 0:
        # Redis miss — try MongoDB
        from app.repositories.mongo import streak_repository
        streak_doc = await streak_repository.get_streak(user_id)
        if streak_doc:
            streak_count = streak_doc.current_streak

    recent_logs: List[ProgressLog] = await progress_repository.get_logs_for_user(
        user_id, limit=7
    )

    # Step 4: Build prompt context
    # Build type/title maps from recent quests for context
    recent_quests = await quest_repository.get_recent_quests(user_id, days=7)
    q_type_map = {q.quest_id: q.type for q in recent_quests}
    q_title_map = {f"title:{q.quest_id}": q.title for q in recent_quests}

    context = build_quest_context(
        user=user,
        streak_count=streak_count,
        recent_logs=recent_logs,
        quest_type_map=q_type_map,
        quest_title_map=q_title_map,
    )

    # Step 5: Call AI (through isolated adapter only)
    try:
        parsed_quests = _call_ai_generate(context)
    except (ValueError, Exception) as exc:
        _logger.error(
            "Quest AI generation failed",
            context={"user_id": user_id, "error": str(exc)[:200]},
        )
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
        return await _get_fallback_quests(user_id)

    # Step 6: Build Quest domain models
    today_midnight = datetime(
        *datetime.now(timezone.utc).timetuple()[:3], tzinfo=timezone.utc
    )
    quest_docs = [_build_quest_doc(pq, user, today_midnight) for pq in parsed_quests]

    # Step 7: Persist to MongoDB
    try:
        stored_quests = await quest_repository.create_many(quest_docs)
    except Exception as exc:
        _logger.error(
            "Quest MongoDB persist failed",
            context={"user_id": user_id, "error": str(exc)[:200]},
        )
        return await _get_fallback_quests(user_id)

    # Step 8: Cache in Redis (TTL 24h)
    try:
        await redis_cache.cache_quests(user_id, stored_quests)
    except Exception as exc:
        _logger.warning(
            "Quest Redis cache failed (non-fatal)",
            context={"user_id": user_id, "error": str(exc)[:200]},
        )

    latency_ms = (_time.monotonic() - t0) * 1000
    _logger.info(
        "Quest generation complete",
        context={
            "user_id": user_id,
            "count": len(stored_quests),
            "latency_ms": round(latency_ms, 1),
        },
    )

    return stored_quests


async def get_today_quests(user_id: str) -> List[Quest]:
    """
    T5.2: GET /quests/today — cache-first read of today's quests.
    Returns cached quests if available, else fetches from MongoDB.
    """
    cached = await redis_cache.get_cached_quests(user_id)
    if cached:
        return cached

    today = datetime.now(timezone.utc).date()
    return await quest_repository.get_quests_for_user_today(user_id, today)


async def skip_quest(quest_id: str, user_id: str) -> Optional[Quest]:
    """
    T5.2: POST /quests/{id}/skip — mark quest as skipped and invalidate cache.
    Returns the updated Quest or None if not found.
    §09: QuestSkippedEvent fired as background task by route handler.
    """
    quest = await quest_repository.get_quest_by_id(quest_id)
    if quest is None:
        return None
    if quest.user_id != user_id:
        raise PermissionError(f"Quest {quest_id} does not belong to user {user_id}")

    await quest_repository.update_quest_status(quest_id, "skipped")
    await redis_cache.invalidate_quest_cache(user_id)

    _logger.info(
        "Quest skipped",
        context={"quest_id": quest_id, "user_id": user_id},
    )

    return await quest_repository.get_quest_by_id(quest_id)
