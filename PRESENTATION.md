# Presentation: StudyPack AI (AI Study Notes Generator)

*16 slides — use as a script for slide software, or convert directly.*

---

## Slide 1 — Title
**StudyPack AI (AI Study Notes Generator)**
Turning study material into notes, questions, and flashcards with generative AI.

Team ID: PE-B13-07 · Team Name: PromptCraft · Batch: B13-B24

---

## Slide 2 — Team

**Team Leader:** Nishtha Mahani (S24CSEU1230)

**Team Members:**
1. Nishtha Mahani (S24CSEU1230) — Leader
2. Aditya Singh (S24CSEU1228)
3. Goutam Kumar (S24CSEU1214)
4. Aditya Singh (S24CSEU1255)
5. Arjun Tiwari (S24CSEU1293)
6. Sambhav Jain (S24CSEU1216)

---

## Slide 3 — Agenda
1. Problem
2. Existing solutions & their gaps
3. Proposed solution
4. Tech stack
5. System architecture
6. Core features (demo walkthrough)
7. Prompt engineering approach
8. Results
9. Limitations & future scope
10. Conclusion

---

## Slide 4 — The Problem
- Study material is scattered: PDFs, slides, pasted text.
- Turning it into notes, summaries, and self-test questions is slow and manual.
- Students need multiple study formats (read, test, recall) from one source.

---

## Slide 5 — Existing Systems
- Manual note-taking — slow, inconsistent.
- Generic AI chatbots — no structured, repeatable workflow.
- Flashcard apps (e.g., Anki) — cards must be authored by hand.
- PDF annotators — no new content generated.

---

## Slide 6 — Proposed Solution
**StudyPack AI** — one app that:
- Ingests PDF / DOCX / TXT / pasted text
- Generates notes, summaries, questions, and flashcards automatically
- Lets students ask questions about their own material
- All powered by Google Gemini

---

## Slide 7 — Objectives
- Automate note generation from raw material
- Generate MCQ, short-answer, and long-answer practice questions
- Provide active-recall flashcards
- Provide a grounded Q&A assistant
- Deliver a premium, professional UI

---

## Slide 8 — Tech Stack
- **Frontend/App:** Python + Streamlit
- **AI:** Google Gemini API
- **Parsing:** pypdf, python-docx
- **Config:** python-dotenv
- No database, no LangChain, no Docker — kept simple by design.

---

## Slide 9 — System Architecture
```
Streamlit UI  →  document_parser.py  →  plain text
                                     →  prompts.py
                                     →  gemini_service.py
                                     →  Google Gemini API
                                     →  structured JSON
                                     →  rendered UI (notes/quiz/cards/chat)
```

---

## Slide 10 — Feature: Upload & Parse
- Upload PDF, DOCX, or TXT — or paste text directly
- Automatic text extraction with page/character counts
- Clean upload confirmation UI

---

## Slide 11 — Feature: Notes & Summaries
- Notes organized into Key Concepts, Definitions, Important Points,
  Examples, and "Remember This"
- Three summary depths: Quick, Standard, Detailed

---

## Slide 12 — Feature: Practice & Flashcards
- Auto-generated MCQ quiz with instant feedback and scoring
- Short-answer and long-answer questions with model answers
- Flip-style flashcards for active recall

---

## Slide 13 — Feature: Ask AI
- Chat interface grounded strictly in the uploaded material
- Suggested starter questions
- Designed to avoid hallucinated answers outside the source material

---

## Slide 14 — Prompt Engineering Approach
Every prompt follows:
**ROLE → CONTEXT → TASK → CONSTRAINTS → OUTPUT FORMAT (strict JSON)**
- Keeps answers grounded in the material
- Produces reliably parseable, structured output

---

## Slide 15 — Results & Demo
- Successfully generates notes, summaries, questions, and flashcards
  from real PDF/DOCX/TXT material
- Modern, card-based UI — not default Streamlit
- *(Live demo here)*

---

## Slide 16 — Conclusion & Future Scope
- A focused, lightweight tool that meaningfully speeds up exam revision
- Future: OCR for scanned PDFs, persistent storage, spaced repetition,
  multi-document study packs, PDF/DOCX export

**Thank you — Questions?**
