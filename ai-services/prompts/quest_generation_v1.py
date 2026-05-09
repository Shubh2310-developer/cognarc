"""
COGNARC — Quest Generation Prompt v1
ai-services/prompts/quest_generation_v1.py

T3.1: Versioned system + user prompt templates for MVP quest generation.
T3.3: Registered in PROMPT_VERSIONS dict.

§07: Single prompt template — no chain-of-thought, no multi-step prompts.
§16: Prompts are versioned. Never edit a deployed version in-place.
     Create v2.py when changes are needed.
§16: Prompt injection risk: caller must sanitize user-controlled strings
     (username, skill node names) before passing to format_user_prompt_v1().

Output contract: Groq must return a JSON array of exactly 3 objects.
The output schema is embedded in the system prompt to enforce structure.
"""
from __future__ import annotations

# ── System Prompt V1 ──────────────────────────────────────────

SYSTEM_PROMPT_V1 = """You are Cognarc, an expert skill development engine for developers.
Generate exactly 3 learning quests as valid JSON matching the provided schema.
Rules:
  - Vary quest types across the 3 quests (no repeated type)
  - Match difficulty to user level and difficulty_modifier
  - Quests must be completable in estimated_minutes on a laptop
  - Do not generate quests similar to recent_quest_summaries
  - Every quest must map to exactly one skill_node
  - Output ONLY valid JSON. No explanation, no markdown fences.

Output schema (array of 3 objects):
[
  {
    "title": string,
    "type": "theory"|"coding"|"debug"|"research"|"build",
    "difficulty": "easy"|"medium"|"hard",
    "estimated_minutes": integer,
    "xp_reward": integer,
    "skill_node": string,
    "hints": [string]
  }
]"""

# ── User Prompt Template V1 ───────────────────────────────────

USER_PROMPT_TEMPLATE_V1 = """USER CONTEXT:
- Level: {user_level} | Skill Focus: {skill_node_current} ({node_progress_pct}% complete)
- Streak: {streak_count} days | Difficulty modifier: {difficulty_modifier}
- 7-day completion rate: {completion_rate_7d_pct}%
- Recent quest types: {recent_quest_types}
- Recent quest summaries (do NOT repeat): {recent_quest_summaries}

Generate today's 3 quests."""

# ── Template Formatting ───────────────────────────────────────

_REQUIRED_CONTEXT_KEYS = (
    "user_level",
    "skill_node_current",
    "node_progress_pct",
    "streak_count",
    "difficulty_modifier",
    "completion_rate_7d_pct",
    "recent_quest_types",
    "recent_quest_summaries",
)


def format_user_prompt_v1(context: dict) -> str:
    """
    Render the v1 user prompt with the provided context dict.

    Applies safe defaults for any missing keys to ensure the prompt
    is always well-formed, even with partial context.

    §16: Caller (quest_context_builder.py) MUST sanitize all user-controlled
    strings BEFORE calling this function. Sanitization is NOT done here
    to maintain separation of concerns (template ≠ sanitizer).

    Args:
        context: Dict with keys matching USER_PROMPT_TEMPLATE_V1 placeholders.

    Returns:
        Formatted user prompt string ready for Groq API.
    """
    safe = {
        "user_level": context.get("user_level", 1),
        "skill_node_current": context.get("skill_node_current", "Python Fundamentals"),
        "node_progress_pct": context.get("node_progress_pct", 0),
        "streak_count": context.get("streak_count", 0),
        "difficulty_modifier": context.get("difficulty_modifier", 1.0),
        "completion_rate_7d_pct": context.get("completion_rate_7d_pct", 0),
        "recent_quest_types": context.get("recent_quest_types", "none"),
        "recent_quest_summaries": context.get("recent_quest_summaries", "none"),
    }
    return USER_PROMPT_TEMPLATE_V1.format(**safe)
