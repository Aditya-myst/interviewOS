"""The vocabulary, loaded from data/taxonomy.yaml — not from code.

If parsing can only recognise skills listed in a Python file, then adding a skill
means editing the parser. Here the taxonomy is data: 41 skills, 137 subtopics, and
the aliases that the matcher turns into patterns.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import yaml

from app.config import DATA_DIR


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    category: str
    aliases: tuple[str, ...]
    interview_relevance: float
    subtopic_ids: tuple[str, ...]

    @property
    def terms(self) -> tuple[str, ...]:
        """The name itself is always a term; aliases add spellings."""
        return tuple(dict.fromkeys((self.name, *self.aliases)))


@lru_cache(maxsize=1)
def load() -> dict[str, Skill]:
    path = DATA_DIR / "taxonomy.yaml"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing — the parser has no vocabulary")
    raw = yaml.safe_load(path.read_text()) or {}
    skills: dict[str, Skill] = {}
    for row in raw.get("skills", []):
        skills[row["id"]] = Skill(
            id=row["id"],
            name=row["name"],
            category=row.get("category", "Other"),
            aliases=tuple(row.get("aliases") or ()),
            interview_relevance=float(row.get("interview_relevance", 0.5)),
            subtopic_ids=tuple(t.get("id", "") for t in row.get("subtopics") or []),
        )
    if not skills:
        raise ValueError(f"{path} parsed to zero skills")
    return skills


def categories() -> dict[str, str]:
    return {skill.id: skill.category for skill in load().values()}
