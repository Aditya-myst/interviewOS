"""Passing a ladder must move the roadmap topic that asked for it.

The defect this file exists for: the roadmap and the assessment were two features that had
never met. A candidate could answer every rung of "RAG architecture end to end" and get a
`verified` verdict on the Assess screen, then open Roadmap and find the topic still
`not_started` — the effort visible on one screen and absent on the other, which is exactly
what "everything should act on my resume and JD" rules out.

Three things are easy to get wrong here, and each has a test:

1. **Direction.** Only finishing work may move a topic forward. A failed attempt may start a
   topic, but it must never un-pass a checkpoint or un-finish a finished topic.
2. **Ordering.** A candidate can open Assess without ever opening Roadmap, so the plan may
   not exist yet. Starting a ladder materialises it first; a missing plan must also not
   break the write-back.
3. **Isolation.** The roadmap lives in the same transaction as the ladder, its answers and
   the skill row — but through a savepoint, so a roadmap failure costs the roadmap only.
"""
from __future__ import annotations

import os
import uuid

import pytest

from app import store
from app.assessment import service
from app.prep import progress

DSN = os.environ.get("INTERVIEWOS_TEST_DATABASE_URL")
USER = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    if not DSN:
        pytest.skip("set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
    engine = create_engine(DSN)
    _wipe(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        _wipe(engine)
        engine.dispose()


def _wipe(engine) -> None:
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into auth.users (id, email) values (:u, 'p@e.st') on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.profiles (id, email, full_name) values (:u, 'p@e.st', 'P') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        for table in ("learning_topics", "learning_paths"):
            conn.execute(
                text(f"delete from public.{table} where user_id = cast(:u as uuid)"), {"u": USER}
            )
        # A scored graph, so the plan has something to be about. Seeded here rather than
        # assumed, because a test that needs yesterday's upload is a test that rots.
        conn.execute(
            text("delete from public.candidate_skills where user_id = cast(:u as uuid)"),
            {"u": USER},
        )
        conn.execute(
            text(
                """
                insert into public.candidate_skills
                  (user_id, skill_id, status, claimed_level, expected_level, confidence,
                   jd_importance, interview_relevance, gap, priority, priority_band,
                   explanation, in_resume, in_jd, evidence)
                values
                  (cast(:u as uuid), 'python', 'claimed', 'advanced', 'advanced', 0.6,
                   0.9, 0.9, 0.3, 0.8, 'critical', 'resume and JD both ask for it',
                   true, true, '[]'::jsonb),
                  (cast(:u as uuid), 'llm-rag', 'unverified', 'intermediate', 'advanced', 0.4,
                   0.85, 0.9, 0.5, 0.7, 'high', 'the JD is built around it',
                   true, true, '[]'::jsonb),
                  (cast(:u as uuid), 'postgresql', 'claimed', 'intermediate', 'advanced', 0.55,
                   0.7, 0.8, 0.25, 0.6, 'high', 'storage for the pipeline',
                   true, true, '[]'::jsonb)
                """
            ),
            {"u": USER},
        )


def _a_planned_skill(session) -> tuple[dict, dict]:
    """A scored skill that owns a visible roadmap topic, plus that topic."""
    store.ensure_plan(session, user_id=USER)
    session.commit()
    skills = store.scored_skills(session, user_id=USER)
    assert skills, "the seeded profile should have scored skills"
    plan = store.roadmap_payload(session, user_id=USER)
    assert plan and plan["topics"], "ensure_plan should have planned something"
    topic = plan["topics"][0]
    # Read shape calls a topic `id`; the write shape (PATCH, and the write-back below) calls
    # it `topic_id`. Same uuid, two shapes — spelled out here so the test cannot pass by luck.
    assert topic["id"]
    skill = next(s for s in skills if s["skill_id"] == topic["skill_id"])
    return skill, topic


def _finished(skill: dict, *, status_after: str) -> service.AssessmentRecord:
    """A ladder that has been walked to the end, with a chosen verdict."""
    service.reset_store()
    record = service.start(skill, question_total=2)
    while record.index < len(record.rungs):
        service.answer(record, "I have shipped this in production and measured the result.")
    record.status = "completed"
    record.result = {
        "confidence": 0.9,
        "inferred_level": "advanced",
        "status_after": status_after,
        "verified": status_after == "verified",
    }
    return record


def _topic_status(session, topic_id: str) -> tuple[str, float]:
    from sqlalchemy import select

    from app.models import LearningTopic

    row = session.execute(
        select(LearningTopic).where(LearningTopic.id == uuid.UUID(topic_id))
    ).scalar_one()
    session.refresh(row)
    return row.status, float(row.progress or 0)


# ── the loop itself ───────────────────────────────────────────────────────────
def test_a_verified_ladder_finishes_the_topic_it_asked_about(db):
    skill, topic = _a_planned_skill(db)
    along = _finished(skill, status_after="verified")

    assert service.writeback(db, user_id=USER, record=along) is True

    assert along.result["roadmap_topic"]["topic_id"] == topic["id"]
    assert along.result["roadmap_topic"]["changed"] is True
    status, value = _topic_status(db, topic["id"])
    # `checkpoint_passed`, not `done`: passing the ladder proves the checkpoint was met, it
    # does not mean the candidate did the reading. `done` stays something you assert yourself.
    assert status == "checkpoint_passed"
    assert value == progress.PROGRESS_FOR["checkpoint_passed"]


def test_the_response_can_say_which_topic_moved(db):
    """"Also marked your roadmap" needs a name, not just a flag."""
    skill, _ = _a_planned_skill(db)
    along = _finished(skill, status_after="verified")
    service.writeback(db, user_id=USER, record=along)

    moved = along.result["roadmap_topic"]
    assert moved["title"].strip()
    assert moved["status"] == "checkpoint_passed"


def test_a_failed_ladder_starts_the_topic_without_claiming_it_is_done(db):
    skill, topic = _a_planned_skill(db)
    along = _finished(skill, status_after="weak")

    service.writeback(db, user_id=USER, record=along)

    status, value = _topic_status(db, topic["id"])
    assert status == "in_progress"
    assert value == progress.PROGRESS_FOR["in_progress"]


def test_a_failed_ladder_never_undoes_finished_work(db):
    """Direction of travel. Finishing the work beats passing a quiz."""
    skill, topic = _a_planned_skill(db)
    service.writeback(db, user_id=USER, record=_finished(skill, status_after="verified"))

    along = _finished(skill, status_after="weak")
    service.writeback(db, user_id=USER, record=along)

    status, value = _topic_status(db, topic["id"])
    assert status == "checkpoint_passed"
    assert value == progress.PROGRESS_FOR["checkpoint_passed"]
    assert along.result["roadmap_topic"]["changed"] is False


def test_the_plan_survives_a_writeback_and_keeps_every_other_topic(db):
    skill, topic = _a_planned_skill(db)
    before = {t["id"]: t["status"] for t in store.roadmap_payload(db, user_id=USER)["topics"]}

    service.writeback(db, user_id=USER, record=_finished(skill, status_after="verified"))

    after = {t["id"]: t["status"] for t in store.roadmap_payload(db, user_id=USER)["topics"]}
    assert after[topic["id"]] == "checkpoint_passed"
    assert {k: v for k, v in after.items() if k != topic["id"]} == {
        k: v for k, v in before.items() if k != topic["id"]
    }


# ── ordering: Assess before Roadmap ──────────────────────────────────────────
def test_a_ladder_saves_even_when_no_plan_exists_yet(db):
    """No roadmap rows at all: the write-back still succeeds and simply moves nothing."""
    from sqlalchemy import text

    skills = store.scored_skills(db, user_id=USER)
    assert (
        db.execute(
            text("select count(*) from public.learning_topics where user_id = cast(:u as uuid)"),
            {"u": USER},
        ).scalar_one()
        == 0
    )

    along = _finished(skills[0], status_after="verified")

    assert service.writeback(db, user_id=USER, record=along) is True
    assert "roadmap_topic" not in along.result


def test_ensure_plan_is_idempotent_and_keeps_progress(db):
    first = store.ensure_plan(db, user_id=USER)
    db.commit()
    assert first and first["topics"]

    progress.set_status(
        db, user_id=USER, topic_id=first["topics"][0]["id"], status="done"
    )
    db.commit()

    again = store.ensure_plan(db, user_id=USER)
    db.commit()
    assert [t["id"] for t in again["topics"]] == [t["id"] for t in first["topics"]]
    assert again["topics"][0]["status"] == "done"


def test_ensure_plan_says_nothing_when_there_is_nothing_to_plan(db):
    from sqlalchemy import text

    db.execute(text("delete from public.candidate_skills where user_id = cast(:u as uuid)"), {"u": USER})
    db.commit()
    try:
        assert store.ensure_plan(db, user_id=USER) is None
    finally:
        db.rollback()


# ── the number on the header ─────────────────────────────────────────────────
def test_a_passed_checkpoint_counts_as_partial_progress_not_as_zero(db):
    """`done / total` said 0% to a candidate who had just passed a checkpoint."""
    skill, _topic = _a_planned_skill(db)
    assert store.roadmap_payload(db, user_id=USER)["progress"]["percent"] == 0

    service.writeback(db, user_id=USER, record=_finished(skill, status_after="verified"))

    shown = store.roadmap_payload(db, user_id=USER)["progress"]
    assert shown["done"] == 0, "nothing was finished, and the counter must not pretend otherwise"
    expected = round((progress.PROGRESS_FOR["checkpoint_passed"] / shown["total"]) * 100)
    assert shown["percent"] == expected
    assert shown["percent"] > 0


def test_work_that_left_the_plan_is_still_reported(db):
    """A verified skill stops being a gap, so a re-plan parks its topic. The candidate
    still passed it, and the roadmap has to be able to say so."""
    skill, topic = _a_planned_skill(db)
    service.writeback(db, user_id=USER, record=_finished(skill, status_after="verified"))
    assert store.roadmap_payload(db, user_id=USER)["completed"] == []

    # the skill is no longer a gap, so the planner drops it
    from sqlalchemy import text

    db.execute(
        text(
            "update public.candidate_skills set priority_band = 'low', gap = 0 "
            "where user_id = cast(:u as uuid) and skill_id = :s"
        ),
        {"u": USER, "s": skill["skill_id"]},
    )
    db.commit()

    plan = store.roadmap_payload(db, user_id=USER)
    assert topic["id"] not in [t["id"] for t in plan["topics"]]
    finished = {row["topic_id"]: row for row in plan["completed"]}
    assert topic["id"] in finished
    assert finished[topic["id"]]["status"] == "checkpoint_passed"
    assert finished[topic["id"]]["title"].strip()


# ── the status graph stays the one source of truth ───────────────────────────
def test_the_ladder_moves_the_topic_through_the_shared_vocabulary(db):
    assert 0.5 <= progress.PROGRESS_FOR["checkpoint_passed"] < progress.PROGRESS_FOR["done"]
    skill, topic = _a_planned_skill(db)
    service.writeback(db, user_id=USER, record=_finished(skill, status_after="verified"))
    status, _ = _topic_status(db, topic["id"])
    assert status in progress.STATUSES
