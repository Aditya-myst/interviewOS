"""The assessment ladder.

What these tests protect, in order of how much it would hurt to lose:

1. The ladder is built from the curriculum, for *any* role — the marketing skills get
   checkpoints exactly like FastAPI does.
2. A vague answer cannot verify anything, and one strong answer cannot carry a weak one.
3. The session API follows the contract: start, answer, complete, and the two 404s.
"""
from __future__ import annotations

import pytest

from app.assessment import service
from app.assessment.ladder import LEVELS, build_ladder

THOROUGH = [
    ("I use the HTTP verbs by intent: GET reads and never changes state, POST creates, PUT "
    "replaces, PATCH updates a field, DELETE removes. Status codes follow from that: 200 "
    "for a read, 201 with a Location header for a create, 204 for a delete, 404 when the "
    "resource is missing, 409 on a conflict, and 422 when validation fails."),
    ("I validate input with a Pydantic model per endpoint so the body is parsed and typed "
    "before the handler runs. For output I use a separate response model to shape what "
    "leaves the service, so internal fields like tenant_id never leak; validation errors "
    "return 422, and because the model is a dependency I can override it in tests."),
    ("I implemented token auth: login checks credentials and issues a short-lived JWT, and "
    "a dependency verifies that token on every protected route. The flow is request, "
    "verify signature and expiry, load the user, check scopes. I rotated the signing key "
    "behind a kid header with no downtime and measured p95 at 40 ms; the trade-off was "
    "one extra round trip."),
]
VAGUE = "It is about doing things the right way and being careful, which I think matters a lot in practice."
OFF_TOPIC = "I designed the seating plan for a 90 person event, sourcing vendors and staying 12 percent under budget."


@pytest.fixture(autouse=True)
def _clean_store():
    service.reset_store()
    yield
    service.reset_store()


# ------------------------------------------------------------------ the ladder


def test_a_skill_gets_three_rungs_in_order():
    rungs = build_ladder({"skill_id": "fastapi", "name": "FastAPI"})
    assert len(rungs) == 3
    assert [r.level for r in rungs] == ["conceptual", "practical", "applied"]
    assert [r.index for r in rungs] == [1, 2, 3]


def test_every_rung_probes_a_different_subtopic_with_a_rubric():
    rungs = build_ladder({"skill_id": "fastapi", "name": "FastAPI"})
    subtopics = [r.subtopic_id for r in rungs]
    assert len(set(subtopics)) == 3, subtopics
    for rung in rungs:
        assert rung.question.rubric, rung.subtopic_title
        assert "fastapi" in rung.question.text.lower()


def test_the_ladder_works_for_a_role_that_is_not_engineering():
    """Marketing, design, teaching — the ladder cannot assume a stack."""
    rungs = build_ladder({"skill_id": "content-strategy", "name": "Content Strategy"})
    assert len(rungs) == 3
    for rung in rungs:
        assert rung.question.rubric
        assert "content" in rung.question.text.lower()
        # no engineering vocabulary leaking into a marketing checkpoint
        for word in ("code", "api", "deploy", "compiler"):
            assert word not in rung.question.text.lower()


def test_the_rubric_ignores_instruction_words():
    """'correctly', 'without', 'explain' describe the question, not the answer."""
    rungs = build_ladder({"skill_id": "fastapi", "name": "FastAPI"})
    terms = {item.key for rung in rungs for item in rung.question.rubric}
    assert not terms & {"correctly", "without", "explain", "fundamentals", "basics"}


def test_a_skill_with_no_subtopics_returns_no_ladder():
    assert build_ladder({"skill_id": "not-a-real-skill", "name": "Nope"}) == []
    with pytest.raises(ValueError):
        service.start({"skill_id": "not-a-real-skill", "name": "Nope"})


# ------------------------------------------------------------------ the score


def _run(answers: list[str]) -> dict:
    record = service.start({"skill_id": "fastapi", "name": "FastAPI"})
    state = None
    for text in answers:
        state = service.answer(record, text)
    assert state is not None
    return state


def test_a_thorough_ladder_verifies_the_skill():
    state = _run(THOROUGH)
    assert state["status"] == "completed"
    assert state["result"]["status_after"] == "verified"
    assert state["result"]["inferred_level"] in ("advanced", "expert")
    assert state["result"]["confidence"] <= 0.9
    assert all(answer["quote"] for answer in state["answers"])


