"""Interview endpoints, implementing the contract that already existed.

`contracts/openapi.yaml` specified these five paths before any engine did: start,
answer, transcript, evaluate, report. The paths and payloads here follow that spec
rather than inventing new ones — `audio_url` is in the answer body because voice was
planned, and `channel` is in the start body for the same reason.

The read endpoints in this app serve fixtures until a database answers; the interview
cannot work that way, because a session is state, not a payload. So this router states
where the session lives in a response header:

* database configured and a profile exists -> `X-Data-Source: database`;
* otherwise -> sessions live in process memory (`X-Data-Source: memory`) and the report
  carries `persisted: false`. A demo that works and says it is not saved beats a 503
  that explains itself.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app import fixtures, store
from app.db import db_status, session_factory
from app.interview import service
from app.interview.store import NotFound
from app.interview.store import memory_store as _memory

log = logging.getLogger(__name__)
router = APIRouter(tags=["interview"])

InterviewMode = Literal[
    "beginner_practice",
    "intermediate_technical",
    "advanced_technical",
    "resume_based",
    "jd_based",
    "full_mock",
]


class InterviewStart(BaseModel):
    mode: InterviewMode = "jd_based"
    channel: Literal["text", "voice"] = "text"
    question_count: int = Field(default=6, ge=3, le=12)


class InterviewAnswerInput(BaseModel):
    session_id: str
    answer: str = Field(default="", max_length=6000)
    audio_url: str | None = None


@contextmanager
def _backend(response: Response) -> Iterator[tuple[list[dict[str, Any]], Any, Any, str | None]]:
    """Yield (skills, store, db_session_or_None, user_id) and set the source header once.

    One decision point for "where does this live", used by every endpoint, so the header
    can never disagree with the store that actually answered.
    """
    # The setup is inside the try; the yield is NOT. A context manager that yields inside a
    # try/except turns an endpoint's own HTTPException into `RuntimeError: generator didn't
    # stop after throw()` — a 404 for "skill not in your profile" arrived as a 500, and the
    # handler then went on to yield the fixture fallback, which is how a live request can
    # quietly answer from fixtures.
    db = None
    skills: list[dict[str, Any]] | None = None
    user_id: str | None = None
    if db_status()["state"] == "connected":
        try:
            db = session_factory()()
            user_id, _ = store.resolve_user(db)
            skills = store.scored_skills(db, user_id=user_id)
        except store.UserUnresolved:
            response.headers["X-Fallback-Reason"] = "no_profile"
        except Exception:
            log.exception("interview backend read failed — using memory")
            response.headers["X-Fallback-Reason"] = "db_error"

    if skills and db is not None and user_id:
        response.headers["X-Data-Source"] = "database"
        try:
            yield skills, service.store_for(db_session=db, user_id=user_id), db, user_id
        finally:
            db.close()
        return

    if db is not None:
        db.close()
    response.headers.setdefault("X-Fallback-Reason", "no_rows" if skills is not None else "no_db")
    response.headers["X-Data-Source"] = "memory"
    yield _fixture_skills(), _memory(), None, None


def _fixture_skills() -> list[dict[str, Any]]:
    data = fixtures.load("dashboard")
    return list(data.get("priority_skills") or [])


@router.post("/interview/start")
def start(response: Response, body: InterviewStart | None = None) -> dict[str, Any]:
    payload = body or InterviewStart()
    with _backend(response) as (skills, store_obj, _db, _user):
        try:
            return service.start(
                store_obj,
                skills=skills,
                target_role=skills[0].get("category") if skills else None,
                total=payload.question_count,
                mode=payload.mode,
                channel=payload.channel,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/interview/answer")
def answer(response: Response, body: InterviewAnswerInput) -> dict[str, Any]:
    with _backend(response) as (skills, store_obj, db, user_id):
        writeback = None
        if db is not None and user_id:

            def writeback(skill_id, result, level=None):
                service.writeback_to_candidate_skills(
                    db, user_id=user_id, skill_id=skill_id, result=result, level=level
                )

        try:
            return service.answer(
                store_obj,
                session_id=body.session_id,
                text=body.answer,
                skills=skills,
                writeback=writeback,
                audio_url=body.audio_url,
            )
        except NotFound as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/interview/{session_id}/transcript")
def read_transcript(session_id: str, response: Response) -> dict[str, Any]:
    with _backend(response) as (_skills, store_obj, _db, _user):
        try:
            return service.transcript(store_obj, session_id)
        except NotFound as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc


@router.post("/interview/{session_id}/evaluate")
def evaluate(session_id: str, response: Response) -> dict[str, Any]:
    """Re-score a session from its transcript.

    Idempotent by construction: the report is a function of the stored messages, so
    evaluating twice returns the same numbers. That is also the audit path — a
    reviewer can re-run scoring without trusting the stored report.
    """
    with _backend(response) as (skills, store_obj, _db, _user):
        try:
            return service.evaluate(store_obj, session_id=session_id, skills=skills)
        except NotFound as exc:
            raise HTTPException(status_code=404, detail="session not found") from exc


@router.get("/interview/{session_id}/report")
def get_report(session_id: str, response: Response) -> dict[str, Any]:
    with _backend(response) as (_skills, store_obj, _db, _user):
        report = store_obj.get_report(session_id)
        if report is not None:
            report.setdefault("persisted", store_obj.source == "database")
            return report

    # No live session behind this id: serve the recorded report so the screen stays
    # reviewable, and say plainly that it is a fixture rather than a session that just
    # happened.
    response.headers["X-Data-Source"] = "fixture"
    response.headers["X-Fallback-Reason"] = "no_session"
    return fixtures.load("interview_report")


__all__ = ["router"]
