"""JD → requirements. Same deterministic matcher as the resume, different sections.

A job description says two different things and they must not be mixed:
"you must have RAG experience" (required) and "nice to have: LangGraph" (preferred).
Both name the same skill; only one of them should pull a topic to the top of the
plan. So the section a mention sits in decides `requirement_type`, and the model is
not asked to guess.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.parsing import matcher, taxonomy
from app.parsing import sections as sections_mod

EXPERT_SIGNALS = ("expert", "extensive", "at scale", "years of", "production")
ADVANCED_SIGNALS = ("strong", "deep", "solid", "proven", "comfortable with")
# "Kubernetes is a plus" inside a Requirements block is still a nice-to-have.
PREFERRED_INLINE = ("is a plus", "a plus", "bonus", "nice to have", "good to have", "preferred")
SENIORITY_WORDS = {"intern": "intern", "junior": "junior", "mid": "mid", "senior": "senior",
                   "staff": "staff", "lead": "lead", "principal": "principal"}
YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*years?", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*(?:[-•*·–—]|\d+[.)])\s+(.*\S)", re.MULTILINE)


@dataclass
class Requirement:
    skill_id: str
    name: str
    requirement_type: str          # required | preferred
    jd_importance: float
    expected_level: str
    mentions: int
    evidence: list[dict] = field(default_factory=list)


@dataclass
class ParsedJD:
    title: str | None
    company: str | None
    role: str | None
    seniority: str | None
    min_years_experience: float | None
    requirements: list[Requirement]
    topics: list[str]
    interview_rounds: list[str]
    rounds_inferred: bool
    stats: dict

    def as_json(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "role": self.role,
            "seniority": self.seniority,
            "min_years_experience": self.min_years_experience,
            "parse_status": "ok",
            "rounds_inferred": self.rounds_inferred,
            "interview_rounds": self.interview_rounds,
            "topics": self.topics,
            "requirements": [
                {
                    "skill_id": r.skill_id,
                    "name": r.name,
                    "requirement_type": r.requirement_type,
                    "jd_importance": r.jd_importance,
                    "expected_level": r.expected_level,
                    "mentions": r.mentions,
                    "evidence": r.evidence,
                }
                for r in self.requirements
            ],
            "stats": self.stats,
        }


SECTION_KIND = {
    "requirements": "required",
    "skills": "required",
    "preferred": "preferred",
    "responsibilities": "responsibility",
}


def _heading_kind(text: str, section_list: list[sections_mod.Section]) -> dict[int, str]:
    """Map each section to required / preferred / responsibility / other.

    The section detector already does the structural work ("Requirements" and
    "Nice to have" are headings in both a resume and a JD); this only names what
    each section means for a job description.
    """
    kinds: dict[int, str] = {}
    for index, section in enumerate(section_list):
        kinds[index] = SECTION_KIND.get(section.name, "other")
    return kinds


def _section_index(section_list: list[sections_mod.Section], offset: int) -> int:
    for index, section in enumerate(section_list):
        if section.start <= offset < section.end:
            return index
    return 0


def _expected_level(quote: str, requirement_type: str) -> str:
    lowered = quote.lower()
    if any(signal in lowered for signal in PREFERRED_INLINE):
        return "intermediate"
    if any(signal in lowered for signal in EXPERT_SIGNALS):
        return "expert"
    if any(signal in lowered for signal in ADVANCED_SIGNALS):
        return "advanced"
    return "advanced" if requirement_type == "required" else "intermediate"


_LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}


def _importance(requirement_type: str, mentions: int) -> float:
    if requirement_type == "required":
        return round(min(0.65 + 0.07 * mentions, 0.95), 2)
    return round(min(0.35 + 0.05 * mentions, 0.65), 2)


def _rounds(text: str, requirements: list[Requirement]) -> tuple[list[str], bool]:
    """Inferred, and labelled as inferred. 'rounds_inferred: true' is the contract's
    way of telling the UI not to present this as fact."""
    lowered = text.lower()
    skills = {r.skill_id for r in requirements}
    rounds: list[str] = ["technical"]
    if "system-design" in skills or "architecture" in lowered or "design" in lowered:
        rounds.append("system_design")
    if "data-structures" in skills or "algorithms" in skills or "coding" in lowered:
        rounds.append("coding")
    if "behavioral" in lowered or "stakeholder" in lowered or "communication" in lowered:
        rounds.append("behavioral")
    return rounds, True


def _topics(text: str, section_list: list[sections_mod.Section], kinds: dict[int, str]) -> list[str]:
    topics: list[str] = []
    for index, section in enumerate(section_list):
        if kinds.get(index) not in ("responsibility", "required"):
            continue
        body = text[section.start : section.end]
        for match in BULLET_RE.finditer(body):
            line = " ".join(match.group(1).split())
            if 12 <= len(line) <= 160:
                topics.append(line)
    return topics[:8]


def parse(text: str) -> ParsedJD:
    section_list = sections_mod.detect(text)
    kinds = _heading_kind(text, section_list)
    mentions = matcher.find_mentions(text, section_list)
    vocab = taxonomy.load()

    grouped: dict[str, list[matcher.Mention]] = {}
    for mention in mentions:
        grouped.setdefault(mention.skill_id, []).append(mention)

    requirements: list[Requirement] = []
    for skill_id, group in grouped.items():
        in_required = any(kinds.get(_section_index(section_list, m.start)) == "required" for m in group)
        in_preferred = any(kinds.get(_section_index(section_list, m.start)) == "preferred" for m in group)
        # a skill named in the requirements section is required even if it also
        # appears in "nice to have" — the stronger claim wins, and that is stated
        # section decides first, then the sentence itself gets a veto:
        # "Experience with Docker; Kubernetes is a plus" sits in Requirements
        says_plus = any(
            any(signal in m.quote.lower() for signal in PREFERRED_INLINE) for m in group
        )
        if says_plus:
            requirement_type = "preferred"
        elif in_required:
            requirement_type = "required"
        elif in_preferred:
            requirement_type = "preferred"
        else:
            requirement_type = "required"
        # cite the requirement line before the job title: "AI Engineer (LLM
        # Applications)" mentioning LLM is true but proves nothing about the bar
        kind_rank = {"required": 0, "preferred": 1, "responsibility": 2, "other": 3}
        group = sorted(
            group,
            key=lambda m: (kind_rank.get(kinds.get(_section_index(section_list, m.start), "other"), 3), m.start),
        )
        # the strongest wording anywhere in the JD sets the bar, not the first one
        expected = max(
            (_expected_level(m.quote, requirement_type) for m in group),
            key=lambda level: _LEVEL_RANK.get(level, 0),
        )
        requirements.append(
            Requirement(
                skill_id=skill_id,
                name=vocab[skill_id].name,
                requirement_type=requirement_type,
                jd_importance=_importance(requirement_type, len(group)),
                expected_level=expected,
                mentions=len(group),
                evidence=[
                    {
                        "type": "resume_skill_list",
                        "quote": m.quote,
                        "section": m.section,
                        "start": m.quote_start,
                        "end": m.quote_end,
                    }
                    for m in group[:2]
                ],
            )
        )

    requirements.sort(key=lambda r: (-r.jd_importance, r.skill_id))
    rounds, inferred = _rounds(text, requirements)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    title = lines[0] if lines and len(lines[0]) <= 90 else None
    company = None
    for line in lines[:6]:
        match = re.search(r"\bat\s+([A-Z][\w&.\- ]{2,40})", line)
        if match:
            company = match.group(1).strip()
            break

    seniority = None
    for word, label in SENIORITY_WORDS.items():
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            seniority = label
            break
    years = [float(m.group(1)) for m in YEARS_RE.finditer(text)]
    years = [y for y in years if 0 < y <= 25]

    return ParsedJD(
        title=title,
        company=company,
        role=title.split("(")[0].strip() if title else None,
        seniority=seniority,
        min_years_experience=max(years) if years else None,
        requirements=requirements,
        topics=_topics(text, section_list, kinds),
        interview_rounds=rounds,
        rounds_inferred=inferred,
        stats={
            "chars": len(text),
            "sections_detected": len(section_list),
            "section_kinds": {section_list[i].header or "(top)": kinds[i] for i in kinds},
            "requirements_found": len(requirements),
            "required": sum(1 for r in requirements if r.requirement_type == "required"),
            "preferred": sum(1 for r in requirements if r.requirement_type == "preferred"),
            "method": "deterministic (taxonomy aliases, no model)",
        },
    )
