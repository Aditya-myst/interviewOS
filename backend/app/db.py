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

_engine = None
_Session: sessionmaker[Session] | None = None


def engine():
    """Lazily built so importing the app never opens a socket."""
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.database_configured:
            return None
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            connect_args={"connect_timeout": 8},
        )
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
