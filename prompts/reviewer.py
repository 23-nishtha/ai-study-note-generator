"""Prompt builders for the post-generation groundedness reviewer step."""

from __future__ import annotations


def build_review_prompt(section_name: str, generated_content: str, source_notes: str) -> str:
    """Build a strict source-grounded verification prompt for a single section."""
    return f"""ROLE:
You are a strict academic fact-checker auditing AI-generated study material against source lecture notes.

TASK:
Check the generated "{section_name}" section below claim-by-claim against the SUPPLIED SOURCE NOTES.

STRICT RULES:
1. Judge ONLY against the SUPPLIED SOURCE NOTES. Never use outside knowledge, general facts, or background training.
2. Treat any reasonable inference, unstated statistic, external example, definition, or extrapolation NOT explicitly stated in the supplied notes as UNSUPPORTED.
3. Explicit refusal text such as "Not covered in the supplied notes" is acceptable and is NOT an unsupported claim.
4. Return JSON ONLY (you may return raw JSON or a ```json fenced block) with this exact schema:
{{
  "status": "passed" | "failed",
  "unsupported_claims": ["exact unsupported claim 1", "..."],
  "reason": "1-2 sentence explanation of the verdict"
}}
5. Validation rule:
   - If you find one or more unsupported claims, "status" MUST be "failed" and "unsupported_claims" MUST be a non-empty list of strings.
   - If every claim is explicitly supported by the notes, "status" MUST be "passed" and "unsupported_claims" MUST be [].
   - NEVER return "status": "failed" with an empty "unsupported_claims" list.

SUPPLIED SOURCE NOTES:
{source_notes}

GENERATED SECTION ({section_name}):
{generated_content}"""


def build_repair_prompt(section_name: str, invalid_output: str, validation_error: str) -> str:
    """Build a single repair prompt when the reviewer output fails parsing or schema checks."""
    return f"""Your previous review output for section "{section_name}" was invalid.

VALIDATION ERROR:
{validation_error}

PREVIOUS INVALID OUTPUT:
{invalid_output}

Repair it and return ONLY valid JSON matching this exact schema:
{{
  "status": "passed" | "failed",
  "unsupported_claims": ["string", ...],
  "reason": "string"
}}

Rules:
- If "status" is "failed", "unsupported_claims" MUST contain at least one non-empty string.
- If "status" is "passed", "unsupported_claims" MUST be [].
- Return JSON only, with no commentary outside the JSON."""
