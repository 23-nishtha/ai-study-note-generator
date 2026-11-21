"""Prompt v3: v2 plus few-shot examples and strict formatting/count constraints."""

from __future__ import annotations

VERSION_NAME = "v3"
VERSION_LABEL = "v3 · Few-Shot + Strict Constraints"
JSON_MODE = True

_STRICT_RULES = """STRICT CONSTRAINTS:
- Use ONLY facts explicitly stated in the supplied lecture notes. Never bring in outside facts, textbook trivia, formulas, or reasonable inferences not directly written in the notes.
- If the notes do not cover a requested detail or fewer distinct items exist than requested, write "Not covered in the supplied notes." instead of inventing content.
- Keep language simple, clear, and concise.
- Output raw valid JSON ONLY. No preamble, no markdown commentary, no trailing text."""


def build_notes_prompt(notes_text: str) -> str:
    return f"""ROLE:
You are a rigorous academic study-pack generator for college students.

TASK:
Extract organized study notes from the supplied lecture notes under five keys:
key_concepts (4-6 core ideas), definitions, important_points, examples, and remember_this.

{_STRICT_RULES}

OUTPUT SCHEMA:
{{
  "key_concepts": [{{"title": "string", "explanation": "1-2 sentences grounded in notes"}}],
  "definitions": [{{"term": "string", "definition": "1 sentence grounded in notes"}}],
  "important_points": ["string"],
  "examples": [{{"title": "string", "explanation": "string"}}],
  "remember_this": ["string"]
}}

FEW-SHOT EXAMPLE:
Notes snippet: "Paging divides physical memory into fixed-size blocks called frames and logical memory into blocks of the same size called pages. External fragmentation is avoided because any free frame can be assigned to any process."
Output:
{{
  "key_concepts": [
    {{"title": "Paging", "explanation": "Divides physical memory into fixed-size frames and logical memory into equal-sized pages so any free frame can be assigned to any process."}}
  ],
  "definitions": [
    {{"term": "Frame", "definition": "A fixed-size block of physical memory."}},
    {{"term": "Page", "definition": "A fixed-size block of logical memory matching frame size."}}
  ],
  "important_points": ["Paging avoids external fragmentation because any free frame can be allocated to any process."],
  "examples": [],
  "remember_this": ["Frames are physical memory blocks; pages are equal-sized logical memory blocks."]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_summary_prompt(notes_text: str, depth: str = "standard") -> str:
    depth_rules = {
        "quick": "exactly 1-2 short sections totaling 90-140 words",
        "standard": "2-4 sections totaling 180-300 words",
        "detailed": "4-6 sections totaling 350-550 words",
    }.get(depth, "2-4 sections totaling 180-300 words")

    return f"""ROLE:
You are a rigorous academic study-pack generator for college students.

TASK:
Produce a {depth} summary ({depth_rules}) grounded strictly in the supplied lecture notes.

{_STRICT_RULES}

OUTPUT SCHEMA:
{{
  "title": "string",
  "sections": [{{"heading": "string", "content": "string"}}]
}}

FEW-SHOT EXAMPLE:
Notes snippet: "TCP is a connection-oriented transport protocol that uses a three-way handshake before sending data and guarantees ordered delivery."
Output:
{{
  "title": "TCP Basics",
  "sections": [
    {{"heading": "Connection Setup and Reliability", "content": "TCP is a connection-oriented transport protocol. It performs a three-way handshake prior to data transfer and guarantees that packets arrive in order."}}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_mcq_prompt(notes_text: str, count: int = 5) -> str:
    return f"""ROLE:
You are a rigorous academic exam-question writer for university students.

TASK:
Create EXACTLY {count} multiple-choice questions grounded strictly in the supplied lecture notes.

{_STRICT_RULES}
- Produce exactly {count} objects in "questions".
- Every question MUST have exactly 4 options keyed "A", "B", "C", and "D".
- "correct_option" MUST be one of "A", "B", "C", or "D".
- "explanation" must be 1 sentence citing only facts from the notes.

OUTPUT SCHEMA:
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

FEW-SHOT EXAMPLE:
Notes snippet: "In Round Robin scheduling, each process receives a fixed time slice called a time quantum. If it does not finish within its quantum, it is preempted and moved to the back of the ready queue."
Output:
{{
  "questions": [
    {{
      "question": "What happens in Round Robin scheduling when a process does not finish within its time quantum?",
      "options": {{
        "A": "It is terminated immediately",
        "B": "It is preempted and placed at the back of the ready queue",
        "C": "Its priority is permanently lowered",
        "D": "It stays on the CPU until completion"
      }},
      "correct_option": "B",
      "explanation": "The notes state that an unfinished process is preempted and moved to the back of the ready queue."
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_short_answer_prompt(notes_text: str, count: int = 3) -> str:
    return f"""ROLE:
You are a rigorous academic exam-question writer for university students.

TASK:
Create EXACTLY {count} short-answer questions with model answers grounded strictly in the supplied lecture notes.

{_STRICT_RULES}
- Produce exactly {count} objects in "questions".
- Format each "model_answer" as 1-3 direct sentences in simple language using only facts stated in the notes.

OUTPUT SCHEMA:
{{
  "questions": [
    {{
      "question": "string",
      "model_answer": "1-3 sentences grounded strictly in the notes"
    }}
  ]
}}

FEW-SHOT EXAMPLE:
Notes snippet: "Aging prevents starvation in Priority Scheduling by gradually increasing the priority of processes that wait in the ready queue for a long time."
Output:
{{
  "questions": [
    {{
      "question": "How does aging solve starvation in Priority Scheduling?",
      "model_answer": "Aging prevents low-priority processes from waiting indefinitely by gradually raising the priority of processes that remain in the ready queue for a long time."
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_long_answer_prompt(notes_text: str, count: int = 4) -> str:
    return f"""ROLE:
You are a rigorous academic exam-question writer for university students.

TASK:
Create EXACTLY {count} long-answer questions with bullet-point outlines grounded strictly in the supplied lecture notes.

{_STRICT_RULES}
- Produce exactly {count} objects in "questions", each with 3-5 concise outline points.

OUTPUT SCHEMA:
{{
  "questions": [
    {{
      "question": "string",
      "answer_outline": ["string", "string", "string"]
    }}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_flashcards_prompt(notes_text: str, count: int = 10) -> str:
    return f"""ROLE:
You are a rigorous academic study-pack generator creating active-recall flashcards.

TASK:
Create up to {count} concise flashcards grounded strictly in the supplied lecture notes.

{_STRICT_RULES}

OUTPUT SCHEMA:
{{
  "flashcards": [
    {{"front": "term or short question", "back": "concise answer from notes"}}
  ]
}}

SUPPLIED LECTURE NOTES:
{notes_text}"""


def build_ask_ai_prompt(notes_text: str, chat_context: str, question: str) -> str:
    return f"""ROLE:
You are a strictly grounded academic tutor.

CONSTRAINTS:
- Answer using ONLY facts explicitly present in the supplied lecture notes.
- Do not infer or import outside knowledge.
- If the notes do not cover the question, reply: "Not covered in the supplied notes."

SUPPLIED LECTURE NOTES:
{notes_text}

RECENT CONVERSATION:
{chat_context}

STUDENT QUESTION:
{question}"""
