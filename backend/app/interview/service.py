"""The interview loop: session -> question -> answer -> score -> report.

One turn is: ask the question at `asked`, take the answer, score it against that
question's rubric, write the score back to the candidate's skill graph, then either ask
the next question or close the session and build the report.

Evidence rules that the API must not break:

* every answer message is stored verbatim, and the quote in the score is a substring
  of it — a report can never show a quote the candidate did not say;
* `communication_transcript_based` is only ever set from the transcript, and the field
  name says so because the contract says so;
* an answer with no quote scores at most 0.25, so a fluent non-answer cannot lift a
  skill to verified.
"""
from __future__ import annotations

from typing import Any

from app.interview import questions as engine
from app.interview.store import MemorySessionStore, NotFound, SessionRecord


def _question_payload(question: engine.Question) -> dict[str, Any]:
    return {
        "text": question.text,
        "question_type": question.question_type,
        "skill_id": question.skill_id,
        "source": question.source,
        "skill_name": question.skill_name,
        "rubric_size": len(question.rubric),
    }


def state_of(store, record: SessionRecord, plan: list[engine.Question]) -> dict[str, Any]:
    """`InterviewState` from contracts/types.ts."""
    nxt = plan[record.asked] if 0 <= record.asked < len(plan) else None
    return {
        "session_id": record.id,
        "status": record.status,
        "asked": record.asked,
        "total": record.total,
        "question": _question_payload(nxt) if nxt and record.status == "active" else None,
    }


def start(
    store,
    *,
    skills: list[dict],
    target_role: str | None,
    total: int = 6,
    mode: str = "jd_based",
    channel: str = "text",
) -> dict[str, Any]:
    plan = engine.build_plan(skills, total=total)
    if not plan:
        raise ValueError("no scoreable skills yet — upload a resume and a JD first")
    record = store.create(
        plan=[_question_payload(q) for q in plan],
        target_role=target_role,
        user_id=None,
        mode=mode,
        channel=channel,
    )
    store.append(
        record.id,
        role="interviewer",
        content=plan[0].text,
        question_type=plan[0].question_type,
        skill_id=plan[0].skill_id,
    )
    return state_of(store, record, plan)


def answer(
    store,
    *,
    session_id: str,
    text: str,
    skills: list[dict],
    writeback=None,
    audio_url: str | None = None,
) -> dict[str, Any]:
    record = store.get(session_id)
    if record is None:
        raise NotFound(session_id)
    if record.status != "active":
        raise ValueError("this session is already closed")

    plan = engine.build_plan(skills, total=record.total)
    if not plan or record.asked >= len(plan):
        raise ValueError("question plan is exhausted")

    question = plan[record.asked]
    result = engine.score_answer(question, text)

    store.append(
        session_id,
        role="candidate",
        content=text,
        question_type=None,
        skill_id=question.skill_id,
        audio_url=audio_url,
    )
    store.advance(session_id)

    if writeback is not None:
        writeback(question.skill_id, result)

    record = store.get(session_id) or record
    if record.asked >= len(plan):
        store.complete(session_id, score=None)
        record = store.get(session_id) or record
        report = build_report(store, session_id=session_id, plan=plan, skills=skills)
        store.save_report(session_id, report)
        return {
            "state": state_of(store, record, plan),
            "feedback": _feedback(question, result),
            "report": report,
        }

    next_question = plan[record.asked]
    store.append(
        session_id,
        role="interviewer",
        content=next_question.text,
        question_type=next_question.question_type,
        skill_id=next_question.skill_id,
    )
    return {
        "state": state_of(store, record, plan),
        "feedback": _feedback(question, result),
        "report": None,
    }


def _feedback(question: engine.Question, result: engine.AnswerScore) -> dict[str, Any]:
    return {
        "skill_id": question.skill_id,
        "skill_name": question.skill_name,
        "score": result.score,
        "status_after": result.status_after,
        "quote": result.quote,
        "matched": list(result.matched),
        "missing": list(result.missing),
        "why": result.why,
        "scored_by": result.scored_by,
        "flags": list(result.flags),
    }


