# Phase 4 — the API service

**Goal:** make the frontend's data come from a service that is honest about what it knows,
and put the two fragile external dependencies (Postgres, LLM) behind interfaces that can
fail visibly.

Everything in this phase is verifiable by curl in under a minute. Run
[backend/README.md](../backend/README.md) §2 and compare.

---

## What exists

| Piece | File | Verified how |
|---|---|---|
| Settings, fixture mode detection | `backend/app/config.py` | empty `DATABASE_URL` ⇒ `mode: fixture` in `/health` |
| 18 SQLAlchemy models | `backend/app/models.py` | `len(Base.metadata.tables) == 18`, matching `docs/sql/001_init.sql` |
| Lazy engine + status probe | `backend/app/db.py` | `/ready` reports `unconfigured` / `connected` + table count |
| Provider-agnostic LLM gateway | `backend/app/llm/gateway.py` | 5 tests: fallback, all-fail raises, cache hit, cache split, invalid JSON |
| Persistent cache | `backend/app/llm/cache.py` | `DbCache` when connected, `MemoryCache` otherwise |
| 9 routes | `backend/app/api/*.py` | `/openapi.json` path list |
| 21 tests, no network | `backend/tests/` | `uv run pytest` |

## Decisions worth defending

**1. Models reflect the schema; the app never creates it.**
`docs/sql/001_init.sql` is pasted into Supabase by hand. If the app called `create_all`,
the deployed schema and the reviewed SQL would drift silently and the "database via
handover" rule would be a fiction. Consequence: a wrong column is a hard failure at query
time, not a self-healing migration.

**2. Degraded is a first-class state, not an error.**
`/ready` returns **200** with `status: degraded` when there is no database but the fixtures
are present, and **503** only when neither exists. This is what lets a recruiter see the
product working before any cloud project is created.

**3. The gateway has no canned-answer rung.**
The tempting design ends with "if both providers fail, return a helpful static message".
That turns an outage into a lie the UI cannot detect. Instead `LLMUnavailable` carries
`gemini: rate limited; groq: timeout` and the route maps it to `503 llm_unavailable`.

**4. Invalid JSON is a failure, not a cache entry.**
The gateway takes a `validator` callable. If a provider returns prose instead of the schema,
that response is discarded, the next provider is tried, and nothing is written to cache —
so one bad generation cannot poison every future call for the same prompt.

## Measured, not assumed (2026-11-01, first live run)

| Observation | What it changed |
|---|---|
| `gemini-2.5-flash` → `404 no longer available to new users` | model names resolve from the provider's live list; `GEMINI_MODEL=auto` |
| `llama-3.3-70b-versatile` → `404 does not exist or you do not have access` | `GROQ_MODEL=auto`, largest open-weight model wins |
| Gemini read-timed-out at **45 s** twice; Groq answered in **2.7 s** | default order flipped to groq → gemini, `LLM_TIMEOUT_S=25` |
| second (cached) call still waited 45 s for the dead primary | cache is searched across the whole chain before any network call |
| both providers down | `/dev/llm` returned both reasons; nothing was invented |

## The honest gap (unchanged by this phase)

`/v1/*` routes still read `contracts/fixtures/*.json`. They are shaped exactly like the
pipeline output and are labelled `X-Data-Source: fixture` on every response — so the day
Phase 5 writes rows, the header flips to `database` and no frontend code changes.

That fixture set is itself recorded data: the numbers come from the seeded taxonomy
(31 skills / 100 subtopics, band thresholds computed in code) and the resource URLs from a
40/40-alive link audit (`scripts/check_links.py`). Phase 5 replaces *authorship*, not shape.

## Not done, deliberately

- No auth/RLS enforcement in the API yet — RLS policies exist in SQL; the service uses the
  session credentials and will move to per-user JWT claims in Phase 5.
- No background workers. Ingestion is request/response until there is a real document to
  process.
- No `/v1` write routes. Nothing writes to the database until the pipeline can produce
  evidenced rows.

## Next

Phase 5 — resume parse → JD parse → skill merge → priority scoring → evidence gate, with
every extraction holding a `quote` span so `/v1/skills/profile` can be backed by rows
instead of a fixture.
