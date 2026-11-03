"""A configured-but-unusable database must not stop the API from starting.

This is the failure a real user hit on Windows: DATABASE_URL pointed at Supabase,
psycopg2 was not installed, and the app died during lifespan before serving a single
request. A credential or driver problem is a state to report, not a crash.
"""
from __future__ import annotations

import pytest

from app import db as db_module
from app.config import Settings


@pytest.fixture(autouse=True)
def _reset_engine(monkeypatch):
    monkeypatch.setattr(db_module, "_engine", None)
    monkeypatch.setattr(db_module, "_Session", None)
    monkeypatch.setattr(db_module, "_engine_error", None)
    yield


def test_a_bare_postgres_url_names_the_driver_we_ship():
    settings = Settings(database_url="postgres://u:p@host:5432/db")
    assert settings.sqlalchemy_url == "postgresql+psycopg://u:p@host:5432/db"


def test_an_explicit_driver_is_left_alone():
    settings = Settings(database_url="postgresql+asyncpg://u:p@host/db")
    assert settings.sqlalchemy_url == "postgresql+asyncpg://u:p@host/db"


def test_a_missing_driver_returns_no_engine_and_a_reason(monkeypatch):
    monkeypatch.setattr(db_module, "get_settings", lambda: Settings(database_url="postgresql+nosuchdriver://u@host/db"))

    assert db_module.engine() is None
    status = db_module.db_status()
    assert status["ok"] is False
    assert status["state"] in ("driver_missing", "error")
    assert "nosuchdriver" in status["detail"]


def test_the_api_reports_degraded_and_still_serves_fixtures(monkeypatch):
    """The whole point: boot, then serve. /ready says why it is in fixture mode."""
    from fastapi import Response

    from app.api import system

    monkeypatch.setattr(
        db_module, "get_settings", lambda: Settings(database_url="postgresql+nosuchdriver://u@host/db")
    )
    ready = system.ready(Response())

    assert ready.mode == "fixture"
    assert ready.checks["database"]["state"] in ("driver_missing", "error")
