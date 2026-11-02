# InterviewOS backend

FastAPI service that the Next.js frontend consumes. It implements
`contracts/openapi.yaml` — it never invents a field the contract does not have.

**The rule this service is built around: it does not lie about its own state.** If there is
no database, `/ready` says `degraded`. If there is no LLM key, LLM routes return
`llm_unavailable` with a per-provider reason instead of a canned answer. Every data response
carries `X-Data-Source` so you can tell fixture output from real pipeline output without
reading any code.

---

## 1. Run it (PowerShell, Windows 11)

From the **repo root**:

```powershell
cd backend
uv sync                                    # or: python -m pip install -e .
uv run uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000/docs> — every route below is there with its schema.

No `.env` needed to boot. With no `DATABASE_URL` and no LLM keys the service starts in
**fixture mode**, which is the honest, fully-working demo state.

## 2. Prove what you are looking at

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/ready
curl.exe -i http://localhost:8000/v1/analytics/dashboard   # note X-Data-Source: fixture
curl.exe http://localhost:8000/dev/db                          # expected vs actual, no psql
# PowerShell note: single quotes around the JSON body. Backslash is NOT an escape
# character in PowerShell, so \" breaks the argument and curl ends up with a
# fragment like `tFormat` and asks for a host password. Nothing is wrong with the API.
curl.exe -X POST http://localhost:8000/dev/llm -H "content-type: application/json" -d '{"prompt":"hello"}'

# Or let PowerShell build the JSON, which cannot be mangled by quoting:
$body = @{ prompt = 'reply with only the word ok'; json_mode = $true } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/dev/llm -Method Post -ContentType 'application/json' -Body $body
```

Expected with nothing configured:

| Call | Answer | Why |
|---|---|---|
| `GET /health` | `200 {"status":"ok","mode":"fixture"}` | Liveness only. Touches no dependency, so it never flaps. |
| `GET /ready` | `200 {"status":"degraded", checks:{database:unconfigured, fixtures:present, llm:unconfigured}}` | Degraded ≠ broken: fixtures are present, so the product still demos. |
| `GET /v1/analytics/dashboard` | `200`, `X-Data-Source: fixture`, `readiness 42`, 7 history points | Reads `contracts/fixtures/dashboard.json` verbatim. |
| `GET /v1/analytics/dashboard?state=empty` | `200`, zeros | A real empty payload, not a 404 — the UI has an empty state to render. |
| `POST /dev/llm` | `503 llm_unavailable`, `configured: []`, `detail: "gemini: not configured; groq: not configured"` | The gateway refuses rather than fabricating. |
| `GET /nope` | `404` | |

## 3. Flip to the real database

The schema is **handed over, not auto-migrated** — `docs/sql/001_init.sql`, `002_seed.sql`,
`003_storage.sql` are pasted into the Supabase SQL editor by you, and the models here
*reflect* that schema. The app never calls `create_all`, so it can never quietly invent a
table that disagrees with `docs/sql/`.

```powershell
# .env at the repo root
DATABASE_URL=postgresql+psycopg://postgres.<ref>:<pw>@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

Restart, then prove it landed without opening psql:

```powershell
curl.exe http://localhost:8000/dev/db
```

Every check comes back with `expected` and `actual` side by side — `tables 18`,
`rls_tables 18`, `enums 22`, `extensions 3`, `skills 31`, `subtopics 100`,
`resources 39`. A wrong Supabase project shows up as a named failure, not a shrug.

`GET /ready` flips from

```
"database": {"ok": false, "state": "unconfigured"}
```

to

```
"status": "ready", "checks": {"database": {"ok": true, "state": "connected", "detail": "18 tables, PostgreSQL 15.x"}}
```

Two more things change the moment it connects, with no code edit:

- The LLM cache switches from `MemoryCache` (per-process, lost on restart) to `DbCache`,
  which persists in `public.llm_cache` with `on conflict` upsert.
- `X-Data-Source` stays `fixture` until the Phase 5 pipeline writes real rows — it is
  driven by the data path, not by whether a database exists.

## 4. LLM gateway

One interface, two free providers, no paid tier:

```
prompt ──▶ cache ──hit──▶ return (no network, no quota spent)
             │miss
             ├─▶ primary (Gemini 2.5 Flash, raw httpx generateContent)
             │        └─ invalid JSON or error ──▶ not cached, next provider
             └─▶ fallback (Groq, chat/completions)
                      └─ all exhausted ──▶ LLMUnavailable(reasons)
