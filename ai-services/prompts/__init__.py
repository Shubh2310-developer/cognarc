"""
COGNARC — Prompt Registry
ai-services/prompts/__init__.py

T3.3: PROMPT_VERSIONS registry — single source of truth for prompt versioning.
§16: Never edit a deployed version in-place. Always create a new version file.
"""
from __future__ import annotations

from ai_services.prompts import quest_generation_v1, quest_generation_v2

# Registry: version_string → prompt module
# Keys are semantic version strings. Add new entries only — never remove deployed ones.
PROMPT_VERSIONS: dict[str, object] = {
    "v1": quest_generation_v1,
    "v2": quest_generation_v2,  # stub — not yet deployed
}

__all__ = ["PROMPT_VERSIONS"]
