"""Dashboard payload, computed from rows. Pure functions, no I/O.

**Readiness is a defined number, not a vibe.** It is the JD-weighted average of how
much of each required skill you can currently show:

    attainment(skill) = min(1, level_value(held) / level_value(expected))
    readiness         = 100 × Σ(jd_importance × attainment) / Σ(jd_importance)

`held` is the verified level if an assessment produced one, otherwise the level the
resume claims. A skill the JD requires and the resume never mentions contributes
attainment 0 — that is the point of measuring against the JD rather than against the
whole taxonomy.

The thresholds for the label live here, in one place, because "am I early or
approaching?" should never depend on which screen you are looking at.
"""
from __future__ import annotations

from datetime import date

from app.prep.priority import LEVEL_VALUE

# readiness() is a percentage, so the thresholds are too — mixing the two scales is
# exactly the kind of bug that silently labels a 24.9% profile "interview ready".
LABEL_THRESHOLDS = ((75.0, "interview_ready"), (50.0, "approaching"), (25.0, "early"))
LABEL_FLOOR = "not_ready"


def readiness_label(readiness: float) -> str:
    for threshold, label in LABEL_THRESHOLDS:
        if readiness >= threshold:
            return label
    return LABEL_FLOOR


def attainment(*, held: str | None, expected: str | None) -> float:
    expected_value = LEVEL_VALUE.get(expected or "intermediate", 0.55) or 0.55
    held_value = LEVEL_VALUE.get(held or "none", 0.0)
    return round(min(1.0, held_value / expected_value), 3)


def readiness(rows: list) -> float:
    """Weighted by what the JD actually asks for; unweighted skills do not count."""
    total_weight = 0.0
    total = 0.0
    for row in rows:
        weight = float(row.jd_importance or 0)
        if weight <= 0:
            continue
        total_weight += weight
        total += weight * attainment(
            held=row.verified_level or row.claimed_level, expected=row.expected_level
        )
    if total_weight == 0:
        return 0.0
    return round(100 * total / total_weight, 1)


def coverage(rows: list) -> list[dict]:
    """Same three buckets the profile screen uses, counted per category.

    Retired rows (neither in the resume nor in the posting) are left out: a backend
    candidate should not see a "Marketing 0/2" bar left over from a resume they replaced.
    """
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        if not (getattr(row, "in_resume", True) or getattr(row, "in_jd", True)):
            continue
        entry = buckets.setdefault(
            row.category, {"category": row.category, "verified": 0, "developing": 0, "unverified": 0}
        )
        if row.verified_level:
            entry["verified"] += 1
        elif row.claimed_level:
            entry["developing"] += 1
        else:
            entry["unverified"] += 1
    return sorted(buckets.values(), key=lambda e: (-(e["verified"] + e["developing"] + e["unverified"]), e["category"]))


def build_dashboard(
    rows: list,
    *,
    target_role: str | None,
    interviews: list[dict] | None = None,
    topics_done: int = 0,
    topics_total: int = 0,
    today: date | None = None,
) -> dict:
    interviews = interviews or []
    score = (
        round(sum(i.get("score") or 0 for i in interviews) / len(interviews), 1)
        if interviews
        else None
    )
    readiness_value = readiness(rows)
    day = (today or date.today()).isoformat()

    return {
        "readiness": readiness_value,
        "readiness_label": readiness_label(readiness_value),
        "provisional": not any(row.verified_level for row in rows),
        "target_role": target_role,
        # One point today, because that is how many measurements exist. Filling this
        # with a fake seven-day curve would be the single most tempting lie on the
        # screen, and the sparkline would look better for it.
        "readiness_history": [{"date": day, "readiness": readiness_value}] if rows else [],
        "history_basis": (
            "one measurement per day, recorded when skills change — "
            "history accumulates as you work, it is not backfilled"
        ),
        "stats": {
            "verified_skills": sum(1 for row in rows if row.status == "verified"),
            "skills_total": len(rows),
            "mock_interviews": len(interviews),
            "topics_done": topics_done,
            "topics_total": topics_total,
            "avg_interview_score": score,
        },
        "coverage": coverage(rows),
        "priority_skills": [row.as_json() for row in rows[:3]],
        "interviews": interviews,
    }
