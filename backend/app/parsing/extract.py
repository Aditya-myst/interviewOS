"""Text extraction — the first step that can silently ruin everything after it.

Two rules:

1. **The text we store is the text we quote from.** Offsets recorded in evidence point
   into `resumes.raw_text`, so normalisation happens exactly once, here, before any
   span is computed. If we tidy the text later, every stored quote stops matching.
2. **A document we cannot read is a stated status, not an exception.** A scanned PDF
   has no text layer; that is `parse_status: unparseable` with the reason, not a 500
   and not an empty resume that looks like a blank candidate.
"""
from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass, field

MAX_BYTES = 10 * 1024 * 1024  # matches the check constraint on resumes.size_bytes

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class UnparseableDocument(RuntimeError):
    """The reason travels to the API response verbatim. Never swallowed."""

    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}" if detail else reason)


@dataclass
class Page:
    number: int
    start: int
    end: int


@dataclass
class Document:
    text: str
    kind: str
    pages: list[Page] = field(default_factory=list)
    sha256: str = ""
    size_bytes: int = 0
    filename: str = ""
    warnings: list[str] = field(default_factory=list)

    def page_of(self, offset: int) -> int | None:
        for page in self.pages:
            if page.start <= offset < page.end:
                return page.number
        return None


def _normalise(raw: str) -> str:
    """One canonical form: LF newlines, no trailing spaces, no runs of blank lines.

    Deliberately conservative — no case folding, no dash unification, nothing that
    would make a stored quote fail to match the stored text.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _from_pdf(data: bytes) -> tuple[str, list[Page], list[str]]:
    from pypdf import PdfReader

    warnings: list[str] = []
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise UnparseableDocument("pdf_unreadable", str(exc)) from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise UnparseableDocument("pdf_encrypted", "password-protected PDF") from exc

    chunks: list[str] = []
    pages: list[Page] = []
    cursor = 0
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 — one bad page must not lose the rest
            warnings.append(f"page {index} failed to extract: {type(exc).__name__}")
            page_text = ""
        page_text = page_text.strip()
        if not page_text:
            warnings.append(f"page {index} has no text layer (scanned image?)")
        block = page_text + "\n\n"
        pages.append(Page(number=index, start=cursor, end=cursor + len(block)))
        chunks.append(block)
        cursor += len(block)

    return "".join(chunks), pages, warnings


def _from_docx(data: bytes) -> str:
    import docx

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise UnparseableDocument("docx_unreadable", str(exc)) from exc

    lines: list[str] = [p.text for p in document.paragraphs]
    # tables are where resumes hide dates and skill grids; a parser that skips them
    # silently loses content, which is worse than a slightly noisy line
    for table in document.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(lines)


def extract(filename: str, data: bytes) -> Document:
    if not data:
        raise UnparseableDocument("empty_file", "0 bytes")
    if len(data) > MAX_BYTES:
        raise UnparseableDocument("too_large", f"{len(data)} bytes > {MAX_BYTES}")

    lowered = filename.lower()
    extension = "." + lowered.rsplit(".", 1)[-1] if "." in lowered else ""
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnparseableDocument(
            "unsupported_type", f"{extension or 'no extension'} — accepted: pdf, docx, txt, md"
        )

    warnings: list[str] = []
    pages: list[Page] = []

    if extension == ".pdf":
        raw, pages, warnings = _from_pdf(data)
        kind = "pdf"
    elif extension == ".docx":
        raw = _from_docx(data)
        kind = "docx"
    else:
        try:
            raw = data.decode("utf-8")
        except UnicodeDecodeError:
            raw = data.decode("latin-1")
            warnings.append("decoded as latin-1 — not valid UTF-8")
        kind = "text"

    text = _normalise(raw)
    if not pages:
        pages = [Page(number=1, start=0, end=len(text))]
    else:
        # normalisation changes length; re-anchor page ranges onto the final text
        shift = len(text) - len(raw.strip()) if len(raw.strip()) else 0
        pages = [Page(p.number, max(0, p.start - shift), min(len(text), p.end - shift)) for p in pages]

    if len(text) < 120:
        raise UnparseableDocument(
            "no_text_layer",
            f"only {len(text)} characters extracted — likely a scanned or image-only document",
        )

    return Document(
        text=text,
        kind=kind,
        pages=pages,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        filename=filename,
        warnings=warnings,
    )
