"""The pipeline endpoints: document in, evidenced rows out.

Three rules this file encodes:

1. **A bad document is a 422 with a reason**, not a 500 and not an empty profile.
2. **Nothing is persisted unless the database is connected** — the response says
   `persisted: false` and `X-Data-Source: pipeline`, so a fixture-mode demo never
   looks like it wrote to Postgres.
3. **The merge step always recomputes from stored text.** The resume's `raw_text`
   and the JD's `body` are the inputs, so re-running produces the same scores; no
   derived state is trusted on its own.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy import text as sql_text
from sqlalchemy.exc import SQLAlchemyError

from app import store
from app.config import get_settings
from app.db import db_status, get_session
from app.parsing import jd as jd_mod
from app.parsing import resume as resume_mod
from app.parsing.extract import Document, Page, UnparseableDocument, extract
from app.prep import priority

log = logging.getLogger(__name__)

router = APIRouter(tags=["preparation"])

MAX_BYTES = 10 * 1024 * 1024


def _db_reason(exc: SQLAlchemyError) -> str:
    """One readable line from a driver exception — enough to act on, short enough to show."""
    raw = str(getattr(exc, "orig", exc)).strip().splitlines()
    line = raw[0] if raw else exc.__class__.__name__
    return line[:240]


def _db_ready() -> bool:
    return db_status()["state"] == "connected"


def _document_from_stored(text_value: str, filename: str = "stored") -> Document:
    """Rebuild the extraction result from stored raw text — identical input, so the
    deterministic pass reproduces identical output."""
    return Document(
        text=text_value,
        kind="stored",
        pages=[Page(number=1, start=0, end=len(text_value))],
        sha256="",
        size_bytes=len(text_value.encode()),
        filename=filename,
    )


def _recompute(session, user_id: str) -> dict:
    """resume + latest JD → rescored candidate_skills. Called after either upload."""
    stored = session.execute(
        sql_text(
            "select raw_text from public.resumes where user_id = cast(:u as uuid) "
            "order by created_at desc limit 1"
        ),
        {"u": user_id},
    ).scalar()
    jd_body = session.execute(
        sql_text(
            "select body from public.job_descriptions where user_id = cast(:u as uuid) "
            "order by created_at desc limit 1"
        ),
        {"u": user_id},
    ).scalar()

    if not stored:
        return {"scored": 0, "reason": "no resume stored yet"}
    if not jd_body:
        return {"scored": 0, "reason": "no job description stored yet"}

    parsed_resume = resume_mod.parse(_document_from_stored(stored))
    parsed_jd = jd_mod.parse(jd_body)
    rows = priority.score(parsed_resume, parsed_jd)
    written = store.upsert_skills(session, user_id=user_id, rows=rows)
    return {"scored": written, "reason": None}


class JdRequest(BaseModel):
    text: str
    title: str | None = None
    company: str | None = None


@router.post("/resume/upload")
async def resume_upload(
    response: Response,
    file: UploadFile = File(...),  # noqa: B008 — FastAPI's documented file-upload form
) -> dict[str, Any]:
    """Parse a resume. Persists only when a database is connected."""
    settings = get_settings()
    body = await file.read()
    if len(body) > min(MAX_BYTES, settings.max_upload_mb * 1024 * 1024):
        raise HTTPException(
            status_code=413,
            detail={
                "code": "too_large",
                "message": f"{len(body)} bytes exceeds the {settings.max_upload_mb} MB limit",
            },
        )

    try:
        document = extract(file.filename or "resume", body)
    except UnparseableDocument as exc:
        # a document we cannot read is a stated outcome, not a server error
        response.headers["X-Data-Source"] = "pipeline"
        raise HTTPException(
            status_code=422,
            detail={"code": exc.reason, "message": exc.detail or exc.reason},
        ) from exc

    parsed = resume_mod.parse(document)
    result: dict[str, Any] = {
        "parse_status": "ok",
        "persisted": False,
        "resume_id": None,
        "user_source": None,
        "document": {
            "filename": document.filename,
            "kind": document.kind,
            "chars": len(document.text),
            "pages": len(document.pages),
            "sha256": document.sha256,
        },
        "stats": parsed.stats,
        "experience_years": parsed.experience_years,
        "experience_basis": parsed.experience_basis,
        "warnings": document.warnings,
        "skills": parsed.as_json()["skills"],
    }

    if _db_ready():
        try:
            # Nothing is marked persisted until the whole transaction has committed. A
            # write that is rolled back after the resume row (the merge, for instance) must
            # not leave `persisted: true` and a resume_id pointing at a row that is gone.
            with get_session() as session:
                user_id, user_source = store.resolve_user(session)
                resume_id = store.save_resume(
                    session,
                    user_id=user_id,
                    document=document,
                    parsed=parsed,
                    mime_type=file.content_type,
                )
                merge = _recompute(session, user_id)
            result["resume_id"] = resume_id
            result["persisted"] = True
            result["user_source"] = user_source
            result["merge"] = merge
        except store.UserUnresolved as exc:
            result["persist_error"] = {"code": "user_unresolved", "message": exc.detail}
        except store.EvidenceRequired as exc:
            result["persist_error"] = {"code": "evidence_required", "message": str(exc)}
        except SQLAlchemyError as exc:
            # The schema refused the write (a guard, a constraint, a bad column). The
            # document still parsed, so the caller gets the parse plus a reason instead of
            # a 500 that hides which of the two things went wrong.
            log.exception("resume upload parsed but could not be stored")
            result["persist_error"] = {
                "code": "persist_failed",
                "message": _db_reason(exc),
            }

    response.headers["X-Data-Source"] = "database" if result["persisted"] else "pipeline"
    return result


@router.post("/jd/analyze")
def jd_analyze(body: JdRequest, response: Response) -> dict[str, Any]:
    """Parse a job description and rescore against the stored resume."""
    text_value = jd_mod.normalise(body.text)
    if len(text_value) < 80:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "jd_too_short",
                "message": f"{len(text_value)} characters — a usable JD needs a few lines",
            },
        )

    parsed = jd_mod.parse(text_value)
    if body.title:
        parsed.title = body.title
    if body.company:
        parsed.company = body.company

    result: dict[str, Any] = {
        "parse_status": "ok",
        "persisted": False,
        "jd_id": None,
        "user_source": None,
        "parsed": parsed.as_json(),
    }

    if _db_ready():
        try:
            with get_session() as session:
                user_id, user_source = store.resolve_user(session)
                jd_id = store.save_jd(session, user_id=user_id, body=text_value, parsed=parsed)
                merge = _recompute(session, user_id)
            result["jd_id"] = jd_id
            result["persisted"] = True
            result["user_source"] = user_source
            result["merge"] = merge
        except store.UserUnresolved as exc:
            result["persist_error"] = {"code": "user_unresolved", "message": exc.detail}
        except SQLAlchemyError as exc:
            log.exception("JD analysed but could not be stored")
            result["persist_error"] = {"code": "persist_failed", "message": _db_reason(exc)}

    response.headers["X-Data-Source"] = "database" if result["persisted"] else "pipeline"
    return result


@router.get("/resume/latest")
def resume_latest(response: Response) -> dict[str, Any]:
    if not _db_ready():
        raise HTTPException(
            status_code=503,
            detail={"code": "degraded_mode", "message": "no database — nothing has been stored"},
        )
    with get_session() as session:
        user_id, _ = store.resolve_user(session)
        row = store.latest_resume(session, user_id=user_id)
    if row is None:
        raise HTTPException(
            status_code=404, detail={"code": "no_resume", "message": "no resume uploaded yet"}
        )
    response.headers["X-Data-Source"] = "database"
    return {**row, "id": str(row["id"])}


__all__ = ["MAX_BYTES", "router"]
