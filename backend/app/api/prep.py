"""Read endpoints for the preparation screens.

The interview report endpoint moved to app/api/interview.py when live sessions arrived:
two routers claiming GET /v1/interview/{id}/report meant the *fixture* one won (it was
registered first), so a finished session returned a recorded report instead of its own.
One owner per path.


Phase 4 serves them from contracts/fixtures and says so in the `X-Data-Source`
header. Phase 5 replaces the bodies with SQL against candidate_skills,
learning_paths and learning_topics — the response models do not change, so the
frontend switches on its own schedule.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app import fixtures, store
from app.db import db_status, get_session
from app.prep import progress
from app.schemas import Dashboard, Roadmap, SkillProfile

router = APIRouter(tags=["preparation"])


def _serve(
    response: Response,
    name: str,
    demo_state: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """The fixture path. `X-Fallback-Reason` says why we are here.

    `no_rows` and `db_error` both serve fixtures, and that is exactly how a wrong column
    name hid for a week: the query threw, the screen still rendered, and the header said
    "fixture". Now the header says which one it is, and a broken read is visible in one
    request instead of a screenshot.
    """
    response.headers["X-Data-Source"] = "fixture"
    response.headers["X-Fallback-Reason"] = reason or "no_rows"
    data = fixtures.load(name)

    # `?state=empty` is the new-account shape: no skills, no evidence, no path.
    # The API owes the UI a real empty payload rather than "null means empty".
    if demo_state == "empty" and name == "dashboard":
        data = {
            **data,
            "readiness": 0,
            "readiness_label": "not_ready",
            "provisional": True,
            "readiness_history": [],
            "stats": {
                "verified_skills": 0,
                "skills_total": 0,
                "mock_interviews": 0,
                "topics_done": 0,
                "topics_total": 0,
                "avg_interview_score": None,
            },
            "coverage": [],
            "priority_skills": [],
            "interviews": [],
        }
    return data


def _from_store(builder: str) -> tuple[dict[str, Any] | None, str | None]:
    """Every read endpoint goes through here, so "database or fixture" is one decision.

    Returns `(payload, reason)`: payload when rows were read, otherwise None plus why —
    `no_db`, `no_profile`, `no_rows` or `db_error`. Split out so tests can exercise both
    paths without a live Postgres. A failing query still serves fixtures, because a
    broken read must not take the screen down, but the reason travels to the header.
    """
    if db_status()["state"] != "connected":
        return None, "no_db"
    try:
        with get_session() as session:
            user_id, _ = store.resolve_user(session)
            payload = getattr(store, builder)(session, user_id=user_id)
    except store.UserUnresolved:
        return None, "no_profile"
    except Exception:
        import logging

        logging.getLogger(__name__).exception("%s failed — serving fixtures", builder)
        return None, "db_error"
    if payload is None:
        return None, "no_rows"
    return payload, None


@router.get("/analytics/dashboard", response_model=Dashboard)
def dashboard(response: Response, state: str | None = None) -> dict[str, Any]:
    """Rows when they exist, fixtures otherwise. Same keys either way."""
    stored, reason = _from_store("dashboard_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "dashboard", state, reason)


@router.get("/skills/profile", response_model=SkillProfile)
def skills_profile(response: Response, state: str | None = None) -> dict[str, Any]:
    """Rows when they exist, fixtures otherwise — and the header says which.

    This is the switch Phase 5 was built for. The payload shape is identical, so
    the frontend does not change; only `X-Data-Source` does, and it is never wrong:
    `database` means these numbers came out of candidate_skills.
    """
    stored, reason = _from_store("profile_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "skill_profile", state, reason)


@router.get("/learning/roadmap", response_model=Roadmap)
def roadmap(response: Response, state: str | None = None) -> dict[str, Any]:
    stored, reason = _from_store("roadmap_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "roadmap", state, reason)


class TopicStatusUpdate(BaseModel):
    """Only the two fields the candidate owns. Everything else is the planner's."""

    status: Literal["not_started", "in_progress", "checkpoint_passed", "done"]
    progress: float | None = Field(default=None, ge=0, le=1)


def _write_session():
    """A session for a write, or an honest 503.

    Read endpoints fall back to fixtures because a screen must still render; a write has
    nothing to fall back to, so it says why it cannot proceed instead of pretending.
    """
    if db_status()["state"] != "connected":
        raise HTTPException(
            status_code=503,
            detail="no database configured — progress is stored in Postgres, so nothing was saved",
        )
    return get_session()


@router.post("/preparation/create")
def create_plan(response: Response) -> dict[str, Any]:
    """Persist the computed plan. Idempotent: same candidate, same topics, same ids.

    The UI never has to call this — reading the roadmap already stores it — but automation
    and the CLI want an explicit verb, and an idempotent one is safe to retry.
    """
    stored, reason = _from_store("roadmap_payload")
    if stored is None:
        raise HTTPException(
            status_code=409,
            detail=f"nothing to plan yet ({reason}) — upload a resume and analyse a JD first",
        )
    response.headers["X-Data-Source"] = "database"
    return stored


@router.patch("/preparation/topics/{topic_id}")
def update_topic_status(topic_id: str, body: TopicStatusUpdate, response: Response) -> dict[str, Any]:
    """Mark one topic started, checked off, or done.

    This is the write that makes `topics_done` mean something: before it existed the column
    was read by the dashboard and written by nobody.
    """
    try:
        with _write_session() as session:
            user_id, _ = store.resolve_user(session)
            result = progress.set_status(
                session, user_id=user_id, topic_id=topic_id, status=body.status, progress=body.progress
            )
    except progress.TopicNotFound:
        raise HTTPException(
            status_code=404, detail=f"topic {topic_id!r} is not in your plan"
        ) from None
    except store.UserUnresolved:
        raise HTTPException(status_code=409, detail="no profile yet — finish onboarding first") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    response.headers["X-Data-Source"] = "database"
    return result


@router.get("/preparation/latest")
def preparation_latest(response: Response) -> dict[str, Any]:
    """The plan for *this* candidate: readiness, skills and topics from the database."""
    stored, reason = _from_store("preparation_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "preparation_plan", None, reason)
