# InterviewOS — frontend

Next.js 16 (App Router, Cache Components). Every screen is a server component that
reads FastAPI; nothing on screen is hardcoded.

## Run it

Two terminals, both from the repo root:

```powershell
# 1. API — http://127.0.0.1:8000
cd backend
uv run uvicorn app.main:app --reload

# 2. UI — http://localhost:3000
cd frontend
pnpm dev
```

If the API runs somewhere else:

```powershell
# frontend/.env.local
INTERVIEWOS_API_URL=http://127.0.0.1:8000
```

## Where the numbers come from

`lib/api.ts` is the only module that talks to FastAPI. It returns the payload **and**
its provenance, read from the API's own headers:

| badge | meaning |
|---|---|
| **Postgres** (green) | rows came out of `candidate_skills` for this user, just now |
| **Fixture** (amber) | the API answered but had no rows, so it served its contract fixture — the badge prints the reason (`no_rows`, `no_profile`, `no_db`, `db_error`) |
| **Offline** (red) | the API did not answer at all; the page is showing fixtures read from `contracts/fixtures` |

Every data screen ends with a provenance strip listing the endpoints it actually
called. "Is this dummy data?" is a question the UI answers about itself.

`?state=` is a demo switch (`empty`, `loading`, `degraded`); it only affects the
fixture path, so a live database is never faked into showing an empty state.

## Files

| path | what it is |
|---|---|
| `lib/api.ts` | the API client and the three data-source values |
| `lib/fixtures.ts` | the saved fixtures `lib/api.ts` falls back to |
| `components/app/DataSourceBadge.tsx` | the provenance pill |
| `app/(app)/dashboard` | readiness, priority map, next moves |
| `app/(app)/gap-map` | skill matrix + evidence table |
| `app/(app)/roadmap` | topics in priority order, with named resource gaps |
