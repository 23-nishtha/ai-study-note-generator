"""Prompt v1 (baseline): plain role + task + required output list.

Intentionally weak control version: no JSON output schema, no source-grounding
constraint, and no instruction to refuse when notes omit information.
"""

from __future__ import annotations

VERSION_NAME = "v1_baseline"
VERSION_LABEL = "v1 · Baseline (plain prompt)"
JSON_MODE = False


def build_notes_prompt(notes_text: str) -> str:
    return (
        "You are a helpful study assistant.\n"
        "Read the lecture notes below and create comprehensive study notes.\n"
        "Include:\n"
        "- Key concepts\n"
        "- Definitions\n"
        "- Important points\n"
        "- Examples\n"
        "- Things to remember\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_summary_prompt(notes_text: str, depth: str = "standard") -> str:
    return (
        "You are a helpful study assistant.\n"
        f"Write a {depth} summary of the lecture notes below.\n"
        "Include a clear title and organized sections with headings.\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_mcq_prompt(notes_text: str, count: int = 5) -> str:
    return (
        "You are a helpful study assistant.\n"
        f"Create {count} multiple-choice questions based on the lecture notes below.\n"
        "Include:\n"
        "- Each question\n"
        "- Answer options\n"
        "- The correct answer\n"
        "- A short explanation\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_short_answer_prompt(notes_text: str, count: int = 3) -> str:
    return (
        "You are a helpful study assistant.\n"
        f"Create {count} short-answer practice questions with model answers "
        "for the lecture notes below.\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_long_answer_prompt(notes_text: str, count: int = 4) -> str:
    return (
        "You are a helpful study assistant.\n"
        f"Create {count} long-answer essay questions with bullet-point outlines "
        "for the lecture notes below.\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_flashcards_prompt(notes_text: str, count: int = 10) -> str:
    return (
        "You are a helpful study assistant.\n"
        f"Create {count} study flashcards (front and back) from the lecture notes below.\n\n"
        f"Lecture notes:\n{notes_text}"
    )


def build_ask_ai_prompt(notes_text: str, chat_context: str, question: str) -> str:
    return (
        "You are a helpful study assistant.\n"
        "Answer the student's question about the lecture notes below.\n\n"
        f"Lecture notes:\n{notes_text}\n\n"
        f"Recent conversation:\n{chat_context}\n\n"
        f"Student question: {question}"
    )
