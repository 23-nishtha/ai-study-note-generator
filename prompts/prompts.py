"""Unified prompt version registry and compatibility re-exports.

Exposes the shared interface across v1_baseline, v2, and v3 so app.py and
gemini_service.py can swap versions without branching logic, while keeping
direct imports from prompts.prompts working.
"""

from __future__ import annotations

from types import ModuleType

from prompts import v1_baseline, v2, v3

PROMPT_MODULES: dict[str, ModuleType] = {
    "v3": v3,
    "v2": v2,
    "v1_baseline": v1_baseline,
}

PROMPT_VERSION_OPTIONS: list[str] = ["v3", "v2", "v1_baseline"]


def get_prompt_module(version: str = "v3") -> ModuleType:
    """Return the prompt module for the requested version."""
    if version not in PROMPT_MODULES:
        raise ValueError(f"Unknown prompt version '{version}'. Expected one of {list(PROMPT_MODULES)}.")
    return PROMPT_MODULES[version]


def get_version_label(version: str) -> str:
    """Return human-readable label for sidebar selector."""
    return getattr(get_prompt_module(version), "VERSION_LABEL", version)


# Compatibility re-exports (default to v3)
VERSION_NAME = v3.VERSION_NAME
VERSION_LABEL = v3.VERSION_LABEL
JSON_MODE = v3.JSON_MODE
build_notes_prompt = v3.build_notes_prompt
build_summary_prompt = v3.build_summary_prompt
build_mcq_prompt = v3.build_mcq_prompt
build_short_answer_prompt = v3.build_short_answer_prompt
build_long_answer_prompt = v3.build_long_answer_prompt
build_flashcards_prompt = v3.build_flashcards_prompt
build_ask_ai_prompt = v3.build_ask_ai_prompt
