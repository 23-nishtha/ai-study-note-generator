# Project Report: StudyPack AI (AI Study Notes Generator)

**Team ID:** PE-B13-07
**Team Name:** PromptCraft
**Batch / Group:** B13-B24
**Team Leader:** Nishtha Mahani (S24CSEU1230)

**Team Members:**
1. Nishtha Mahani (S24CSEU1230) — Leader
2. Aditya Singh (S24CSEU1228)
3. Goutam Kumar (S24CSEU1214)
4. Aditya Singh (S24CSEU1255)
5. Arjun Tiwari (S24CSEU1293)
6. Sambhav Jain (S24CSEU1216)

---

## Abstract

The AI Study Notes Generator is a web-based application that leverages
generative artificial intelligence to help students convert raw study
material — textbook chapters, lecture notes, or pasted text — into
structured, exam-ready learning resources. The system accepts documents in
PDF, DOCX, or plain text format, extracts their textual content, and uses the
Google Gemini large language model to automatically generate organized notes,
multi-depth summaries, multiple-choice and written practice questions, active
recall flashcards, and a contextual question-answering assistant. Built with
Python and Streamlit, the application demonstrates how generative AI can be
integrated into a lightweight, practical education tool without the
complexity of a full production stack, while still delivering a premium,
modern user interface comparable to commercial AI SaaS products.

---

## Introduction

Students today are overwhelmed with study material scattered across PDFs,
slides, and handwritten or typed notes, and converting that raw material into
a form suitable for revision — organized notes, summaries, and self-test
questions — is a time-consuming manual task. Recent advances in generative
AI, particularly large language models (LLMs), make it possible to automate
much of this process: an LLM can read a passage of text and, guided by a
well-designed prompt, produce coherent notes, questions, and explanations
grounded in that text. This project explores that idea directly, building an
end-to-end application that takes a student from "I have a document" to "I
have notes, a quiz, and flashcards" in a single click.

---

## Problem Statement

Manually converting study material into revision-ready notes, summaries, and
practice questions is slow, inconsistent, and mentally taxing, especially
under exam time pressure. Existing note-taking tools are largely passive —
they store what the student types but do not generate new study aids from
existing material. Students need a tool that can read their own material and
actively produce structured notes, multiple forms of self-testing content,
and answer follow-up questions, without requiring them to leave a single,
simple interface.

---

## Existing System

Currently, students rely on a combination of:

- **Manual note-taking**, which is slow and depends entirely on the
  student's own summarization skill.
- **Generic AI chatbots**, which can answer questions but do not provide a
  structured, repeatable workflow for notes, quizzes, and flashcards
  specific to uploaded material.
- **Flashcard apps** (e.g., Anki), which require the student to manually
  author every card.
- **PDF readers/highlighters**, which help annotate material but generate no
  new content.

None of these existing tools combine document ingestion, structured note
generation, multi-format question generation, and grounded Q&A in a single,
purpose-built workflow.

---

## Proposed System

The proposed system, StudyAI, is a single Streamlit web application that:

1. Accepts study material via file upload (PDF/DOCX/TXT) or direct paste.
2. Extracts plain text from the material using lightweight parsing
   libraries.
3. Sends the extracted text to the Google Gemini API using carefully
   engineered, task-specific prompts.
4. Renders the AI's structured JSON responses as polished, card-based UI
   components: notes, summaries, quizzes, flashcards, and a chat interface.
5. Allows the student to download the complete generated study pack.

The system deliberately avoids unnecessary complexity (no database, no
vector store, no separate backend server) while still producing a
professional, modern user experience.

---

## Objectives

- To automate the creation of structured study notes from raw material.
- To generate multiple types of practice questions (MCQ, short-answer,
  long-answer) directly from that material.
- To provide an active-recall flashcard study mode.
- To provide a conversational assistant that answers questions strictly
  grounded in the uploaded material (minimizing hallucination).
- To deliver all of the above through an interface that feels like a
  polished, professional education product rather than a basic script.

---

## Scope

**In scope:** single-user, single-session study material processing;
PDF/DOCX/TXT ingestion; AI-generated notes, summaries, MCQs, short/long
questions, flashcards, and Q&A; downloadable notes.

**Out of scope:** multi-user accounts and authentication, persistent
database storage across sessions, collaborative study features, mobile
native apps, and spaced-repetition scheduling algorithms.

---

## Methodology

The project follows an iterative, modular development approach:

1. **Document ingestion layer** — implemented first, using `pypdf` and
   `python-docx` to reliably extract plain text from common file formats.
2. **Prompt engineering layer** — a dedicated `prompts/prompts.py` module
   defines one prompt template per generation task, each following a
   consistent ROLE / CONTEXT / TASK / CONSTRAINTS / OUTPUT FORMAT structure
   and requesting strict JSON output for reliable parsing.
3. **AI service layer** — `services/gemini_service.py` wraps all calls to
   the Gemini API, handling configuration, JSON-mode responses, and error
   handling in one place.
4. **Presentation layer** — `app.py` uses Streamlit with extensive custom
   CSS to render a card-based, premium UI, replacing Streamlit's default
   appearance entirely.
