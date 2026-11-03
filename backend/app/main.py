"""InterviewOS API.

Boots with an empty .env on purpose: `/health` answers immediately, `/ready`
reports exactly what is missing, and every read endpoint serves the same fixtures
the UI already renders. A backend that refuses to start without credentials is a
backend nobody can review.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import JSONResponse as _StarletteJSON


class UTF8JSONResponse(_StarletteJSON):
    """JSON that declares its encoding.

    RFC 8259 says JSON is UTF-8, so most clients assume it — the browser does, and curl
    does. Windows PowerShell 5.1 does not: without a charset it decodes the bytes as
    latin-1, and every curly quote and em dash in a resume quote arrives as "â€œ". The
    header costs nothing and stops that.
    """

    media_type = "application/json; charset=utf-8"

from app.api import assessment, interview, pipeline, prep, system
from app.config import get_settings
from app.fixtures import FixtureMissing
from app.llm import LLMUnavailable, get_gateway

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("interviewos")


def create_app() -> FastAPI:
    settings = get_settings()
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        from app.db import db_status

        status = db_status()
        data = "database" if status["state"] == "connected" else "fixture"
        if status["state"] not in ("connected", "unconfigured"):
            log.warning("database configured but unusable (%s) — serving fixtures", status.get("detail"))
        try:
            llm = ", ".join(get_gateway().available_providers()) or "none"
        except Exception as exc:  # noqa: BLE001 — a key problem is not a startup failure
            llm = f"unavailable ({type(exc).__name__})"
        log.info("interviewos ready — env=%s data=%s llm=%s", settings.env, data, llm)
        yield

    app = FastAPI(
        title="InterviewOS API",
        default_response_class=UTF8JSONResponse,
        lifespan=lifespan,
        version=system.VERSION,
        description=(
            "Evidence-gated preparation plans. Every skill status has a quote "
            "behind it, or it is marked unverified."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Data-Source"],
    )

    app.include_router(system.router)
    app.include_router(prep.router, prefix="/v1")
    app.include_router(pipeline.router, prefix="/v1")
    app.include_router(interview.router, prefix="/v1")
    app.include_router(assessment.router, prefix="/v1")

    @app.exception_handler(LLMUnavailable)
    async def _llm_unavailable(_: Request, exc: LLMUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "llm_unavailable",
                    "message": "No model provider could answer this request.",
                    "detail": str(exc),
                }
            },
        )

    @app.exception_handler(FixtureMissing)
    async def _fixture_missing(_: Request, exc: FixtureMissing) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "degraded_mode",
                    "message": "Fixture data is missing and no database is configured.",
                    "detail": str(exc),
                }
            },
        )

    return app


app = create_app()
