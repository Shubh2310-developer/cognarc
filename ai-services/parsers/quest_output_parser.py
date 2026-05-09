"""
COGNARC — Quest Output Parser
ai-services/parsers/quest_output_parser.py

T4.1: Parse and validate Groq JSON output into ParsedQuest Pydantic models.
§07: This is the ONLY safe entry point from raw Groq string to typed objects.
§16: Never trust AI output. All outputs pass through Pydantic validators.

Output contract from Groq:
    JSON array of 3 objects, each with:
        title, type, difficulty, estimated_minutes, xp_reward, skill_node, hints

Raises ValueError on:
    - Non-JSON output
    - JSON that doesn't match ParsedQuest schema
    - Array count != 3
    - Any individual field validation error

§19: Parse failures are logged to Sentry by the caller (quest_service.py).
     The raw output is truncated to 500 chars before logging (§16 safety rule).
"""
from __future__ import annotations

import json
import re
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ── Domain Model ─────────────────────────────────────────────


class ParsedQuest(BaseModel):
    """
    Typed representation of a single quest from Groq API output.
    Maps 1:1 with the output schema in SYSTEM_PROMPT_V1.

    §16: extra="forbid" — reject any unexpected AI-generated keys.
    §17: snake_case fields matching the JSON output schema.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    type: Literal["theory", "coding", "debug", "research", "build"]
    difficulty: Literal["easy", "medium", "hard"]
    estimated_minutes: int = Field(ge=5, le=480)
    xp_reward: int = Field(ge=10, le=1000)
    skill_node: str = Field(min_length=1, max_length=200)
    hints: List[str] = Field(default_factory=list)


# ── Parser ────────────────────────────────────────────────────


def _extract_json_array(raw: str) -> str:
    """
    Extract a JSON array from the raw Groq output.

    Handles common Groq responses that include markdown fences (```json ... ```)
    despite the system prompt forbidding them. This is a defense-in-depth
    measure — the system prompt still tells Groq to output raw JSON.

    Returns the raw JSON string for json.loads().
    """
    # Strip leading/trailing whitespace
    raw = raw.strip()

    # Remove markdown code fences if present
    # Matches ```json ... ``` or ``` ... ```
    fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
    match = fence_pattern.search(raw)
    if match:
        raw = match.group(1).strip()

    # Extract first [...] JSON array if embedded in prose
    if not raw.startswith("["):
        array_match = re.search(r"(\[[\s\S]*\])", raw)
        if array_match:
            raw = array_match.group(1)

    return raw


def parse_quest_output(raw: str) -> List[ParsedQuest]:
    """
    T4.1: Parse and validate Groq JSON string → list of ParsedQuest models.

    Raises:
        ValueError: On JSON decode error, validation error, or count != 3.
                    Caller (quest_service) catches this to trigger fallback.

    §16: Never use exec() or eval() on AI output.
    §19: Truncate raw output to 500 chars before logging (called by quest_service).
    """
    if not raw or not raw.strip():
        raise ValueError("Quest parse failure: Groq returned empty response")

    try:
        # First: try to parse the raw output directly as JSON
        stripped = raw.strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            # Fall back to fence/prose extraction
            extracted = _extract_json_array(stripped)
            data = json.loads(extracted)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Quest parse failure: invalid JSON from Groq — {exc}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            f"Quest parse failure: expected JSON array, got {type(data).__name__}"
        )

    try:
        quests = [ParsedQuest(**q) for q in data]
    except (ValidationError, TypeError, KeyError) as exc:
        raise ValueError(f"Quest parse failure: schema mismatch — {exc}") from exc

    if len(quests) != 3:
        raise ValueError(
            f"Quest parse failure: expected 3 quests, got {len(quests)}"
        )

    return quests
