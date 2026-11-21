"""Google Gemini API wrapper and offline demo-mode study-pack generator."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts.prompts import get_prompt_module
from utils.helpers import chunk_text, extract_json

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


class GeminiServiceError(Exception):
    """Raised when a Gemini API call or response parse fails."""


def is_demo_mode() -> bool:
    """Return True when no GEMINI_API_KEY is configured."""
    return not bool(GEMINI_API_KEY)


def call_model(prompt: str, temperature: float = 0.2, json_mode: bool = False) -> str:
    """Send a single prompt to the configured Gemini model and return raw text."""
    if is_demo_mode():
        raise GeminiServiceError("GEMINI_API_KEY is not set.")

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        config_kwargs: dict[str, Any] = {"temperature": temperature}
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        text = (response.text or "").strip()
        if not text:
            raise GeminiServiceError("Gemini returned an empty response.")
        return text
    except GeminiServiceError:
        raise
    except Exception as exc:
        raise GeminiServiceError(f"Gemini API request failed: {exc}") from exc


def _coerce_unstructured_response(task: str, raw_text: str) -> dict[str, Any]:
    """Wrap plain-text responses (e.g. v1_baseline prose) into app.py-compatible dicts."""
    cleaned = raw_text.strip()
    if task == "notes":
        return {
            "key_concepts": [{"title": "Unstructured Notes Output", "explanation": cleaned}],
            "definitions": [],
            "important_points": [],
            "examples": [],
            "remember_this": [],
        }
    if task == "summary":
        return {
            "title": "Generated Summary",
            "sections": [{"heading": "Summary", "content": cleaned}],
        }
    if task in {"mcqs", "short_answers", "long_answers"}:
        return {"questions": [], "raw_text": cleaned}
    if task == "flashcards":
        return {"flashcards": [], "raw_text": cleaned}
    return {"raw_text": cleaned}


def _normalize_dict(task: str, parsed: Any) -> dict[str, Any]:
    """Ensure expected top-level keys exist on parsed JSON payloads."""
    if not isinstance(parsed, dict):
        return _coerce_unstructured_response(task, str(parsed))

    if task == "notes":
        return {
            "key_concepts": list(parsed.get("key_concepts") or []),
            "definitions": list(parsed.get("definitions") or []),
            "important_points": list(parsed.get("important_points") or []),
            "examples": list(parsed.get("examples") or []),
            "remember_this": list(parsed.get("remember_this") or []),
        }
    if task == "summary":
        return {
            "title": str(parsed.get("title") or "Summary"),
            "sections": list(parsed.get("sections") or []),
        }
    if task in {"mcqs", "short_answers", "long_answers"}:
        return {"questions": list(parsed.get("questions") or [])}
    if task == "flashcards":
        return {"flashcards": list(parsed.get("flashcards") or [])}
    return parsed


def _run_structured_prompt(task: str, prompt: str, json_mode: bool) -> dict[str, Any]:
    raw = call_model(prompt, temperature=0.2, json_mode=json_mode)
    try:
        parsed = extract_json(raw)
        return _normalize_dict(task, parsed)
    except ValueError:
        if json_mode:
            raise GeminiServiceError(f"Could not parse JSON for '{task}' from model output.")
        return _coerce_unstructured_response(task, raw)


# ---------------------------------------------------------------------------
# Offline Demo Mode helpers
# ---------------------------------------------------------------------------

def _extract_sentences(text: str, limit: int = 12) -> list[str]:
    """Pull clean declarative sentences from the supplied notes for offline demo mode."""
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", normalized) if len(p.strip()) > 25]
    if not parts and normalized:
        parts = [normalized[:240]]
    return parts[:limit]


def _demo_notes(text: str, prompt_version: str) -> dict[str, Any]:
    sentences = _extract_sentences(text, 8)
    s0 = sentences[0] if len(sentences) > 0 else "Core concept extracted from your supplied notes."
    s1 = sentences[1] if len(sentences) > 1 else s0
    s2 = sentences[2] if len(sentences) > 2 else s0
    s3 = sentences[3] if len(sentences) > 3 else s1

    concepts = [
        {"title": "Core Topic Overview", "explanation": s0},
        {"title": "Primary Mechanism", "explanation": s1},
        {"title": "Key Trade-off / Metric", "explanation": s2},
        {"title": "Practical Handling", "explanation": s3},
    ]

    if prompt_version == "v1_baseline":
        concepts.append({
            "title": "Modern Cloud Optimization (Extrapolated)",
            "explanation": "Modern cloud hypervisors solve this automatically using proprietary hardware-level quantum scheduling.",
        })

    return {
        "key_concepts": concepts,
        "definitions": [
            {"term": "Source Concept 1", "definition": s0},
            {"term": "Source Concept 2", "definition": s1},
        ],
        "important_points": [s0, s1, s2],
        "examples": [{"title": "Example from Notes", "explanation": s3}],
        "remember_this": [s0, s2],
    }


def _demo_summary(text: str, depth: str, prompt_version: str) -> dict[str, Any]:
    sentences = _extract_sentences(text, 8)
    joined_1 = " ".join(sentences[:2]) or "Summary grounded in the supplied notes."
    joined_2 = " ".join(sentences[2:5]) or joined_1

    sections = [
        {"heading": "Main Ideas", "content": joined_1},
        {"heading": "Details & Mechanisms", "content": joined_2},
    ]

    if depth == "quick":
        sections = [{"heading": "Quick Overview", "content": joined_1}]
    elif depth == "detailed":
        joined_3 = " ".join(sentences[5:8]) or joined_2
        sections.append({"heading": "Additional Notes", "content": joined_3})

    if prompt_version == "v1_baseline":
        sections.append({
            "heading": "Industry Benchmarks",
            "content": "Empirical benchmarks show a 65% latency reduction on production Linux servers when applying these defaults.",
        })
    elif prompt_version == "v2":
        sections.append({
            "heading": "Scope Note",
            "content": "Not covered in the supplied notes: hardware-specific clock speed benchmarks.",
        })

    return {"title": f"Study Summary ({depth.title()})", "sections": sections}


def _demo_mcqs(text: str, count: int, prompt_version: str) -> dict[str, Any]:
    sentences = _extract_sentences(text, 6)
    base_items = []
    for i in range(count):
        fact = sentences[i % len(sentences)] if sentences else "The supplied notes describe this concept."
        q_text = f"According to the supplied notes, which statement accurately reflects point {i + 1}?"
        explanation = f"Directly supported by the notes: {fact}"
        correct = "A"
        options = {
            "A": fact,
            "B": "It requires replacing all system memory with static cache.",
            "C": "It only applies when no processes are running.",
            "D": "It disables all scheduling and resource checks permanently.",
        }

        # Inject a deliberate unsupported claim on the final question so offline demo mode
        # demonstrates the reviewer flagging unsupported inferences cleanly.
        if i == count - 1:
            if prompt_version == "v1_baseline":
                q_text = "What throughput gain do production benchmarks report according to standard textbooks?"
                options["A"] = "Benchmarks report an exact 47% throughput improvement."
                explanation = "Standard industry textbooks report a 47% throughput gain."
            elif prompt_version == "v2":
                options["A"] = f"{fact} Therefore, this guarantees zero latency in real-time medical devices."
                explanation = "Inferred applicability to real-time medical devices."
            else:
                options["A"] = f"{fact} This mechanism guarantees zero CPU idle time in multi-core cloud servers."
                explanation = "States zero CPU idle time in multi-core cloud servers."

        base_items.append({
            "question": q_text,
            "options": options,
            "correct_option": correct,
            "explanation": explanation,
        })
    return {"questions": base_items}


def _demo_short_answers(text: str, count: int, prompt_version: str) -> dict[str, Any]:
    sentences = _extract_sentences(text, 6)
    questions = []
    for i in range(count):
        fact = sentences[i % len(sentences)] if sentences else "Covered in the supplied lecture notes."
        answer = fact
        if prompt_version == "v1_baseline" and i == 0:
            answer = f"{fact} POSIX additionally mandates a fixed 5 ms quantum across all desktop operating systems."
        questions.append({
            "question": f"Briefly explain concept {i + 1} covered in the supplied notes.",
            "model_answer": answer,
        })
    return {"questions": questions}


def _demo_long_answers(text: str, count: int) -> dict[str, Any]:
    sentences = _extract_sentences(text, 6)
    questions = []
    for i in range(count):
        fact = sentences[i % len(sentences)] if sentences else "Core topic from notes."
        questions.append({
            "question": f"Discuss the major aspects of topic {i + 1} from the material.",
            "answer_outline": [fact, "Explain key conditions or trade-offs described in the notes."],
        })
    return {"questions": questions}


def _demo_flashcards(text: str, count: int) -> dict[str, Any]:
    sentences = _extract_sentences(text, count)
    cards = [
        {"front": f"Key Point {i + 1}", "back": sentences[i % len(sentences)] if sentences else "From notes."}
        for i in range(min(count, max(4, len(sentences))))
    ]
    return {"flashcards": cards}


# ---------------------------------------------------------------------------
# Public generation functions
# ---------------------------------------------------------------------------

def generate_notes(text: str, prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_notes(text, prompt_version)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_notes_prompt(chunk_text(text))
    return _run_structured_prompt("notes", prompt, getattr(prompt_mod, "JSON_MODE", False))


def generate_summary(text: str, depth: str = "standard", prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_summary(text, depth, prompt_version)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_summary_prompt(chunk_text(text), depth)
    return _run_structured_prompt("summary", prompt, getattr(prompt_mod, "JSON_MODE", False))


def generate_mcqs(text: str, count: int = 5, prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_mcqs(text, count, prompt_version)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_mcq_prompt(chunk_text(text), count)
    return _run_structured_prompt("mcqs", prompt, getattr(prompt_mod, "JSON_MODE", False))


def generate_short_answers(text: str, count: int = 3, prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_short_answers(text, count, prompt_version)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_short_answer_prompt(chunk_text(text), count)
    return _run_structured_prompt("short_answers", prompt, getattr(prompt_mod, "JSON_MODE", False))


def generate_long_answers(text: str, count: int = 4, prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_long_answers(text, count)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_long_answer_prompt(chunk_text(text), count)
    return _run_structured_prompt("long_answers", prompt, getattr(prompt_mod, "JSON_MODE", False))


def generate_flashcards(text: str, count: int = 10, prompt_version: str = "v3") -> dict[str, Any]:
    if is_demo_mode():
        return _demo_flashcards(text, count)
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_flashcards_prompt(chunk_text(text), count)
    return _run_structured_prompt("flashcards", prompt, getattr(prompt_mod, "JSON_MODE", False))


def ask_question(text: str, chat_context: str, question: str, prompt_version: str = "v3") -> str:
    if is_demo_mode():
        sentences = _extract_sentences(text, 3)
        snippet = sentences[0] if sentences else "your uploaded notes"
        return f"(Demo Mode) Based on the supplied notes: {snippet}"
    prompt_mod = get_prompt_module(prompt_version)
    prompt = prompt_mod.build_ask_ai_prompt(chunk_text(text), chat_context, question)
    return call_model(prompt, temperature=0.2, json_mode=False)
