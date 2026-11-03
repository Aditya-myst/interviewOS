"""Skill status transitions — the schema's rules, in one place, so app code cannot fight
the database.

`docs/sql/001_init.sql` installs `enforce_skill_transition()`, which refuses illegal moves
with a CHECK violation. That guard is right: `verified` must not slide backwards silently.
But a guard that raises inside a request is a 500 for the user, so the application has to
*ask* what is legal before it writes.

This module is that question, and its table is a mirror of the trigger (there is a test
that asserts the two agree by attempting every pair against a real database).

The important case it exists for: an interview scoring 0.2 means "needs rework", but for a
skill that was only ever `claimed` there is nothing to revise — it was never verified. The
honest state there is `weak`. Writing `needs_revision` instead crashed the interview with
`illegal transition claimed -> needs_revision`.
"""
from __future__ import annotations

STATUSES = ("claimed", "unverified", "weak", "developing", "verified", "needs_revision")

# Mirrors enforce_skill_transition() exactly. A status may always stay where it is.
LEGAL: dict[str, frozenset[str]] = {
    "claimed": frozenset({"weak", "developing", "verified"}),
    "unverified": frozenset({"weak", "developing", "verified"}),
    "weak": frozenset({"developing", "verified"}),
    "developing": frozenset({"verified", "weak"}),
    "verified": frozenset({"needs_revision"}),
    "needs_revision": frozenset({"developing", "verified"}),
}

# When the wanted status is not reachable from where the skill is, these are the honest
# fallbacks. Two rules decide them:
#
#  - "needs_revision" without a prior verification is "weak" — you cannot revise a thing you
#    never proved. (This is the mapping that crashed the interview.)
#  - anything else that cannot move stays where it is. A bad answer must never *promote* a
#    skill as a side effect, and staying put is always legal (the trigger no-ops on it).
FALLBACK: dict[str, tuple[str, ...]] = {
    "needs_revision": ("weak",),
    "weak": ("needs_revision",),      # a verified row that no longer holds needs revision
    "developing": ("needs_revision",),
    "verified": (),
    "claimed": (),
    "unverified": (),
}


def can_transition(current: str | None, wanted: str) -> bool:
    if not current or current == wanted:
        return True
    return wanted in LEGAL.get(current, frozenset())


def reconcile(current: str | None, wanted: str) -> str:
    """The status to actually write: `wanted` when the schema allows it, else the closest
    honest one. Never returns a value that would trip the trigger."""
    if not current or current == wanted:
        return wanted or current or "unverified"
    if wanted not in STATUSES:
        return current
    if wanted in LEGAL.get(current, frozenset()):
        return wanted
    for candidate in FALLBACK.get(wanted, ()):
        if candidate in LEGAL.get(current, frozenset()):
            return candidate
    return current  # stay put: a no-op is legal, and a promotion would be a lie


__all__ = ["FALLBACK", "LEGAL", "STATUSES", "can_transition", "reconcile"]
