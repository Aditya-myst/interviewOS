"""Roadmap progress: the plan becomes rows you can move.

The roadmap was computed on every read and thrown away. `learning_paths` and
`learning_topics` — eighteen tables exist for this — stayed empty, so `topics_done` on the
dashboard counted rows in a table nothing ever wrote, and it could not leave zero no matter
how much the candidate studied. A progress bar that cannot move is decoration.

What this module guarantees:

1. **The plan is the same plan.** Topic ids are the deterministic uuid5 the roadmap already
   computes from (skill, subtopic), so a row written today is the same row tomorrow, and a
   re-plan updates content instead of duplicating.
2. **Progress is never overwritten by a re-plan.** Syncing writes titles, objectives and
   ordering; it never touches `status` or `progress`. Re-running the JD analysis must not
   mark a finished topic unfinished.
3. **A topic that drops out of scope keeps its row but leaves the totals.** If a new resume
   stops mentioning a skill, its topic is parked out of the current plan (order_index at or
   above ORDER_PARK) and excluded from every count, so "2 of 5 done" cannot silently become
   "2 of 10". The history survives, so switching back does not erase what was done.
4. **Two candidates cannot share a topic.** Topic ids are uuid5 of the curriculum, so they
   are guessable; every write filters on `user_id` and a stale id is a 404, not someone
   else's row.
5. **Concurrent syncs converge.** Reading the plan writes it, so two tabs open at once both
   sync. The archive/park statements take row locks in the same order and the upserts are
   idempotent, so the second request waits and then finds the work already done.
6. **Ordering changes cannot collide.** `learning_topics` is unique on (path_id,
   order_index). Re-ordering in place would hit that constraint halfway through, so the sync
   parks existing rows in a far-away range inside the same transaction before writing the
   new order.
"""
from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import Any

from sqlalchemy import func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import LearningPath, LearningTopic

log = logging.getLogger(__name__)

# One path per candidate. Deterministic, so "create the plan" is idempotent by construction
# and two concurrent requests cannot produce two active paths.
PATH_NAMESPACE = uuid.UUID("2f1c4e6a-8b3d-5f70-9c11-0a5b6d7e8f90")

STATUSES = ("not_started", "in_progress", "checkpoint_passed", "done")

# A status implies a progress value unless the caller passes one explicitly: "done" with a
# bar at 40% would be two answers to one question.
PROGRESS_FOR = {"not_started": 0.0, "in_progress": 0.5, "checkpoint_passed": 0.75, "done": 1.0}

# Parked rows live here during a re-order; far above any plausible plan length. The same
# threshold separates "in the plan" from "kept for history": a row at or above it belongs to
# a plan the candidate's documents no longer ask for, so it is excluded from every total. The
# modulo keeps the value from growing by another 100k on every re-plan.
ORDER_PARK = 100_000


class TopicNotFound(LookupError):
    """The topic id is not in this candidate's plan."""


