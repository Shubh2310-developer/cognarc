"""
COGNARC — Unit Tests: Quest Validator
apps/api/tests/unit/test_quest_validator.py

Covers: T4.2 validate_quests() business rules
- Distinct quest types
- Difficulty-level gating (novice/expert)
- XP range validation
- String sanitization
"""
from __future__ import annotations

import pytest

from ai_services.parsers.quest_output_parser import ParsedQuest
from ai_services.validation.quest_validator import validate_quests


# ── Fixtures ──────────────────────────────────────────────────


def make_quests(
    types=("coding", "debug", "theory"),
    difficulties=("medium", "easy", "medium"),
    xp_rewards=(100, 50, 80),
) -> list[ParsedQuest]:
    """Create 3 ParsedQuest objects with configurable types/difficulties."""
    return [
        ParsedQuest(
            title=f"Quest {i}",
            type=t,
            difficulty=d,
            estimated_minutes=30,
            xp_reward=x,
            skill_node="Python",
            hints=["hint1"],
        )
        for i, (t, d, x) in enumerate(zip(types, difficulties, xp_rewards))
    ]


# ── Happy Path ────────────────────────────────────────────────


def test_validate_quests_accepts_valid_input():
    """T4.2: validate_quests() returns 3 quests for valid input."""
    quests = make_quests()
    result = validate_quests(quests, user_level=5)
    assert len(result) == 3


def test_validate_quests_sanitizes_title():
    """T4.2: Control characters stripped from titles."""
    q = make_quests()
    q[0] = q[0].model_copy(update={"title": "Quest\x00\x1fTitle"})
    result = validate_quests(q, user_level=5)
    assert "\x00" not in result[0].title
    assert "\x1f" not in result[0].title


def test_validate_quests_sanitizes_hints():
    """T4.2: Control characters stripped from hints."""
    q = make_quests()
    q[0] = q[0].model_copy(update={"hints": ["hint\x00one", "hint\x1ftwo"]})
    result = validate_quests(q, user_level=5)
    assert "\x00" not in result[0].hints[0]


# ── Type Distinctness ─────────────────────────────────────────


def test_validate_quests_raises_on_duplicate_type():
    """T4.2: ValueError when two quests have the same type."""
    quests = make_quests(types=("coding", "coding", "debug"))
    with pytest.raises(ValueError, match="duplicate quest type"):
        validate_quests(quests, user_level=5)


# ── Difficulty-Level Gating ───────────────────────────────────


def test_validate_quests_blocks_hard_for_novice():
    """T4.2: Levels 1–3 cannot have 'hard' quests."""
    quests = make_quests(
        types=("coding", "debug", "theory"),
        difficulties=("hard", "easy", "medium"),
        xp_rewards=(200, 50, 80),
    )
    with pytest.raises(ValueError, match="hard"):
        validate_quests(quests, user_level=3)


def test_validate_quests_allows_hard_for_level4():
    """T4.2: Level 4+ can have 'hard' quests."""
    quests = make_quests(
        types=("coding", "debug", "theory"),
        difficulties=("hard", "easy", "medium"),
        xp_rewards=(200, 50, 80),
    )
    result = validate_quests(quests, user_level=4)
    assert len(result) == 3


def test_validate_quests_blocks_easy_for_expert():
    """T4.2: Level 8+ cannot have 'easy' quests."""
    quests = make_quests(
        types=("coding", "debug", "theory"),
        difficulties=("medium", "easy", "medium"),
        xp_rewards=(100, 50, 80),
    )
    with pytest.raises(ValueError, match="easy"):
        validate_quests(quests, user_level=8)


def test_validate_quests_allows_easy_for_level7():
    """T4.2: Level 7 can still have 'easy' quests."""
    quests = make_quests(
        types=("coding", "debug", "theory"),
        difficulties=("medium", "easy", "medium"),
        xp_rewards=(100, 50, 80),
    )
    result = validate_quests(quests, user_level=7)
    assert len(result) == 3


# ── XP Range Validation ───────────────────────────────────────


def test_validate_quests_blocks_xp_above_max():
    """T4.2: XP reward above max for difficulty raises ValueError."""
    quests = make_quests(
        types=("coding", "debug", "theory"),
        difficulties=("easy", "medium", "medium"),
        xp_rewards=(500, 100, 80),   # 500 > easy max (100)
    )
    with pytest.raises(ValueError, match="xp_reward"):
        validate_quests(quests, user_level=5)


def test_validate_quests_blocks_xp_below_min():
    """T4.2: XP reward below min for difficulty raises ValueError."""
    # Use model_construct() to bypass Pydantic field validators
    # so we can test the quest_validator's XP range check independently
    quests = [
        ParsedQuest.model_construct(
            title=f"Quest {i}",
            type=t,
            difficulty=d,
            estimated_minutes=30,
            xp_reward=x,
            skill_node="Python",
            hints=["hint1"],
        )
        for i, (t, d, x) in enumerate(zip(
            ("coding", "debug", "theory"),
            ("hard", "medium", "medium"),
            (5, 100, 80),   # 5 < hard min (100)
        ))
    ]
    with pytest.raises(ValueError, match="xp_reward"):
        validate_quests(quests, user_level=5)


def test_validate_quests_accepts_boundary_xp():
    """T4.2: XP at exact boundary values passes validation."""
    quests = make_quests(
        types=("coding", "debug", "research"),
        difficulties=("easy", "medium", "hard"),
        xp_rewards=(10, 200, 500),  # Exact max values
    )
    result = validate_quests(quests, user_level=5)
    assert len(result) == 3


# ── Wrong Count ───────────────────────────────────────────────


def test_validate_quests_raises_on_wrong_count():
    """T4.2: ValueError when not exactly 3 quests provided."""
    quests = make_quests()[:2]
    with pytest.raises(ValueError, match="expected 3 quests"):
        validate_quests(quests, user_level=5)
