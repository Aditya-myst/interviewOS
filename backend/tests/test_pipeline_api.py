"""The pipeline endpoints, exercised without a database.

Two things matter here and both are about honesty rather than plumbing:
a document we cannot read must be a 422 with a reason, and a write that did not
happen must never be reported as `persisted: true`.
"""
import pathlib

import pytest
from fastapi.testclient import TestClient

from app import fixtures, store
from app.main import app

DATA = pathlib.Path(__file__).parent / "data"
RESUME = (DATA / "sample_resume.txt").read_bytes()
JD = (DATA / "sample_jd.txt").read_text()


@pytest.fixture()
def client():
    return TestClient(app)


def test_upload_parses_without_a_database_and_says_so(client):
    response = client.post(
        "/v1/resume/upload", files={"file": ("resume.txt", RESUME, "text/plain")}
    )
    assert response.status_code == 200
    assert response.headers["x-data-source"] == "pipeline"
    body = response.json()
    assert body["parse_status"] == "ok"
    assert body["persisted"] is False and body["resume_id"] is None
    assert body["skills"] and all(skill["evidence"] for skill in body["skills"])
    assert body["stats"]["method"].startswith("deterministic")


def test_every_uploaded_skill_quote_can_be_found_in_the_document(client):
    body = client.post(
        "/v1/resume/upload", files={"file": ("resume.txt", RESUME, "text/plain")}
    ).json()
    text = RESUME.decode()
    flat = " ".join(text.split())
    for skill in body["skills"]:
        for item in skill["evidence"]:
            assert " ".join(item["quote"].split()) in flat


def test_an_unreadable_document_is_a_422_with_a_code(client):
    response = client.post(
        "/v1/resume/upload", files={"file": ("resume.pages", b"x" * 500, "application/octet-stream")}
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "unsupported_type"
    assert "pdf" in detail["message"]


def test_a_scanned_pdf_is_a_422_not_an_empty_profile(client):
    empty_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    response = client.post("/v1/resume/upload", files={"file": ("scan.pdf", empty_pdf, "application/pdf")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] in {"no_text_layer", "pdf_unreadable"}


def test_an_oversized_upload_is_refused_by_size_not_by_parser(client):
    response = client.post(
        "/v1/resume/upload", files={"file": ("big.txt", b"x" * (11 * 1024 * 1024), "text/plain")}
    )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "too_large"


def test_jd_analyze_returns_requirements_with_quotes(client):
    response = client.post("/v1/jd/analyze", json={"text": JD})
    assert response.status_code == 200
    body = response.json()
    assert response.headers["x-data-source"] == "pipeline"
    assert body["persisted"] is False
    requirements = body["parsed"]["requirements"]
    assert requirements and all(r["evidence"] for r in requirements)
    assert body["parsed"]["stats"]["required"] >= 5


def test_a_too_short_jd_is_refused(client):
    response = client.post("/v1/jd/analyze", json={"text": "We need a dev."})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "jd_too_short"


def test_profile_falls_back_to_fixtures_with_the_right_header(client):
    response = client.get("/v1/skills/profile")
    assert response.status_code == 200
    assert response.headers["x-data-source"] == "fixture"


def test_profile_switches_to_database_when_rows_exist(client, monkeypatch):
    payload = {
        "provisional": False,
        "counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "verified": 1, "unverified": 0},
        "coverage_by_category": [{"category": "AI", "verified": 1, "developing": 0, "unverified": 0}],
        "skills": [{"skill_id": "llm-rag", "name": "LLM & RAG", "category": "AI",
                    "status": "verified", "verified_level": "advanced", "priority": 0.6,
                    "priority_band": "critical", "evidence": [{"type": "assessment_answer",
                    "quote": "Measured recall@10 on a labelled set."}]}],
    }
    monkeypatch.setattr("app.api.prep._from_store", lambda builder: (payload, None) if builder == "profile_payload" else (None, "no_rows"))
    response = client.get("/v1/skills/profile")
    assert response.headers["x-data-source"] == "database"
    assert response.json()["skills"][0]["skill_id"] == "llm-rag"


def test_latest_resume_without_a_database_is_a_stated_degraded_mode(client):
    response = client.get("/v1/resume/latest")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "degraded_mode"


def test_store_refuses_to_write_a_skill_with_no_evidence():
    """The storage layer repeats the product rule: no quote, no row."""

    class Row:
        skill_id = "python"
        status = "claimed"
        claimed_level = "listed"
        verified_level = None
        expected_level = "advanced"
        confidence = 0.6
        jd_importance = 0.7
        interview_relevance = 0.9
        gap = 0.5
        priority = 0.3
        priority_band = "medium"
        explanation = "because"
        in_resume = True
        in_jd = True
        evidence: list = []  # noqa: RUF012 — the point of the fixture

    class FakeSession:
        def execute(self, *a, **k):  # pragma: no cover - must never be reached
            raise AssertionError("nothing should be written")

    with pytest.raises(store.EvidenceRequired):
        store.upsert_skills(FakeSession(), user_id="00000000-0000-4000-8000-000000000000", rows=[Row()])


def test_a_broken_read_says_so_instead_of_looking_empty(client, monkeypatch):
    """A SQL error and an empty account both serve fixtures. The header now tells them
    apart — that difference is what turned a wrong column name into a quiet fixture."""
    monkeypatch.setattr("app.api.prep._from_store", lambda builder: (None, "db_error"))
    response = client.get("/v1/analytics/dashboard")
    assert response.headers["x-data-source"] == "fixture"
    assert response.headers["x-fallback-reason"] == "db_error"


def test_an_empty_account_is_labelled_no_rows(client, monkeypatch):
    monkeypatch.setattr("app.api.prep._from_store", lambda builder: (None, "no_rows"))
    response = client.get("/v1/learning/roadmap")
    assert response.headers["x-fallback-reason"] == "no_rows"


def test_the_database_path_carries_no_fallback_reason(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.prep._from_store",
        lambda builder: (fixtures.load("dashboard"), None),
    )
    response = client.get("/v1/analytics/dashboard")
    assert response.headers["x-data-source"] == "database"
    assert "x-fallback-reason" not in response.headers


def test_a_database_rejection_is_a_stated_failure_not_a_500(client, monkeypatch):
    """The upload that crashed on a real Postgres.

    A resume re-upload tried to reset a graded skill's status; the schema's transition
    guard raised, and the exception escaped as a 500 — the user saw "the API answered 500"
    with no idea which half failed. The document parses either way, so a rejected write is
    a 200 that says `persisted: false` and names the reason.
    """
    from sqlalchemy.exc import IntegrityError

    monkeypatch.setattr("app.api.pipeline._db_ready", lambda: True)

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise IntegrityError(
                "insert into candidate_skills", {}, Exception("illegal transition weak -> unverified")
            )

    class FakeContext:
        def __enter__(self):
            return BrokenSession()

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr("app.api.pipeline.get_session", lambda: FakeContext())
    monkeypatch.setattr("app.api.pipeline.store.resolve_user", lambda session: ("u", "demo"))
    monkeypatch.setattr(
        "app.api.pipeline.store.save_resume", lambda *a, **k: "11111111-1111-4111-8111-111111111111"
    )

    response = client.post(
        "/v1/resume/upload", files={"file": ("resume.txt", RESUME, "text/plain")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parse_status"] == "ok", "the parse is still real and still returned"
    assert body["persisted"] is False, "a rejected write must never claim to be saved"
    assert body["persist_error"]["code"] == "persist_failed"
    assert "illegal transition" in body["persist_error"]["message"]
    assert response.headers["x-data-source"] == "pipeline"
