"""Resume section detection.

A skill mentioned in a `SKILLS` list is a claim; the same skill named inside a
project bullet is a claim *plus* a place it was used. That difference decides the
claimed level, so we have to know where we are in the document.

Headers are detected structurally (short line, no trailing punctuation, either
ALL CAPS or a known keyword) rather than by asking a model — this runs on every
document and must be reproducible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

SECTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "skills": (
        "skills", "technical skills", "core skills", "technologies", "tech stack",
        "technical proficiency", "competencies", "expertise", "tools",
    ),
    "experience": (
        "experience", "work experience", "professional experience", "employment",
        "internships", "internship", "career history",
    ),
    "projects": ("projects", "personal projects", "academic projects", "selected projects"),
    "education": ("education", "academic background", "academics"),
    "certifications": ("certifications", "certificates", "licenses", "awards", "achievements"),
    "summary": ("summary", "profile", "objective", "about", "about me"),
}

_ALIASES = {phrase: name for name, phrases in SECTION_KEYWORDS.items() for phrase in phrases}
_TRAILING_BAD = (".", ",", ";", ":")


@dataclass
class Section:
    name: str
    start: int
    end: int
    header: str


def _classify(line: str) -> str | None:
    stripped = line.strip().strip("#*").strip()
    if not stripped or len(stripped) > 60 or len(stripped.split()) > 6:
        return None
    if stripped.endswith(_TRAILING_BAD) and not stripped.endswith(":"):
        return None
    lowered = stripped.lower().rstrip(":").strip()
    if lowered in _ALIASES:
        return _ALIASES[lowered]
    # "SKILLS & TOOLS", "Technical Skills:", "PROJECTS — 2024"
    for phrase, name in _ALIASES.items():
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            return name
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) >= 3 and all(c.isupper() for c in letters):
        return "other"
    return None


def detect(text: str) -> list[Section]:
    lines = text.split("\n")
    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line) + 1

    headers: list[tuple[int, int, str, str]] = []
    for line, offset in zip(lines, offsets, strict=False):
        name = _classify(line)
        if name:
            headers.append((offset, offset + len(line), name, line.strip()))

    if not headers:
        return [Section("other", 0, len(text), "")]

    sections: list[Section] = []
    if headers[0][0] > 0:
        sections.append(Section("header", 0, headers[0][0], ""))
    for index, (start, _, name, header) in enumerate(headers):
        end = headers[index + 1][0] if index + 1 < len(headers) else len(text)
        sections.append(Section(name, start, max(start, end), header))
    return sections


def section_of(sections: list[Section], offset: int) -> str:
    for section in sections:
        if section.start <= offset < section.end:
            return section.name
    return "other"
