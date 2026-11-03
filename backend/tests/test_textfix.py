"""Encoding repair and the charset header.

Both exist because of one observed failure: a resume quote came back as
"â€œunderstanding why content worksâ€" in the terminal, which makes a verbatim quote wrong.
"""
from fastapi.testclient import TestClient

from app.main import create_app
from app.parsing.textfix import repair_mojibake

INTACT = "â€œUnderstanding why content works â€” and why hooks matter.â€"
TRUNCATED = "Understanding why content works, distribution psychology, narratives.â"
CLEAN = "Understanding why content works — and why “hooks” matter."
FRENCH = "J'ai travaillé sur la stratégie de contenu à Paris."


def test_intact_mojibake_is_repaired_to_real_punctuation():
    fixed, changed = repair_mojibake(INTACT)
    assert changed is True
    assert "“" in fixed and "—" in fixed
    assert "â€" not in fixed


def test_a_truncated_fragment_does_not_leave_rubbish_in_a_quote():
    fixed, _changed = repair_mojibake(TRUNCATED)
    assert "â" not in fixed


def test_correct_text_is_never_touched():
    assert repair_mojibake(CLEAN) == (CLEAN, False)


def test_french_is_not_mistaken_for_mojibake():
    """The failure mode of an over-eager repair: mangling valid accents."""
    assert repair_mojibake(FRENCH) == (FRENCH, False)


def test_accented_bytes_are_repaired():
    fixed, changed = repair_mojibake("trÃ¨s intÃ©ressant, Ã  Paris")
    assert changed is True
    assert "très intéressant" in fixed and "à Paris" in fixed


def test_every_json_response_declares_utf8():
    """PowerShell 5.1 decodes without a charset as latin-1 — this header is why the
    terminal stopped showing garbage."""
    with TestClient(create_app()) as api:
        response = api.post("/v1/interview/start", json={"mode": "jd_based", "question_count": 3})
        assert response.headers["content-type"] == "application/json; charset=utf-8"
