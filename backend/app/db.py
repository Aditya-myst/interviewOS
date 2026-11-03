"""Database access.

The schema is owned by docs/sql/001_init.sql — these models *reflect* it, they
never create it. `create_all` is deliberately absent: two sources of truth for a
schema is how a project ends up with drift nobody can explain.

When DATABASE_URL is empty the app runs in fixture mode: reads come from
contracts/fixtures, writes are refused with `degraded_mode`. That keeps the
frontend unblocked before a database exists and keeps the honesty honest — the
UI can tell the user which mode it is looking at.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

log = logging.getLogger(__name__)

# Module name -> the package that provides it, so the message tells the truth for
# whichever driver the URL asks for.
DRIVER_PACKAGES = {
    "psycopg2": "psycopg2-binary",
    "psycopg": "psycopg[binary]",
    "asyncpg": "asyncpg",
    "pg8000": "pg8000",
}

_engine = None
_Session: sessionmaker[Session] | None = None
# Why the engine could not be built, if it could not. Kept so /ready can say it
# instead of the process dying during startup.
_engine_error: dict[str, str] | None = None


def engine():
    """Lazily built so importing the app never opens a socket.

    Returns None when the database is absent *or unusable* — a missing driver is a
    configuration fact, not a reason to refuse to start. The reason lands in
    `_engine_error` so /ready and the startup log can report it.
    """
    global _engine, _engine_error
    if _engine is not None:
        return _engine
    if _engine_error is not None:
        return None  # already explained once; do not repeat the warning on every request
    settings = get_settings()
    if not settings.database_configured:
        return None
    try:
        _engine = create_engine(
            settings.sqlalchemy_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            connect_args={"connect_timeout": 8},
        )
    except ModuleNotFoundError as exc:
        missing = exc.name or "the configured driver"
        hint = DRIVER_PACKAGES.get(missing, missing)
        _engine_error = {
            "state": "driver_missing",
            "detail": (
                f"DATABASE_URL is set but the {missing} driver is not installed — "
                f'run `pip install "{hint}"` or `uv sync` in backend/. '
                "Serving fixtures until then."
            ),
        }
        log.warning(_engine_error["detail"])
        return None
    except Exception as exc:  # noqa: BLE001 — a bad URL is information, not a crash
        _engine_error = {"state": "error", "detail": f"{type(exc).__name__}: {exc}"}
        log.warning("database engine could not be built — %s", _engine_error["detail"])
        return None
    return _engine


def session_factory() -> sessionmaker[Session] | None:
    global _Session
    if _Session is None and engine() is not None:
        _Session = sessionmaker(bind=engine(), expire_on_commit=False)
    return _Session


@contextmanager
def get_session() -> Iterator[Session]:
    factory = session_factory()
    if factory is None:
        raise RuntimeError("database not configured — fixture mode")
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def db_status() -> dict:
    """What /ready reports. Never raises: a broken database is information."""
    settings = get_settings()
    if not settings.database_configured:
        return {
            "ok": False,
            "state": "unconfigured",
            "detail": "DATABASE_URL is empty — serving fixtures",
        }

    eng = engine()
    if eng is None:
        return {"ok": False, "state": "error", "detail": "engine could not be built", **(_engine_error or {})}
    try:
        with eng.connect() as conn:
            tables = conn.execute(
                text(
                    "select count(*) from information_schema.tables "
                    "where table_schema = 'public' and table_type = 'BASE TABLE'"
                )
            ).scalar_one()
            version = conn.execute(text("show server_version")).scalar_one()
        return {
            "ok": True,
            "state": "connected",
            "tables": int(tables),
            "server_version": str(version),
            "migrations": "applied" if int(tables) >= 18 else "missing",
        }
    except Exception as exc:  # noqa: BLE001 — the reason matters more than the type
        return {"ok": False, "state": "error", "detail": f"{type(exc).__name__}: {exc}"}
