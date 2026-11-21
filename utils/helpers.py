"""Shared utility helpers for session state, formatting, JSON parsing, and run logging."""

from __future__ import annotations

import csv
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

RUNS_CSV_COLUMNS = [
    "timestamp",
    "notes_filename",
    "prompt_version",
    "n_key_concepts",
    "n_mcqs",
    "n_short_answers",
    "n_unsupported_claims",
    "sections_failed",
    "verifier_errors",
]


def init_session_state() -> None:
    """Initialize all expected Streamlit session_state keys once."""
    defaults = {
        "page": "dashboard",
        "materials": [],
        "study_pack": {},
        "quiz_state": {},
        "flashcard_state": {},
        "chat_history": {},
        "active_material_id": None,
        "notes_generated_count": 0,
        "questions_generated_count": 0,
        "flashcards_generated_count": 0,
        "prompt_version": "v3",
        "summary_depth": "standard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_active_material() -> dict | None:
    """Return the currently selected material dict, or None."""
    active_id = st.session_state.get("active_material_id")
    if not active_id:
        return None
    for material in st.session_state.get("materials", []):
        if material["id"] == active_id:
            return material
    return None


def get_pack_for(material_id: str) -> dict | None:
    """Return the cached study pack for a material ID, or None."""
    return st.session_state.get("study_pack", {}).get(material_id)


def set_page(page: str) -> None:
    """Switch the active page key in session_state."""
    st.session_state["page"] = page


def new_id() -> str:
    """Generate a short unique identifier."""
    return uuid.uuid4().hex[:10]


def char_count(text: str) -> int:
    """Return character count of text."""
    return len(text or "")


def estimate_pages(text: str, chars_per_page: int = 1800) -> int:
    """Estimate page count from plain text length."""
    cleaned = (text or "").strip()
    if not cleaned:
        return 1
    return max(1, (len(cleaned) + chars_per_page - 1) // chars_per_page)


def truncate(text: str, max_len: int = 60) -> str:
    """Truncate text cleanly with an ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def format_file_size(size_bytes: int) -> str:
    """Format byte size into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_date(dt: datetime | str | None) -> str:
    """Format a datetime object for display."""
    if dt is None:
        return "Just now"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%b %d, %H:%M")


def chunk_text(text: str, max_chars: int = 24000) -> str:
    """Cap overly long notes while preserving the opening and closing sections."""
    cleaned = (text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    head_len = int(max_chars * 0.6)
    tail_len = max_chars - head_len
    marker = "\n\n[... middle section truncated due to length ...]\n\n"
    return cleaned[:head_len].rstrip() + marker + cleaned[-tail_len:].lstrip()


def _find_balanced_json(text: str) -> str | None:
    """Locate the first balanced JSON object or array inside text."""
    for start_idx, ch in enumerate(text):
        if ch not in "{[":
            continue
        closing = "}" if ch == "{" else "]"
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start_idx, len(text)):
            curr = text[idx]
            if escaped:
                escaped = False
                continue
            if curr == "\\" and in_string:
                escaped = True
                continue
            if curr == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if curr == ch:
                depth += 1
            elif curr == closing:
                depth -= 1
                if depth == 0:
                    return text[start_idx : idx + 1]
    return None


def extract_json(raw_text: str) -> Any:
    """Parse JSON directly, from markdown code fences, or from first balanced block."""
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response; expected JSON.")

    cleaned = raw_text.strip()

    # 1. Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        try:
            return json.loads(fenced)
        except json.JSONDecodeError:
            candidate = _find_balanced_json(fenced)
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass

    # 3. Scan full text for first balanced JSON object/array
    candidate = _find_balanced_json(cleaned)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON structure: {exc}") from exc

    raise ValueError("No JSON object or array found in model response.")


def append_run_log(csv_path: str | Path, row: dict[str, Any]) -> None:
    """Append a single generation-and-review run record to runs.csv."""
    path = Path(csv_path)
    write_header = not path.exists() or path.stat().st_size == 0

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUNS_CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in RUNS_CSV_COLUMNS})