def test_a_vague_ladder_cannot_verify_anything():
    state = _run([VAGUE] * 3)
    assert state["result"]["status_after"] == "needs_revision"
    assert state["result"]["mean_score"] == 0.0
    assert all(answer["quote"] is None for answer in state["answers"])


def test_an_off_topic_ladder_earns_no_credit():
    state = _run([OFF_TOPIC] * 3)
    assert state["result"]["status_after"] == "needs_revision"
    assert state["result"]["mean_score"] < 0.3


def test_one_strong_answer_cannot_carry_a_weak_one():
    """Verification needs a floor, not just an average."""
    state = _run([THOROUGH[0], VAGUE, THOROUGH[2]])
    result = state["result"]
    assert result["lowest_score"] < 0.5
    assert result["status_after"] != "verified"
    assert result["verified"] is False


def test_a_finished_ladder_names_what_to_redo():
    state = _run([THOROUGH[0], VAGUE, THOROUGH[2]])
    redo = state["result"]["redo"]
    assert len(redo) == 1
    assert redo[0]["question"].startswith("FastAPI")
    assert redo[0]["score"] < 0.5


def test_the_state_carries_every_field_the_contract_requires():
    record = service.start({"skill_id": "fastapi", "name": "FastAPI"})
    state = service.state(record)
    for key in ("assessment_id", "skill_id", "level", "status", "question_index", "question_total", "question"):
        assert key in state
    assert state["question"]["rubric_size"] >= 1
    assert state["question"]["question_type"] in {
        "fundamentals", "advanced", "coding", "debugging",
        "project_deep_dive", "scenario", "system_design", "behavioral",
    }
    # no invented dimension: there is no audio, so there is no communication score
    assert "communication" not in (state.get("feedback") or {}).get("scores", {})


# ------------------------------------------------------------------ the API


def test_the_api_walks_a_ladder_to_completion():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    started = client.post("/v1/assessment/start", json={"skill_id": "fastapi"})
    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "in_progress"
    assert body["question_index"] == 1

    state = body
    for text in THOROUGH:
        answered = client.post(
            "/v1/assessment/answer", json={"assessment_id": body["assessment_id"], "answer": text}
        )
        assert answered.status_code == 200
        state = answered.json()

    assert state["status"] == "completed"
    assert state["question"] is None
    assert state["result"]["status_after"] == "verified"
    # no database in tests, so the response says so rather than pretending
    assert state["persisted"] is False


def test_answering_a_completed_ladder_is_a_conflict():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    body = client.post("/v1/assessment/start", json={"skill_id": "fastapi"}).json()
    for text in THOROUGH:
        client.post("/v1/assessment/answer", json={"assessment_id": body["assessment_id"], "answer": text})
    again = client.post(
        "/v1/assessment/answer", json={"assessment_id": body["assessment_id"], "answer": THOROUGH[0]}
    )
    assert again.status_code == 409


def test_unknown_skill_and_unknown_assessment_are_404():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    assert client.post("/v1/assessment/start", json={"skill_id": "astrology"}).status_code == 404
    assert client.post("/v1/assessment/answer", json={"assessment_id": "nope", "answer": "x"}).status_code == 404
    assert client.get("/v1/assessment/nope").status_code == 404


def test_an_empty_answer_is_rejected_before_it_reaches_the_scorer():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    body = client.post("/v1/assessment/start", json={"skill_id": "fastapi"}).json()
    assert (
        client.post("/v1/assessment/answer", json={"assessment_id": body["assessment_id"], "answer": ""}).status_code
        == 422
    )


def test_levels_are_the_three_the_contract_names():
    assert set(LEVELS) == {"conceptual", "practical", "applied"}


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def test_an_unknown_skill_is_a_404_not_a_500(client):
    """Regression: the status was raised inside a context manager that yielded in its try,
    so FastAPI saw `RuntimeError: generator didn't stop after throw()` and answered 500 —
    after which the handler went on to yield fixture data."""
    response = client.post("/v1/assessment/start", json={"skill_id": "definitely-not-a-skill"})
    assert response.status_code == 404
    assert "not in this profile" in str(response.json().get("detail"))


def test_an_endpoint_error_does_not_flip_the_data_source(client):
    """A refused request must not claim to be served from the database or from memory."""
    response = client.post("/v1/assessment/start", json={"skill_id": "definitely-not-a-skill"})
    assert response.status_code == 404
    assert response.headers.get("x-data-source") in (None, "fixture", "memory")
