"""Response models. They mirror contracts/types.ts field for field.

`extra="allow"` is deliberate: the contract can grow without the backend
crashing a demo, and the frontend is the thing that decides what it renders.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Loose(BaseModel):
    model_config = ConfigDict(extra="allow")


class ReadinessPoint(Loose):
    date: str
    readiness: float


class DashboardStats(Loose):
    verified_skills: int
    skills_total: int
    mock_interviews: int
    topics_done: int
    topics_total: int
    avg_interview_score: float | None = None


class CoverageRow(Loose):
    category: str
    verified: int
    developing: int
    unverified: int


class Dashboard(Loose):
    readiness: float
    readiness_label: str
    provisional: bool = False
    target_role: str | None = None
    readiness_history: list[ReadinessPoint] = []
    stats: DashboardStats
    coverage: list[CoverageRow]
    priority_skills: list[dict[str, Any]]
    interviews: list[dict[str, Any]]


class SkillProfile(Loose):
    provisional: bool = False
    counts: dict[str, int]
    skills: list[dict[str, Any]]
    coverage_by_category: list[CoverageRow] = []


class Roadmap(Loose):
    id: str
    status: str
    target_role: str | None = None
    summary: str
    progress: dict[str, int]
    topics: list[dict[str, Any]]


class HealthResponse(Loose):
    status: str
    env: str
    version: str
    mode: str


class CheckResult(Loose):
    ok: bool
    state: str
    detail: str | None = None


class ReadyResponse(Loose):
    status: str
    mode: str
    checks: dict[str, Any]


class ErrorBody(Loose):
    code: str
    message: str
    detail: str | None = None


class ErrorEnvelope(Loose):
    error: ErrorBody
