"""Post-generation groundedness reviewer for study pack sections."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from prompts.reviewer import build_repair_prompt, build_review_prompt
from services import gemini_service
from services.gemini_service import GeminiServiceError
from utils.helpers import chunk_text, extract_json

REVIEWED_SECTIONS: tuple[str, ...] = (
    "summary",
    "key_concepts",
    "mcqs",
    "short_answers",
)

SECTION_LABELS: dict[str, str] = {
    "summary": "Summary",
    "key_concepts": "Key Concepts",
    "mcqs": "MCQs",
    "short_answers": "Short-Answer Q&A",
}


def validate_review_payload(payload: Any) -> dict[str, Any]:
    """Validate reviewer JSON schema and enforce strict consistency rules."""
    if not isinstance(payload, dict):
        raise ValueError("Reviewer response must be a JSON object.")

    status = payload.get("status")
    if status not in {"passed", "failed"}:
        raise ValueError("Field 'status' must be either 'passed' or 'failed'.")

    claims = payload.get("unsupported_claims")
    if not isinstance(claims, list) or not all(isinstance(c, str) and c.strip() for c in claims):
        raise ValueError("Field 'unsupported_claims' must be a list of non-empty strings.")

    cleaned_claims = [c.strip() for c in claims]

    # Explicit requirement: "failed" with an empty unsupported_claims list is invalid.
    if status == "failed" and not cleaned_claims:
        raise ValueError("Status 'failed' must include at least one unsupported claim.")
    if status == "passed" and cleaned_claims:
        raise ValueError("Status 'passed' cannot include unsupported claims.")

    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Field 'reason' must be a non-empty string.")

    return {
        "status": status,
        "unsupported_claims": cleaned_claims,
        "reason": reason.strip(),
    }


def format_section_for_review(section_key: str, pack: dict[str, Any]) -> str:
    """Serialize a single study-pack section into plain text for the reviewer prompt."""
    if section_key == "summary":
        std = pack.get("summaries", {}).get("standard", {})
        parts = [f"Title: {std.get('title', '')}"]
        for sec in std.get("sections", []):
            parts.append(f"## {sec.get('heading', '')}\n{sec.get('content', '')}")
        return "\n\n".join(parts).strip()

    if section_key == "key_concepts":
        concepts = pack.get("notes", {}).get("key_concepts", [])
        if not concepts:
            return "(No key concepts generated.)"
        return "\n".join(
            f"- {item.get('title', '')}: {item.get('explanation', '')}" for item in concepts
        )

    if section_key == "mcqs":
        mcqs = pack.get("mcqs", {})
        questions = mcqs.get("questions", [])
        if not questions:
            return mcqs.get("raw_text") or "(No MCQs generated.)"
        lines: list[str] = []
        for idx, q in enumerate(questions, 1):
            opts = " | ".join(f"{k}. {v}" for k, v in (q.get("options") or {}).items())
            lines.append(
                f"MCQ {idx}: {q.get('question', '')}\n"
                f"Options: {opts}\n"
                f"Correct: {q.get('correct_option', '')}\n"
                f"Explanation: {q.get('explanation', '')}"
            )
        return "\n\n".join(lines)

    if section_key == "short_answers":
        short_qs = pack.get("short_qs", {})
        questions = short_qs.get("questions", [])
        if not questions:
            return short_qs.get("raw_text") or "(No short-answer questions generated.)"
        return "\n\n".join(
            f"Q{idx}: {q.get('question', '')}\nModel Answer: {q.get('model_answer', '')}"
            for idx, q in enumerate(questions, 1)
        )

    raise ValueError(f"Unsupported section key '{section_key}'.")


def _demo_review_for(section_key: str, prompt_version: str) -> dict[str, Any]:
    """Return canned demo-mode review results matching canned demo outputs."""
    if prompt_version == "v1_baseline":
        canned_v1 = {
            "summary": {
                "status": "failed",
                "unsupported_claims": [
                    "Claims empirical benchmarks show a 65% latency reduction on production Linux servers."
                ],
                "reason": "The summary adds benchmark statistics not present in the supplied notes.",
            },
            "key_concepts": {
                "status": "failed",
                "unsupported_claims": [
                    "Claims modern cloud hypervisors use proprietary hardware-level quantum scheduling."
                ],
                "reason": "Introduces an outside concept not stated anywhere in the notes.",
            },
            "mcqs": {
                "status": "failed",
                "unsupported_claims": [
                    "MCQ 5 claims standard benchmarks report an exact 47% throughput improvement."
                ],
                "reason": "MCQ 5 relies on fabricated benchmark numbers outside the supplied notes.",
            },
            "short_answers": {
                "status": "failed",
                "unsupported_claims": [
                    "Q1 answer claims POSIX mandates a fixed 5 ms quantum across all desktop operating systems."
                ],
                "reason": "Adds an unstated POSIX standard claim absent from the lecture notes.",
            },
        }
        return canned_v1[section_key]

    if prompt_version == "v2":
        if section_key == "mcqs":
            return {
                "status": "failed",
                "unsupported_claims": [
                    "Final MCQ claims this guarantees zero latency in real-time medical devices."
                ],
                "reason": "Includes an unstated real-time medical device inference not in the notes.",
            }
        return {
            "status": "passed",
            "unsupported_claims": [],
            "reason": "All claims in this section are directly supported by the supplied notes.",
        }

    # Default v3 demo mode: keep at least one failed section so the feature works offline.
    if section_key == "mcqs":
        return {
            "status": "failed",
            "unsupported_claims": [
                "Final MCQ claims this mechanism guarantees zero CPU idle time in multi-core cloud servers."
            ],
            "reason": "MCQ 5 extrapolates beyond the notes by claiming zero CPU idle time in multi-core cloud servers.",
        }
    return {
        "status": "passed",
        "unsupported_claims": [],
        "reason": "All statements are explicitly supported by the supplied lecture notes.",
    }


def review_section(
    section_key: str,
    generated_content: str,
    source_notes: str,
    prompt_version: str = "v3",
) -> dict[str, Any]:
    """Review one generated section against source notes with at most one repair retry."""
    if gemini_service.is_demo_mode():
        return _demo_review_for(section_key, prompt_version)

    section_label = SECTION_LABELS.get(section_key, section_key)
    notes_snippet = chunk_text(source_notes)
    prompt = build_review_prompt(section_label, generated_content, notes_snippet)

    raw_output = ""
    try:
        raw_output = gemini_service.call_model(prompt, temperature=0.0, json_mode=False)
        parsed = extract_json(raw_output)
        return validate_review_payload(parsed)
    except (GeminiServiceError, ValueError) as first_err:
        # Attempt exactly ONE repair when output is unparseable or violates schema.
        previous = raw_output or str(first_err)
        repair_prompt = build_repair_prompt(section_label, previous, str(first_err))
        try:
            repaired_raw = gemini_service.call_model(
                repair_prompt, temperature=0.0, json_mode=False
            )
            repaired_parsed = extract_json(repaired_raw)
            return validate_review_payload(repaired_parsed)
        except (GeminiServiceError, ValueError) as repair_err:
            return {
                "status": "verifier_error",
                "unsupported_claims": [],
                "reason": f"Verifier output remained invalid after repair attempt: {repair_err}",
            }


def review_study_pack(
    pack: dict[str, Any],
    source_notes: str,
    prompt_version: str = "v3",
) -> dict[str, dict[str, Any]]:
    """Review summary, key_concepts, mcqs, and short_answers separately."""
    if gemini_service.is_demo_mode():
        return {
            key: _demo_review_for(key, prompt_version)
            for key in REVIEWED_SECTIONS
        }

    section_inputs = {
        key: format_section_for_review(key, pack)
        for key in REVIEWED_SECTIONS
    }
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(REVIEWED_SECTIONS)) as pool:
        futures = {
            key: pool.submit(
                review_section, key, content, source_notes, prompt_version
            )
            for key, content in section_inputs.items()
        }
        for key, future in futures.items():
            results[key] = future.result()
    return results
