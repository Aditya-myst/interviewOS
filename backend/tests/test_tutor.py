"""The tutor's promise, as tests.

The important one is `test_every_answer_line_is_cited`: the tutor is only trustworthy if a
claim cannot appear without a row behind it. The rest keep its honesty honest — an
off-domain question gets "not in my sources", never the user's own gap dressed up as an
answer.
"""
from __future__ import annotations

import pytest

from app import fixtures
from app.config import DATA_DIR
from app.parsing import taxonomy
from app.tutor import service

PROFILE = fixtures.load("skill_profile")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def ask(question: str, **kwargs):
    return service.ask(question, profile=kwargs.pop("profile", PROFILE), **kwargs)


def test_answer_names_the_skill_asked_about():
    answer = ask("how do I get better at rag?")
    assert answer.matched
    assert answer.scope["skill_id"] == "llm-rag"
    assert answer.scope["in_profile"] is True


def test_three_steps_come_from_the_curriculum():
    answer = ask("how do I get better at rag?")
    ids = {sub["id"] for sub in taxonomy.raw_subtopics()["llm-rag"]}
    assert 1 <= len(answer.focus) <= service.MAX_FOCUS
    for node in answer.focus:
        assert node.subtopic_id in ids, f"{node.subtopic_id} is not a real subtopic"
        assert node.objective, "every step must carry the curriculum objective"


def test_every_answer_line_is_cited():
    """No sentence without a row: profile, evidence, subtopic or catalogue entry."""
    answer = ask("how do I improve my rag evaluation?")
    kinds = {c.kind for c in answer.citations}
    assert {"profile", "subtopic"} <= kinds
    # the evidence keeps the type it has in the profile (resume_project, assessment_answer…)
    assert any(kind in {"resume_project", "resume_quote", "assessment_answer"} for kind in kinds)
    for node in answer.focus:
        assert node.subtopic_id
        assert any(c.subtopic_id == node.subtopic_id for c in answer.citations)


def test_resources_are_real_catalogue_urls():
    """A link the user clicks must exist in data/curated.yaml, not in a model's memory."""
    catalogue = service.catalogue()
    allowed = {
        entry["url"]
        for skill in catalogue.values()
        for subtopics in skill.values()
        for entry in subtopics
    }
    answer = ask("how do I get better at rag?")
    urls = [c.url for c in answer.citations if c.kind == "resource"]
    assert urls, "the RAG skill has curated links and must show them"
    for url in urls:
        assert url in allowed


def test_free_resources_come_first():
    answer = ask("how do I get better at rag?")
    for node in answer.focus:
        paid = [bool(entry.get("is_paid")) for entry in node.resources]
        assert paid == sorted(paid), "a paywalled link must never sit above a free one"


def test_off_domain_question_is_refused():
    answer = ask("what is the salary at google?")
    assert answer.matched is False
    assert answer.focus == []
    assert "no row mentions" in answer.unknown["reason"]
    assert answer.unknown["can_answer"], "refusal must list what it can answer"


def test_open_question_falls_back_to_the_top_gap():
    answer = ask("what should I do next?")
    assert answer.matched
    assert answer.scope["skill_id"] == "llm-rag"  # the critical band on this profile


def test_skill_outside_the_catalogue_says_so():
    answer = ask("how do I get better at javascript?")
    assert answer.matched
    assert answer.scope["skill_id"] == "javascript"
    assert answer.scope["in_profile"] is False
    assert "no curated links" in answer.limits
    assert not [c for c in answer.citations if c.kind == "resource"]


def test_empty_profile_refuses_instead_of_teaching():
    answer = ask("how do I get better at rag?", profile={"skills": []})
    assert answer.matched is False
    assert answer.scope is None
    assert "no skills" in answer.unknown["reason"]


def test_same_question_same_answer():
    """Deterministic: no clock, no randomness, no network."""
    assert ask("explain rag evaluation").as_json() == ask("explain rag evaluation").as_json()


def test_never_claims_a_grade():
    answer = ask("how do I get better at rag?")
    assert "does not grade" in answer.limits
    blob = " ".join(
        [answer.lead or "", answer.standing or "", answer.limits or ""]
    ).lower()
    for forbidden in ("confident", "you are ready", "you will pass"):
        assert forbidden not in blob


@pytest.mark.parametrize("question", ["", "a", "hi"])
def test_short_question_is_rejected_by_the_api(client, question):
    response = client.post("/v1/tutor/ask", json={"question": question})
    assert response.status_code == 422


def test_api_answers_and_declares_its_source(client):
    response = client.post("/v1/tutor/ask", json={"question": "how do I get better at rag?"})
    assert response.status_code == 200
    body = response.json()
    assert body["matched"] is True
    assert body["scope"]["skill_id"] == "llm-rag"
    assert response.headers["x-data-source"] == "fixture"
    assert response.headers["x-fallback-reason"] == "no_db"


def test_api_empty_state_has_no_evidence_to_show(client):
    response = client.post("/v1/tutor/ask?state=empty", json={"question": "how do I improve rag?"})
    assert response.status_code == 200
    assert response.json()["matched"] is False
    assert DATA_DIR.exists()
