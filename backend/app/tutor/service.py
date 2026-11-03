"""The tutor — retrieval over the candidate's own rows, then composition.

Four rules, all of them testable:

1. **Three sources only.** The candidate's skill row (levels, band, evidence quotes), the
   curriculum subtopics for that skill (title, level, objective), and the curated catalogue
   entries mapped to those subtopics (title, url, provider, licence). No sentence here is
   written freehand by a model, because a model asked "how do I get better at RAG" will
   happily invent a course that does not exist.
2. **Every claim carries a citation.** The focus rows cite a subtopic id, the resource rows
   cite a catalogue url, the standing paragraph cites a resume quote or an assessment
   answer. `test_tutor.py` walks every line and fails on an uncited one.
3. **Nothing found is a stated outcome.** No row → `matched: false` and the reason, plus
   the skills that *can* be answered about. Never a plausible paragraph about a topic with
   no row behind it.
4. **It explains, it does not grade.** No level moves because the tutor spoke.

Deterministic on purpose: same question + same profile = same answer, no key, no network,
so the demo works offline and the tests are exact.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

import yaml

from app.config import DATA_DIR
from app.parsing import taxonomy

MIN_QUESTION_CHARS = 4
MAX_QUESTION_CHARS = 1000
MAX_FOCUS = 3

STOP = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "could", "do", "does", "for", "from", "get", "got", "has", "have", "how", "i", "if", "in", "into", "is", "it", "its", "me", "my", "of", "on", "or", "should", "so", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "to", "up", "us", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "would", "you", "your", "about", "more", "most", "much", "better", "best", "good", "learn", "learning", "improve", "start", "starting", "prepare", "preparing", "help", "need", "want", "next", "begin", "focus", "priority", "priorities", "gap", "gaps", "plan", "plan", "recommend", "suggestion", "suggestions", "first"]
)

LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}


@dataclass(frozen=True)
class Citation:
    """One row the answer leans on. `kind` is what the UI colours the chip by."""

    kind: str  # profile | resume_quote | assessment_answer | jd_requirement | subtopic | resource
    label: str
    detail: str | None = None
    url: str | None = None
    subtopic_id: str | None = None


@dataclass(frozen=True)
class Focus:
    subtopic_id: str
    title: str
    level: str
    objective: str
    why: str
    resources: tuple[dict[str, Any], ...] = ()


@dataclass
class Answer:
    matched: bool
    scope: dict[str, Any] | None = None
    standing: str | None = None
    lead: str | None = None
    focus: list[Focus] = field(default_factory=list)
    limits: str | None = None
    citations: list[Citation] = field(default_factory=list)
    unknown: dict[str, Any] | None = None
    suggestions: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "scope": self.scope,
            "standing": self.standing,
            "lead": self.lead,
            "focus": [
                {**asdict(row), "resources": list(row.resources)} for row in self.focus
            ],
            "limits": self.limits,
            "citations": [asdict(c) for c in self.citations],
            "unknown": self.unknown,
            "suggestions": self.suggestions,
        }


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", (text or "").lower())
    return {word.strip(".-") for word in words if word not in STOP and len(word) > 2}


def catalogue() -> dict[str, dict[str, list[dict[str, Any]]]]:
    path = DATA_DIR / "curated.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text()) or {}
    return raw.get("catalogue") or {}


def _first_quote(row: dict[str, Any]) -> tuple[str, str] | None:
    for evidence in row.get("evidence") or []:
        quote = (evidence.get("quote") or "").strip()
        if quote:
            return evidence.get("type") or "evidence", quote
    return None


def _level_gap(verified: str | None, expected: str | None) -> str | None:
    if not verified or not expected:
        return None
    a = LEVEL_ORDER.get(str(verified).lower())
    b = LEVEL_ORDER.get(str(expected).lower())
    if a is None or b is None or a >= b:
        return None
    return f"Verified {verified}, the posting expects {expected}"


def _resolve_scope(
    question: str, tokens: set[str], skill_id: str | None, profile: dict[str, Any]
) -> tuple[str | None, dict[str, Any] | None, str]:
    """Explicit id wins; then an alias named in the question; then a subtopic word; then
    the profile's own top priority, which is what a candidate means by "this"."""
    skills = taxonomy.load()
    rows = {row.get("skill_id"): row for row in profile.get("skills") or []}

    if skill_id and skill_id in skills:
        return skill_id, rows.get(skill_id), "explicit"

    best: tuple[int, str] | None = None
    for sid, skill in skills.items():
        for term in skill.terms:
            words = _tokens(term)
            if words and words.issubset(tokens):
                score = len(words) * 10 + len(term)
                if best is None or score > best[0]:
                    best = (score, sid)
    if best:
        return best[1], rows.get(best[1]), "alias"

    # a subtopic title can name the topic when the skill itself was not said
    for sid, subs in taxonomy.raw_subtopics().items():
        for sub in subs:
            words = _tokens(f"{sub.get('title', '')} {sub.get('objective', '')}")
            overlap = len(words & tokens)
            if overlap >= 2 and (best is None or overlap * 10 > best[0]):
                best = (overlap * 10, sid)
    if best:
        return best[1], rows.get(best[1]), "subtopic"

    # fall back to the candidate's most urgent skill, and say so in the lead
    ranked = sorted(
        (r for r in rows.values() if r.get("skill_id")),
        key=lambda r: r.get("priority") or 0,
        reverse=True,
    )
    if ranked:
        return ranked[0]["skill_id"], ranked[0], "fallback"
    return None, None, "none"


