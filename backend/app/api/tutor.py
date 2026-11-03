"""The tutor endpoint.

One path in, one composed answer out. There is no chat history on the server: the reply is
a pure function of the question and the profile, so a reload cannot lose an answer and a
stale conversation cannot become "context" that quietly rewrites a claim.

The profile comes from the same `_from_store("profile_payload")` switch every other read
uses, so a database row and a fixture row are indistinguishable in shape and the
`X-Data-Source` header on this endpoint means exactly what it means everywhere else.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app import fixtures
from app.api.prep import _from_store
from app.tutor import service

router = APIRouter(tags=["tutor"])


class TutorRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=service.MAX_QUESTION_CHARS)
    skill_id: str | None = None


def _profile(response: Response, state: str | None) -> dict[str, Any]:
    stored, reason = _from_store("profile_payload")
    if stored is not None and stored.get("skills"):
        response.headers["X-Data-Source"] = "database"
        return stored

    response.headers["X-Data-Source"] = "fixture"
    response.headers["X-Fallback-Reason"] = reason or "no_rows"
    data = dict(fixtures.load("skill_profile"))
    if state == "empty":
        data = {**data, "skills": [], "coverage_by_category": [], "provisional": True}
    return data


@router.post("/tutor/ask")
def tutor_ask(body: TutorRequest, response: Response, state: str | None = None) -> dict[str, Any]:
    question = body.question.strip()
    if len(question) < service.MIN_QUESTION_CHARS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "question_too_short",
                "message": f"{len(question)} characters — ask a full question",
            },
        )

    profile = _profile(response, state)
    answer = service.ask(question, skill_id=body.skill_id, profile=profile)
    return {"question": question, **answer.as_json()}