def evaluate(store, *, session_id: str, skills: list[dict]) -> dict[str, Any]:
    """Re-derive the report from the stored transcript. Idempotent, by design."""
    record = store.get(session_id)
    if record is None:
        raise NotFound(session_id)
    plan = engine.build_plan(skills, total=record.total)
    report = build_report(store, session_id=session_id, plan=plan, skills=skills)
    store.save_report(session_id, report)
    return report


def transcript(store, session_id: str) -> dict[str, Any]:
    record = store.get(session_id)
    if record is None:
        raise NotFound(session_id)
    return {"session_id": session_id, "messages": store.messages(session_id)}


def build_report(store, *, session_id: str, plan: list[engine.Question], skills: list[dict]) -> dict[str, Any]:
    """Aggregate the session into `InterviewReport`.

    The report is built from the stored message pairs, so it is reproducible: read the
    transcript, re-score, and you get the same numbers.
    """
    messages = store.messages(session_id)
    asked = [m for m in messages if m["role"] == "interviewer"]
    said = [m for m in messages if m["role"] == "candidate"]

    per_skill: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    scored_total = 0.0

    for index, question in enumerate(plan[: len(said)]):
        text = said[index]["content"]
        result = engine.score_answer(question, text)
        scored_total += result.score
        per_skill.append(
            {
                "skill_id": question.skill_id,
                "name": question.skill_name,
                "score": result.score,
                "status_after": result.status_after,
                "comment": result.why,
                "quote": result.quote,
                "scored_by": result.scored_by,
            }
        )
        if result.score < 0.5:
            weak.append(
                {
                    "question": question.text,
                    "score": result.score,
                    "why_weak": result.why,
                    "better_answer_outline": _outline(question),
                }
            )

    overall = round(scored_total / len(per_skill), 2) if per_skill else 0.0
    verified = [row for row in per_skill if row["status_after"] == "verified"]
    gaps = [row for row in per_skill if row["status_after"] in ("weak", "needs_revision")]

    return {
        "session_id": session_id,
        "overall_scores": {
            "overall": overall,
            "technical": round(
                sum(r["score"] for r in per_skill if r["skill_id"] in core_skill_ids(skills))
                / max(1, len([r for r in per_skill if r["skill_id"] in core_skill_ids(skills)])),
                2,
            )
            if any(r["skill_id"] in core_skill_ids(skills) for r in per_skill)
            else None,
            # Transcript-derived only: word count and structure, nothing about accent,
            # pace or confidence. The field name is the disclaimer.
            "communication_transcript_based": _communication(asked, said),
        },
        "per_skill": per_skill,
        "strengths": [
            f"{row['name']}: {row['comment']}" for row in verified
        ][:3]
        or ["No skill reached verified in this session — that is a finding, not a failure."],
        "gaps": [f"{row['name']}: {row['comment']}" for row in gaps][:4],
        "weak_answers": weak[:3],
        "next_actions": _next_actions(per_skill),
        "persisted": store.source == "database",
        "scored_by": "rubric",
        "created_at": None,
    }


def _next_actions(per_skill: list[dict[str, Any]]) -> list[str]:
    """Three things to do next, worst-first, each traceable to a score in this session."""
    if not per_skill:
        return ["Answer at least one question before this report means anything."]

    actions: list[str] = []
    for row in sorted(per_skill, key=lambda r: r["score"]):
        if row["status_after"] in ("weak", "needs_revision"):
            reason = "no quotable example" if not row.get("quote") else "thin coverage"
            actions.append(
                f"Re-prepare {row['name']}: scored {row['score']:.2f} ({reason}). "
                "Write one concrete example with a number before the next session."
            )
        elif row["status_after"] == "developing":
            actions.append(
                f"Deepen {row['name']}: scored {row['score']:.2f}. Add the outcome and the "
                "trade-off you chose."
            )
        if len(actions) == 3:
            break

    if not actions:
        actions.append(
            "Nothing scored weak here. Move to the next band on the roadmap and re-run at a "
            "harder level."
        )
    return actions


