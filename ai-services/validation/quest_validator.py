"""
COGNARC — Quest Validator
ai-services/validation/quest_validator.py

T4.2: Business-rule validation on parsed quest output.
§16: Never trust AI output. All AI outputs pass through validators before storage.
§16: AI never awards XP directly — XP validation happens here deterministically.

Validation rules enforced:
  1. Quest type is one of 5 allowed values (redundant with Pydantic but explicit)
  2. All 3 quests have DISTINCT types (no repeated type across the set)
  3. Difficulty matches user level range:
       level 1–3  → no "hard" quests
       level 4–7  → all difficulties allowed
       level 8+   → no "easy" quests
  4. xp_reward is within expected range for the difficulty tier
  5. title and hints are sanitized (strip control chars, enforce max length)

Raises ValueError on any rule violation — caller triggers fallback.
"""
from __future__ import annotations

import re
from typing import List

from ai_services.parsers.quest_output_parser import ParsedQuest

# ── Constants ─────────────────────────────────────────────────

ALLOWED_TYPES = frozenset({"theory", "coding", "debug", "research", "build"})
ALLOWED_DIFFICULTIES = frozenset({"easy", "medium", "hard"})

# XP range per difficulty (inclusive)
XP_RANGES: dict[str, tuple[int, int]] = {
    "easy": (10, 100),
    "medium": (50, 200),
    "hard": (100, 500),
}

# Difficulty rules by level bracket
_NOVICE_MAX_LEVEL = 3     # levels 1–3: no "hard" quests
_EXPERT_MIN_LEVEL = 8     # levels 8+: no "easy" quests

# String sanitization limits
_MAX_TITLE_LEN = 200
_MAX_HINT_LEN = 500
_MAX_HINTS_COUNT = 5

# Control character pattern (strips all non-printable ASCII)
_CTRL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


# ── Sanitization ──────────────────────────────────────────────


def _sanitize_string(value: str, max_len: int, field_name: str) -> str:
    """
    Strip control characters and enforce maximum length on a string.
    §16: Prompt injection mitigation for user-controlled AI output strings.
    """
    if not isinstance(value, str):
        raise ValueError(f"Quest validation failure: {field_name} must be a string")

    sanitized = _CTRL_CHAR_RE.sub("", value).strip()

    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]

    if not sanitized:
        raise ValueError(
            f"Quest validation failure: {field_name} is empty after sanitization"
        )

    return sanitized


def _sanitize_hints(hints: list) -> list[str]:
    """Sanitize each hint string. Returns cleaned list (empty hints dropped)."""
    if not isinstance(hints, list):
        return []

    sanitized = []
    for hint in hints[:_MAX_HINTS_COUNT]:
        if not isinstance(hint, str):
            continue
        cleaned = _CTRL_CHAR_RE.sub("", hint).strip()[:_MAX_HINT_LEN]
        if cleaned:
            sanitized.append(cleaned)

    return sanitized


# ── Difficulty Gate ───────────────────────────────────────────


def _validate_difficulty_for_level(difficulty: str, user_level: int, quest_idx: int) -> None:
    """
    T4.2 Rule 3: Validate that quest difficulty is appropriate for user level.

    Levels 1–3: no "hard" quests (novice protection)
    Levels 4–7: all difficulties allowed
    Levels 8+:  no "easy" quests (expert fast-track)

    Raises ValueError on violation.
    """
    if user_level <= _NOVICE_MAX_LEVEL and difficulty == "hard":
        raise ValueError(
            f"Quest validation failure: quest[{quest_idx}] difficulty='hard' "
            f"is not allowed for user level {user_level} (max level for hard: "
            f"{_NOVICE_MAX_LEVEL + 1})"
        )

    if user_level >= _EXPERT_MIN_LEVEL and difficulty == "easy":
        raise ValueError(
            f"Quest validation failure: quest[{quest_idx}] difficulty='easy' "
            f"is not allowed for user level {user_level} (min level for easy: "
            f"{_EXPERT_MIN_LEVEL - 1})"
        )


# ── XP Range Validator ────────────────────────────────────────


def _validate_xp_reward(xp_reward: int, difficulty: str, quest_idx: int) -> None:
    """
    T4.2 Rule 4: Validate xp_reward is within expected range for difficulty.
    §16: AI never awards XP directly. We deterministically gate the range.
    """
    min_xp, max_xp = XP_RANGES.get(difficulty, (10, 500))
    if not (min_xp <= xp_reward <= max_xp):
        raise ValueError(
            f"Quest validation failure: quest[{quest_idx}] xp_reward={xp_reward} "
            f"is outside allowed range [{min_xp}, {max_xp}] for difficulty='{difficulty}'"
        )


# ── Primary Validator ─────────────────────────────────────────


def validate_quests(
    quests: List[ParsedQuest],
    user_level: int = 1,
) -> List[ParsedQuest]:
    """
    T4.2: Full business-rule validation on a list of 3 ParsedQuest objects.

    Mutates title and hints fields in-place with sanitized values.
    Returns the validated (and sanitized) list unchanged if all checks pass.

    Raises:
        ValueError: On any rule violation — caller triggers fallback.

    Args:
        quests:     List of ParsedQuest objects from parse_quest_output().
        user_level: Current user level (int ≥ 1) — used for difficulty gating.
    """
    if len(quests) != 3:
        raise ValueError(
            f"Quest validation failure: expected 3 quests, got {len(quests)}"
        )

    # Rule 2: All 3 quests must have DISTINCT types
    types_seen: set[str] = set()
    for i, quest in enumerate(quests):
        if quest.type in types_seen:
            raise ValueError(
                f"Quest validation failure: duplicate quest type '{quest.type}' "
                f"at index {i}. All 3 quests must have distinct types."
            )
        types_seen.add(quest.type)

    # Per-quest rules
    validated: List[ParsedQuest] = []
    for i, quest in enumerate(quests):
        # Rule 1: type must be one of 5 allowed values (belt-and-suspenders)
        if quest.type not in ALLOWED_TYPES:
            raise ValueError(
                f"Quest validation failure: quest[{i}] has unknown type '{quest.type}'"
            )

        if quest.difficulty not in ALLOWED_DIFFICULTIES:
            raise ValueError(
                f"Quest validation failure: quest[{i}] has unknown difficulty '{quest.difficulty}'"
            )

        # Rule 3: Difficulty must match user level
        _validate_difficulty_for_level(quest.difficulty, user_level, i)

        # Rule 4: XP reward must be within range for difficulty
        _validate_xp_reward(quest.xp_reward, quest.difficulty, i)

        # Rule 5: Sanitize title and hints
        sanitized_title = _sanitize_string(quest.title, _MAX_TITLE_LEN, f"quest[{i}].title")
        sanitized_hints = _sanitize_hints(quest.hints)

        # Rebuild with sanitized values (Pydantic model is immutable-ish — use copy)
        sanitized_quest = quest.model_copy(
            update={"title": sanitized_title, "hints": sanitized_hints}
        )
        validated.append(sanitized_quest)

    return validated
