# 🎓 StudyPack AI — AI Study Notes Generator

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

Turn any study material — a PDF, a Word document, plain text, or something you
paste in directly — into organized notes, summaries, practice questions, and
flashcards, and ask an AI assistant questions about it. Built with **Python**,
**Streamlit**, and the **Google Gemini API**.

---

## ✨ Features

- 📤 Upload PDF, DOCX, or TXT study material (or paste text directly)
- 📝 AI-generated study notes (key concepts, definitions, important points, examples)
- 📘 Three-depth summaries: Quick / Standard / Detailed
- ❓ Auto-generated multiple-choice quiz with instant feedback and scoring
- ✍️ Short-answer and long-answer practice questions with model answers
- 🧠 Flip-style flashcards for active recall
- 💬 "Ask AI" chat assistant that answers questions using only your material
- ⬇️ Download your full study pack as a Markdown file
- 🎨 A clean, modern, premium interface — not a default Streamlit look

---

## 🛠️ Tech Stack

| Layer         | Technology                     |
|---------------|---------------------------------|
| UI / App      | Streamlit                      |
| AI Generation | Google Gemini API               |
| PDF parsing   | pypdf                          |
| DOCX parsing  | python-docx                    |
| Config        | python-dotenv                  |

No databases, no vector stores, no extra frameworks — kept intentionally simple.

---

## 📦 Installation

### 1. Clone / unzip the project and move into it

```bash
cd ai_study_notes_generator
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Copy `.env.example` to `.env`:

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Then edit `.env` and add your key (get one free at
[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)):

```
GEMINI_API_KEY=your_key
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📁 Project Structure

```
ai_study_notes_generator/
│
├── app.py                       # Main Streamlit application (UI + routing)
├── requirements.txt
├── README.md
├── PROJECT_REPORT.md            # Full academic project report
├── PRESENTATION.md              # 15-slide presentation outline
├── VIVA.md                      # 30+ viva questions & answers
├── .env.example
├── .gitignore
│
├── services/
│   ├── gemini_service.py        # All Gemini API calls + demo mode
│   ├── reviewer.py              # Post-generation groundedness reviewer + repair retry
│   └── document_parser.py       # PDF / DOCX / TXT text extraction
│
├── prompts/
│   ├── prompts.py               # Prompt version registry + v3 re-exports
│   ├── v1_baseline.py           # Control: plain prompt (no schema, no grounding)
│   ├── v2.py                    # Explicit role, JSON schema, grounding + refusal rules
│   ├── v3.py                    # v2 + few-shot examples + strict format/count constraints
│   └── reviewer.py              # Groundedness check and single-repair prompt builders
│
├── utils/
│   └── helpers.py               # Formatting, JSON parsing, session state, runs.csv logging
│
├── runs.csv                     # Experiment log written on every generation run
└── data/
    └── sample_study_material.txt # Sample file to try the app with
```

---

## 🚀 How to Use

1. Open the app and upload a PDF/DOCX/TXT file, or paste text directly.
2. Pick a **Prompt Version** in the sidebar (`v3`, `v2`, or `v1_baseline`; defaults to `v3`).
3. Click **✨ Generate Study Pack** — the AI creates notes, summaries, MCQs, short/long questions, and flashcards, then runs the **Reviewer** step against your original notes.
4. Inspect the **Groundedness Check** badge (`PASSED`, `FAILED`, or `VERIFIER ERROR`) and any flagged unsupported claims directly beneath each reviewed section (**Key Concepts**, **Summary**, **MCQs**, **Short-Answer Q&A**).
5. Download your study pack (including per-section review results) from the Overview tab, and inspect `runs.csv` to compare prompt versions.

Try it instantly with the included `data/sample_study_material.txt`.

---

## 🔍 Groundedness Reviewer Step

After generation completes, `services/reviewer.py` audits four sections **separately** against the original extracted lecture notes (`summary`, `key_concepts`, `mcqs`, `short_answers`):

- **Strict source-only evaluation**: `prompts/reviewer.py` instructs the model (`temperature=0`) to rely *only* on the supplied notes and treat any outside knowledge or reasonable inference not stated in the notes as unsupported.
- **Structured verdict & validation**: The reviewer must return JSON (`status`: `"passed"` | `"failed"`, `unsupported_claims`: `[...]`, `reason`: `"..."`). Returning `"failed"` with an empty `unsupported_claims` list (or `"passed"` with non-empty claims) is rejected as invalid.
- **Single repair attempt**: If parsing (`utils.helpers.extract_json`, including fenced JSON) or schema validation fails, the reviewer performs **one** repair call with a separate repair prompt. If that also fails, it marks the section `"verifier_error"` instead of silently passing.
- **Demo mode**: When `GEMINI_API_KEY` is empty, offline demo mode still exercises the full pipeline using canned reviewer results (including at least one `"failed"` section so the UI flags are demonstrable without an API key).

---

## 🧪 Prompt Versions (`prompts/`)

All three versions expose identical prompt-builder functions so `app.py` and `services/gemini_service.py` swap them without branching logic:

| Version | File | What it tests |
|---|---|---|
| `v1_baseline` | `prompts/v1_baseline.py` | **Control baseline**: plain role + task + list of outputs; no JSON schema, no grounding instruction, no refusal instruction. |
| `v2` | `prompts/v2.py` | Adds explicit academic role, strict JSON output schema, `"use only the supplied notes"`, and explicit refusal (`"Not covered in the supplied notes."`) when notes omit details. |
| `v3` (default) | `prompts/v3.py` | Everything in `v2` plus **few-shot examples** and tighter constraints (exact question counts, 4 MCQ options A–D, concise 1–3 sentence short answers, raw JSON with no preamble). |

---

## 📊 How to Read `runs.csv`

Every study-pack generation (including Offline Demo Mode) appends one row to `runs.csv`:

| Column | Meaning |
|---|---|
| `timestamp` | Local ISO-8601 timestamp when the run finished. |
| `notes_filename` | Uploaded file name or pasted-text title. |
| `prompt_version` | Prompt version used (`v1_baseline`, `v2`, or `v3`). |
| `n_key_concepts` | Number of key concepts generated. |
| `n_mcqs` | Number of MCQs generated. |
| `n_short_answers` | Number of short-answer Q&As generated. |
| `n_unsupported_claims` | Total unsupported claims flagged across all reviewed sections. |
| `sections_failed` | Semicolon-separated list of sections marked `"failed"` (or `"none"`). |
| `verifier_errors` | Semicolon-separated list of sections marked `"verifier_error"` (or `"none"`). |

---

## ⚠️ Known Limitations

- **Shared-model reviewer blind spots**: The reviewer step uses the same Gemini model as the generator (`GEMINI_MODEL_NAME`), so it shares the same training biases and blind spots—it can miss subtle hallucinations or occasionally flag valid paraphrases as unsupported.
- **No retrieval / chunking limit**: Long documents exceeding the character limit are truncated via `chunk_text` (keeping start and end), rather than retrieved per query.
- **Small-scale manual evaluation**: Prompt comparisons rely on sample academic notes and author judgment rather than a large annotated benchmark.
- **Other notes**: Scanned/image-only PDFs without a text layer are not supported; `GEMINI_API_KEY` is read only from `.env` and never shown in the UI.


## No API key required
If `GEMINI_API_KEY` is empty, the app automatically runs in Offline Demo Mode. Upload study material and use the full UI without creating a Google AI Studio project. Add a valid Gemini key later to switch to real Gemini generation.
