"""Assessment endpoints.

`/assessment/start` and `/assessment/answer` were in `contracts/openapi.yaml` before any
code was, so the paths and payloads are the spec's, not mine. Extra fields are additive
(`answers`, `persisted`) and the contract's `AssessmentState` fields are all present.

Where the session lives follows the interview's rule, because it is the same problem: a
session is state, not a payload. With a database the ladder is written to `assessments`
and `assessment_answers` and moves the skill in `candidate_skills`; without one it lives
in memory and every response says `persisted: false`.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.api.interview import _backend
from app.assessment import service
from app.assessment.service import NotFound as AssessmentNotFound

log = logging.getLogger(__name__)
router = APIRouter(tags=["assessment"])


class AssessmentStart(BaseModel):
    skill_id: str
    mode: Literal["quick", "adaptive"] = "quick"
    question_total: int = Field(default=3, ge=2, le=5)


class AssessmentAnswerInput(BaseModel):
    assessment_id: str
    answer: str = Field(min_length=1, max_length=6000)


def _find_skill(skills: list[dict[str, Any]], skill_id: str) -> dict[str, Any]:
    for row in skills:
        if str(row.get("skill_id")) == skill_id:
            return row
    raise HTTPException(
        status_code=404,
        detail=f"skill {skill_id!r} is not in this profile — nothing to assess",
    )


@router.post("/assessment/start")
def start(response: Response, body: AssessmentStart) -> dict[str, Any]:
    with _backend(response) as (skills, _store, _db, _user):
        skill = _find_skill(skills, body.skill_id)
        try:
            record = service.start(skill, question_total=body.question_total)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return service.state(record)


@router.post("/assessment/answer")
def answer(response: Response, body: AssessmentAnswerInput) -> dict[str, Any]:
    with _backend(response) as (_skills, _store, db, user_id):
        try:
            record = service.get(body.assessment_id)
        except AssessmentNotFound as exc:
            raise HTTPException(status_code=404, detail="assessment not found") from exc
        try:
            state = service.answer(record, body.answer)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        if record.status == "completed" and db is not None and user_id:
            service.writeback(db, user_id=user_id, record=record)
            state = service.state(record)  # persisted flag may have changed
        return state


@router.get("/assessment/{assessment_id}")
def read(response: Response, assessment_id: str) -> dict[str, Any]:
    with _backend(response) as (_skills, _store, _db, _user):
        try:
            return service.state(service.get(assessment_id))
        except AssessmentNotFound as exc:
            raise HTTPException(status_code=404, detail="assessment not found") from exc
