"""
COGNARC — Gamification Engine: XP Calculator
apps/api/app/engines/gamification_engine/xp_calculator.py

T5.3: calculate_xp() — pure deterministic function per §21 formula.
§16: AI never awards XP directly. XP calculation ALWAYS happens here.
§17: Pure function — no I/O, no DB calls, no side effects.

Formula (§21):
    xp_earned = base_xp[difficulty]
                * difficulty_modifier      (0.5–2.0)
                * streak_multiplier        (1.00–2.00)
                * time_bonus_multiplier    (1.2 if time_bonus else 1.0)
                * quest_type_multiplier    (0.8–1.3)

Result is floor-rounded to an integer.
"""
from __future__ import annotations

# ── XP Tables (§21) ──────────────────────────────────────────

BASE_XP: dict[str, int] = {
    "easy": 50,
    "medium": 100,
    "hard": 200,
    "boss": 500,
}

TYPE_MULTIPLIER: dict[str, float] = {
    "theory": 0.8,
    "coding": 1.0,
    "debug": 1.1,
    "research": 1.0,
    "build": 1.3,
}

# Streak thresholds → multiplier
# streak_count 1–6: 1.00, 7–13: 1.25, 14–29: 1.50, 30+: 2.00
_STREAK_BRACKETS: list[tuple[int, float]] = [
    (30, 2.00),
    (14, 1.50),
    (7, 1.25),
    (1, 1.00),
]

# Difficulty modifier is clamped to this range (from behavioral_profile)
_DIFFICULTY_MODIFIER_MIN = 0.5
_DIFFICULTY_MODIFIER_MAX = 2.0

# Time bonus multiplier (1.2x if completed in < 80% of estimated time)
_TIME_BONUS_MULT = 1.2
_TIME_BONUS_THRESHOLD = 0.8  # 80% of estimated_minutes


# ── Helpers ───────────────────────────────────────────────────


def get_streak_multiplier(streak_count: int) -> float:
    """
    Return the streak XP multiplier for the given streak count.

    Brackets:
      streak 1–6:   1.00x
      streak 7–13:  1.25x
      streak 14–29: 1.50x
      streak 30+:   2.00x

    streak_count = 0 → treated as 1 (no-streak users get base rate).
    """
    effective = max(streak_count, 1)
    for threshold, multiplier in _STREAK_BRACKETS:
        if effective >= threshold:
            return multiplier
    return 1.00


def has_time_bonus(time_taken_min: int, estimated_minutes: int) -> bool:
    """
    Returns True if the user completed the quest in < 80% of estimated time.
    Both values must be positive integers; returns False on degenerate input.
    """
    if estimated_minutes <= 0 or time_taken_min < 0:
        return False
    return time_taken_min < (estimated_minutes * _TIME_BONUS_THRESHOLD)


# ── Primary Calculator ────────────────────────────────────────


def calculate_xp(
    difficulty: str,
    streak_count: int,
    quest_type: str,
    difficulty_modifier: float = 1.0,
    time_bonus: bool = False,
) -> int:
    """
    T5.3: Deterministic XP calculation per §21 formula.

    Args:
        difficulty:          Quest difficulty tier — "easy" | "medium" | "hard" | "boss".
        streak_count:        Current user streak (days). 0 is treated as 1.
        quest_type:          Quest type — one of theory/coding/debug/research/build.
        difficulty_modifier: Float 0.5–2.0 from behavioral_profile (default 1.0 = neutral).
        time_bonus:          True if user completed quest in < 80% of estimated_minutes.

    Returns:
        Integer XP earned. Always ≥ 1.

    §16: This is the ONLY place XP is calculated. AI output never sets XP directly.
    """
    # Clamp modifier to allowed range
    modifier = max(_DIFFICULTY_MODIFIER_MIN, min(_DIFFICULTY_MODIFIER_MAX, difficulty_modifier))

    base = BASE_XP.get(difficulty, BASE_XP["medium"])
    streak_mult = get_streak_multiplier(streak_count)
    type_mult = TYPE_MULTIPLIER.get(quest_type, 1.0)
    time_mult = _TIME_BONUS_MULT if time_bonus else 1.0

    xp = base * modifier * streak_mult * time_mult * type_mult
    return max(1, int(xp))


def calculate_xp_from_quest(
    *,
    difficulty: str,
    estimated_minutes: int,
    time_taken_min: int,
    streak_count: int,
    quest_type: str,
    difficulty_modifier: float = 1.0,
) -> int:
    """
    Convenience wrapper: resolves time_bonus from raw time values.

    Use this in route handlers — pass raw quest + timing data,
    get back integer XP without needing to compute time_bonus manually.
    """
    bonus = has_time_bonus(time_taken_min, estimated_minutes)
    return calculate_xp(
        difficulty=difficulty,
        streak_count=streak_count,
        quest_type=quest_type,
        difficulty_modifier=difficulty_modifier,
        time_bonus=bonus,
    )