# Categories that used to define "technical". Kept only as a note: a marketing candidate,
# a designer or a teacher has no skills in this set, and their report then showed
# `technical: null` — the product quietly assuming every user is an engineer.
TECH_CATEGORIES = ("Backend", "Data", "Infra", "AI")


def core_skill_ids(skills: list[dict], *, limit: int = 3) -> set[str]:
    """The skills this *role* is actually about: its highest JD-importance demands.

    Role-agnostic on purpose. A content lead's core is content strategy and distribution;
    a backend engineer's is their stack. The report's "technical" line means "how you did
    on the things this job most cares about", which is a fair question for every role.
    """
    ranked = sorted(
        [s for s in skills if s.get("skill_id")],
        key=lambda s: float(s.get("jd_importance") or 0),
        reverse=True,
    )
    return {str(s["skill_id"]) for s in ranked[:limit]}


def _outline(question: engine.Question) -> list[str]:
    """What a strong answer to *this* question looks like, from its own rubric."""
    subtopics = {
        str(sub.get("id")): sub for sub in (engine.taxonomy.raw_subtopics().get(question.skill_id or "") or [])
    }
    outline = ["Name the situation and your role in it, in one sentence."]
    for item in question.rubric:
        sub = subtopics.get(item.key)
        if sub:
            outline.append(f"Show {sub.get('title', item.key).lower()}: {sub.get('objective', '')}")
    outline.append("Finish with the outcome — a number, or what changed because of you.")
    return outline


def _communication(asked: list[dict], said: list[dict]) -> float | None:
    """A transcript-only proxy, deliberately crude and deliberately labelled."""
    if not said:
        return None
    lengths = [len(m["content"].split()) for m in said]
    answered = sum(1 for n in lengths if n >= 25)
    # The ceiling is 0.92 on purpose: words on a page can show that someone answered
    # at length and in full sentences, and cannot show that they were clear to listen
    # to. A transcript score of 100 would claim something we never measured.
    raw = 0.5 * answered / max(1, len(asked)) + 0.5 * min(1.0, sum(lengths) / (len(lengths) * 90))
    return round(min(0.92, raw), 2)


def store_for(*, db_session=None, user_id: str | None = None):
    """SQL when a database is configured, memory otherwise — never a silent fallback."""
    if db_session is not None and user_id:
        from app.interview.store import SqlSessionStore

        return SqlSessionStore(db_session, user_id=user_id)
    from app.interview.store import memory_store

    return memory_store()


def writeback_to_candidate_skills(db_session, *, user_id: str, skill_id: str | None, result: engine.AnswerScore):
    """Record what the interview proved, in the same table the dashboard reads."""
    if not skill_id:
        return None
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.models import CandidateSkill

    row = db_session.execute(
        select(CandidateSkill).where(
            CandidateSkill.user_id == user_id,
            CandidateSkill.skill_id == skill_id,
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    evidence = list(row.evidence or [])
    if result.quote:
        evidence.append(
            {
                "type": "interview_answer",
                "quote": result.quote,
                "score": result.score,
                "status_after": result.status_after,
            }
        )
    row.evidence = evidence
    row.status = result.status_after
    # Confidence moves toward the score, but slowly: one answer is one measurement.
    previous = float(row.confidence or 0)
    row.confidence = round(previous + (result.score - previous) * 0.5, 2)
    row.last_assessed_at = datetime.now(UTC)
    db_session.commit()
    return row


__all__ = [
    "MemorySessionStore",
    "NotFound",
    "answer",
    "build_report",
    "start",
    "state_of",
    "store_for",
    "transcript",
    "writeback_to_candidate_skills",
]
