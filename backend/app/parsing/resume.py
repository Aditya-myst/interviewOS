"""Resume → claimed skills, with a span behind every one of them.

This is the deterministic pass. It runs with no model, no quota and no network, so
the profile it produces can always be produced again — which matters when the same
resume must yield the same plan tomorrow as it did today.

The model's job (later in the pipeline) is to *extend* this, and every extension
goes through the same quote gate.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field

from app.parsing import matcher
from app.parsing import sections as sections_mod
from app.parsing.extract import Document

SKILL_LINE_PREFIX = re.compile(
    r"^(languages?|technical skills?|skills?|tools?|technologies|tech stack|frameworks?|"
    r"libraries|platforms?|databases?|cloud|devops|ai/ml|data)\s*[:\-]\s*",
    re.IGNORECASE,
)
SEGMENT_SPLIT = re.compile(r"[,|•·;]|\s{3,}")
# "Marketing: HubSpot" and "Analytics: Excel" are one category prefix on a list, not
# a skill named "Marketing: HubSpot"
CATEGORY_PREFIX = re.compile(r"^[A-Za-z][A-Za-z /&+-]{1,22}:\s*")
NOT_A_SKILL = {"and", "or", "etc", "other", "others", "misc", "n/a", "none", "all"}

YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", re.IGNORECASE)
RANGE_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|2\d)\d{2}|present|current)",
                      re.IGNORECASE)


@dataclass
class ParsedResume:
    skills: list[matcher.SkillClaim]
    experience_years: float | None
    experience_basis: str
    sections: list[dict]
    stats: dict
    warnings: list[str] = field(default_factory=list)

    def as_json(self) -> dict:
        return {
            "skills": [
                {
                    "skill_id": c.skill_id,
                    "name": c.name,
                    "category": c.category,
                    "claimed_level": c.claimed_level,
                    "claim_basis": c.claim_basis,
                    "confidence": c.confidence,
                    "in_resume": True,
                    "evidence": c.evidence,
                }
                for c in self.skills
            ],
            "experience_years": self.experience_years,
            "experience_basis": self.experience_basis,
            "sections": self.sections,
            "stats": self.stats,
            "warnings": self.warnings,
        }


WORK_SECTIONS = ("experience", "projects")


def _experience(
    text: str, section_list: list[sections_mod.Section]
) -> tuple[float | None, str]:
    """Years of experience, from work evidence only.

    The first version of this read the education line "B.Tech, 2023 - 2027" and
    reported four years of experience for a student. Degree dates are not work
    dates, and a future end year is not history.
    """
    this_year = datetime.date.today().year
    work = [s for s in section_list if s.name in WORK_SECTIONS]
    scoped = "\n".join(text[s.start : s.end] for s in work) if work else ""
    where = "work sections" if scoped else "document"

    stated = [float(m.group(1)) for m in YEARS_RE.finditer(scoped or text)]
    stated = [y for y in stated if 0 < y <= 45]
    if stated:
        return max(stated), f"stated in the {where}"

    spans: list[tuple[int, int]] = []
    for match in RANGE_RE.finditer(scoped):
        start_year = int(match.group(1))
        end_raw = match.group(2).lower()
        end_year = this_year if end_raw in ("present", "current") else int(end_raw)
        if 1980 <= start_year <= end_year <= this_year + 1:
            spans.append((start_year, end_year))
    if spans:
        earliest = min(s for s, _ in spans)
        latest = max(e for _, e in spans)
        return float(latest - earliest), (
            f"computed from date ranges in the {where} (earliest {earliest}, latest {latest})"
        )

    return None, "not stated — no explicit years and no readable work date ranges"


def vocabulary_gaps(
    text: str, section_list: list[sections_mod.Section], matched_terms: set[str], *, limit: int = 40
) -> list[str]:
    """What the resume lists that our vocabulary does not know.

    This is the measurement that turns "only 2 skills found" from a mystery into a
    diff. A skills section saying "HubSpot, Zoho, SEO" against a taxonomy of 31
    engineering skills is not a parser bug — it is a vocabulary gap, and printing
    the gap is more honest than silently finding nothing.
    """
    gaps: list[str] = []
    seen: set[str] = set()

    for section in section_list:
        if section.name not in ("skills", "requirements"):
            continue
        body = text[section.start : section.end]
        for raw_line in body.split("\n"):
            if raw_line.strip() == section.header.strip():
                continue                                  # the heading is not a skill
            line = SKILL_LINE_PREFIX.sub("", raw_line.strip()).strip(" -–—:")
            line = CATEGORY_PREFIX.sub("", line).strip()
            if not line or len(line) > 200:
                continue
            for piece in SEGMENT_SPLIT.split(line):
                term = piece.strip(" .-–—:()[]")
                key = term.lower()
                if not (2 <= len(term) <= 32) or key in seen or key in NOT_A_SKILL:
                    continue
                if any(term.lower() in matched.lower() or matched.lower() in key for matched in matched_terms if matched):
                    continue
                if term.replace(".", "").isdigit():
                    continue
                seen.add(key)
                gaps.append(term)
                if len(gaps) >= limit:
                    return gaps
    return gaps


def parse(document: Document) -> ParsedResume:
    section_list = sections_mod.detect(document.text)
    claims = matcher.claims_from(document.text, section_list)
    years, basis = _experience(document.text, section_list)

    by_level: dict[str, int] = {}
    for claim in claims:
        by_level[claim.claimed_level] = by_level.get(claim.claimed_level, 0) + 1

    matched_terms = {m.alias for c in claims for m in c.mentions}
    gaps = vocabulary_gaps(document.text, section_list, matched_terms)

    quoted = sum(len(c.mentions) for c in claims)
    stats = {
        "chars": len(document.text),
        "pages": len(document.pages),
        "sections_detected": len(section_list),
        "skills_found": len(claims),
        "quotes": quoted,
        "by_claimed_level": by_level,
        "method": "deterministic (taxonomy aliases, no model)",
        # empty list, not None: "no gaps" and "not measured" must not look alike
        "vocabulary_gaps": gaps,
        "vocabulary_note": (
            "terms your skills sections list that the 31-skill taxonomy does not know"
            if gaps else "every listed term matched the taxonomy"
        ),
    }
    return ParsedResume(
        skills=claims,
        experience_years=years,
        experience_basis=basis,
        sections=[{"name": s.name, "header": s.header, "start": s.start, "end": s.end} for s in section_list],
        stats=stats,
        warnings=list(document.warnings),
    )
