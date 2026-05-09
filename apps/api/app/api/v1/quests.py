"""
COGNARC — Quests Router
apps/api/app/api/v1/quests.py

T5.2: POST /quests/generate, GET /quests/today, POST /quests/{id}/skip
T5.4: POST /quests/{id}/evaluate — MVP self-reporting with XP calculation.

§06: Routes ONLY. No business logic. No DB calls. No AI calls.
     All business logic delegated to quest_service and gamification_engine.
§20: All routes require JWT via Depends(get_current_user).
§20: /quests/generate is rate-limited to 5/day via Redis counter in quest_service.
§17: Accepts Pydantic schemas. Returns Pydantic schemas.

HTTP Status Codes (§06):
    200 OK           — success
    201 Created      — quests generated
    400 Bad Request  — invalid input
    401 Unauthorized — missing/invalid JWT
    403 Forbidden    — wrong user
    404 Not Found    — quest not found
    429 Too Many Requests — rate limit exceeded
    503 Service Unavailable — AI generation failed with no fallback
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.dependencies import AuthenticatedUser, get_current_user
from app.core.logger import get_logger
from app.engines.gamification_engine import calculate_xp_from_quest
from app.models.progress_log import ProgressLog
from app.repositories.mongo import quest_repository, progress_repository, user_repository
from app.schemas.quest_schemas import (
    QuestGenerateRequest,
    QuestListResponse,
    QuestResponse,
    QuestStatusUpdateRequest,
)
from app.services import quest_service

router = APIRouter()
_logger = get_logger("router.quests")

# ── Schema Helper ─────────────────────────────────────────────


def _quest_to_response(quest) -> QuestResponse:
    """Map a Quest domain model to a QuestResponse schema."""
    return QuestResponse(
        id=quest.quest_id,
        quest_id=quest.quest_id,
        user_id=quest.user_id,
        date=quest.date,
        title=quest.title,
        description=quest.description,
        type=quest.type,
        difficulty=quest.difficulty,
        estimated_minutes=quest.estimated_minutes,
        xp_reward=quest.xp_reward,
        skill_node=quest.skill_node,
        skill_tree=quest.skill_tree,
        evaluation_criteria=quest.evaluation_criteria,
        hints=quest.hints,
        status=quest.status,
        generated_by=quest.generated_by,
        created_at=quest.created_at,
        completed_at=quest.completed_at,
    )


# ── Routes ────────────────────────────────────────────────────


@router.post(
    "/generate",
    response_model=QuestListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate today's quests via Groq AI",
    description=(
        "Triggers AI quest generation for the authenticated user. "
        "Idempotent: returns cached quests if already generated today. "
        "Rate-limited to 5 calls/day."
    ),
)
async def generate_quests(
    request: QuestGenerateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> QuestListResponse:
    """
    T5.2: POST /quests/generate
    §20: Rate-limited to 5/day. Idempotent (cache-first).
    §07: AI call delegated to quest_service → ai_services (isolated).
    """
    user_id = user.user_id

    # Rate limit check (§20: 5/day)
    allowed = await quest_service.check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quest generation rate limit exceeded (5/day). Try again tomorrow.",
        )

    quests = await quest_service.generate_quests_for_user(user_id)

    if not quests:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Quest generation temporarily unavailable. Please try again later.",
        )

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    _logger.info(
        "quest_generated event",
        context={
            "user_id": user_id,
            "count": len(quests),
            "date": today_str,
        },
    )

    return QuestListResponse(
        quests=[_quest_to_response(q) for q in quests],
        total=len(quests),
        date=today_str,
    )


@router.get(
    "/today",
    response_model=QuestListResponse,
    summary="Fetch today's quests",
    description="Returns the authenticated user's quests for today (cache-first).",
)
async def get_today_quests(
    user: AuthenticatedUser = Depends(get_current_user),
) -> QuestListResponse:
    """T5.2: GET /quests/today — cache-first."""
    user_id = user.user_id
    quests = await quest_service.get_today_quests(user_id)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return QuestListResponse(
        quests=[_quest_to_response(q) for q in quests],
        total=len(quests),
        date=today_str,
    )


@router.post(
    "/{quest_id}/skip",
    response_model=QuestResponse,
    summary="Skip a quest",
    description="Mark a quest as skipped. Records a behavioral signal.",
)
async def skip_quest(
    quest_id: str,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(get_current_user),
) -> QuestResponse:
    """
    T5.2: POST /quests/{id}/skip
    §09: QuestSkippedEvent fired as background task for behavioral engine.
    """
    user_id = user.user_id

    try:
        updated = await quest_service.skip_quest(quest_id, user_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only skip your own quests.",
        )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quest '{quest_id}' not found.",
        )

    # Background task: fire QuestSkippedEvent for behavioral engine (§09)
    background_tasks.add_task(_record_skip_signal, user_id=user_id, quest_id=quest_id)

    return _quest_to_response(updated)


@router.post(
    "/{quest_id}/evaluate",
    response_model=QuestResponse,
    summary="Evaluate (self-report) quest completion",
    description=(
        "MVP self-reporting endpoint. User confirms quest completion. "
        "XP is calculated deterministically and stored. ProgressLog written to MongoDB."
    ),
)
async def evaluate_quest(
    quest_id: str,
    payload: QuestStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(get_current_user),
) -> QuestResponse:
    """
    T5.4: POST /quests/{id}/evaluate — MVP self-report completion.

    1. Fetch quest from MongoDB
    2. Verify ownership
    3. Calculate XP via gamification_engine.calculate_xp()  (§16: deterministic)
    4. Update quest status to 'completed'
    5. Write ProgressLog to MongoDB
    6. Update user.total_xp in MongoDB
    7. Invalidate quest cache
    8. Fire QuestCompletedEvent as background task (§09)

    §16: AI never awards XP. XP = deterministic engine only.
    """
    user_id = user.user_id

    # 1. Fetch quest
    quest = await quest_repository.get_quest_by_id(quest_id)
    if quest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quest '{quest_id}' not found.",
        )

    # 2. Verify ownership
    if quest.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only evaluate your own quests.",
        )

    if quest.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quest already has status '{quest.status}'. Cannot re-evaluate.",
        )

    # 3. Calculate XP (§16: deterministic engine, never AI-awarded)
    from app.repositories.cache import redis_cache
    from app.repositories.mongo import streak_repository

    streak_count = await redis_cache.get_streak_counter(user_id)
    if streak_count == 0:
        streak_doc = await streak_repository.get_streak(user_id)
        if streak_doc:
            streak_count = streak_doc.current_streak

    user_model = await user_repository.get_user_by_auth_id(user_id)
    difficulty_modifier = 1.0
    if user_model:
        difficulty_modifier = user_model.behavioral_profile.difficulty_modifier

    xp_earned = calculate_xp_from_quest(
        difficulty=quest.difficulty,
        estimated_minutes=quest.estimated_minutes,
        time_taken_min=payload.time_taken_min,
        streak_count=streak_count,
        quest_type=quest.type,
        difficulty_modifier=difficulty_modifier,
    )

    # 4. Update quest status to 'completed'
    await quest_repository.update_quest_status(quest_id, "completed")

    # 5. Write ProgressLog
    log = ProgressLog(
        user_id=user_id,
        quest_id=quest_id,
        xp_earned=xp_earned,
        time_taken_min=payload.time_taken_min,
        evaluation_score=payload.evaluation_score,
        evaluation_method="self_report" if payload.self_reported else "ai_review",
    )
    await progress_repository.create_log(log)

    # 6. Update user.total_xp in MongoDB
    if user_model:
        new_xp = user_model.total_xp + xp_earned
        await user_repository.update_user(
            user_id=str(user_model.auth_id),
            updates={"total_xp": new_xp},
        )

    # 7. Invalidate quest cache (forces fresh fetch next time)
    await redis_cache.invalidate_quest_cache(user_id)

    # 8. Background: streak update + QuestCompletedEvent (§09)
    background_tasks.add_task(
        _handle_quest_completed,
        user_id=user_id,
        quest_id=quest_id,
        xp_earned=xp_earned,
    )

    _logger.info(
        "Quest evaluated (self-report)",
        context={
            "user_id": user_id,
            "quest_id": quest_id,
            "xp_earned": xp_earned,
            "difficulty": quest.difficulty,
            "type": quest.type,
        },
    )

    # Return updated quest
    updated = await quest_repository.get_quest_by_id(quest_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Quest not found after update")

    return _quest_to_response(updated)


# ── Background Tasks ──────────────────────────────────────────


async def _record_skip_signal(user_id: str, quest_id: str) -> None:
    """Background: record QuestSkippedEvent for behavioral engine (§09)."""
    _logger.info(
        "QuestSkippedEvent",
        context={"user_id": user_id, "quest_id": quest_id},
    )
    # Phase 4: emit to behavioral engine. MVP: logging only.


async def _handle_quest_completed(
    user_id: str, quest_id: str, xp_earned: int
) -> None:
    """
    Background: update streak counter and fire QuestCompletedEvent (§09).
    Non-fatal — failure here must never break the HTTP response.
    """
    try:
        from app.repositories.mongo import streak_repository
        from app.repositories.cache import redis_cache as _cache
        from app.models.streak import Streak
        from datetime import date

        # Update streak in MongoDB
        existing = await streak_repository.get_streak(user_id)
        today = date.today()

        if existing is None:
            new_streak = Streak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_completion_date=today,
            )
        else:
            # Increment streak if completed consecutive day
            last = existing.last_completion_date
            days_since = (today - last).days if last else 999

            if days_since == 1:
                new_count = existing.current_streak + 1
                new_longest = max(existing.longest_streak, new_count)
                new_streak = existing.model_copy(update={
                    "current_streak": new_count,
                    "longest_streak": new_longest,
                    "last_completion_date": today,
                })
            elif days_since == 0:
                new_streak = existing  # Already completed today — no change
            else:
                # Streak broken
                new_streak = existing.model_copy(update={
                    "current_streak": 1,
                    "last_completion_date": today,
                })

        updated_streak = await streak_repository.upsert_streak(user_id, new_streak)
        await _cache.set_streak_counter(user_id, updated_streak.current_streak)

        _logger.info(
            "QuestCompletedEvent",
            context={
                "user_id": user_id,
                "quest_id": quest_id,
                "xp_earned": xp_earned,
                "streak": updated_streak.current_streak,
            },
        )

    except Exception as exc:
        _logger.error(
            "QuestCompletedEvent background handler failed (non-fatal)",
            context={"user_id": user_id, "error": str(exc)[:200]},
        )
