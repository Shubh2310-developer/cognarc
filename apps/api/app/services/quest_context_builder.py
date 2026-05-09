"""
COGNARC — Quest Context Builder
apps/api/app/services/quest_context_builder.py

T6.1: Aggregates user data from MongoDB + Redis into the prompt context payload.
§06: Service layer — no direct DB access. Calls repositories.
§07: AI calls never cross into services. Context is passed up to ai-services.
§16: All user-controlled strings sanitized before injection into prompts.

Public API:
    build_quest_context(user, streak_count, recent_logs) → dict

Returns a dict matching the USER_PROMPT_TEMPLATE_V1 placeholders.
"""
from __future__ import annotations

import re
from typing import List

from app.models.progress_log import ProgressLog
from app.models.user import User

_logger = None  # lazy import to avoid circular deps


def _get_logger():
    global _logger
    if _logger is None:
        from app.core.logger import get_logger
        _logger = get_logger("service.quest_context_builder")
    return _logger


# ── String Sanitization ───────────────────────────────────────

_CTRL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f<>{}|\\^`]")
_MAX_FIELD_LEN = 200


def _sanitize(value: str, max_len: int = _MAX_FIELD_LEN) -> str:
    """
    §16 Prompt injection mitigation: strip control characters and
    potentially dangerous chars from user-controlled strings.
    Truncate to max_len to prevent prompt bloat.
    """
    if not isinstance(value, str):
        return str(value)[:max_len]
    cleaned = _CTRL_CHAR_RE.sub("", value).strip()
    return cleaned[:max_len]


# ── Progress Log Aggregation ──────────────────────────────────


def _get_recent_quest_types(logs: List[ProgressLog], quest_map: dict) -> str:
    """Extract distinct quest types from recent progress logs."""
    types: list[str] = []
    for log in logs[:7]:
        # quest_map maps quest_id → type string (provided by caller)
        q_type = quest_map.get(log.quest_id, "")
        if q_type and q_type not in types:
            types.append(q_type)
    return ", ".join(types) if types else "none"


def _get_recent_quest_summaries(logs: List[ProgressLog], quest_map: dict) -> str:
    """
    Build a brief summary string of recent quest titles for the prompt.
    Truncated to avoid prompt bloat. Max 5 entries, 50 chars each.
    §16: Sanitize quest titles before injection.
    """
    summaries: list[str] = []
    for log in logs[:5]:
        title = quest_map.get(f"title:{log.quest_id}", "")
        if title:
            safe_title = _sanitize(title, max_len=60)
            summaries.append(safe_title)
    return "; ".join(summaries) if summaries else "none"


# ── Node Progress ─────────────────────────────────────────────


def _get_node_progress_pct(user: User) -> int:
    """
    Get the progress percentage for the current skill node (0–100).
    Reads from user.skill_state[active_skill_tree].node_progress.
    Returns 0 if skill state is not yet populated.
    """
    tree = user.active_skill_tree
    state = user.skill_state.get(tree)
    if state is None:
        return 0
    return int(state.node_progress * 100)


def _get_current_node(user: User) -> str:
    """Get the current skill node ID for the active skill tree."""
    tree = user.active_skill_tree
    state = user.skill_state.get(tree)
    if state is None:
        return _sanitize(tree)  # Fallback to tree name itself
    return _sanitize(state.current_node)


# ── Completion Rate ───────────────────────────────────────────


def _compute_completion_rate_7d(logs: List[ProgressLog]) -> int:
    """
    Compute 7-day completion rate from recent logs.
    Returns integer percentage 0–100.
    """
    if not logs:
        return 0
    # In MVP, all logged quests are completed — count them vs 3 per day * 7 days
    completed = len(logs)
    max_possible = 21  # 3 quests/day × 7 days
    rate = min(1.0, completed / max_possible)
    return int(rate * 100)


# ── Primary Builder ───────────────────────────────────────────


def build_quest_context(
    user: User,
    streak_count: int,
    recent_logs: List[ProgressLog],
    quest_type_map: dict | None = None,
    quest_title_map: dict | None = None,
) -> dict:
    """
    T6.1: Assemble the prompt context payload for quest generation.

    Args:
        user:            User domain model from MongoDB.
        streak_count:    Current streak count (from Redis or MongoDB fallback).
        recent_logs:     Last 7 ProgressLog entries for this user.
        quest_type_map:  {quest_id: type} for recent quests (optional).
        quest_title_map: {quest_id: title} for recent quests (optional).

    Returns:
        Dict with all keys needed by USER_PROMPT_TEMPLATE_V1:
            user_level, skill_node_current, node_progress_pct,
            streak_count, difficulty_modifier, completion_rate_7d_pct,
            recent_quest_types, recent_quest_summaries.

    §16: All user-controlled strings sanitized. Never pass raw user
         input directly into Groq prompts.
    """
    log = _get_logger()

    q_type_map = quest_type_map or {}
    q_title_map_combined = {**q_type_map, **(quest_title_map or {})}

    node = _get_current_node(user)
    node_pct = _get_node_progress_pct(user)
    difficulty_mod = user.behavioral_profile.difficulty_modifier
    completion_pct = _compute_completion_rate_7d(recent_logs)

    recent_types = _get_recent_quest_types(recent_logs, q_type_map)
    recent_summaries = _get_recent_quest_summaries(recent_logs, q_title_map_combined)

    context = {
        "user_level": max(1, user.level),
        "skill_node_current": node,
        "node_progress_pct": node_pct,
        "streak_count": max(0, streak_count),
        "difficulty_modifier": round(max(0.5, min(2.0, difficulty_mod)), 2),
        "completion_rate_7d_pct": completion_pct,
        "recent_quest_types": recent_types,
        "recent_quest_summaries": recent_summaries,
    }

    log.info(
        "Quest context built",
        context={
            "user_level": context["user_level"],
            "skill_node": node,
            "streak": streak_count,
            "difficulty_mod": difficulty_mod,
        },
    )

    return context