def path_id_for(user_id: str | uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(PATH_NAMESPACE, f"path:{user_id}")


def sync_plan(
    session,
    *,
    user_id: str,
    plan: dict[str, Any],
    target_role: str | None = None,
    readiness: float | None = None,
    readiness_label: str | None = None,
) -> uuid.UUID:
    """Write (or refresh) the computed plan. Returns the path id.

    Content only: status and progress belong to the candidate, not to the planner.
    """
    pid = path_id_for(user_id)
    topics = list(plan.get("topics") or [])

    values = {
        "id": pid,
        "user_id": uuid.UUID(str(user_id)),
        "title": f"Preparation for {target_role}" if target_role else "Your preparation path",
        "summary": str(plan.get("summary") or ""),
        "status": "active",
        "target_role": target_role,
    }
    if readiness is not None:
        values["readiness"] = round(float(readiness), 2)
    if readiness_label:
        values["readiness_label"] = readiness_label

    stmt = pg_insert(LearningPath).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[LearningPath.id],
        set_={
            "title": stmt.excluded.title,
            "summary": stmt.excluded.summary,
            "status": "active",
            "target_role": stmt.excluded.target_role,
            "updated_at": func.now(),
            **({"readiness": stmt.excluded.readiness} if "readiness" in values else {}),
            **({"readiness_label": stmt.excluded.readiness_label} if "readiness_label" in values else {}),
        },
    )
    session.execute(stmt)

    if topics:
        keep = [uuid.UUID(str(t["id"])) for t in topics]

        # Step 1: archive rows the current documents no longer ask for. They keep their
        # status (history is not deleted) and are appended after the archived range, so two
        # archive passes can never fight over the same (path_id, order_index) slot -- which
        # is exactly what happened when the first version used a modulo: an in-plan topic at
        # index 2 was parked onto an archived topic already sitting at 100002, the unique
        # constraint raised, and the whole overlay silently degraded to "nothing done".
        session.execute(
            text(
                """
                with stale as (
                    select id, row_number() over (order by id) as rn,
                           coalesce((select max(order_index) - :park + 1
                                     from public.learning_topics
                                     where user_id = cast(:user as uuid)
                                       and order_index >= :park), 0) as base
                    from public.learning_topics
                    where user_id = cast(:user as uuid)
                      and order_index < :park
                      and not (id = any(cast(:keep as uuid[])))
                )
                update public.learning_topics t
                set order_index = :park + stale.base + stale.rn - 1, updated_at = now()
                from stale
                where t.id = stale.id
                """
            ),
            {"user": str(user_id), "park": ORDER_PARK, "keep": keep},
        )

        # Step 2: park the rows that stay, out of the low range, so a re-order can write
        # 0..n in any order without two rows ever claiming the same slot mid-transaction.
        session.execute(
            update(LearningTopic)
            .where(LearningTopic.path_id == pid, LearningTopic.order_index < ORDER_PARK)
            .values(order_index=LearningTopic.order_index + (ORDER_PARK * 2))
        )

        # Step 3: upsert by id with the new order and content.
        for topic in topics:
            row = {
                "id": uuid.UUID(str(topic["id"])),
                "path_id": pid,
                "user_id": uuid.UUID(str(user_id)),
                "skill_id": topic.get("skill_id"),
                "title": str(topic.get("title") or "Untitled topic"),
                "objective": topic.get("objective"),
                "subtopics": list(topic.get("subtopics") or []),
                "depth": topic.get("depth") or "core",
                "order_index": int(topic.get("order_index") or 0),
                "estimated_minutes": topic.get("estimated_minutes"),
                "status": "not_started",
                "progress": 0.0,
            }
            ins = pg_insert(LearningTopic).values(**row)
            ins = ins.on_conflict_do_update(
                index_elements=[LearningTopic.id],
                set_={
                    # content only — never status, never progress
                    "path_id": ins.excluded.path_id,
                    "skill_id": ins.excluded.skill_id,
                    "title": ins.excluded.title,
                    "objective": ins.excluded.objective,
                    "subtopics": ins.excluded.subtopics,
                    "depth": ins.excluded.depth,
                    "order_index": ins.excluded.order_index,
                    "estimated_minutes": ins.excluded.estimated_minutes,
                    "updated_at": func.now(),
                },
            )
            session.execute(ins)

    session.commit()
    return pid


def topic_states(session, *, user_id: str) -> dict[str, dict[str, Any]]:
    """{topic_id: {status, progress}} for this candidate. Empty when nothing is stored."""
    rows = session.execute(
        select(LearningTopic.id, LearningTopic.status, LearningTopic.progress).where(
            LearningTopic.user_id == uuid.UUID(str(user_id)),
            LearningTopic.order_index < ORDER_PARK,
        )
    ).all()
    return {
        str(row.id): {"status": row.status, "progress": float(row.progress or 0)}
        for row in rows
    }


def set_status(
    session,
    *,
    user_id: str,
    topic_id: str,
    status: str,
    progress: float | None = None,
) -> dict[str, Any]:
    """Mark one topic. Returns the stored row plus the plan's new totals."""
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}; expected one of {', '.join(STATUSES)}")

    try:
        tid = uuid.UUID(str(topic_id))
    except (ValueError, AttributeError) as exc:
        raise TopicNotFound(topic_id) from exc

    row = session.execute(
        select(LearningTopic).where(
            LearningTopic.id == tid, LearningTopic.user_id == uuid.UUID(str(user_id))
        )
    ).scalar_one_or_none()
    if row is None:
        raise TopicNotFound(topic_id)

    value = PROGRESS_FOR[status] if progress is None else max(0.0, min(1.0, float(progress)))
    row.status = status
    row.progress = value
    row.updated_at = dt.datetime.now(dt.UTC)
    session.commit()

    totals = _totals(session, user_id=user_id)
    return {
        "topic_id": str(row.id),
        "status": row.status,
        "progress": float(row.progress or 0),
        "plan": totals,
    }


def _totals(session, *, user_id: str) -> dict[str, Any]:
    rows = session.execute(
        select(LearningTopic.status, func.count())
        .where(
            LearningTopic.user_id == uuid.UUID(str(user_id)),
            LearningTopic.order_index < ORDER_PARK,  # current plan only, not archived rows
        )
        .group_by(LearningTopic.status)
    ).all()
    by_status = {status: int(count) for status, count in rows}
    total = sum(by_status.values())
    done = by_status.get("done", 0)
    return {
        "done": done,
        "total": total,
        "percent": round((done / total) * 100) if total else 0,
        "by_status": by_status,
    }


__all__ = [
    "PROGRESS_FOR",
    "STATUSES",
    "TopicNotFound",
    "path_id_for",
    "set_status",
    "sync_plan",
    "topic_states",
]
