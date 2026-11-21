"""Document text extraction for PDF, DOCX, and TXT study material."""

from __future__ import annotations

import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from utils.helpers import estimate_pages


class DocumentParseError(Exception):
    """Raised when a document cannot be read or contains no extractable text."""


def _parse_pdf(file_bytes: bytes) -> tuple[str, int]:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentParseError(f"Could not read PDF file: {exc}") from exc

    page_texts: list[str] = []
    for page in reader.pages:
        extracted = (page.extract_text() or "").strip()
        if extracted:
            page_texts.append(extracted)

    text = "\n\n".join(page_texts).strip()
    if not text:
        raise DocumentParseError(
            "No extractable text was found in this PDF. It appears to be scanned or image-only."
        )
    return text, max(1, len(reader.pages))


def _parse_docx(file_bytes: bytes) -> tuple[str, int]:
    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentParseError(f"Could not read DOCX file: {exc}") from exc

    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    text = "\n\n".join(parts).strip()
    if not text:
        raise DocumentParseError("This DOCX file contains no readable text.")
    return text, estimate_pages(text)


def _parse_txt(file_bytes: bytes) -> tuple[str, int]:
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="replace")

    cleaned = text.strip()
    if not cleaned:
        raise DocumentParseError("This text file is empty.")
    return cleaned, estimate_pages(cleaned)


def parse_document(filename: str, file_bytes: bytes) -> tuple[str, int, str]:
    """Extract plain text, page count, and file type label from uploaded bytes."""
    if not file_bytes:
        raise DocumentParseError("The uploaded file is empty.")

    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        text, pages = _parse_pdf(file_bytes)
        return text, pages, "PDF"
    if ext == ".docx":
        text, pages = _parse_docx(file_bytes)
        return text, pages, "DOCX"
    if ext == ".txt":
        text, pages = _parse_txt(file_bytes)
        return text, pages, "TXT"

    raise DocumentParseError(f"Unsupported file format '{ext or 'unknown'}'. Use PDF, DOCX, or TXT.")
