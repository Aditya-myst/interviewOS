"""Fixture access.

Phase 3–4 reads come from contracts/fixtures — the same JSON the UI already
renders. When the pipeline exists these reads move to SQL; the response shape
does not change, which is why the frontend can switch on its own schedule.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import FIXTURE_DIR

FIXTURES = ("dashboard", "skill_profile", "roadmap", "preparation_plan", "interview_report")


class FixtureMissing(RuntimeError):
    pass


@lru_cache
def load(name: str) -> dict[str, Any]:
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():
        raise FixtureMissing(f"{path} is missing — is the repo root intact?")
    return json.loads(path.read_text())


def available() -> dict[str, bool]:
    return {name: (FIXTURE_DIR / f"{name}.json").exists() for name in FIXTURES}