5. **Testing** — manual testing with the included sample study material
   (`data/sample_study_material.txt`) as well as real PDF/DOCX files, to
   validate parsing robustness and prompt output quality.

---

## System Architecture

```
                ┌─────────────────────────┐
                │        Streamlit UI      │
                │   (app.py — pages, CSS)  │
                └────────────┬─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
   ┌──────────▼───────┐ ┌────▼─────────┐ ┌──▼─────────────┐
   │ document_parser.py│ │ prompts.py   │ │ gemini_service.py│
   │ (PDF/DOCX/TXT →   │ │ (prompt      │ │ (Gemini API calls,│
   │  plain text)       │ │  templates)  │ │  JSON parsing)   │
   └───────────────────┘ └──────────────┘ └────────┬─────────┘
                                                     │
                                          ┌──────────▼─────────┐
                                          │  Google Gemini API   │
                                          └─────────────────────┘
```

Session state (uploaded materials, generated study packs, quiz/flashcard
progress, and chat history) is held entirely in Streamlit's
`st.session_state`, avoiding the need for an external database.

---

## Modules

| Module | Responsibility |
|---|---|
| `app.py` | UI rendering, page routing, session state orchestration |
| `services/document_parser.py` | Extracts text from PDF, DOCX, TXT |
| `services/gemini_service.py` | Configures and calls the Gemini API; parses JSON responses |
| `prompts/prompts.py` | Defines all AI prompt templates |
| `utils/helpers.py` | Formatting, JSON extraction/repair, session state initialization |

---

## Technology Stack

- **Language:** Python 3.9+
- **UI Framework:** Streamlit (with custom CSS for a non-default look)
- **Generative AI:** Google Gemini API (`google-generativeai` SDK)
- **Document Parsing:** pypdf, python-docx
- **Configuration:** python-dotenv (for secure API key handling)

---

## GenAI Integration

Google Gemini is the sole AI engine powering the application. It is used for
every content-generation task: notes, summaries (at three depths), MCQs,
short-answer questions, long-answer questions, flashcards, and the Ask AI
chat assistant. The model is called in **JSON response mode**, meaning each
prompt requests a strict JSON schema back, which the application parses
directly into Python dictionaries for rendering — eliminating fragile
text-scraping logic.

---

## Prompt Engineering

Every prompt in `prompts/prompts.py` follows a consistent five-part
structure:

- **ROLE** — establishes the persona the model should adopt (e.g., "expert
  academic tutor").
- **CONTEXT** — the study material (and, for Ask AI, recent conversation
  history) is inserted verbatim.
- **TASK** — a precise description of what to produce and how many items.
- **CONSTRAINTS** — instructs the model to rely only on the provided
  material, avoid fabrication, and stay concise and student-friendly.
- **OUTPUT FORMAT** — a strict JSON schema, ensuring predictable, parseable
  output.

This structure was chosen because it consistently produces grounded,
well-formatted responses and made the application significantly more
reliable during testing than free-form prompting.

---

## Implementation

The application is implemented as a single Streamlit entry point (`app.py`)
that composes reusable render functions for each feature (notes, summary,
quiz, flashcards, chat). Generation is triggered explicitly by the user via
a "Generate Study Pack" action, which sequentially calls each Gemini service
function and displays real-time progress using Streamlit's native `st.status`
component. All generated content is cached in `st.session_state` for the
duration of the session, so switching between tabs or pages does not trigger
redundant API calls.

---

## Results

The application successfully:

- Extracts text from PDF, DOCX, and TXT files of varying lengths.
- Produces well-structured notes, summaries, and questions grounded in the
  supplied material.
- Renders a modern, card-based interface that does not resemble a default
  Streamlit application.
- Provides interactive quiz and flashcard experiences with real-time
  scoring and feedback.
- Answers follow-up questions about the material through the Ask AI
  assistant.

---

## Advantages

- Significantly reduces the time needed to convert raw material into
  revision-ready content.
- Provides multiple study modalities (reading, testing, active recall,
  conversational Q&A) from a single source document.
- Simple, dependency-light architecture that is easy to set up and run.
- Professional, modern UI suitable for demonstration or real use.

---

## Limitations

- Generation quality depends on the quality and clarity of the source
  material; scanned/image-only PDFs without OCR are not supported.
- No persistent storage — study packs are lost when the browser session
  ends (by design, to keep the project simple).
- Single-user, single-session design; no collaborative or multi-device sync.
- Subject to the rate limits and occasional latency of the underlying
  Gemini API.

---

## Future Scope

- Add OCR support for scanned/image-based PDFs.
- Introduce optional persistent storage (e.g., a lightweight local database)
  so study packs can be revisited across sessions.
- Add spaced-repetition scheduling for flashcards.
- Support multi-document study packs that combine several files into one
  set of notes.
- Add export to PDF/DOCX in addition to Markdown.

---

## Conclusion

The AI Study Notes Generator demonstrates a practical, focused application
of generative AI to a real student workflow: transforming raw study material
into structured, actionable revision content. By combining a simple, robust
backend with careful prompt engineering and a deliberately premium user
interface, the project shows that a small, well-scoped tool — without
databases, complex frameworks, or heavy infrastructure — can still deliver a
genuinely useful and professional-feeling product.
