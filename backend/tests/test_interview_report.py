"""The interview report has to be honest about two things: who graded it, and whether
anything actually held up.

Both were wrong.

1. **`scored_by` was the string `"rubric"`, hard-coded.** With `LLM_SCORING=true` a model may
   have graded every answer in the session, and the report still credited the deterministic
   rubric. The one field a candidate could use to know whether a model touched their score
   was a constant.
2. **"What held up" was never empty.** When nothing reached `verified`, the list was filled
   with "No skill reached verified in this session — that is a finding, not a failure." — a
   sentence that is not a strength, filed under a heading that says it is. A report that
   pads a section is a report you stop reading.

These tests drive the aggregation directly, with verdicts supplied by hand: the scorer has
its own tests, and what is being checked here is what the report makes of a set of verdicts.
"""
from __future__ import annotations

import os

import pytest

from app.interview import service
from app.interview.questions import AnswerScore, Question, RubricItem
from app.interview.store import MemorySessionStore, report_scored_by

DSN = os.environ.get("INTERVIEWOS_TEST_DATABASE_URL")

SKILLS = [{"skill_id": "python", "name": "Python", "priority_band": "critical"}]


def _question(skill_id: str = "python") -> Question:
    return Question(
        skill_id=skill_id,
        skill_name=skill_id.title(),
        text=f"Tell me about a time you used {skill_id}.",
        question_type="scenario",
        source="scenario",
        rubric=(RubricItem(key="detail", terms=("detail",)),),
    )


def _verdict(score: float, status: str, *, why: str = "graded", by: str = "rubric") -> AnswerScore:
    return AnswerScore(
        score=score,
        status_after=status,
        quote="a verbatim sentence from the answer" if score >= 0.4 else None,
        matched=("detail",) if score >= 0.4 else (),
        missing=() if score >= 0.4 else ("detail",),
        why=why,
        scored_by=by,
    )


def _report(verdicts: list[AnswerScore], monkeypatch) -> dict:
    """A session with one answer per verdict, scored by the supplied verdicts."""
    plan = [_question(f"skill{index}") for index, _ in enumerate(verdicts)]
    store = MemorySessionStore()
    record = store.create(plan=[{"skill_id": q.skill_id} for q in plan], target_role="r", user_id=None)
    for question, verdict in zip(plan, verdicts, strict=True):
        store.append(record.id, role="interviewer", content=question.text,
                     question_type=question.question_type, skill_id=question.skill_id)
        store.append(record.id, role="candidate", content="an answer that was given",
                     question_type=question.question_type, skill_id=question.skill_id)

    scores = iter(verdicts)
    monkeypatch.setattr(service.engine, "score_answer", lambda *_a, **_k: next(scores))
    return service.build_report(store, session_id=record.id, plan=plan, skills=SKILLS)


# ── who graded it ────────────────────────────────────────────────────────────
def test_scored_by_is_derived_from_the_answers_not_assumed():
    assert report_scored_by([{"scored_by": "rubric"}]) == "rubric"
    assert report_scored_by([{"scored_by": "llm"}, {"scored_by": "llm"}]) == "llm"
    assert report_scored_by([{"scored_by": "llm"}, {"scored_by": "rubric"}]) == "rubric+llm"
    # a row written before the field existed is a rubric row, not an unknown
    assert report_scored_by([{}]) == "rubric"
    assert report_scored_by([]) == "rubric"


def test_a_rubric_only_session_says_so(monkeypatch):
    report = _report([_verdict(0.3, "weak"), _verdict(0.2, "needs_revision")], monkeypatch)
    assert report["scored_by"] == "rubric"


def test_a_model_graded_session_does_not_credit_the_rubric(monkeypatch):
    report = _report([_verdict(0.8, "verified", by="llm"), _verdict(0.7, "developing", by="llm")],
                     monkeypatch)
    assert report["scored_by"] == "llm"
    assert all(row["scored_by"] == "llm" for row in report["per_skill"])


def test_a_mixed_session_says_both(monkeypatch):
    report = _report([_verdict(0.8, "verified", by="llm"), _verdict(0.2, "weak", by="rubric")],
                     monkeypatch)
    assert report["scored_by"] == "rubric+llm"


# ── what held up ─────────────────────────────────────────────────────────────
def test_strengths_is_empty_rather_than_padded_with_a_non_strength(monkeypatch):
    report = _report([_verdict(0.22, "needs_revision"), _verdict(0.12, "weak")], monkeypatch)
    assert report["strengths"] == []
    assert report["gaps"], "a weak session must still say what did not work"


def test_the_best_answer_is_named_when_nothing_was_verified(monkeypatch):
    """Naming the best answer is useful; claiming it is verified is not."""
    report = _report([_verdict(0.61, "developing"), _verdict(0.12, "weak")], monkeypatch)
    assert report["strengths"], "a decent answer should not vanish from the report"
    assert all(line.startswith("Held up best:") for line in report["strengths"])


def test_a_verified_skill_is_named_plainly(monkeypatch):
    report = _report([_verdict(0.9, "verified"), _verdict(0.3, "weak")], monkeypatch)
    assert report["strengths"]
    assert all(not line.startswith("Held up best:") for line in report["strengths"])


def test_the_report_is_capped_at_three_lines(monkeypatch):
    report = _report([_verdict(0.9, "verified")] * 5, monkeypatch)
    assert len(report["strengths"]) == 3


# ── read back from Postgres ──────────────────────────────────────────────────
@pytest.mark.skipif(not DSN, reason="set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
def test_a_stored_report_still_says_who_graded_it(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.interview.store import SqlSessionStore

    monkeypatch.setattr(
        service.engine, "score_answer", lambda *_a, **_k: _verdict(0.2, "weak", by="llm")
    )
    engine = create_engine(DSN)
    with Session(engine) as db:
        store = SqlSessionStore(db, user_id="11111111-1111-4111-8111-111111111111")
        state = service.start(store, skills=SKILLS, target_role="AI Engineer", total=1)
        service.answer(store, session_id=state["session_id"], text="an answer", skills=SKILLS)
        plan = service.engine.build_plan(SKILLS, total=1)
        report = service.build_report(
            store, session_id=state["session_id"], plan=plan, skills=SKILLS
        )
        store.save_report(state["session_id"], report)
        read = store.get_report(state["session_id"])

    assert read is not None
    assert read["scored_by"] == report["scored_by"] == "llm"
    assert read["strengths"] == report["strengths"] == []