```

- Cache key is `sha256(model | schema_version | prompt)` — bumping `schema_version`
  invalidates every cached answer for that schema without deleting rows.
- A provider that returns unparseable JSON is a **failure**, not a cache entry.
- There is deliberately **no** "return canned text if everything fails" step. The failure
  carries each provider's reason so the UI can say why.
- A provider failure reports **the provider's own sentence** — `HTTP 400:
  INVALID_ARGUMENT: API key not valid.` — not httpx's `Client error '400 Bad Request'`,
  which throws the response body away. That body is the only place the reason lives.
- **Model names are not hard-coded.** `GEMINI_MODEL`/`GROQ_MODEL` default to `auto`: the
  app asks the provider which models the key can call (`GET /dev/llm/models`) and picks a
  stable Flash / a large open-weight model via a scoring function that is unit-tested.
  A name that was valid last quarter answers `404 ... no longer available to new users`,
  which is out-of-date code, not a broken app.
- **Cache is searched chain-wide before any network call.** Measured bug: primary timed
  out at 45 s, the fallback had the answer cached, and the cached call still cost 45 s
  because the primary was tried first. A cache hit answers in 0 ms even while the primary
  is dead — there is a test for exactly that.
- `GEMINI_THINKING=off` sends `thinkingBudget: 0`; Gemini can otherwise spend tens of
  seconds deciding how hard to think about "reply with ok".
- `GET /dev/llm` shows the chain, the resolved model and its source (`env` or `auto`), the
  cache backend, and the last 4 characters of each key — spending no quota. Use it first
  when a probe fails.
- `POST /dev/llm` is a probe for exactly this and returns 404 when `ENV=prod`. Its
  `error.attempts[]` carries one `{provider, error, ms}` row per provider tried.

## 4b. The pipeline, without the API

```powershell
cd backend
uv run python -m app.cli parse "C:\Users\you\resume.pdf"      # skills + the line behind each
uv run python -m app.cli parse resume.pdf --json               # same, machine-readable
uv run python -m app.cli analyze resume.pdf jd.txt             # scored profile, no DB
```

No model, no network, no quota: taxonomy aliases and document structure. Every claim it
makes carries a `quote` you can find with Ctrl-F in the original file. `--json` output is
the exact shape `/v1/skills/profile` returns, which is how the fixture was always meant to
be replaced — same keys, real provenance.

## 5. Routes

| Method | Path | Source today |
|---|---|---|
| GET | `/health` | in-process |
| GET | `/ready` | live: DB connect attempt, fixture presence, LLM keys |
| GET | `/dev/db` | live: JSON twin of `docs/sql/004_verify.sql` — expected vs actual per check |
| POST | `/dev/llm` | live: gateway probe |
| GET | `/v1/analytics/dashboard` | fixture → Phase 5: aggregated from `sessions`, `skill_evidence` |
| POST | `/v1/resume/upload` | live: parse a PDF/DOCX/txt; persists when the DB is connected |
| POST | `/v1/jd/analyze` | live: parse a JD, rescore against the stored resume |
| GET | `/v1/resume/latest` | live: last stored resume (503 in fixture mode) |
| GET | `/v1/skills/profile` | **rows from `candidate_skills` when present**, fixtures otherwise |
| GET | `/v1/learning/roadmap` | fixture → Phase 6: `roadmap_topics` + `resources` |
| GET | `/v1/preparation/latest` | fixture → Phase 6 |
| GET | `/v1/interview/{session_id}/report` | fixture → Phase 7: `interview_sessions` + `turns` |

## 6. Tests

```powershell
cd backend
uv run pytest            # 78 tests, no network, no database
uv run ruff check .
```

The suite tests the *honesty* properties, not just status codes: `/ready` reports degraded
rather than failing, the empty state is a real payload, every assessed skill has
non-empty evidence, every roadmap topic has three roles or an explicit gap, a provider
returning invalid JSON is not cached, and a total provider failure raises instead of
inventing text.

## 7. Layout

```
app/config.py       settings; empty DATABASE_URL ⇒ fixture mode
app/db.py           lazy engine, db_status(); no create_all, by design
app/models.py       18 SQLAlchemy models reflecting docs/sql/001_init.sql
app/fixtures.py     cached loader over contracts/fixtures, raises FixtureMissing
app/schemas.py      response models mirroring contracts/types.ts
app/llm/            base protocol · providers · cache · gateway
app/api/system.py   /health · /ready · /dev/db · /dev/llm
app/api/prep.py     the five /v1 data routes
app/main.py         create_app, CORS, lifespan, error mapping
```
