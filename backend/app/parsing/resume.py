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


def parse(document: Document) -> ParsedResume:
    section_list = sections_mod.detect(document.text)
    claims = matcher.claims_from(document.text, section_list)
    years, basis = _experience(document.text, section_list)

    by_level: dict[str, int] = {}
    for claim in claims:
        by_level[claim.claimed_level] = by_level.get(claim.claimed_level, 0) + 1

    quoted = sum(len(c.mentions) for c in claims)
    stats = {
        "chars": len(document.text),
        "pages": len(document.pages),
        "sections_detected": len(section_list),
        "skills_found": len(claims),
        "quotes": quoted,
        "by_claimed_level": by_level,
        "method": "deterministic (taxonomy aliases, no model)",
    }
    return ParsedResume(
        skills=claims,
        experience_years=years,
        experience_basis=basis,
        sections=[{"name": s.name, "header": s.header, "start": s.start, "end": s.end} for s in section_list],
        stats=stats,
        warnings=list(document.warnings),
    )
