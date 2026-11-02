"""Deterministic skill matching — no model, no quota, same answer every time.

Every match is a span in the document, so every skill we claim to have found can
be shown to a human as "here is the line". The model is not trusted for this and
does not need to be: a taxonomy of 31 skills with aliases covers most of what a
resume actually says, and what it misses is measured (see `coverage` in the parse
result) rather than guessed.

Ambiguity is handled explicitly. `rest`, `next`, `node`, `lambda`, `ml`, `syntax`
and friends are ordinary words in some sentences and technologies in others, so
they are marked WEAK: they only count with corroboration — a capitalised
spelling, a skills-section context, or another strong alias for the same skill in
the same sentence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.parsing import sections as sections_mod
from app.parsing import taxonomy
from app.parsing.quotes import sentence_around

# alias -> why it is weak. Kept in one visible place so it can be argued with.
WEAK_ALIASES: dict[str, str] = {
    "rest": "ordinary English word ('the rest of the team')",
    "next": "ordinary English word ('next step')",
    "node": "ordinary English word ('node in the graph')",
    "tree": "ordinary English word",
    "express": "ordinary English word ('express interest')",
    "lambda": "'lambda function' is often Python, not AWS",
    "pipeline": "CI/CD or data pipeline — the word alone does not decide",
    "shell": "ordinary English word",
    "bash": "can mean 'a bash script' in any language context",
    "ml": "two letters, matches part of other tokens",
    "py": "two letters",
    "js": "two letters",
    "ts": "two letters",
    "go": "ordinary English verb",
    "api design": "often a phrase inside a longer requirement",
    "architecture": "used loosely about any code",
    "agent framework": "generic phrase",
}

MIN_TERM_LEN = 2  # below this nothing is matchable at all

# sections where a bare technology name is credible evidence
SKILL_SECTIONS = {"skills"}
USE_SECTIONS = {"experience", "projects"}

# section -> EvidenceType in contracts/ENUMS.md §5
EVIDENCE_TYPE = {
    "skills": "resume_skill_list",
    "projects": "resume_project",
    "experience": "resume_experience",
    "summary": "resume_summary",
    "education": "resume_summary",
    "certifications": "resume_summary",
}


@dataclass
class Mention:
    skill_id: str
    alias: str
    start: int
    end: int
    section: str
    weak: bool
    case_exact: bool
    quote: str
    quote_start: int
    quote_end: int

    @property
    def strength(self) -> float:
        if not self.weak:
            return 1.0
        return 0.55 if (self.case_exact or self.section in SKILL_SECTIONS) else 0.2


@dataclass
class SkillClaim:
    skill_id: str
    name: str
    category: str
    mentions: list[Mention]
    confidence: float
    claimed_level: str
    claim_basis: str

    @property
    def evidence(self) -> list[dict]:
        return [
            {
                "type": EVIDENCE_TYPE.get(m.section, "resume_summary"),
                "quote": m.quote,
                "section": m.section,
                "start": m.quote_start,
                "end": m.quote_end,
            }
            for m in self.mentions
        ]


def _pattern(alias: str) -> str:
    body = r"\s+".join(re.escape(part) for part in alias.split())
    return rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])"


@lru_cache(maxsize=1)
def _compiled() -> list[tuple[str, str, re.Pattern[str], bool]]:
    """(skill_id, alias, pattern, weak) for every term in the taxonomy."""
    rows: list[tuple[str, str, re.Pattern[str], bool]] = []
    for skill in taxonomy.load().values():
        for alias in skill.terms:
            if len(alias.strip()) < MIN_TERM_LEN:
                continue
            rows.append(
                (skill.id, alias, re.compile(_pattern(alias), re.IGNORECASE), alias.lower() in WEAK_ALIASES)
            )
    # longest first so "vector database" wins over "database" style overlaps
    rows.sort(key=lambda row: len(row[1]), reverse=True)
    return rows


def _in_noise_token(text: str, start: int, end: int) -> bool:
    """A match inside an email address or a URL is not evidence of skill.

    `github.com/example` in a contact line said nothing about how well someone
    uses Git; `aditya@example.com` says nothing about anything.
    """
    left = max(text.rfind(" ", 0, start), text.rfind("\n", 0, start), text.rfind("\t", 0, start))
    right_candidates = [i for i in (text.find(" ", end), text.find("\n", end), text.find("\t", end)) if i != -1]
    right = min(right_candidates) if right_candidates else len(text)
    token = text[left + 1 : right]
    if "@" in token or "://" in token or token.count("/") >= 1:
        return True
    return bool(re.fullmatch(r"[\w.-]+\.[a-z]{2,}", token.lower()))


def _same_sentence(text: str, left: tuple[int, int], right: tuple[int, int]) -> bool:
    gap = text[min(left[1], right[1]) : max(left[0], right[0])]
    return "\n" not in gap and len(gap) < 160


def find_mentions(text: str, section_list: list[sections_mod.Section] | None = None) -> list[Mention]:
    section_list = section_list or sections_mod.detect(text)
    raw: list[Mention] = []

    for skill_id, alias, pattern, weak in _compiled():
        for match in pattern.finditer(text):
            start, end = match.start(), match.end()
            if _in_noise_token(text, start, end):
                continue
            # "capitalised" means the document wrote it with a capital: REST, Next.js,
            # S3. Comparing to the alias string is not enough — a case-insensitive
            # match returns the document's own text, so it always looks "exact".
            exact = text[start].isupper()
            quote, qs, qe = sentence_around(text, start, end)
            raw.append(
                Mention(
                    skill_id=skill_id,
                    alias=alias,
                    start=start,
                    end=end,
                    section=sections_mod.section_of(section_list, start),
                    weak=weak,
                    case_exact=exact,
                    quote=quote,
                    quote_start=qs,
                    quote_end=qe,
                )
            )

    # drop weak mentions that nothing corroborates
    strong_spans: dict[str, list[tuple[int, int]]] = {}
    for mention in raw:
        if not mention.weak:
            strong_spans.setdefault(mention.skill_id, []).append((mention.start, mention.end))

    kept: list[Mention] = []
    for mention in raw:
        if mention.weak and mention.strength < 0.5:
            corroborated = any(
                _same_sentence(text, (mention.start, mention.end), span)
                for span in strong_spans.get(mention.skill_id, [])
            )
            if not corroborated:
                continue
        kept.append(mention)

    kept.sort(key=lambda m: m.start)
    return kept


def _confidence(mentions: list[Mention]) -> float:
    """Confidence in the *parse*, not in the person.

    "Listed in the skills section" and "used in a project bullet" are different
    kinds of evidence and should not both read 0.95; the UI sorts by this.
    """
    best = max(m.strength for m in mentions)
    in_use = any(m.section in USE_SECTIONS for m in mentions)
    base = 0.45 + 0.2 * best
    if in_use:
        base += 0.15
    base += min(0.02 * (len(mentions) - 1), 0.06)
    return round(min(base, 0.9), 2)


def claim_level(mentions: list[Mention]) -> tuple[str, str]:
    """What the document *claims* — never more than the document supports.

    A resume cannot claim "advanced". It can list a technology, or show it used in
    a project, and those are different amounts of evidence.
    """
    used = [m for m in mentions if m.section in USE_SECTIONS and not m.weak]
    if used:
        return "intermediate", f"named in {used[0].section} context"
    if any(m.section in SKILL_SECTIONS for m in mentions):
        return "listed", "appears in the skills list only"
    return "listed", "named in the document"


def claims_from(
    text: str, section_list: list[sections_mod.Section] | None = None, *, max_mentions: int = 3
) -> list[SkillClaim]:
    mentions = find_mentions(text, section_list)
    grouped: dict[str, list[Mention]] = {}
    for mention in mentions:
        grouped.setdefault(mention.skill_id, []).append(mention)

    vocab = taxonomy.load()
    claims: list[SkillClaim] = []
    for skill_id, group in grouped.items():
        # keep the most informative mentions, in document order
        group = sorted(group, key=lambda m: (-m.strength, m.start))[:max_mentions]
        group.sort(key=lambda m: m.start)
        skill = vocab[skill_id]
        level, basis = claim_level(group)
        claims.append(
            SkillClaim(
                skill_id=skill_id,
                name=skill.name,
                category=skill.category,
                mentions=group,
                confidence=_confidence(group),
                claimed_level=level,
                claim_basis=basis,
            )
        )
    claims.sort(key=lambda c: (-c.confidence, c.skill_id))
    return claims
