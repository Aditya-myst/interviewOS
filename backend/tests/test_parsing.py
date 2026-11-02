"""Parsing tests: extraction, sections, deterministic matching, and the quote gate.

The invariant under test is the product's promise: **every skill carries a span
that exists in the document**. If these pass, a fabricated claim cannot reach the
database; if they fail, the whole profile is theatre.
"""
import io
import pathlib

import pytest

from app.parsing import matcher, resume, sections, taxonomy
from app.parsing.extract import UnparseableDocument, extract
from app.parsing.quotes import sentence_around, verify

SAMPLE = pathlib.Path(__file__).parent / "data" / "sample_resume.txt"
TEXT = SAMPLE.read_text()


def make_pdf(lines: list[str]) -> bytes:
    """A real, minimal single-page PDF — no extra dependency needed to test pypdf."""
    ops = ["BT", "/F1 12 Tf", "72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            ops.append("0 -16 Td")
        ops.append(f"({line}) Tj")
    ops.append("ET")
    stream = "\n".join(ops).encode()
    bodies = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(bodies, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(bodies) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(bodies) + 1,
        xref,
    )
    return bytes(out)


# ── extraction ────────────────────────────────────────────────────────────────
def test_text_extraction_is_the_text_we_will_quote_from():
    doc = extract("resume.txt", TEXT.encode())
    assert doc.kind == "text"
    assert doc.text.startswith("ADITYA KUMAR JHA")
    assert doc.sha256 and len(doc.sha256) == 64
    # the stored text must be exactly what page offsets point into
    page = doc.pages[0]
    assert doc.text[page.start : page.end] == doc.text


def test_normalisation_keeps_offsets_honest():
    doc = extract("resume.txt", b"line one\r\n\r\n\r\n\r\nline two\r\n" + TEXT.encode())
    assert "\r" not in doc.text
    assert "\n\n\n" not in doc.text


def test_pdf_text_layer_is_read():
    pdf = make_pdf([
        "SKILLS",
        "Python, FastAPI, PostgreSQL, Docker",
        "PROJECTS",
        "Built a RAG chatbot backend in Python with FastAPI over 1200 documents",
        "Chunked documents by paragraph and served answers through a REST API",
    ])
    doc = extract("resume.pdf", pdf)
    assert doc.kind == "pdf"
    assert "FastAPI" in doc.text
    assert doc.pages[0].number == 1


def test_docx_is_read_including_tables():
    import docx

    document = docx.Document()
    document.add_paragraph("TECHNICAL SKILLS")
    document.add_paragraph(
        "Python, FastAPI, PostgreSQL, Redis, Docker, Git, Linux, pytest and GitHub Actions"
    )
    document.add_paragraph(
        "Built a RAG chatbot backend in Python with FastAPI over 1,200 college documents"
    )
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Docker"
    table.rows[0].cells[1].text = "PostgreSQL"
    buffer = io.BytesIO()
    document.save(buffer)

    doc = extract("resume.docx", buffer.getvalue())
    assert "Python" in doc.text and "Docker" in doc.text


def test_a_scanned_pdf_is_a_stated_status_not_a_crash():
    with pytest.raises(UnparseableDocument) as excinfo:
        extract("scan.pdf", make_pdf([""]))
    assert excinfo.value.reason in {"no_text_layer", "empty_file"}


def test_an_unsupported_type_says_what_is_supported():
    with pytest.raises(UnparseableDocument) as excinfo:
        extract("resume.pages", b"x" * 200)
    assert excinfo.value.reason == "unsupported_type"
    assert "pdf" in str(excinfo.value)


# ── sections ──────────────────────────────────────────────────────────────────
def test_sections_are_found_structurally():
    found = sections.detect(TEXT)
    names = [s.name for s in found]
    assert {"skills", "projects", "education"} <= set(names)
    skills_section = next(s for s in found if s.name == "skills")
    assert TEXT[skills_section.start : skills_section.end].count("FastAPI") == 1


# ── deterministic matching ────────────────────────────────────────────────────
def test_strong_skills_are_found_with_a_quote_each():
    claims = {c.skill_id: c for c in matcher.claims_from(TEXT)}
    for expected in ("python", "fastapi", "postgresql", "llm-rag", "docker"):
        assert expected in claims, f"{expected} should be matched deterministically"
    for claim in claims.values():
        assert claim.evidence, f"{claim.skill_id} has a claim with no quote"
        for item in claim.evidence:
            assert item["quote"], "empty quote"
            assert item["quote"] in TEXT or " ".join(item["quote"].split()) in " ".join(TEXT.split())


def test_an_ordinary_english_word_does_not_become_a_skill():
    """These exact phrases are in the sample document. Neither is evidence."""
    assert "the rest of the team" in TEXT and "next step" in TEXT
    prose_only = "EXPERIENCE\nDocumented the rest of the team's onboarding flow. The next step was deployment.\n"
    claims = {c.skill_id for c in matcher.claims_from(prose_only)}
    assert "rest-api" not in claims
    assert "nextjs" not in claims


def test_the_same_sentence_does_claim_the_skill_when_it_is_meant():
    """The weak-alias rule must not throw away real mentions: the sample says
    'REST API design' in its skills list and 'a REST API' in a project."""
    claims = {c.skill_id for c in matcher.claims_from(TEXT)}
    assert "rest-api" in claims


def test_weak_alias_counts_when_it_is_corroborated():
    """'next js' is weak in general but 'Next.js' in a project heading is explicit."""
    text = ("PROJECTS\nInterview Prep Tracker - Next.js, PostgreSQL\n"
            "Built a dashboard. Ran weekly reviews.\n")
    claims = {c.skill_id for c in matcher.claims_from(text)}
    assert "nextjs" in claims


def test_a_resume_can_claim_a_listing_or_a_use_but_never_advanced():
    claims = matcher.claims_from(TEXT)
    levels = {c.claimed_level for c in claims}
    assert levels <= {"listed", "intermediate"}
    python_claim = next(c for c in claims if c.skill_id == "python")
    assert python_claim.claimed_level == "intermediate"
    assert "projects" in python_claim.claim_basis


def test_every_claim_confidence_is_bounded():
    for claim in matcher.claims_from(TEXT):
        assert 0 < claim.confidence <= 0.95


def test_vocabulary_comes_from_the_taxonomy_file():
    vocab = taxonomy.load()
    assert len(vocab) == 31
    assert vocab["llm-rag"].interview_relevance == 1.0
    assert "rag" in vocab["llm-rag"].terms


# ── the quote gate ────────────────────────────────────────────────────────────
def test_gate_accepts_a_real_quote_and_locates_it():
    quote = "Built a RAG chatbot backend in Python with FastAPI"
    found = verify(quote, TEXT)
    assert found is not None
    assert TEXT[found.start : found.end] == quote


def test_gate_rejects_a_fabricated_quote():
    invented = "Led a team of six engineers building production RAG evaluation harnesses"
    assert verify(invented, TEXT) is None


def test_gate_tolerates_line_breaks_but_not_word_changes():
    broken = "Chunked\ndocuments by paragraph"
    assert verify(broken, TEXT) is not None                      # PDF line wrap
    assert verify("Chunked records by paragraph", TEXT) is None  # paraphrase
    assert verify("short", TEXT) is None                          # too short to be evidence


def test_sentence_helper_never_returns_a_span_outside_the_text():
    quote, start, end = sentence_around(TEXT, TEXT.index("FastAPI"), TEXT.index("FastAPI") + 7)
    assert 0 <= start < end <= len(TEXT)
    assert quote in TEXT[start:end] or quote.strip() in TEXT


# ── the whole deterministic pass ──────────────────────────────────────────────
def test_parse_reports_its_own_method_and_evidence_count():
    doc = extract("resume.txt", TEXT.encode())
    parsed = resume.parse(doc)
    assert parsed.stats["method"] == "deterministic (taxonomy aliases, no model)"
    assert parsed.stats["skills_found"] == len(parsed.skills) > 0
    assert parsed.stats["quotes"] >= parsed.stats["skills_found"]
    # the sample says "Teaching Assistant, Data Structures - 2025", a single year,
    # which is a date, not a duration — so the honest answer is None with a reason
    assert parsed.experience_years is None
    assert "not stated" in parsed.experience_basis


def test_parse_json_maps_every_skill_to_the_contract_fields():
    parsed = resume.parse(extract("resume.txt", TEXT.encode()))
    payload = parsed.as_json()
    for skill in payload["skills"]:
        assert set(skill) >= {
            "skill_id", "name", "category", "claimed_level", "confidence", "in_resume", "evidence",
        }
        for evidence in skill["evidence"]:
            assert evidence["type"] in {
                "resume_project", "resume_skill_list", "resume_experience", "resume_summary",
            }
            assert isinstance(evidence["start"], int) and isinstance(evidence["end"], int)
            assert evidence["end"] > evidence["start"]


def test_an_email_or_url_is_not_evidence_of_a_skill():
    """A contact line reading `github.com/example` said nothing about how well
    anyone uses Git, and the first version of the matcher claimed it did."""
    contact_only = "ADITYA KUMAR JHA\naditya@example.com | github.com/example\n\nEDUCATION\nB.Tech, 2023 - 2027\n"
    claims = {c.skill_id for c in matcher.claims_from(contact_only)}
    assert "git" not in claims


def test_degree_dates_are_not_work_experience():
    """The first version reported 4 years of experience for a second-year student
    by reading 'B.Tech Computer Science, 2023 - 2027'."""
    doc = extract("resume.txt", ("SKILLS\nPython, FastAPI, PostgreSQL, Docker, Git\n\n"
                                 "EDUCATION\nB.Tech Computer Science, 2023 - 2027\n" * 3).encode())
    parsed = resume.parse(doc)
    assert parsed.experience_years is None
    assert "not stated" in parsed.experience_basis


def test_work_date_ranges_do_count_and_stop_at_today():
    text = ("EXPERIENCE\nBackend intern, Acme - 2022 - 2024\nBuilt FastAPI services in Python.\n"
            "PROJECTS\nSide project - 2025 - present\nShipped a Docker image.\n")
    parsed = resume.parse(extract("resume.txt", text.encode()))
    assert parsed.experience_years == 4  # 2022 -> 2026 (present)
    assert "date ranges" in parsed.experience_basis


def test_confidence_separates_listed_from_used():
    claims = {c.skill_id: c for c in matcher.claims_from(TEXT)}
    listed = claims["rest-api"].confidence
    used = claims["fastapi"].confidence
    assert used > listed, "a project mention should outrank a skills-list mention"
    assert listed < 0.9 and used <= 0.9