def _vocabulary() -> set[str]:
    """Every word the curriculum can talk about. A question that touches none of it is
    off-domain, and the honest reply is "not in my sources" — not the user's top gap."""
    words: set[str] = set()
    for skill in taxonomy.load().values():
        for term in skill.terms:
            words |= _tokens(term)
    for subs in taxonomy.raw_subtopics().values():
        for sub in subs:
            words |= _tokens(f"{sub.get('title', '')} {sub.get('objective', '')}")
    return words


def _rank_subtopics(skill_id: str, tokens: set[str]) -> list[dict[str, Any]]:
    subs = taxonomy.raw_subtopics().get(skill_id) or []
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, sub in enumerate(subs):
        words = _tokens(f"{sub.get('title', '')} {sub.get('objective', '')} {sub.get('id', '')}")
        scored.append((len(words & tokens), index, sub))
    scored.sort(key=lambda row: (-row[0], row[1]))
    # Ranked hits first, then the rest in curriculum order: the ladder should have three
    # rungs even when one word only matched one subtopic.
    return [row[2] for row in scored[:MAX_FOCUS]]


def _resources_for(skill_id: str, subtopic_id: str) -> list[dict[str, Any]]:
    entries = catalogue().get(skill_id, {}).get(subtopic_id) or []
    # Free first, then concept before practice: the tutor never sends someone to a paywall
    # without saying so.
    order = {"concept": 0, "practice": 1, "reference": 2, "project": 3}
    return sorted(
        (dict(entry) for entry in entries),
        key=lambda e: (bool(e.get("is_paid")), order.get(e.get("role", ""), 9), e.get("title", "")),
    )


