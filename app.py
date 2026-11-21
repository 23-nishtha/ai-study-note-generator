"""
AI Study Notes Generator — app.py

A Streamlit application that turns uploaded/pasted study material into
AI-generated notes, summaries, practice questions, flashcards, and an
interactive Q&A assistant — powered by Google Gemini.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import html
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import streamlit as st

from prompts.prompts import PROMPT_VERSION_OPTIONS, get_version_label
from services import gemini_service, reviewer
from services.document_parser import parse_document, DocumentParseError
from services.gemini_service import GeminiServiceError
from utils.helpers import (
    init_session_state,
    get_active_material,
    get_pack_for,
    set_page,
    format_file_size,
    format_date,
    estimate_pages,
    char_count,
    truncate,
    new_id,
    append_run_log,
)

RUNS_CSV_PATH = Path(__file__).resolve().parent / "runs.csv"

# ==========================================================================
# PAGE CONFIG
# ==========================================================================

st.set_page_config(
    page_title="StudyAI · AI Study Notes Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()


# ==========================================================================
# CUSTOM CSS — this is what makes the app look like a premium SaaS product
# rather than a default Streamlit app.
# ==========================================================================

def load_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');

        :root {
            --bg: #F6F7FC;
            --surface: #FFFFFF;
            --surface-alt: #FBFBFE;
            --primary: #6D5BF6;
            --primary-2: #8B5CF6;
            --primary-dark: #5443E0;
            --primary-soft: #F1EEFE;
            --text: #191A2B;
            --text-muted: #6B7085;
            --text-faint: #9296A8;
            --border: #E8E9F3;
            --success: #17A673;
            --success-bg: #E9F9F1;
            --warning: #B7791F;
            --warning-bg: #FEF6E7;
            --danger: #E24C4C;
            --danger-bg: #FDECEC;
            --radius-lg: 20px;
            --radius-md: 14px;
            --radius-sm: 10px;
            --shadow-sm: 0 1px 2px rgba(23, 24, 48, 0.04), 0 1px 3px rgba(23, 24, 48, 0.06);
            --shadow-md: 0 4px 14px rgba(23, 24, 48, 0.07);
            --grad: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%);
        }

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Poppins', 'Inter', sans-serif !important; }

        /* ---- App chrome cleanup ---- */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }
        .stApp { background: var(--bg); color: var(--text); }
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] h1,
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] h2,
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] h3,
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] h4,
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"] li {
            color: var(--text);
        }
        section[data-testid="stMain"] .sa-card { color: var(--text); }
        section[data-testid="stMain"] .sa-hero,
        section[data-testid="stMain"] .sa-hero p,
        section[data-testid="stMain"] .sa-hero h1 { color: #FFFFFF !important; }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        div[data-testid="stDecoration"] { display: none; }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            background: #14132B;
            border-right: 1px solid #24234A;
        }
        section[data-testid="stSidebar"] * { color: #E7E6F7 !important; }
        section[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }

        section[data-testid="stSidebar"] .stButton > button {
            background: transparent;
            border: 1px solid transparent;
            color: #C7C5E6 !important;
            text-align: left;
            font-weight: 500;
            border-radius: var(--radius-sm);
            padding: 0.55rem 0.9rem;
            width: 100%;
            transition: all 0.15s ease;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: #221F45;
            border-color: #322F5E;
            color: #FFFFFF !important;
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--grad) !important;
            color: #FFFFFF !important;
            border: none;
            box-shadow: 0 4px 12px rgba(109, 91, 246, 0.35);
        }
        section[data-testid="stSidebar"] hr { border-color: #262450; margin: 1.1rem 0; }

        .sidebar-brand {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.25rem;
            color: #FFFFFF !important;
            margin-bottom: 1.4rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .sidebar-status {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.82rem;
            color: #9C9AC4 !important;
            margin-top: 0.3rem;
        }
        .status-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #2ED47A;
            box-shadow: 0 0 0 3px rgba(46, 212, 122, 0.18);
            display: inline-block;
        }

        /* ---- Buttons (main area) ---- */
        .stButton > button, .stDownloadButton > button {
            border-radius: 999px;
            font-weight: 600;
            padding: 0.55rem 1.3rem;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text);
            transition: all 0.15s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--primary);
            color: var(--primary-dark);
            transform: translateY(-1px);
        }
        .main .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--grad);
            border: none;
            color: white !important;
            box-shadow: 0 6px 16px rgba(109, 91, 246, 0.3);
        }
        .main .stButton > button[kind="primary"]:hover { filter: brightness(1.06); color: white !important; }

        /* ---- Generic surface card ---- */
        .sa-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.4rem 1.5rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 1rem;
            transition: box-shadow 0.15s ease, transform 0.15s ease;
        }
        .sa-card:hover { box-shadow: var(--shadow-md); }

        /* ---- Hero ---- */
        .sa-hero {
            background: var(--grad);
            border-radius: 28px;
            padding: 3.2rem 3rem;
            color: white;
            margin-bottom: 1.8rem;
            position: relative;
            overflow: hidden;
        }
        .sa-hero::after {
            content: "";
            position: absolute; right: -60px; top: -60px;
            width: 260px; height: 260px; border-radius: 50%;
            background: rgba(255,255,255,0.08);
        }
        .sa-hero h1 {
            font-size: 2.6rem; font-weight: 800; margin: 0 0 0.6rem 0; color: white !important;
        }
        .sa-hero p { font-size: 1.08rem; color: rgba(255,255,255,0.88); max-width: 560px; margin-bottom: 0; }

        /* ---- Stat cards ---- */
        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1.1rem 1.3rem;
            box-shadow: var(--shadow-sm);
        }
        .stat-label { color: var(--text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
        .stat-value { font-size: 1.9rem; font-weight: 800; color: var(--text); font-family: 'Poppins', sans-serif; margin-top: 0.15rem; }

        /* ---- Section headings ---- */
        .sa-title { font-size: 1.5rem; font-weight: 700; color: var(--text); margin-bottom: 0.15rem; }
        .sa-subtitle { color: var(--text-muted); font-size: 0.97rem; margin-bottom: 1.3rem; }

        /* ---- Badges / pills ---- */
        .pill {
            display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px;
            font-size: 0.76rem; font-weight: 700; letter-spacing: 0.02em;
        }
        .pill-purple { background: var(--primary-soft); color: var(--primary-dark); }
        .pill-green { background: var(--success-bg); color: var(--success); }
        .pill-red { background: var(--danger-bg); color: var(--danger); }
        .pill-amber { background: var(--warning-bg); color: var(--warning); }
        .pill-gray { background: #F0F1F6; color: var(--text-muted); }

        .review-box {
            background: var(--surface-alt);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.85rem 1.05rem;
            margin: 0.65rem 0 1.15rem 0;
        }
        .review-box.failed { border-left: 4px solid var(--danger); background: #FFF9F9; }
        .review-box.passed { border-left: 4px solid var(--success); }
        .review-box.verifier_error { border-left: 4px solid var(--warning); background: #FFFDF7; }

        /* ---- Material card ---- */
        .material-card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: var(--radius-md); padding: 1.1rem 1.3rem;
            box-shadow: var(--shadow-sm); margin-bottom: 0.85rem;
        }
        .material-icon {
            width: 42px; height: 42px; border-radius: 12px; background: var(--primary-soft);
            display: flex; align-items: center; justify-content: center; font-size: 1.3rem;
        }
        .material-name { font-weight: 700; color: var(--text); font-size: 1rem; }
        .material-meta { color: var(--text-faint); font-size: 0.82rem; }

        /* ---- Notes cards ---- */
        .note-card {
            background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--primary);
            border-radius: var(--radius-md); padding: 1rem 1.2rem; margin-bottom: 0.75rem; box-shadow: var(--shadow-sm);
        }
        .note-card h4 { margin: 0 0 0.35rem 0; font-size: 1rem; color: var(--text); }
        .note-card p { margin: 0; color: var(--text-muted); font-size: 0.93rem; line-height: 1.55; }

        /* ---- Upload dropzone ---- */
        div[data-testid="stFileUploaderDropzone"] {
            background: var(--surface-alt) !important;
            border: 1.5px dashed #CFCBF5 !important;
            border-radius: var(--radius-lg) !important;
        }

        /* ---- Tabs ---- */
        .stTabs [data-baseweb="tab-list"] { gap: 0.3rem; border-bottom: 1px solid var(--border); }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0; padding: 0.6rem 1.1rem; font-weight: 600; color: var(--text-muted);
        }
        .stTabs [aria-selected="true"] { color: var(--primary-dark) !important; background: var(--primary-soft); }

        /* ---- Quiz options ---- */
        .quiz-progress-label { color: var(--text-muted); font-weight: 600; font-size: 0.88rem; margin-bottom: 0.4rem; }
        .quiz-question { font-size: 1.25rem; font-weight: 700; color: var(--text); margin: 0.4rem 0 1rem 0; }
        .feedback-correct {
            background: var(--success-bg); color: var(--success); border-radius: var(--radius-sm);
            padding: 0.7rem 1rem; font-weight: 700; margin: 0.6rem 0;
        }
        .feedback-incorrect {
            background: var(--danger-bg); color: var(--danger); border-radius: var(--radius-sm);
            padding: 0.7rem 1rem; font-weight: 700; margin: 0.6rem 0;
        }
        .explain-box { color: var(--text-muted); font-size: 0.9rem; padding: 0 0.2rem; }

        /* ---- Flashcard ---- */
        .flash-card {
            background: var(--grad); border-radius: 22px; padding: 3rem 2rem; min-height: 220px;
            display: flex; align-items: center; justify-content: center; text-align: center;
            color: white; font-size: 1.35rem; font-weight: 700; box-shadow: var(--shadow-md);
            margin-bottom: 1rem;
        }
        .flash-card.back { background: var(--surface); color: var(--text); border: 1px solid var(--border); font-weight: 500; font-size: 1.1rem; }
        .flash-tag { position: absolute; }

        /* ---- Suggested question chips ---- */
        .stButton > button.chip { border-radius: 999px; font-size: 0.85rem; }

        /* ---- Misc ---- */
        hr.sa-divider { border: none; border-top: 1px solid var(--border); margin: 1.6rem 0; }
        .muted { color: var(--text-muted); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================================
# SIDEBAR
# ==========================================================================

NAV_ITEMS = [
    ("dashboard", "🏠  Dashboard"),
    ("material", "📚  My Study Material"),
    ("generate", "✨  Generate Notes"),
    ("practice", "📝  Practice"),
    ("flashcards", "🧠  Flashcards"),
    ("ask_ai", "💬  Ask AI"),
]


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🎓 StudyAI</div>', unsafe_allow_html=True)

        for key, label in NAV_ITEMS:
            is_active = st.session_state["page"] == key
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                set_page(key)
                st.rerun()

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown(
            '<div style="font-weight:600; font-size:0.85rem; color:#B9B7E0; margin-bottom:0.35rem;">🧪 Prompt Version</div>',
            unsafe_allow_html=True,
        )
        current_version = st.session_state.get("prompt_version", "v3")
        if current_version not in PROMPT_VERSION_OPTIONS:
            current_version = "v3"
        st.session_state["prompt_version"] = st.radio(
            "Prompt Version",
            options=PROMPT_VERSION_OPTIONS,
            index=PROMPT_VERSION_OPTIONS.index(current_version),
            format_func=get_version_label,
            label_visibility="collapsed",
        )

        st.markdown("<hr/>", unsafe_allow_html=True)

        with st.expander("⚙️  Settings"):
            api_ok = bool(gemini_service.GEMINI_API_KEY)
            st.caption(f"Model: `{gemini_service.GEMINI_MODEL_NAME}`")
            if api_ok:
                st.success("Gemini API key detected · Real AI mode", icon="🔑")
            else:
                st.info("Demo Mode active · No API key required", icon="✨")
            if st.button("🗑️ Clear all data", use_container_width=True):
                for k in ["materials", "study_pack", "quiz_state", "flashcard_state", "chat_history",
                          "active_material_id", "notes_generated_count", "questions_generated_count",
                          "flashcards_generated_count"]:
                    st.session_state.pop(k, None)
                init_session_state()
                st.rerun()

        st.markdown(
            """
            <div style="margin-top: 1rem;">
                <div style="font-weight:600; font-size:0.85rem; color:#B9B7E0;">AI Study Assistant</div>
                <div class="sidebar-status"><span class="status-dot"></span> Ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================================
