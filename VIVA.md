# Viva Questions & Answers — StudyPack AI (AI Study Notes Generator)

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

**1. What does your project do?**
It takes study material (PDF, DOCX, TXT, or pasted text) and uses the Google
Gemini AI model to automatically generate study notes, summaries, practice
questions, flashcards, and answer questions about that material.

**2. What problem does it solve?**
It automates the time-consuming manual work of converting raw study material
into organized, exam-ready revision content.

**3. What technologies did you use?**
Python, Streamlit for the UI, the Google Gemini API for AI generation, pypdf
and python-docx for document parsing, and python-dotenv for configuration.

**4. Why did you choose Streamlit instead of a full frontend framework like React?**
Streamlit lets a single Python developer build a complete, interactive web
UI quickly without needing separate frontend/backend codebases, which fits
the project's goal of staying simple while still looking professional.

**5. Why Google Gemini specifically?**
Gemini offers a capable, cost-effective API with native JSON-mode responses,
which made it straightforward to get structured, reliably parseable output
for notes, questions, and flashcards.

**6. How does the app extract text from a PDF?**
It uses the `pypdf` library's `PdfReader` to read each page and call
`extract_text()`, then joins the page texts together into one string.

**7. How does it handle DOCX files?**
It uses `python-docx`'s `Document` class to read all paragraphs (and table
cells) and joins their text together.

**8. What happens if a PDF is scanned/image-only with no text layer?**
The parser detects that no text was extracted and raises a clear error
telling the user the PDF appears to be image-only, since OCR is out of
scope for this version.

**9. How do you prevent the AI from hallucinating information not in the material?**
Every prompt explicitly instructs the model, in a CONSTRAINTS section, to
base its answer only on the provided study material and not invent facts,
and the Ask AI feature is told to say so if the material doesn't cover a
question rather than fabricate an answer.

**10. What is "prompt engineering" and how did you apply it here?**
Prompt engineering is the practice of carefully structuring instructions to
an AI model to get reliable, high-quality output. Every prompt in this
project follows a consistent ROLE / CONTEXT / TASK / CONSTRAINTS / OUTPUT
FORMAT structure.

**11. Why do your prompts request JSON output specifically?**
Requesting strict JSON lets the application parse the AI's response directly
into Python data structures, avoiding fragile string-parsing and making the
UI rendering predictable and robust.

**12. What do you do if the AI returns malformed JSON?**
The `extract_json` helper function attempts direct parsing first, then falls
back to stripping markdown code fences and locating the first balanced JSON
object/array in the text, and raises a clear error if all attempts fail.

**13. How is application state managed without a database?**
The app uses Streamlit's built-in `st.session_state`, which persists data
(uploaded materials, generated study packs, quiz progress, chat history) for
the duration of a user's browser session.

**14. Why didn't you use a database like MongoDB?**
The project scope is a single-user, single-session study tool; a database
would add unnecessary complexity without meaningfully improving the core
experience, so state is kept in memory via session state instead.

**15. Why didn't you use LangChain?**
LangChain is designed for complex, multi-step AI pipelines and agents. This
project's AI calls are simple, single-turn prompt-response calls, so calling
the Gemini SDK directly is simpler and easier to understand and maintain.

**16. How does the multiple-choice quiz work?**
Each MCQ, generated with exactly four options and one correct answer, is
shown one at a time. When the student selects an option, the app compares it
to the correct answer, shows immediate feedback and an explanation, and lets
the student move to the next question. At the end, it calculates and
displays the score and accuracy.

**17. How are flashcards implemented?**
Each flashcard has a "front" (question/term) and "back" (answer/definition).
The UI shows the front by default; clicking "Show Answer" reveals the back.
Previous/Next buttons navigate between cards, tracked per material in
session state.

**18. How does the "Ask AI" feature stay grounded in the material?**
The full study material text (along with recent chat history) is included
directly in the prompt sent to Gemini, and the prompt instructs the model to
answer only from that material.

**19. What is the difference between the three summary depths?**
Quick is a ~100-150 word single-section summary for a fast review; Standard
is a ~200-350 word summary in 2-4 sections; Detailed is a ~400-600 word
summary in 4-7 sections covering deeper relationships between concepts.

**20. How do you avoid sending overly long text to the AI model?**
The `chunk_text` helper caps the material at a maximum character count,
keeping the beginning and end of the text (typically the most
information-dense parts) if the material exceeds that limit.

**21. Where is the Gemini API key stored, and why?**
It is stored in a local `.env` file (excluded from version control via
`.gitignore`) and loaded with `python-dotenv`. It is never hard-coded in
source code, which keeps it out of the codebase and any repository history.

**22. What happens if the API key is missing?**
The `gemini_service` module raises a clear `GeminiServiceError` explaining
that `GEMINI_API_KEY` must be set in `.env`, and the sidebar Settings panel
also shows a warning if no key is detected.

**23. How is the project structured into modules?**
`app.py` handles the UI and routing; `services/document_parser.py` handles
text extraction; `services/gemini_service.py` handles all AI calls;
`prompts/prompts.py` holds all prompt templates; `utils/helpers.py` holds
shared formatting and state utilities.

**24. Why is the project split this way instead of one big file?**
Separating concerns (parsing, prompting, AI calls, utilities, UI) makes the
code easier to test, read, and modify independently — for example, changing
a prompt doesn't require touching the UI code.

**25. How did you make the UI look "premium" instead of like default Streamlit?**
Through extensive custom CSS injected via `st.markdown`, covering the
sidebar, buttons, cards, tabs, typography (Google Fonts), spacing, colors,
and hiding Streamlit's default menu/footer — replacing the default look
entirely with a consistent design system.

**26. What color scheme did you use and why?**
A soft light background with white cards and a blue-purple gradient accent
color, chosen to feel modern, calm, and academic rather than loud or
distracting, consistent with contemporary AI education products.

**27. How does the app show generation progress to the user?**
It uses Streamlit's native `st.status` component, updating the status label
and log lines as each real generation step (notes, summaries, questions,
flashcards) actually completes — not a simulated/fake progress bar.

**28. Is the download feature saving a real file?**
Yes — the "Download Notes" button compiles the notes, summary, questions,
and flashcards into a single Markdown document and offers it via Streamlit's
`st.download_button`, which the browser saves as a real `.md` file.

**29. What are the main limitations of your project?**
It has no OCR for scanned PDFs, no persistent storage across sessions, is
single-user only, and depends on the availability and rate limits of the
external Gemini API.

**30. What would you improve given more time?**
Add OCR support for image-based PDFs, persistent storage so study packs
survive across sessions, spaced-repetition scheduling for flashcards, and
export to PDF/DOCX formats in addition to Markdown.

**31. How does your app handle errors from the AI API gracefully?**
All Gemini calls are wrapped in try/except blocks that raise a custom
`GeminiServiceError` with a clear message, which the UI catches and displays
to the user via `st.error` instead of crashing the app.

**32. Can the app support other file types in the future?**
Yes — the `parse_document` function dispatches by file extension, so adding
support for a new format (e.g., PPTX) would mean adding one new parser
function and one new dispatch branch, without touching the rest of the app.

**33. Why did you generate the entire study pack in one action instead of on-demand per tab?**
Generating everything upfront (notes, summaries, questions, flashcards) in
a single guided flow gives the student a complete, ready-to-use study pack
immediately and avoids repeated waiting when switching between tabs.
