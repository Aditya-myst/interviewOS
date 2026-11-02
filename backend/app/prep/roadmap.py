"""Roadmap payload, computed from the scored profile and the resource catalogue.

Two rules shape this file:

1. **Every topic is a subtopic that exists in `data/taxonomy.yaml`.** The plan cannot
   invent a syllabus, which is the whole reason the taxonomy is curated.
2. **A missing resource is a named gap, not an empty space.** The design calls for
   three roles per topic — concept, practice, checkpoint. When the catalogue has no
   row for a role, the payload says `missing_roles: ["checkpoint"]` so the UI can
   render an honest gap instead of a card that looks finished.

Nothing here writes to Postgres: `learning_paths` / `learning_topics` stay empty until
a path is accepted (POST /v1/preparation/create), and the read path recomputes.
"""
from __future__ import annotations

import uuid

from app.parsing import taxonomy

ROLES = ("concept", "practice", "checkpoint")

# resource.kind -> the role it can fill. A repo or an exercise is something you do;
# docs, articles, papers and books are something you read.
ROLE_FOR_KIND = {
    "docs": "concept",
    "article": "concept",
    "paper": "concept",
    "book": "concept",
    "course": "practice",
    "exercise": "practice",
    "repo": "practice",
    "video": "practice",
}

# A checkpoint has to be something you can fail, so only an exercise or a course can
# fill it. This is why most topics will honestly report a missing checkpoint.
CHECKPOINT_KINDS = {"exercise", "course"}

LEVEL_MINUTES = {"beginner": 45, "intermediate": 60, "advanced": 90}
LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}

TOPIC_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


def _topic_id(skill_id: str, subtopic_id: str) -> str:
    """Deterministic: the same plan produces the same ids, so links stay stable."""
    return str(uuid.uuid5(TOPIC_NAMESPACE, f"{skill_id}:{subtopic_id}"))


def _depth(band: str, gap: float) -> str:
    if band == "critical" or gap >= 0.7:
        return "deep_dive"
    if band == "high" or gap >= 0.45:
        return "core"
    return "refresh"


def _resources_for(
    rows: list[dict], *, take: int = 2
) -> tuple[list[dict], list[str]]:
    """Rows are catalogue entries for one (skill, subtopic). Pick at most one per role."""
    picked: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: (r.get("is_paid") or False, r.get("title") or "")):
        kind = (row.get("kind") or "").lower()
        role = ROLE_FOR_KIND.get(kind)
        if role is None:
            continue
        if role == "practice" and kind in CHECKPOINT_KINDS and "checkpoint" not in picked:
            role = "checkpoint" if "practice" in picked else "practice"
        if role in picked:
            continue
        picked[role] = {
            "id": row.get("id"),
            "role": role,
            "title": row.get("title"),
            "url": row.get("url"),
            "provider": row.get("provider"),
            "kind": kind,
            "is_paid": bool(row.get("is_paid")),
            "license": row.get("license"),
            "verified_at": row.get("verified_at"),
        }
        if len(picked) >= take:
            break
    ordered = [picked[r] for r in ROLES if r in picked]
    missing = [r for r in ROLES if r not in picked]
    return ordered, missing


def build_roadmap(
    rows: list,
    catalogue: dict[tuple[str, str], list[dict]],
    *,
    target_role: str | None,
    limit: int = 5,
) -> dict:
    """`catalogue` maps (skill_id, subtopic_id) -> resource rows from the database."""
    vocabulary = taxonomy.load()
    topics: list[dict] = []

    for row in rows:
        if len(topics) >= limit:
            break
        if row.priority_band == "low" and row.gap < 0.2:
            continue                       # nothing to teach and nothing to prove
        skill = vocabulary.get(row.skill_id)
        if skill is None:
            continue

        subtopics = _subtopics(skill)
        if not subtopics:
            continue
        # teach the rungs at or above where you currently are, so a listed skill
        # starts at the beginning and an advanced one skips the basics
        held = row.verified_level or row.claimed_level or "none"
        floor = LEVEL_ORDER.get("beginner" if held in ("none", "listed") else held, 0)
        wanted = [s for s in subtopics if LEVEL_ORDER.get(s["level"], 0) >= floor] or subtopics
        wanted = wanted[:2]

        for subtopic in wanted:
            if len(topics) >= limit:
                break
            resources, missing = _resources_for(catalogue.get((row.skill_id, subtopic["id"]), []))
            topics.append(
                {
                    "id": _topic_id(row.skill_id, subtopic["id"]),
                    "skill_id": row.skill_id,
                    "skill_name": row.name,
                    "title": subtopic["title"],
                    "objective": subtopic.get("objective") or "",
                    "status": "not_started",
                    "depth": _depth(row.priority_band, row.gap),
                    "order_index": len(topics),
                    "estimated_minutes": LEVEL_MINUTES.get(subtopic["level"], 60),
                    "progress": 0.0,
                    "priority": row.priority,
                    "priority_band": row.priority_band,
                    "why": row.explanation,
                    "subtopics": [s["title"] for s in wanted][:4],
                    "resources": resources,
                    "missing_roles": missing,
                }
            )

    done = sum(1 for topic in topics if topic["status"] == "done")
    bands = [t["priority_band"] for t in topics]
    summary = _summary(topics, bands, target_role)

    return {
        "id": str(uuid.uuid5(TOPIC_NAMESPACE, "|".join(t["id"] for t in topics) or "empty")),
        "status": "active" if topics else "empty",
        "target_role": target_role,
        "summary": summary,
        "progress": {"done": done, "total": len(topics)},
        "topics": topics,
    }


def _subtopics(skill) -> list[dict]:
    rows = taxonomy.raw_subtopics().get(skill.id) or []
    return sorted(rows, key=lambda s: LEVEL_ORDER.get(s.get("level", "beginner"), 0))


def _summary(topics: list[dict], bands: list[str], target_role: str | None) -> str:
    if not topics:
        return (
            "No topics yet — the roadmap is built from skills the JD asks for that your "
            "evidence does not cover. Upload a resume and a job description first."
        )
    critical = sum(1 for b in bands if b == "critical")
    high = sum(1 for b in bands if b == "high")
    role = f" for {target_role}" if target_role else ""
    missing = sum(1 for t in topics if t["missing_roles"])
    return (
        f"{len(topics)} topic{'s' if len(topics) != 1 else ''}{role}, ordered by interview impact: "
        f"{critical} critical and {high} high priority. "
        f"{missing} topic{'s' if missing != 1 else ''} still lack a full set of resources — "
        "shown as gaps rather than filled with links nobody checked."
    )
