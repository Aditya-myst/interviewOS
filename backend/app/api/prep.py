"""Read endpoints for the preparation screens.

Phase 4 serves them from contracts/fixtures and says so in the `X-Data-Source`
header. Phase 5 replaces the bodies with SQL against candidate_skills,
learning_paths and learning_topics — the response models do not change, so the
frontend switches on its own schedule.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response

from app import fixtures, store
from app.db import db_status, get_session
from app.schemas import Dashboard, Roadmap, SkillProfile

router = APIRouter(tags=["preparation"])


def _serve(response: Response, name: str, demo_state: str | None = None) -> dict[str, Any]:
    response.headers["X-Data-Source"] = "fixture"
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


def _from_store(builder: str) -> dict[str, Any] | None:
    """Every read endpoint goes through here, so "database or fixture" is one decision.

    Split out so tests can exercise both paths without a live Postgres. A failing
    query serves fixtures and logs: a broken read must not take the screen down, and
    the header still tells the truth about what you are looking at.
    """
    if db_status()["state"] != "connected":
        return None
    try:
        with get_session() as session:
            user_id, _ = store.resolve_user(session)
            return getattr(store, builder)(session, user_id=user_id)
    except store.UserUnresolved:
        return None
    except Exception:
        import logging

        logging.getLogger(__name__).exception("%s failed — serving fixtures", builder)
        return None


@router.get("/analytics/dashboard", response_model=Dashboard)
def dashboard(response: Response, state: str | None = None) -> dict[str, Any]:
    """Rows when they exist, fixtures otherwise. Same keys either way."""
    stored = _from_store("dashboard_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "dashboard", state)


@router.get("/skills/profile", response_model=SkillProfile)
def skills_profile(response: Response, state: str | None = None) -> dict[str, Any]:
    """Rows when they exist, fixtures otherwise — and the header says which.

    This is the switch Phase 5 was built for. The payload shape is identical, so
    the frontend does not change; only `X-Data-Source` does, and it is never wrong:
    `database` means these numbers came out of candidate_skills.
    """
    stored = _from_store("profile_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "skill_profile", state)


@router.get("/learning/roadmap", response_model=Roadmap)
def roadmap(response: Response, state: str | None = None) -> dict[str, Any]:
    stored = _from_store("roadmap_payload")
    if stored is not None:
        response.headers["X-Data-Source"] = "database"
        return stored
    return _serve(response, "roadmap", state)


@router.get("/preparation/latest")
def preparation_latest(response: Response) -> dict[str, Any]:
    return _serve(response, "preparation_plan")


@router.get("/interview/{session_id}/report")
def interview_report(session_id: str, response: Response) -> dict[str, Any]:
    return _serve(response, "interview_report")
