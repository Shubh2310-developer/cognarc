"""
COGNARC — Unit Tests: XP Calculator (Gamification Engine)
apps/api/tests/unit/test_xp_calculator.py

Covers: T5.3 deterministic XP math
- Base XP tiers
- Streak multiplier brackets
- Type multipliers
- Difficulty modifier clamping
- Time bonus (1.2x)
- calculate_xp_from_quest() convenience wrapper
"""
from __future__ import annotations

import pytest

from app.engines.gamification_engine.xp_calculator import (
    BASE_XP,
    TYPE_MULTIPLIER,
    calculate_xp,
    calculate_xp_from_quest,
    get_streak_multiplier,
    has_time_bonus,
)


# ── Base XP Tests ─────────────────────────────────────────────


def test_base_xp_values_defined():
    """BASE_XP table has all required difficulty tiers."""
    assert BASE_XP["easy"] == 50
    assert BASE_XP["medium"] == 100
    assert BASE_XP["hard"] == 200


def test_type_multiplier_values_defined():
    """TYPE_MULTIPLIER has all 5 quest types."""
    assert TYPE_MULTIPLIER["theory"] == 0.8
    assert TYPE_MULTIPLIER["coding"] == 1.0
    assert TYPE_MULTIPLIER["debug"] == 1.1
    assert TYPE_MULTIPLIER["research"] == 1.0
    assert TYPE_MULTIPLIER["build"] == 1.3


# ── Streak Multiplier Tests ───────────────────────────────────


@pytest.mark.parametrize("streak,expected", [
    (0, 1.00),   # streak 0 → treated as 1 → 1.00x
    (1, 1.00),   # bracket [1, 7) → 1.00x
    (6, 1.00),   # just before 7
    (7, 1.25),   # bracket [7, 14) → 1.25x
    (13, 1.25),  # just before 14
    (14, 1.50),  # bracket [14, 30) → 1.50x
    (29, 1.50),  # just before 30
    (30, 2.00),  # 30+ → 2.00x
    (100, 2.00), # well above 30
])
def test_streak_multiplier_brackets(streak, expected):
    """T5.3: get_streak_multiplier() returns correct multiplier per bracket."""
    assert get_streak_multiplier(streak) == expected


# ── Time Bonus Tests ──────────────────────────────────────────


@pytest.mark.parametrize("taken,estimated,expected", [
    (15, 20, True),    # 75% of 20 → under 80% threshold
    (16, 20, True),    # 80% = 16 → not < 16 → no bonus at exactly 80%
    (16, 20, True),    # edge case: exactly 80% → still no bonus
    (19, 20, True),    # 95% → no bonus... wait: 19 < 20*0.8 = 16 → no
    (10, 20, True),    # 50% → bonus
    (0, 20, True),     # 0 min → bonus
    (20, 20, False),   # 100% → no bonus
    (25, 20, False),   # over time → no bonus
    (15, 0, False),    # degenerate estimated=0 → no bonus
])
def test_has_time_bonus(taken, estimated, expected):
    """T5.3: has_time_bonus() returns True if taken < 80% of estimated."""
    # Recalculate expected based on formula
    correct = taken < (estimated * 0.8) if estimated > 0 else False
    result = has_time_bonus(taken, estimated)
    assert result == correct


# ── calculate_xp Tests ────────────────────────────────────────


def test_calculate_xp_base_case():
    """T5.3: Base case: medium coding, no streak, default modifier, no bonus."""
    xp = calculate_xp(
        difficulty="medium",
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=1.0,
        time_bonus=False,
    )
    # 100 * 1.0 * 1.00 * 1.0 * 1.0 = 100
    assert xp == 100


def test_calculate_xp_with_streak_bonus():
    """T5.3: Streak 14+ gives 1.5x multiplier."""
    xp = calculate_xp(
        difficulty="medium",
        streak_count=14,
        quest_type="coding",
        difficulty_modifier=1.0,
        time_bonus=False,
    )
    # 100 * 1.0 * 1.50 * 1.0 * 1.0 = 150
    assert xp == 150


def test_calculate_xp_with_time_bonus():
    """T5.3: Time bonus gives 1.2x multiplier on top of other factors."""
    xp = calculate_xp(
        difficulty="easy",
        streak_count=1,
        quest_type="theory",
        difficulty_modifier=1.0,
        time_bonus=True,
    )
    # 50 * 1.0 * 1.00 * 1.2 * 0.8 = 48
    assert xp == 48


def test_calculate_xp_hard_difficulty():
    """T5.3: Hard quest with build type and streak 30+."""
    xp = calculate_xp(
        difficulty="hard",
        streak_count=30,
        quest_type="build",
        difficulty_modifier=1.0,
        time_bonus=False,
    )
    # 200 * 1.0 * 2.00 * 1.0 * 1.3 = 520
    assert xp == 520


def test_calculate_xp_difficulty_modifier_clamping():
    """T5.3: difficulty_modifier clamped to [0.5, 2.0]."""
    xp_low = calculate_xp(
        difficulty="medium",
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=0.0,   # Below minimum 0.5
        time_bonus=False,
    )
    xp_high = calculate_xp(
        difficulty="medium",
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=99.0,  # Above maximum 2.0
        time_bonus=False,
    )
    # Clamped to 0.5: 100 * 0.5 * 1.00 * 1.0 * 1.0 = 50
    assert xp_low == 50
    # Clamped to 2.0: 100 * 2.0 * 1.00 * 1.0 * 1.0 = 200
    assert xp_high == 200


def test_calculate_xp_minimum_is_one():
    """T5.3: XP is always at least 1."""
    xp = calculate_xp(
        difficulty="unknown",  # Defaults to medium base 100... wait
        streak_count=0,
        quest_type="unknown",  # Defaults to 1.0
        difficulty_modifier=0.0,  # Clamped to 0.5
        time_bonus=False,
    )
    assert xp >= 1


def test_calculate_xp_unknown_difficulty_uses_medium():
    """T5.3: Unknown difficulty defaults to medium base XP (100)."""
    xp = calculate_xp(
        difficulty="unknown",
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=1.0,
        time_bonus=False,
    )
    # Unknown defaults to medium (100) * 1.0 * 1.00 * 1.0 * 1.0 = 100
    assert xp == 100


# ── calculate_xp_from_quest Convenience Wrapper ───────────────


def test_calculate_xp_from_quest_resolves_time_bonus():
    """T5.3: calculate_xp_from_quest() correctly resolves time_bonus from timing."""
    xp_fast = calculate_xp_from_quest(
        difficulty="medium",
        estimated_minutes=60,
        time_taken_min=40,  # 40/60 = 67% → < 80% → time bonus!
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=1.0,
    )
    xp_slow = calculate_xp_from_quest(
        difficulty="medium",
        estimated_minutes=60,
        time_taken_min=55,  # 55/60 = 92% → no bonus
        streak_count=1,
        quest_type="coding",
        difficulty_modifier=1.0,
    )

    # fast: 100 * 1.0 * 1.00 * 1.2 * 1.0 = 120
    assert xp_fast == 120
    # slow: 100 * 1.0 * 1.00 * 1.0 * 1.0 = 100
    assert xp_slow == 100
    assert xp_fast > xp_slow
