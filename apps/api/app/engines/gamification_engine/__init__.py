"""
COGNARC — Gamification Engine Package
apps/api/app/engines/gamification_engine/__init__.py

Phase 3 MVP: XP calculation only.
calculate_xp() is the sole public interface for XP awards in the MVP.
§16: AI never awards XP. XP is always calculated by this deterministic engine.
"""
from __future__ import annotations

from app.engines.gamification_engine.xp_calculator import (
    BASE_XP,
    TYPE_MULTIPLIER,
    calculate_xp,
    calculate_xp_from_quest,
    get_streak_multiplier,
    has_time_bonus,
)

__all__ = [
    "calculate_xp",
    "calculate_xp_from_quest",
    "get_streak_multiplier",
    "has_time_bonus",
    "BASE_XP",
    "TYPE_MULTIPLIER",
]
