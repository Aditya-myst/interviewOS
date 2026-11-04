"""Progress must be stored, and re-planning must never undo it.

The defect this file exists for: `learning_topics` was read by the dashboard and written by
nobody, so "0 of 5 topics done" could not move. Two things are easy to get wrong once you
start writing it, and both are tested here:

1. **A re-plan must not reset progress.** Running the JD analysis again rewrites the plan.
   If that sync touched `status`, a candidate who finished two topics would find them
   unfinished — a worse bug than the frozen counter it replaces.
2. **A re-order must not collide.** `learning_topics` is unique on (path_id, order_index),
   so swapping two topics in place hits the constraint mid-update. The first version of this
   code parked rows with a modulo, landed an in-plan row exactly on an archived one, raised
   `UniqueViolation`, and the read path silently degraded to "nothing done". The tests below
   drive that exact sequence against Postgres.
"""
from __future__ import annotations

import os
import uuid

import pytest

from app.prep import progress

DSN = os.environ.get("INTERVIEWOS_TEST_DATABASE_URL")
USER = "11111111-1111-4111-8111-111111111111"


# ── no database needed ────────────────────────────────────────────────────────
def test_path_id_is_stable_and_per_candidate():
    assert progress.path_id_for(USER) == progress.path_id_for(USER)
    assert progress.path_id_for(USER) != progress.path_id_for("22222222-2222-4222-8222-222222222222")
    assert isinstance(progress.path_id_for(USER), uuid.UUID)


def test_a_status_implies_a_progress_value():
    """'done' with a bar at 40% would be two answers to one question."""
    assert progress.PROGRESS_FOR["done"] == 1.0
    assert progress.PROGRESS_FOR["not_started"] == 0.0
    assert set(progress.PROGRESS_FOR) == set(progress.STATUSES)


def test_the_api_says_why_it_cannot_save_without_a_database(client):
    response = client.patch(
        f"/v1/preparation/topics/{uuid.uuid4()}", json={"status": "done"}
    )
    assert response.status_code == 503
    assert "Postgres" in response.json()["detail"]


def test_an_unknown_status_is_rejected_before_any_write(client):
    response = client.patch(f"/v1/preparation/topics/{uuid.uuid4()}", json={"status": "finished"})
    assert response.status_code == 422


def test_create_is_idempotent_and_honest_without_a_database(client):
    response = client.post("/v1/preparation/create")
    assert response.status_code == 409
    assert "upload a resume" in response.json()["detail"]


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


# ── against Postgres ──────────────────────────────────────────────────────────
def _topic(index: int, skill: str, title: str) -> dict:
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{skill}:{title}")),
        "skill_id": skill,
        "skill_name": skill,
        "title": title,
        "objective": "describe it",
        "subtopics": [title],
        "depth": "core",
        "order_index": index,
        "estimated_minutes": 60,
    }


def _plan(*topics: dict) -> dict:
    return {"summary": "test plan", "topics": list(topics)}


@pytest.fixture
def db():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    if not DSN:
        pytest.skip("set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
    engine = create_engine(DSN)
    with engine.begin() as conn:
        conn.execute(
            text("insert into auth.users (id, email) values (:u, 'p@e.st') on conflict (id) do nothing"),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.profiles (id, email, full_name) values (:u, 'p@e.st', 'P') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text("delete from public.learning_topics where user_id = cast(:u as uuid)"), {"u": USER}
        )
        conn.execute(
            text("delete from public.learning_paths where user_id = cast(:u as uuid)"), {"u": USER}
        )
    session = Session(engine)
    try:
        yield session
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("delete from public.learning_topics where user_id = cast(:u as uuid)"),
                {"u": USER},
            )
            conn.execute(
                text("delete from public.learning_paths where user_id = cast(:u as uuid)"),
                {"u": USER},
            )
        session.close()


def _rows(session) -> list:
    from sqlalchemy import text

    return session.execute(
        text(
            "select order_index, title, status::text from public.learning_topics "
            "where user_id = cast(:u as uuid) order by order_index"
        ),
        {"u": USER},
    ).all()


def test_sync_is_idempotent(db):
    plan = _plan(_topic(0, "llm-rag", "Tokens"), _topic(1, "llm-rag", "RAG"))
    progress.sync_plan(db, user_id=USER, plan=plan)
    progress.sync_plan(db, user_id=USER, plan=plan)
    progress.sync_plan(db, user_id=USER, plan=plan)
    assert len(_rows(db)) == 2


