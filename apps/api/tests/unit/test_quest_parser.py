"""
COGNARC — Unit Tests: Quest Output Parser
apps/api/tests/unit/test_quest_parser.py

Covers: T4.1 parse_quest_output()
- Accepts valid JSON array of 3 quests
- Raises ValueError on malformed JSON
- Raises ValueError on wrong count
- Raises ValueError on schema mismatch
- Handles markdown code fences gracefully
"""
from __future__ import annotations

import json

import pytest

from ai_services.parsers.quest_output_parser import ParsedQuest, parse_quest_output


# ── Fixtures ──────────────────────────────────────────────────

VALID_QUEST_JSON = [
    {
        "title": "Implement a Binary Search Tree",
        "type": "coding",
        "difficulty": "medium",
        "estimated_minutes": 45,
        "xp_reward": 100,
        "skill_node": "Data Structures",
        "hints": ["Start with insert method", "Recurse left for smaller values"],
    },
    {
        "title": "Debug a Recursive Fibonacci Function",
        "type": "debug",
        "difficulty": "easy",
        "estimated_minutes": 20,
        "xp_reward": 50,
        "skill_node": "Algorithms",
        "hints": ["Check base case"],
    },
    {
        "title": "Research Transformer Architecture",
        "type": "research",
        "difficulty": "medium",
        "estimated_minutes": 30,
        "xp_reward": 80,
        "skill_node": "Machine Learning",
        "hints": [],
    },
]


# ── Happy Path ────────────────────────────────────────────────


def test_parse_quest_output_accepts_valid_json():
    """T4.1: parse_quest_output() returns 3 ParsedQuest objects for valid input."""
    raw = json.dumps(VALID_QUEST_JSON)
    quests = parse_quest_output(raw)

    assert len(quests) == 3
    for q in quests:
        assert isinstance(q, ParsedQuest)


def test_parsed_quest_fields_match_input():
    """T4.1: Parsed fields match the input JSON exactly."""
    raw = json.dumps(VALID_QUEST_JSON)
    quests = parse_quest_output(raw)

    assert quests[0].title == "Implement a Binary Search Tree"
    assert quests[0].type == "coding"
    assert quests[0].difficulty == "medium"
    assert quests[0].estimated_minutes == 45
    assert quests[0].xp_reward == 100
    assert quests[0].skill_node == "Data Structures"
    assert quests[0].hints == ["Start with insert method", "Recurse left for smaller values"]


def test_parse_quest_output_strips_markdown_fences():
    """T4.1: parse_quest_output() handles responses wrapped in ```json ... ```."""
    raw = f"```json\n{json.dumps(VALID_QUEST_JSON)}\n```"
    quests = parse_quest_output(raw)
    assert len(quests) == 3


def test_parse_quest_output_strips_plain_fences():
    """T4.1: parse_quest_output() handles ``` ... ``` without json tag."""
    raw = f"```\n{json.dumps(VALID_QUEST_JSON)}\n```"
    quests = parse_quest_output(raw)
    assert len(quests) == 3


def test_parse_quest_output_empty_hints():
    """T4.1: hints defaults to empty list if not provided."""
    data = [dict(q) for q in VALID_QUEST_JSON]
    del data[0]["hints"]
    raw = json.dumps(data)
    quests = parse_quest_output(raw)
    assert quests[0].hints == []


# ── Error Cases ───────────────────────────────────────────────


def test_parse_quest_output_raises_on_empty_string():
    """T4.1: ValueError on empty Groq response."""
    with pytest.raises(ValueError, match="empty response"):
        parse_quest_output("")


def test_parse_quest_output_raises_on_malformed_json():
    """T4.1: ValueError on non-JSON output from Groq."""
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_quest_output("Sorry, I cannot generate quests right now.")


def test_parse_quest_output_raises_on_wrong_count():
    """T4.1: ValueError when Groq returns fewer or more than 3 quests."""
    raw = json.dumps(VALID_QUEST_JSON[:2])  # Only 2 quests
    with pytest.raises(ValueError, match="expected 3 quests"):
        parse_quest_output(raw)

    raw_4 = json.dumps(VALID_QUEST_JSON + [VALID_QUEST_JSON[0]])  # 4 quests
    with pytest.raises(ValueError, match="expected 3 quests"):
        parse_quest_output(raw_4)


def test_parse_quest_output_raises_on_invalid_type():
    """T4.1: ValueError when quest type is not in allowed set."""
    data = [dict(q) for q in VALID_QUEST_JSON]
    data[0]["type"] = "quiz"  # Not a valid type
    raw = json.dumps(data)
    with pytest.raises(ValueError, match="schema mismatch"):
        parse_quest_output(raw)


def test_parse_quest_output_raises_on_invalid_difficulty():
    """T4.1: ValueError when quest difficulty is not in allowed set."""
    data = [dict(q) for q in VALID_QUEST_JSON]
    data[0]["difficulty"] = "legendary"  # Not a valid difficulty
    raw = json.dumps(data)
    with pytest.raises(ValueError, match="schema mismatch"):
        parse_quest_output(raw)


def test_parse_quest_output_raises_on_missing_required_field():
    """T4.1: ValueError when required field is missing."""
    data = [dict(q) for q in VALID_QUEST_JSON]
    del data[1]["title"]  # Remove required field
    raw = json.dumps(data)
    with pytest.raises(ValueError, match="schema mismatch"):
        parse_quest_output(raw)


def test_parse_quest_output_raises_on_dict_not_array():
    """T4.1: ValueError when Groq returns a dict instead of an array."""
    raw = json.dumps({"quests": VALID_QUEST_JSON})
    with pytest.raises(ValueError, match="expected JSON array"):
        parse_quest_output(raw)