def ask(
    question: str,
    *,
    skill_id: str | None = None,
    profile: dict[str, Any] | None = None,
) -> Answer:
    """One question in, one composed answer out. Pure: no clock, no network, no DB."""
    profile = profile or {"skills": []}
    tokens = _tokens(question)

    skills = taxonomy.load()
    if not profile.get("skills"):
        return Answer(
            matched=False,
            unknown={
                "reason": "Your profile has no skills yet, so there is no row to teach from.",
                "can_answer": [],
                "next": "Upload a resume and paste a job description on /onboarding first.",
            },
            suggestions=[],
        )

    if tokens and not (tokens & _vocabulary()):
        return Answer(
            matched=False,
            scope=None,
            unknown={
                "reason": "That is not in the curriculum, the curated catalogue or your profile.",
                "can_answer": _answerable(profile),
                "next": "Ask about one of those skills, or about a subtopic inside one.",
            },
            suggestions=_suggestions(profile),
        )

    scope_id, row, how = _resolve_scope(question, tokens, skill_id, profile)

    # "What is the salary at Google?" touches one vocabulary word by accident. Answering it
    # with the user's top gap would look like comprehension and be a non-answer, so a
    # fallback scope is only allowed when every content word is one this skill covers.
    if how == "fallback" and scope_id:
        skill_words: set[str] = set()
        for term in taxonomy.load()[scope_id].terms:
            skill_words |= _tokens(term)
        for sub in taxonomy.raw_subtopics().get(scope_id) or []:
            skill_words |= _tokens(f"{sub.get('title', '')} {sub.get('objective', '')}")
        strays = tokens - skill_words
        if strays:
            return Answer(
                matched=False,
                scope=None,
                unknown={
                    "reason": (
                        "I could not tie that to a skill on your profile or a subtopic in the "
                        f"curriculum — no row mentions {' or '.join(sorted(strays))}."
                    ),
                    "can_answer": _answerable(profile),
                    "next": "Name a skill or a subtopic and I will answer from its rows.",
                },
                suggestions=_suggestions(profile),
            )
    if not scope_id:
        return Answer(
            matched=False,
            unknown={
                "reason": "No skill on your profile matches that question.",
                "can_answer": _answerable(profile),
                "next": "Name a skill from the list, or pick one below.",
            },
            suggestions=_suggestions(profile),
        )

    skill = skills[scope_id]
    focus_subs = _rank_subtopics(scope_id, tokens)
    cited: list[Citation] = []

    # ── where you stand: the profile row, or an honest absence ────────────────
    standing: str | None = None
    if row:
        verified = row.get("verified_level")
        expected = row.get("expected_level")
        band = row.get("priority_band")
        standing = (
            f"{row.get('name', skill.name)} is {row.get('status', 'on your profile')} — "
            f"verified {verified or 'not yet'}"
            + (f", the JD asks for {expected}" if expected else "")
            + (f", {band} priority" if band else "")
            + "."
        )
        cited.append(
            Citation(
                kind="profile",
                label=f"{skill.name} profile row",
                detail=f"status {row.get('status')} · verified {verified} · gap {row.get('gap')}",
            )
        )
        quote = _first_quote(row)
        if quote:
            kind, text = quote
            cited.append(Citation(kind=kind, label=text, detail="your own words"))
            standing += f" Your evidence: “{text}”"

    # ── the three things to do next ──────────────────────────────────────────
    focus: list[Focus] = []
    for sub in focus_subs:
        sub_id = str(sub.get("id") or "")
        gap_note = _level_gap(
            row.get("verified_level") if row else None,
            row.get("expected_level") if row else None,
        )
        if row and gap_note:
            why = f"{gap_note} — {sub.get('level', 'beginner')}-level work closes part of it."
        elif row:
            why = f"Keeps {row.get('verified_level') or 'your'} level honest for {skill.name}."
        else:
            why = "Not on your profile yet; this is the curriculum's first step."

        resources = _resources_for(scope_id, sub_id)
        focus.append(
            Focus(
                subtopic_id=sub_id,
                title=str(sub.get("title") or sub_id),
                level=str(sub.get("level") or "beginner"),
                objective=str(sub.get("objective") or ""),
                why=why,
                resources=tuple(resources),
            )
        )
        cited.append(
            Citation(
                kind="subtopic",
                label=str(sub.get("title") or sub_id),
                detail=f"{scope_id}/{sub_id} · {sub.get('level')}",
                subtopic_id=sub_id,
            )
        )
        for entry in resources:
            cited.append(
                Citation(
                    kind="resource",
                    label=str(entry.get("title") or "resource"),
                    detail=f"{entry.get('provider', '')} · {entry.get('kind', '')}"
                    + (" · paid" if entry.get("is_paid") else " · free"),
                    url=entry.get("url"),
                    subtopic_id=sub_id,
                )
            )

    # ── what this answer cannot do ───────────────────────────────────────────
    limits: list[str] = []
    has_catalogue = bool(catalogue().get(scope_id))
    if not has_catalogue:
        limits.append(
            f"The catalogue has no curated links for {skill.name} yet, so the steps below "
            "come from the curriculum alone."
        )
    if not row:
        limits.append(
            f"{skill.name} is not on your profile, so there is no evidence to point at and "
            "nothing here moves a level."
        )
    limits.append("The tutor does not grade. Scores still come from a rubric answer with a quote.")

    lead = (
        f"{skill.name} ({skill.category}) — {len(focus)} subtopics from the curriculum, "
        f"{sum(len(f.resources) for f in focus)} curated links."
    )
    if not row:
        lead = f"{skill.name} ({skill.category}) — not on your profile yet. " + lead.split("— ", 1)[1]

    return Answer(
        matched=True,
        scope={
            "skill_id": scope_id,
            "name": skill.name,
            "category": skill.category,
            "in_profile": bool(row),
            "source": "profile" if row else "curriculum",
        },
        standing=standing,
        lead=lead,
        focus=focus,
        limits=" ".join(limits),
        citations=cited,
        suggestions=_suggestions(profile, exclude=scope_id),
    )


def _answerable(profile: dict[str, Any]) -> list[str]:
    rows = sorted(
        (r for r in profile.get("skills") or [] if r.get("skill_id")),
        key=lambda r: r.get("priority") or 0,
        reverse=True,
    )
    return [str(r.get("name") or r["skill_id"]) for r in rows[:6]]


def _suggestions(profile: dict[str, Any], exclude: str | None = None) -> list[str]:
    """Questions this tutor can actually answer, built from the candidate's own gaps."""
    rows = sorted(
        (r for r in profile.get("skills") or [] if r.get("skill_id")),
        key=lambda r: r.get("priority") or 0,
        reverse=True,
    )
    picked = [r for r in rows if r.get("skill_id") != exclude][:3]
    return [f"How do I close the gap in {r.get('name') or r['skill_id']}?" for r in picked]