def test_progress_survives_a_replan(db):
    """The whole point: re-running the JD analysis must not un-finish your work."""
    a = _topic(0, "llm-rag", "Tokens")
    b = _topic(1, "llm-rag", "RAG")
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b))
    progress.set_status(db, user_id=USER, topic_id=a["id"], status="done")

    # a different plan entirely — the embedding topic is gone
    progress.sync_plan(db, user_id=USER, plan=_plan(_topic(0, "docker", "Images")))
    # and back again
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b))

    states = progress.topic_states(db, user_id=USER)
    assert states[a["id"]]["status"] == "done", "a re-plan reset a finished topic"
    assert states[b["id"]]["status"] == "not_started"


def test_reordering_cannot_hit_the_unique_index(db):
    """Swap two topics: parks, then writes 0..n. Used to raise UniqueViolation."""
    a = _topic(0, "llm-rag", "Tokens")
    b = _topic(1, "llm-rag", "RAG")
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b))
    swapped_b = {**b, "order_index": 0}
    swapped_a = {**a, "order_index": 1}
    progress.sync_plan(db, user_id=USER, plan=_plan(swapped_b, swapped_a))

    rows = _rows(db)
    assert [(r[0], r[1]) for r in rows] == [(0, "RAG"), (1, "Tokens")]


def test_archived_topics_leave_the_totals_but_keep_their_status(db):
    """'2 of 5 done' must not quietly become '2 of 9' when a skill drops out of scope."""
    a = _topic(0, "llm-rag", "Tokens")
    b = _topic(1, "llm-rag", "RAG")
    c = _topic(2, "docker", "Images")
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b, c))
    progress.set_status(db, user_id=USER, topic_id=c["id"], status="done")

    # the new JD no longer mentions docker
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b))

    states = progress.topic_states(db, user_id=USER)
    assert c["id"] not in states, "an archived topic is not part of the current plan"
    totals = progress._totals(db, user_id=USER)
    assert (totals["done"], totals["total"]) == (0, 2)

    # and it comes back finished, because the row was kept
    progress.sync_plan(db, user_id=USER, plan=_plan(a, b, c))
    assert progress.topic_states(db, user_id=USER)[c["id"]]["status"] == "done"


def test_two_archive_passes_cannot_collide(db):
    """The exact sequence that broke parking: archive, bring back, archive again."""
    a = _topic(0, "llm-rag", "Tokens")
    b = _topic(1, "docker", "Images")
    for _ in range(3):
        progress.sync_plan(db, user_id=USER, plan=_plan(a))
        progress.sync_plan(db, user_id=USER, plan=_plan(b))
    assert len(progress.topic_states(db, user_id=USER)) == 1


def test_set_status_derives_progress_and_rejects_unknown_topics(db):
    a = _topic(0, "llm-rag", "Tokens")
    progress.sync_plan(db, user_id=USER, plan=_plan(a))

    result = progress.set_status(db, user_id=USER, topic_id=a["id"], status="in_progress")
    assert result["progress"] == 0.5
    result = progress.set_status(
        db, user_id=USER, topic_id=a["id"], status="checkpoint_passed", progress=0.9
    )
    assert result["progress"] == 0.9, "an explicit progress value wins"

    with pytest.raises(progress.TopicNotFound):
        progress.set_status(db, user_id=USER, topic_id=str(uuid.uuid4()), status="done")
    with pytest.raises(progress.TopicNotFound):
        progress.set_status(db, user_id=USER, topic_id="not-a-uuid", status="done")
    with pytest.raises(ValueError):
        progress.set_status(db, user_id=USER, topic_id=a["id"], status="finished")


def test_another_candidates_topic_is_not_writable(db):
    """A topic id is a uuid5 of the curriculum, so it is guessable — ownership is checked."""
    a = _topic(0, "llm-rag", "Tokens")
    progress.sync_plan(db, user_id=USER, plan=_plan(a))
    other = "33333333-3333-4333-8333-333333333333"
    with pytest.raises(progress.TopicNotFound):
        progress.set_status(db, user_id=other, topic_id=a["id"], status="done")
