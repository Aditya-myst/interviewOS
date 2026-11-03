"""Interview persistence.

Two implementations behind one protocol:

* `SqlSessionStore` — the real thing, writing to interview_sessions /
  interview_messages / interview_reports, which have existed in the schema since
  001_init.sql and have been empty until now.
* `MemorySessionStore` — used when there is no database. An interview you cannot take
  because Postgres is not configured would be a worse demo than one that works and
  says so: the API reports `X-Data-Source: memory`, and the report carries
  `persisted: false`.

The protocol is small on purpose. Both stores must satisfy the same tests.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InterviewMessage, InterviewReport, InterviewSession


@dataclass
class SessionRecord:
    """What the engine needs to know about a session, provider-agnostic."""

    id: str
    status: str
    asked: int
    total: int
    skill_focus: list[str] = field(default_factory=list)
    target_role: str | None = None
    channel: str = "text"
    mode: str = "jd_based"
    plan: list[dict[str, Any]] = field(default_factory=list)


class SessionStore(Protocol):
    def create(
        self,
        *,
        plan: list[dict[str, Any]],
        target_role: str | None,
        user_id: str | None,
        mode: str = "jd_based",
        channel: str = "text",
    ) -> SessionRecord: ...
    def get(self, session_id: str) -> SessionRecord | None: ...
    def append(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        question_type: str | None,
        skill_id: str | None,
        audio_url: str | None = None,
    ) -> None: ...
    def messages(self, session_id: str) -> list[dict[str, Any]]: ...
    def advance(self, session_id: str) -> None: ...
    def complete(self, session_id: str, *, score: float | None) -> None: ...
    def save_report(self, session_id: str, report: dict[str, Any]) -> None: ...
    def get_report(self, session_id: str) -> dict[str, Any] | None: ...
    @property
    def source(self) -> str: ...


class NotFound(LookupError):
    pass


# ------------------------------------------------------------------- memory store


class MemorySessionStore:
    """Per-process store. Good for tests and for fixture mode."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._messages: dict[str, list[dict[str, Any]]] = {}
        self._reports: dict[str, dict[str, Any]] = {}

    @property
    def source(self) -> str:
        return "memory"

    def create(self, *, plan, target_role, user_id, mode="jd_based", channel="text") -> SessionRecord:
        session_id = str(uuid.uuid4())
        record = SessionRecord(
            id=session_id,
            status="active",
            asked=0,
            total=len(plan),
            skill_focus=[q["skill_id"] for q in plan if q.get("skill_id")],
            target_role=target_role,
            mode=mode,
            channel=channel,
            plan=plan,
        )
        self._sessions[session_id] = record
        self._messages[session_id] = []
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        return self._sessions.get(session_id)

    def append(self, session_id, *, role, content, question_type, skill_id, audio_url=None) -> None:
        if session_id not in self._sessions:
            raise NotFound(session_id)
        self._messages[session_id].append(
            {
                "role": role,
                "content": content,
                "question_type": question_type,
                "skill_id": skill_id,
                "audio_url": audio_url,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )

    def messages(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._messages.get(session_id, []))

    def advance(self, session_id: str) -> None:
        record = self._sessions[session_id]
        record.asked += 1

    def complete(self, session_id: str, *, score: float | None) -> None:
        record = self._sessions[session_id]
        record.status = "completed"
        record.asked = record.total

    def save_report(self, session_id: str, report: dict[str, Any]) -> None:
        self._reports[session_id] = report

    def get_report(self, session_id: str) -> dict[str, Any] | None:
        return self._reports.get(session_id)


# ---------------------------------------------------------------------- sql store


class SqlSessionStore:
    """Writes to the tables that were provisioned in 001_init.sql."""

    def __init__(self, session: Session, *, user_id: str) -> None:
        self._db = session
        self._user_id = user_id

    @property
    def source(self) -> str:
        return "database"

    def create(self, *, plan, target_role, user_id, mode="jd_based", channel="text") -> SessionRecord:
        row = InterviewSession(
            user_id=user_id or self._user_id,
            mode=mode,
            channel=channel,
            status="active",
            target_role=target_role,
            skill_focus=[q["skill_id"] for q in plan if q.get("skill_id")],
            asked=0,
            total=len(plan),
        )
        self._db.add(row)
        self._db.commit()
        return SessionRecord(
            id=str(row.id),
            status="active",
            asked=0,
            total=len(plan),
            skill_focus=list(row.skill_focus or []),
            target_role=row.target_role,
            mode=row.mode,
            channel=row.channel,
            plan=plan,
        )

    def _row(self, session_id: str) -> InterviewSession:
        row = self._db.get(InterviewSession, uuid.UUID(session_id))
        if row is None:
            raise NotFound(session_id)
        return row

    def get(self, session_id: str) -> SessionRecord | None:
        try:
            row = self._row(session_id)
        except (NotFound, ValueError):
            return None
        return SessionRecord(
            id=str(row.id),
            status=row.status,
            asked=row.asked,
            total=row.total,
            skill_focus=list(row.skill_focus or []),
            target_role=row.target_role,
            channel=row.channel,
            mode=row.mode,
        )

    def append(self, session_id, *, role, content, question_type, skill_id, audio_url=None) -> None:
        # audio_url has no column yet: voice arrives in block 4, and inventing a column
        # here would mean a migration the schema owner did not ask for. It is returned in
        # the response and kept in the transcript payload for the memory store.
        self._db.add(
            InterviewMessage(
                session_id=uuid.UUID(session_id),
                user_id=uuid.UUID(self._user_id),
                role=role,
                content=content,
                question_type=question_type,
                skill_id=skill_id,
            )
        )
        self._db.commit()

    def messages(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._db.execute(
            select(InterviewMessage)
            .where(InterviewMessage.session_id == uuid.UUID(session_id))
            .order_by(InterviewMessage.id)
        ).scalars()
        return [
            {
                "role": row.role,
                "content": row.content,
                "question_type": row.question_type,
                "skill_id": row.skill_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    def advance(self, session_id: str) -> None:
        row = self._row(session_id)
        row.asked = (row.asked or 0) + 1
        self._db.commit()

    def complete(self, session_id: str, *, score: float | None) -> None:
        row = self._row(session_id)
        row.status = "completed"
        row.asked = row.total
        row.score = score
        row.completed_at = datetime.now(UTC)
        self._db.commit()

    def save_report(self, session_id: str, report: dict[str, Any]) -> None:
        existing = self._db.execute(
            select(InterviewReport).where(InterviewReport.session_id == uuid.UUID(session_id))
        ).scalar_one_or_none()
        payload = {
            "overall_scores": report.get("overall_scores", {}),
            "per_skill": report.get("per_skill", []),
            "strengths": report.get("strengths", []),
            "gaps": report.get("gaps", []),
            "weak_answers": report.get("weak_answers", []),
            "next_actions": report.get("next_actions", []),
        }
        if existing is None:
            self._db.add(
                InterviewReport(
                    session_id=uuid.UUID(session_id),
                    user_id=uuid.UUID(self._user_id),
                    **payload,
                )
            )
        else:
            for key, value in payload.items():
                setattr(existing, key, value)
        self._db.commit()

    def get_report(self, session_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            select(InterviewReport).where(InterviewReport.session_id == uuid.UUID(session_id))
        ).scalar_one_or_none()
        if row is None:
            return None
        return {
            "session_id": session_id,
            "overall_scores": row.overall_scores or {},
            "per_skill": row.per_skill or [],
            "strengths": row.strengths or [],
            "gaps": row.gaps or [],
            "weak_answers": row.weak_answers or [],
            "next_actions": row.next_actions or [],
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


# ------------------------------------------------------------------------ factory

_MEMORY = MemorySessionStore()


def memory_store() -> MemorySessionStore:
    """One store per process, so a demo survives a request boundary."""
    return _MEMORY
