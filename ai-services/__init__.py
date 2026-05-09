"""
COGNARC — AI Services Package
ai-services/__init__.py

§07 AI Isolation: ALL AI logic lives here. Never import into apps/api/services/ directly.
Public interface exposes ONLY generate_quests() — the single MVP entry point.

T1.3: Expose generate_quests() as the only public interface.

Usage (from apps/api via adapter interface):
    from ai_services import generate_quests
    quests = generate_quests(context)
"""
from __future__ import annotations

from ai_services.adapters.groq_adapter import GroqAdapter
from ai_services.parsers.quest_output_parser import parse_quest_output, ParsedQuest
from ai_services.prompts.quest_generation_v1 import (
    SYSTEM_PROMPT_V1,
    format_user_prompt_v1,
)
from ai_services.validation.quest_validator import validate_quests

__all__ = [
    "generate_quests",
    "ParsedQuest",
]

# Module-level adapter singleton (lazy init — no I/O at import time)
_adapter: GroqAdapter | None = None


def _get_adapter() -> GroqAdapter:
    global _adapter
    if _adapter is None:
        _adapter = GroqAdapter()
    return _adapter


def generate_quests(context: dict) -> list[ParsedQuest]:
    """
    MVP single entry-point: build prompts → call Groq → parse → validate.
    Context dict keys: user_level, skill_node_current, node_progress_pct,
                       streak_count, difficulty_modifier, completion_rate_7d_pct,
                       recent_quest_types, recent_quest_summaries.

    Returns exactly 3 validated ParsedQuest objects.
    Raises ValueError on parse/validation failure (caller handles fallback).
    §07: Single synchronous Groq call — no agents, no LangGraph.
    """
    adapter = _get_adapter()
    user_prompt = format_user_prompt_v1(context)
    raw = adapter.complete(
        system_prompt=SYSTEM_PROMPT_V1,
        user_prompt=user_prompt,
    )
    quests = parse_quest_output(raw)
    validated = validate_quests(quests, user_level=context.get("user_level", 1))
    return validated
