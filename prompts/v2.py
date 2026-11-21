"""Prompt v2: explicit role, explicit JSON schema, and source-grounding rules."""

from __future__ import annotations

VERSION_NAME = "v2"
VERSION_LABEL = "v2 · Structured + Grounded"
JSON_MODE = True

_GROUNDING_RULES = """CONSTRAINTS:
- Use ONLY the supplied lecture notes below. Do not use outside knowledge, external definitions, or unstated assumptions.
- If the supplied notes do not cover a requested detail or topic, say so explicitly ("Not covered in the supplied notes.") instead of guessing or filling the gap.
- Return valid JSON matching the exact schema below."""


def build_notes_prompt(notes_text: str) -> str:
    return f"""ROLE:
You are an academic study-pack generator helping college students revise lecture notes accurately.

TASK:
Extract structured study notes (key concepts, definitions, important points, examples, and items to remember) from the supplied notes.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "key_concepts": [{{"title": "string", "explanation": "string"}}],
  "definitions": [{{"term": "string", "definition": "string"}}],
  "important_points": ["string"],
  "examples": [{{"title": "string", "explanation": "string"}}],
  "remember_this": ["string"]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_summary_prompt(notes_text: str, depth: str = "standard") -> str:
    depth_guide = {
        "quick": "a brief ~100-150 word overview in 1-2 sections",
        "standard": "a balanced ~200-350 word summary in 2-4 sections",
        "detailed": "a thorough ~400-600 word summary in 4-6 sections",
    }.get(depth, "a balanced ~200-350 word summary in 2-4 sections")

    return f"""ROLE:
You are an academic study-pack generator helping college students revise lecture notes accurately.

TASK:
Write {depth_guide} from the supplied lecture notes in simple language.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "title": "string",
  "sections": [
    {{"heading": "string", "content": "string"}}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_mcq_prompt(notes_text: str, count: int = 5) -> str:
    return f"""ROLE:
You are an academic study-pack generator creating exam practice questions for university students.

TASK:
Generate {count} multiple-choice questions from the supplied lecture notes.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "questions": [
    {{
      "question": "string",
      "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
      "correct_option": "A",
      "explanation": "string"
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_short_answer_prompt(notes_text: str, count: int = 3) -> str:
    return f"""ROLE:
You are an academic study-pack generator creating short-answer practice questions for university students.

TASK:
Generate {count} short-answer questions with model answers based on the supplied lecture notes.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "questions": [
    {{
      "question": "string",
      "model_answer": "string"
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_long_answer_prompt(notes_text: str, count: int = 4) -> str:
    return f"""ROLE:
You are an academic study-pack generator creating long-answer practice questions for university students.

TASK:
Generate {count} long-answer questions with bulleted answer outlines from the supplied lecture notes.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "questions": [
    {{
      "question": "string",
      "answer_outline": ["string"]
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_flashcards_prompt(notes_text: str, count: int = 10) -> str:
    return f"""ROLE:
You are an academic study-pack generator creating active-recall flashcards for university students.

TASK:
Generate {count} flashcards from the supplied lecture notes.

{_GROUNDING_RULES}

OUTPUT SCHEMA (JSON):
{{
  "flashcards": [
    {{"front": "string", "back": "string"}}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_ask_ai_prompt(notes_text: str, chat_context: str, question: str) -> str:
    return f"""ROLE:
You are a grounded academic tutor answering a student's question about their notes.

CONSTRAINTS:
- Use ONLY the supplied lecture notes. Do not add outside knowledge.
- If the notes do not answer the question, state explicitly: "Not covered in the supplied notes."

SUPPLIED LECTURE NOTES:
{notes_text}

RECENT CONVERSATION:
{chat_context}

STUDENT QUESTION:
{question}"""