# SHARED WIDGETS
# ==========================================================================

def stat_card(col, label: str, value, icon: str) -> None:
    with col:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">{icon} {label}</div>
                <div class="stat-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def add_material(name: str, file_type: str, content: str, size_bytes: int, pages: int) -> dict:
    material = {
        "id": new_id(),
        "name": name,
        "type": file_type,
        "content": content,
        "size": size_bytes,
        "pages": pages,
        "chars": char_count(content),
        "uploaded_at": datetime.now(),
    }
    st.session_state["materials"].append(material)
    st.session_state["active_material_id"] = material["id"]
    return material


def handle_upload_widget(key_prefix: str) -> None:
    """Renders the upload card + paste box, and processes new material."""
    st.markdown(
        """
        <div class="sa-card" style="text-align:center; padding: 2.2rem 1.5rem;">
            <div style="font-size:2.4rem;">📄</div>
            <div style="font-weight:700; font-size:1.15rem; margin-top:0.3rem;">Upload your material</div>
            <div class="muted" style="margin-bottom:0.6rem;">Drag & drop PDF, DOCX or TXT — or browse below</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Browse files", type=["pdf", "docx", "txt"], key=f"{key_prefix}_uploader",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        already = any(m["name"] == uploaded.name and m["size"] == uploaded.size
                      for m in st.session_state["materials"])
        if not already:
            try:
                file_bytes = uploaded.getvalue()
                text, pages, ftype = parse_document(uploaded.name, file_bytes)
                add_material(uploaded.name, ftype, text, len(file_bytes), pages)
                st.success(f"✓ Material uploaded successfully — **{uploaded.name}**")
                st.rerun()
            except DocumentParseError as e:
                st.error(f"Couldn't process this file: {e}")

    st.markdown('<div style="text-align:center; color:#9296A8; margin: 0.9rem 0;">or paste your text</div>',
                unsafe_allow_html=True)
    pasted = st.text_area("Paste study material", height=140, key=f"{key_prefix}_paste",
                           label_visibility="collapsed",
                           placeholder="Paste your notes, textbook excerpt, or lecture transcript here…")
    c1, _ = st.columns([1, 3])
    with c1:
        if st.button("➕ Add Pasted Text", use_container_width=True, key=f"{key_prefix}_add_paste"):
            if pasted and pasted.strip():
                title = f"Pasted Text · {datetime.now().strftime('%b %d, %H:%M')}"
                add_material(title, "TEXT", pasted.strip(), len(pasted.encode("utf-8")),
                             estimate_pages(pasted))
                st.success("✓ Material added successfully")
                st.rerun()
            else:
                st.warning("Please paste some text first.")


# ==========================================================================
# PAGE: DASHBOARD
# ==========================================================================

def page_dashboard() -> None:
    materials = st.session_state["materials"]

    if not materials:
        st.markdown(
            """
            <div class="sa-hero">
                <h1>Study Smarter with AI.</h1>
                <p>Turn your study material into clear notes, summaries, questions and flashcards in seconds.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, _ = st.columns([1, 3])
        with c1:
            if st.button("✨ Start Learning", type="primary", use_container_width=True):
                pass  # scrolling isn't native; upload card is right below
        st.write("")
        handle_upload_widget(key_prefix="dash")
        return

    st.markdown('<div class="sa-title">Welcome back 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Here\'s a snapshot of your study progress.</div>',
                unsafe_allow_html=True)

    total_notes = st.session_state["notes_generated_count"]
    total_qs = st.session_state["questions_generated_count"]
    total_cards = st.session_state["flashcards_generated_count"]

    c1, c2, c3, c4 = st.columns(4)
    stat_card(c1, "Materials", len(materials), "📄")
    stat_card(c2, "Notes Generated", total_notes, "📝")
    stat_card(c3, "Questions Generated", total_qs, "❓")
    stat_card(c4, "Flashcards", total_cards, "🧠")

    st.markdown('<hr class="sa-divider"/>', unsafe_allow_html=True)
    st.markdown('<div class="sa-title">Your Study Material</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Pick up where you left off, or add new material below.</div>',
                unsafe_allow_html=True)

    render_material_cards(materials, key_prefix="dash")

    with st.expander("➕ Add new study material"):
        handle_upload_widget(key_prefix="dash_more")


def render_material_cards(materials: list, key_prefix: str) -> None:
    icon_map = {"PDF": "📕", "DOCX": "📘", "TXT": "📄", "TEXT": "📝"}
    for m in materials:
        icon = icon_map.get(m["type"], "📄")
        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.markdown(
                f"""
                <div class="material-card">
                    <div style="display:flex; align-items:center; gap:0.9rem;">
                        <div class="material-icon">{icon}</div>
                        <div>
                            <div class="material-name">{truncate(m['name'], 55)}</div>
                            <div class="material-meta">
                                {m['type']} · {m['pages']} page(s) · {format_file_size(m['size'])} ·
                                uploaded {format_date(m['uploaded_at'])}
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.write("")
            if st.button("Open →", key=f"{key_prefix}_open_{m['id']}", use_container_width=True):
                st.session_state["active_material_id"] = m["id"]
                set_page("generate")
                st.rerun()


# ==========================================================================
# PAGE: MY STUDY MATERIAL
# ==========================================================================

def page_material() -> None:
    st.markdown('<div class="sa-title">📚 My Study Material</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">All the material you\'ve uploaded or pasted so far.</div>',
                unsafe_allow_html=True)

    materials = st.session_state["materials"]
    if not materials:
        st.info("You haven't added any study material yet. Add some to get started!")
        handle_upload_widget(key_prefix="mat")
        return

    render_material_cards(materials, key_prefix="mat")

    st.markdown('<hr class="sa-divider"/>', unsafe_allow_html=True)
    with st.expander("➕ Add new study material"):
        handle_upload_widget(key_prefix="mat_more")


# ==========================================================================
# PAGE: GENERATE (Study Pack + tabs)
# ==========================================================================

def _review_badge_html(status: str) -> str:
    if status == "passed":
        return "<span class='pill pill-green'>✅ PASSED</span>"
    if status == "failed":
        return "<span class='pill pill-red'>⚠️ FAILED</span>"
    return "<span class='pill pill-amber'>❗ VERIFIER ERROR</span>"


def render_review_banner(review: dict | None, section_label: str) -> None:
    """Display groundedness verdict and unsupported claims beneath a section."""
    if not review:
        return

    status = review.get("status", "verifier_error")
    reason = html.escape(review.get("reason", ""))
    claims = review.get("unsupported_claims") or []

    claims_html = ""
    if claims:
        items = "".join(f"<li>{html.escape(claim)}</li>" for claim in claims)
        claims_html = (
            "<div style='margin-top:0.5rem; font-weight:600; font-size:0.86rem; color:var(--danger);'>"
            "Unsupported claims flagged against source notes:</div>"
            f"<ul style='margin:0.25rem 0 0 1.2rem; font-size:0.88rem; color:var(--text);'>{items}</ul>"
        )
    elif status == "verifier_error":
        claims_html = (
            "<div style='margin-top:0.45rem; font-size:0.86rem; color:var(--warning); font-weight:600;'>"
            "The reviewer returned invalid output even after one repair attempt. Verify this section manually.</div>"
        )

    css_cls = status if status in {"passed", "failed", "verifier_error"} else "verifier_error"
    st.markdown(
        f"""
        <div class="review-box {css_cls}">
            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
                {_review_badge_html(status)}
                <span style="font-weight:600; font-size:0.88rem; color:var(--text);">
                    {html.escape(section_label)} Groundedness Check
                </span>
            </div>
            <div style="margin-top:0.35rem; font-size:0.88rem; color:var(--text-muted);">{reason}</div>
            {claims_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_review_markdown(section_label: str, review: dict | None) -> list[str]:
    if not review:
        return []
    status = review.get("status", "verifier_error").upper()
    out = [f"> **Groundedness Check ({section_label}) — {status}:** {review.get('reason', '')}"]
    for claim in review.get("unsupported_claims") or []:
        out.append(f"> - Unsupported claim: {claim}")
    out.append("")
    return out


def run_generation_pipeline(material: dict) -> None:
    status = st.status("Creating your study pack ✨", expanded=True)
    prompt_version = st.session_state.get("prompt_version", "v3")
    try:
        status.write(f"✓ Reading material (prompt `{prompt_version}`)")
        text = material["content"]

        status.write("🧠 Generating notes, summaries, questions, and flashcards…")
        if gemini_service.is_demo_mode():
            notes = gemini_service.generate_notes(text, prompt_version=prompt_version)
            summaries = {
                "quick": gemini_service.generate_summary(text, "quick", prompt_version=prompt_version),
                "standard": gemini_service.generate_summary(text, "standard", prompt_version=prompt_version),
                "detailed": gemini_service.generate_summary(text, "detailed", prompt_version=prompt_version),
            }
            mcqs = gemini_service.generate_mcqs(text, 5, prompt_version=prompt_version)
            short_qs = gemini_service.generate_short_answers(text, 3, prompt_version=prompt_version)
            long_qs = gemini_service.generate_long_answers(text, 4, prompt_version=prompt_version)
            flashcards = gemini_service.generate_flashcards(text, 10, prompt_version=prompt_version)
        else:
            with ThreadPoolExecutor(max_workers=6) as pool:
                f_notes = pool.submit(gemini_service.generate_notes, text, prompt_version)
                f_quick = pool.submit(gemini_service.generate_summary, text, "quick", prompt_version)
                f_std = pool.submit(gemini_service.generate_summary, text, "standard", prompt_version)
                f_det = pool.submit(gemini_service.generate_summary, text, "detailed", prompt_version)
                f_mcqs = pool.submit(gemini_service.generate_mcqs, text, 5, prompt_version)
                f_short = pool.submit(gemini_service.generate_short_answers, text, 3, prompt_version)
                f_long = pool.submit(gemini_service.generate_long_answers, text, 4, prompt_version)
                f_cards = pool.submit(gemini_service.generate_flashcards, text, 10, prompt_version)

                notes = f_notes.result()
                summaries = {
                    "quick": f_quick.result(),
                    "standard": f_std.result(),
                    "detailed": f_det.result(),
                }
                mcqs = f_mcqs.result()
                short_qs = f_short.result()
                long_qs = f_long.result()
                flashcards = f_cards.result()

        status.write("✓ Study content generated")

        pack = {
            "notes": notes,
            "summaries": summaries,
            "mcqs": mcqs,
            "short_qs": short_qs,
            "long_qs": long_qs,
            "flashcards": flashcards,
            "prompt_version": prompt_version,
            "generated_at": datetime.now(),
        }

        status.write("🔍 Reviewing sections against source notes…")
        reviews = reviewer.review_study_pack(pack, text, prompt_version=prompt_version)
        pack["reviews"] = reviews
        status.write("✓ Groundedness review complete")

        failed_sections = [
            key for key, res in reviews.items() if res.get("status") == "failed"
        ]
        error_sections = [
            key for key, res in reviews.items() if res.get("status") == "verifier_error"
        ]
        total_unsupported = sum(
            len(res.get("unsupported_claims") or []) for res in reviews.values()
        )
        append_run_log(
            RUNS_CSV_PATH,
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "notes_filename": material["name"],
                "prompt_version": prompt_version,
                "n_key_concepts": len(notes.get("key_concepts", [])),
                "n_mcqs": len(mcqs.get("questions", [])),
                "n_short_answers": len(short_qs.get("questions", [])),
                "n_unsupported_claims": total_unsupported,
                "sections_failed": ";".join(failed_sections) if failed_sections else "none",
                "verifier_errors": ";".join(error_sections) if error_sections else "none",
            },
        )

        st.session_state["study_pack"][material["id"]] = pack

        st.session_state["notes_generated_count"] += 1
        st.session_state["questions_generated_count"] += (
            len(mcqs.get("questions", [])) + len(short_qs.get("questions", [])) + len(long_qs.get("questions", []))
        )
        st.session_state["flashcards_generated_count"] += len(flashcards.get("flashcards", []))

        status.update(label="Your study pack is ready 🎉", state="complete", expanded=False)
        st.balloons()
        st.rerun()

    except GeminiServiceError as e:
        status.update(label="Generation failed", state="error", expanded=True)
        st.error(str(e))


def page_generate() -> None:
    material = get_active_material()

    st.markdown('<div class="sa-title">✨ Generate Study Pack</div>', unsafe_allow_html=True)

    if not material:
        st.markdown('<div class="sa-subtitle">Upload material to generate your AI study pack.</div>',
                    unsafe_allow_html=True)
        handle_upload_widget(key_prefix="gen")
        return

    pack = get_pack_for(material["id"])

    # --- Material picker if multiple materials exist ---
    if len(st.session_state["materials"]) > 1:
        names = [m["name"] for m in st.session_state["materials"]]
        ids = [m["id"] for m in st.session_state["materials"]]
        current_idx = ids.index(material["id"])
        choice = st.selectbox("Active material", names, index=current_idx, label_visibility="collapsed")
        st.session_state["active_material_id"] = ids[names.index(choice)]
        material = get_active_material()
        pack = get_pack_for(material["id"])

    if not pack:
        icon_map = {"PDF": "📕", "DOCX": "📘", "TXT": "📄", "TEXT": "📝"}
        st.markdown(
            f"""
            <div class="sa-card">
                <div style="font-weight:700; color:var(--success); margin-bottom:0.6rem;">✓ Material uploaded successfully</div>
                <div style="display:flex; gap:0.9rem; align-items:center;">
                    <div class="material-icon">{icon_map.get(material['type'], '📄')}</div>
                    <div>
                        <div class="material-name">{material['name']}</div>
                        <div class="material-meta">{material['type']} · {format_file_size(material['size'])} · {material['pages']} page(s)</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("✨ Generate Study Pack", type="primary", use_container_width=False):
            run_generation_pipeline(material)
        return

    # --- Study pack ready: tabbed interface ---
    tabs = st.tabs(["Overview", "Notes", "Summary", "Practice", "Flashcards", "Ask AI"])

    with tabs[0]:
        render_overview_tab(material, pack)
    with tabs[1]:
        render_notes_tab(pack)
    with tabs[2]:
        render_summary_tab(pack)
    with tabs[3]:
        practice_subtabs = st.tabs(["🔘 Multiple Choice", "✍️ Short Answer"])
        with practice_subtabs[0]:
            render_quiz(material["id"], pack)
        with practice_subtabs[1]:
            render_short_answers(pack)
    with tabs[4]:
        render_flashcards(material["id"], pack)
    with tabs[5]:
        render_ask_ai(material, pack)

    st.markdown('<hr class="sa-divider"/>', unsafe_allow_html=True)
    if st.button("🔁 Regenerate Study Pack", use_container_width=False):
        run_generation_pipeline(material)


def render_overview_tab(material: dict, pack: dict) -> None:
    st.markdown('<div style="font-weight:700; font-size:1.05rem; margin-bottom:0.8rem;">Your study pack is ready 🎉</div>',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    stat_card(c1, "Key Concepts", len(pack["notes"].get("key_concepts", [])), "📌")
    stat_card(c2, "MCQs", len(pack["mcqs"].get("questions", [])), "❓")
    stat_card(c3, "Written Qs", len(pack["short_qs"].get("questions", [])) + len(pack["long_qs"].get("questions", [])), "✍️")
    stat_card(c4, "Flashcards", len(pack["flashcards"].get("flashcards", [])), "🧠")

    st.write("")
    p_ver = pack.get("prompt_version", "v3")
    st.markdown(
        f"<span class='pill pill-gray'>Generated {format_date(pack.get('generated_at'))}</span> "
        f"<span class='pill pill-purple'>Prompt: {html.escape(get_version_label(p_ver))}</span>",
        unsafe_allow_html=True,
    )

    reviews = pack.get("reviews", {})
    if reviews:
        st.write("")
        badges = " ".join(
            f"<span style='margin-right:0.65rem;'><strong>{html.escape(reviewer.SECTION_LABELS.get(k, k))}:</strong> "
            f"{_review_badge_html(res.get('status', 'verifier_error'))}</span>"
            for k, res in reviews.items()
        )
        st.markdown(f"<div class='sa-card' style='padding:0.9rem 1.2rem;'>{badges}</div>", unsafe_allow_html=True)

    st.markdown('<hr class="sa-divider"/>', unsafe_allow_html=True)
    build_download_button(material, pack)


def build_download_button(material: dict, pack: dict) -> None:
    reviews = pack.get("reviews", {})
    lines = [
        f"# Study Pack — {material['name']}",
        f"_Prompt Version: {pack.get('prompt_version', 'v3')}_",
        "",
    ]

    lines.append("## 📝 Notes\n")
    notes = pack.get("notes", {})
    if notes.get("key_concepts"):
        lines.append("### 📌 Key Concepts")
        for item in notes["key_concepts"]:
            lines.append(f"- **{item.get('title','')}** — {item.get('explanation','')}")
        lines.append("")
        lines.extend(_format_review_markdown("Key Concepts", reviews.get("key_concepts")))
    if notes.get("definitions"):
        lines.append("### 📖 Definitions")
        for item in notes["definitions"]:
            lines.append(f"- **{item.get('term','')}**: {item.get('definition','')}")
        lines.append("")
    if notes.get("important_points"):
        lines.append("### 💡 Important Points")
        for item in notes["important_points"]:
            lines.append(f"- {item}")
        lines.append("")
    if notes.get("examples"):
        lines.append("### 🔍 Examples")
        for item in notes["examples"]:
            lines.append(f"- **{item.get('title','')}** — {item.get('explanation','')}")
        lines.append("")
    if notes.get("remember_this"):
        lines.append("### ⭐ Remember This")
        for item in notes["remember_this"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 📘 Summary (Standard)\n")
    std = pack.get("summaries", {}).get("standard", {})
    for sec in std.get("sections", []):
        lines.append(f"### {sec.get('heading','')}")
        lines.append(sec.get("content", ""))
        lines.append("")
    lines.extend(_format_review_markdown("Summary", reviews.get("summary")))

    lines.append("## ❓ Multiple Choice Questions\n")
    mcqs_data = pack.get("mcqs", {})
    if mcqs_data.get("questions"):
        for i, q in enumerate(mcqs_data["questions"], 1):
            lines.append(f"{i}. {q.get('question','')}")
            for letter, opt in q.get("options", {}).items():
                marker = "✔" if letter == q.get("correct_option") else " "
                lines.append(f"   - {letter}. {opt} {marker}")
            lines.append(f"   _Explanation: {q.get('explanation','')}_\n")
    elif mcqs_data.get("raw_text"):
        lines.append(mcqs_data["raw_text"])
        lines.append("")
    lines.extend(_format_review_markdown("MCQs", reviews.get("mcqs")))

    lines.append("## ✍️ Short Answer Questions\n")
    short_data = pack.get("short_qs", {})
    if short_data.get("questions"):
        for i, q in enumerate(short_data["questions"], 1):
            lines.append(f"{i}. {q.get('question','')}")
            lines.append(f"   Answer: {q.get('model_answer','')}\n")
    elif short_data.get("raw_text"):
        lines.append(short_data["raw_text"])
        lines.append("")
    lines.extend(_format_review_markdown("Short-Answer Q&A", reviews.get("short_answers")))

    lines.append("## 🧾 Long Answer Questions\n")
    for i, q in enumerate(pack.get("long_qs", {}).get("questions", []), 1):
        lines.append(f"{i}. {q.get('question','')}")
        for point in q.get("answer_outline", []):
            lines.append(f"   - {point}")
        lines.append("")

    lines.append("## 🧠 Flashcards\n")
    for i, card in enumerate(pack.get("flashcards", {}).get("flashcards", []), 1):
        lines.append(f"{i}. **Q:** {card.get('front','')}  **A:** {card.get('back','')}")

    content = "\n".join(lines)
    st.download_button(
        "⬇️ Download Notes", data=content,
        file_name=f"{material['name'].rsplit('.', 1)[0]}_study_pack.md",
        mime="text/markdown", type="primary",
    )


def render_notes_tab(pack: dict) -> None:
    st.markdown('<div class="sa-title">Your Study Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">AI-generated notes organized for quick revision.</div>',
                unsafe_allow_html=True)

    notes = pack.get("notes", {})
    reviews = pack.get("reviews", {})

    if notes.get("key_concepts"):
        st.markdown("#### 📌 Key Concepts")
        for item in notes["key_concepts"]:
            st.markdown(
                f"""<div class="note-card"><h4>{html.escape(str(item.get('title','')))}</h4>
                <p>{html.escape(str(item.get('explanation','')))}</p></div>""",
                unsafe_allow_html=True,
            )
        render_review_banner(reviews.get("key_concepts"), "Key Concepts")

    if notes.get("definitions"):
        st.markdown("#### 📖 Definitions")
        for item in notes["definitions"]:
            st.markdown(
                f"""<div class="note-card"><h4>{item.get('term','')}</h4>
                <p>{item.get('definition','')}</p></div>""",
                unsafe_allow_html=True,
            )

    if notes.get("important_points"):
        st.markdown("#### 💡 Important Points")
        pts = "".join(f"<p>• {p}</p>" for p in notes["important_points"])
        st.markdown(f'<div class="note-card">{pts}</div>', unsafe_allow_html=True)

    if notes.get("examples"):
        st.markdown("#### 🔍 Examples")
        for item in notes["examples"]:
            st.markdown(
                f"""<div class="note-card"><h4>{item.get('title','')}</h4>
                <p>{item.get('explanation','')}</p></div>""",
                unsafe_allow_html=True,
            )

    if notes.get("remember_this"):
        st.markdown("#### ⭐ Remember This")
        pts = "".join(f"<p>• {p}</p>" for p in notes["remember_this"])
        st.markdown(f'<div class="note-card">{pts}</div>', unsafe_allow_html=True)


def render_summary_tab(pack: dict) -> None:
    st.markdown('<div class="sa-title">Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Choose how deep you want to go.</div>', unsafe_allow_html=True)

    options = [
        ("quick", "⚡ Quick", "2-minute revision"),
        ("standard", "📘 Standard", "Balanced explanation"),
        ("detailed", "📚 Detailed", "Deep understanding"),
    ]
    if "summary_depth" not in st.session_state:
        st.session_state["summary_depth"] = "standard"

    cols = st.columns(3)
    for col, (key, label, sub) in zip(cols, options):
        with col:
            selected = st.session_state["summary_depth"] == key
            st.markdown(
                f"""<div class="sa-card" style="text-align:center; border-color:{'var(--primary)' if selected else 'var(--border)'};">
                <div style="font-size:1.3rem; font-weight:700;">{label}</div>
                <div class="muted">{sub}</div></div>""",
                unsafe_allow_html=True,
            )
            if st.button("Select" if not selected else "✓ Selected", key=f"sumsel_{key}",
                         use_container_width=True, type="primary" if selected else "secondary"):
                st.session_state["summary_depth"] = key
                st.rerun()

    st.write("")
    depth = st.session_state["summary_depth"]
    summary = pack.get("summaries", {}).get(depth, {})
    st.markdown(f"### {summary.get('title', 'Summary')}")
    for sec in summary.get("sections", []):
        st.markdown(f"**{sec.get('heading','')}**")
        st.write(sec.get("content", ""))
        st.write("")

    render_review_banner(pack.get("reviews", {}).get("summary"), "Summary")


# ==========================================================================
# QUIZ (Practice)
# ==========================================================================

def render_quiz(material_id: str, pack: dict) -> None:
    mcqs_data = pack.get("mcqs", {})
    questions = mcqs_data.get("questions", [])
    review = pack.get("reviews", {}).get("mcqs")

    if not questions:
        if mcqs_data.get("raw_text"):
            st.markdown(mcqs_data["raw_text"])
        else:
            st.info("No practice questions available yet.")
        render_review_banner(review, "MCQs")
        return

    qstate = st.session_state["quiz_state"].setdefault(
        material_id, {"idx": 0, "answers": {}, "finished": False}
    )
    total = len(questions)

    if qstate["finished"]:
        correct = sum(
            1 for i, q in enumerate(questions) if qstate["answers"].get(i) == q.get("correct_option")
        )
        accuracy = round((correct / total) * 100) if total else 0
        st.markdown(
            f"""
            <div class="sa-card" style="text-align:center; padding: 2.2rem;">
                <div style="font-size:2.2rem;">🎉</div>
                <div style="font-size:1.4rem; font-weight:800; margin:0.3rem 0;">Quiz Complete</div>
                <div class="muted">Here's how you did</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        stat_card(c1, "Score", f"{correct}/{total}", "🏆")
        stat_card(c2, "Correct", correct, "✅")
        stat_card(c3, "Incorrect", total - correct, "❌")
        stat_card(c4, "Accuracy", f"{accuracy}%", "🎯")
        st.write("")
        if st.button("🔄 Try Again", type="primary", key=f"retry_{material_id}"):
            st.session_state["quiz_state"][material_id] = {"idx": 0, "answers": {}, "finished": False}
            st.rerun()
        render_review_banner(review, "MCQs")
        return

    idx = qstate["idx"]
    q = questions[idx]
    st.markdown(f'<div class="quiz-progress-label">Question {idx + 1} of {total}</div>', unsafe_allow_html=True)
    st.progress((idx) / total)
    st.markdown(f'<div class="quiz-question">{q["question"]}</div>', unsafe_allow_html=True)

    answered = idx in qstate["answers"]
    chosen = qstate["answers"].get(idx)

    for letter, option_text in q.get("options", {}).items():
        label = f"{letter}. {option_text}"
        if not answered:
            if st.button(label, key=f"opt_{material_id}_{idx}_{letter}", use_container_width=True):
                qstate["answers"][idx] = letter
                st.rerun()
        else:
            is_correct_option = letter == q.get("correct_option")
            is_chosen = letter == chosen
            prefix = "✅ " if is_correct_option else ("❌ " if is_chosen else "◻️ ")
            st.markdown(
                f"""<div class="sa-card" style="padding:0.7rem 1rem; margin-bottom:0.5rem;
                border-color:{'var(--success)' if is_correct_option else ('var(--danger)' if is_chosen else 'var(--border)')};">
                {prefix}{label}</div>""",
                unsafe_allow_html=True,
            )

    if answered:
        if chosen == q.get("correct_option"):
            st.markdown('<div class="feedback-correct">✓ Correct!</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="feedback-incorrect">✗ Not quite.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="explain-box">💡 {q.get("explanation","")}</div>', unsafe_allow_html=True)
        st.write("")
        btn_label = "Finish Quiz 🏁" if idx == total - 1 else "Next Question →"
        if st.button(btn_label, type="primary", key=f"next_{material_id}_{idx}"):
            if idx == total - 1:
                qstate["finished"] = True
            else:
                qstate["idx"] += 1
            st.rerun()

    render_review_banner(review, "MCQs")


def render_short_answers(pack: dict) -> None:
    short_data = pack.get("short_qs", {})
    questions = short_data.get("questions", [])
    if questions:
        for i, q in enumerate(questions, 1):
            with st.expander(f"Q{i}. {q.get('question','')}"):
                st.write(f"**Model answer:** {q.get('model_answer','')}")
    elif short_data.get("raw_text"):
        st.markdown(short_data["raw_text"])
    else:
        st.info("No short-answer questions available yet.")
    render_review_banner(pack.get("reviews", {}).get("short_answers"), "Short-Answer Q&A")


def page_practice() -> None:
    material = get_active_material()
    st.markdown('<div class="sa-title">📝 Practice</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Test your understanding with an AI-generated quiz.</div>',
                unsafe_allow_html=True)

    if not material:
        st.info("Upload material and generate a study pack first.")
        return
    pack = get_pack_for(material["id"])
    if not pack:
        st.info(f"No study pack yet for **{material['name']}**. Generate one first.")
        if st.button("Go to Generate →", type="primary"):
            set_page("generate")
            st.rerun()
        return

    sub_tabs = st.tabs(["🔘 Multiple Choice", "✍️ Short Answer", "🧾 Long Answer"])
    with sub_tabs[0]:
        render_quiz(material["id"], pack)
    with sub_tabs[1]:
        render_short_answers(pack)
    with sub_tabs[2]:
        for i, q in enumerate(pack.get("long_qs", {}).get("questions", []), 1):
            with st.expander(f"Q{i}. {q.get('question','')}"):
                for point in q.get("answer_outline", []):
                    st.write(f"- {point}")


# ==========================================================================
# FLASHCARDS
# ==========================================================================

def render_flashcards(material_id: str, pack: dict) -> None:
    cards = pack.get("flashcards", {}).get("flashcards", [])
    if not cards:
        st.info("No flashcards available yet.")
        return

    fstate = st.session_state["flashcard_state"].setdefault(material_id, {"idx": 0, "flipped": False})
    total = len(cards)
    idx = fstate["idx"]
    card = cards[idx]

    st.markdown(f'<div class="quiz-progress-label">Card {idx + 1} of {total}</div>', unsafe_allow_html=True)

    if not fstate["flipped"]:
        st.markdown(f'<div class="flash-card">{card.get("front","")}</div>', unsafe_allow_html=True)
        if st.button("👁️ Show Answer", type="primary", key=f"show_{material_id}_{idx}", use_container_width=True):
            fstate["flipped"] = True
            st.rerun()
    else:
        st.markdown(f'<div class="flash-card back">{card.get("back","")}</div>', unsafe_allow_html=True)
        if st.button("🙈 Hide Answer", key=f"hide_{material_id}_{idx}", use_container_width=True):
            fstate["flipped"] = False
            st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Previous", key=f"prev_{material_id}_{idx}", use_container_width=True, disabled=idx == 0):
            fstate["idx"] -= 1
            fstate["flipped"] = False
            st.rerun()
    with c2:
        if st.button("Next →", key=f"nextc_{material_id}_{idx}", use_container_width=True, disabled=idx == total - 1):
            fstate["idx"] += 1
            fstate["flipped"] = False
            st.rerun()


def page_flashcards() -> None:
    material = get_active_material()
    st.markdown('<div class="sa-title">🧠 Flashcards</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Flip through AI-generated flashcards for active recall.</div>',
                unsafe_allow_html=True)

    if not material:
        st.info("Upload material and generate a study pack first.")
        return
    pack = get_pack_for(material["id"])
    if not pack:
        st.info(f"No study pack yet for **{material['name']}**. Generate one first.")
        if st.button("Go to Generate →", type="primary"):
            set_page("generate")
            st.rerun()
        return

    render_flashcards(material["id"], pack)


# ==========================================================================
# ASK AI
# ==========================================================================

SUGGESTED_QUESTIONS = [
    "💡 Explain this topic simply",
    "📌 What are the important concepts?",
    "🎯 What should I revise?",
    "❓ Give me an example",
    "📝 Create a quick revision plan",
]


def render_ask_ai(material: dict, pack: dict) -> None:
    st.markdown('<div class="sa-title">Ask your study assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sa-subtitle">Ask anything about your uploaded study material.</div>',
                unsafe_allow_html=True)

    history = st.session_state["chat_history"].setdefault(material["id"], [])

    if not history:
        with st.chat_message("assistant", avatar="🎓"):
            st.write("Hi! I've studied your material. What would you like to know?")

    for msg in history:
        avatar = "🎓" if msg["role"] == "assistant" else "🙂"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    st.write("")
    chip_cols = st.columns(len(SUGGESTED_QUESTIONS))
    pending_question = None
    for col, question in zip(chip_cols, SUGGESTED_QUESTIONS):
        with col:
            if st.button(question, key=f"chip_{material['id']}_{question}", use_container_width=True):
                pending_question = question.split(" ", 1)[1]

    typed_question = st.chat_input("Ask a question…")
    final_question = typed_question or pending_question

    if final_question:
        history.append({"role": "user", "content": final_question})
        chat_context = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
        try:
            with st.spinner("Thinking…"):
                answer = gemini_service.ask_question(material["content"], chat_context, final_question)
        except GeminiServiceError as e:
            answer = f"Sorry, I ran into an issue: {e}"
        history.append({"role": "assistant", "content": answer})
        st.rerun()


def page_ask_ai() -> None:
    material = get_active_material()
    if not material:
        st.markdown('<div class="sa-title">💬 Ask AI</div>', unsafe_allow_html=True)
        st.info("Upload material first, then come back to ask questions about it.")
        return
    pack = get_pack_for(material["id"])
    render_ask_ai(material, pack)


# ==========================================================================
# MAIN ROUTER
# ==========================================================================

def main() -> None:
    load_css()
    render_sidebar()

    page = st.session_state["page"]
    if page == "dashboard":
        page_dashboard()
    elif page == "material":
        page_material()
    elif page == "generate":
        page_generate()
    elif page == "practice":
        page_practice()
    elif page == "flashcards":
        page_flashcards()
    elif page == "ask_ai":
        page_ask_ai()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
