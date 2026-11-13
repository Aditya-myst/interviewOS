# InterviewOS

**Your resume claims skills. This tells you which ones you can actually defend.**

InterviewOS takes three inputs — your resume, a target job description, and short adaptive
skill checks — and produces a preparation plan ordered by *interview impact*, not by what
happens to be on your CV. Every priority it shows cites the evidence behind it.

> **Status:** frontend (dashboard, gap map, roadmap) + API service, database verified live
> (18 tables / 22 enums / 41 skills / 137 subtopics / 39 resources, `GET /dev/db`).
> `/v1/*` still serves fixtures, labelled `X-Data-Source: fixture`. Resume/JD pipeline next.
> Backend: [backend/README.md](backend/README.md) · Phase log: [docs/PHASE4.md](docs/PHASE4.md).
> See [docs/architecture.md](docs/architecture.md) for the full design and
> [docs/PHASE0.md](docs/PHASE0.md) for the environment checklist.

---

## Why this is not "a chatbot with resume upload"

| Typical AI prep tool | InterviewOS |
|---|---|
| Asks an LLM to grade you from a prompt | Requires **evidence** before a skill can change status |
| One overall "readiness %" | Per-skill state machine: `claimed → weak → developing → verified → needs_revision` |
| Recommends links it invented | Resolves subtopics against a **curated catalogue**, then HTTP-verifies each URL |
| Owns the whole syllabus | Only teaches gaps that the target JD will actually test |
| Skills never go stale | Verified skills decay to `needs_revision` |

## Stack

Next.js 15 (App Router) · TypeScript · Tailwind v4 · shadcn/ui · recharts
FastAPI · Pydantic v2 · SQLAlchemy 2.0 · LangGraph
Supabase Postgres + pgvector · Gemini Flash primary / Groq open-weight fallback
Local embeddings (`fastembed` + bge-small) · `ddgs`/SearXNG for resource discovery

Everything runs on free tiers. No paid search API, no local GPU, no Ollama.

## Repository layout

```
contracts/   openapi.yaml, types.ts, ENUMS.md, fixtures/   ← single source of truth
data/        taxonomy.yaml (41 skills / 137 subtopics), curated.yaml (resource seeds)
docs/        architecture.md, PHASE0.md, sql/ ← the database handover
scripts/     verify_env.py — environment doctor
frontend/    Next.js app
backend/     FastAPI service
```

**Contract rule:** the UI consumes `contracts/types.ts` and the backend implements
`contracts/openapi.yaml`. Neither side invents a field.

## Run it

```bash
# 1. environment
cp .env.example .env         # fill in Supabase, Gemini, Groq keys
uv run python scripts/verify_env.py

# 2. database — 18 tables, RLS, 41 skills, 137 subtopics, 39 curated resources
#    paste docs/sql/001_init.sql, then 002_seed.sql, then 003_storage.sql
#    into the Supabase SQL editor. Full walkthrough: docs/sql/README.md

# 3. frontend — pnpm only (packageManager is pinned; npm/yarn will fight the lockfile)
corepack enable                             # once per machine, gives you pnpm
cd frontend && pnpm install && pnpm dev     # http://localhost:3000

# 4. backend — boots with no .env; /ready honestly says "degraded, fixture mode"
cd backend && uv sync; uv run uvicorn app.main:app --reload --port 8000
#    http://localhost:8000/docs     full API map: backend/README.md
```

## Verify it

One command, whole repo, plain verdict. Run it from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

(There is a copy in `backend/` too, so `cd backend` then the same command also works.)

It runs the backend suite, lint on both sides, and a production build of the frontend, then
prints a PASS/FAIL table and exits non-zero if anything failed. No database and no API key
needed. Add `-SkipBuild` to stop after lint. If `uv` is installed it runs the backend through
`uv run`, so the versions match `uv.lock`; without it, whatever `python` is on PATH is used and
lint is skipped if ruff is missing there.

The backend suite runs without Postgres by default. The one test that proves status moves
match the database trigger only runs when you point it at a database:

```powershell
$env:INTERVIEWOS_TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
python -m pytest tests/test_status_transitions.py
```

## Scoring: rubric first, model second

Every score has a quote behind it, and by default that quote comes from a deterministic
rubric matcher: it needs no API key, gives the same answer twice, and cannot be talked into
anything. Its weakness is vocabulary — an answer that explains a context window's limits
without saying the word "limits" loses the point.

Set a provider key and `LLM_SCORING=true` and a model reads the answer instead. Three things
stop that from becoming a slot machine:

- **The model must quote the answer verbatim.** The quote is checked against the text, so a
  paraphrase is discarded and the rubric score stands.
- **It must account for every rubric point.** Half a verdict is not a verdict.
- **Structural floors stay vocabulary-independent.** No quote, too short, no specifics — those
  caps apply to whatever the model returns. A fluent non-answer cannot be rescued.

Cost, stated plainly: one call per uncached answer, roughly 0.6-3 s on the free Groq/Gemini
tiers, 0 ms on a cache hit. When the model is unavailable — no key, an outage, invalid JSON —
grading silently falls back to the rubric, and the answer's `scored_by` field says which of
the two graded it. It is never inferred, and never "llm" by default.

### The rubric understands more than one way of saying it

Without a key, the deterministic matcher is the whole grader, so it has to be fair on its
own. It was not: three competent system-design answers — read/write ratio, latency budget,
replicas, circuit breakers — scored 22, 29 and 17 out of 100. Nothing was wrong with the
answers. The rubric said *replication* and the answer said *replica*; the rubric said
*queues* and the answer said *queue*; the rubric said *envelope* and the answer said
*budget*. Every correct answer that used another grammatical form, or another word for the
same idea, was logged as a miss.

Two changes, both in `app/prep/lexicon.py` and `app/interview/questions.py`:

- **Forms.** A suffix stemmer (`-s`, `-ing`, `-ation`, `-ency`, plural `-ies`) runs on both
  sides, so a word matches itself in any grammatical shape. It is deliberately conservative:
  a four-character prefix is not enough, because at four `shar` (share) matched `shard`
  (shard).
- **Ideas.** `CONCEPT_SYNONYMS` maps ~25 curriculum concepts to the way candidates actually
  phrase them (`envelope` → budget/estimate, `recall` → retrieval/hits, `faithfulness` →
  hallucination/grounded). It widens the door; it does not open it. The answer still has to
  be sentence-length, specific and quotable, so a fluent non-answer gains nothing.

The same three answers now score 0.61, 0.42 and 0.70 — and the interview, the ladder and
the assessment all read from the same matcher, so the fix lands on every screen at once.

## The ladder moves the roadmap

The roadmap and the ladder used to be two features that had never met: you could pass all
three checkpoints on a skill and the roadmap would still say `not_started`, and
`checkpoint_passed` — a status the schema defines — was set by nothing.

Now `writeback()` calls `progress.mark_checkpoint()` in the same transaction as the ladder,
its answers and the skill row, through a savepoint so a roadmap problem costs the roadmap
and not the candidate's work. The rules are forward-only:

- passing marks the topic `checkpoint_passed` (75%), not `done` — a ladder proves the
  checkpoint, not the reading;
- a failed ladder marks a fresh topic `in_progress` and never un-passes a checkpoint;
- a topic already `done` is never downgraded;
- starting a ladder materialises the plan first, because a candidate can open Assess
  without ever visiting the roadmap.

Two consequences the screens had to learn:

- **Percent is the average of what each topic reached**, not `done / total`. Telling someone
  who just passed a checkpoint that they are at 0% is a lie, however arithmetically correct.
- **Verified work leaves the plan.** A verified skill stops being a gap, so the next re-plan
  drops it — and the topic with it. Those rows now come back in `completed` ("finished
  earlier") so the effort stays on the page.

## Design system

Cream canvas, ink slabs for contrast, one green accent. Green `#22C55E` is used for
**fills only** — text on cream uses `#15803D` so it passes contrast. Status colours are
contrast-corrected variants, not the decorative tones.

## Roadmap

- [x] Contract pack, taxonomy, curated resources, environment doctor
- [x] Design system, marketing page
- [x] Dashboard, gap map, roadmap
- [x] API service: /health, /ready, honest degraded mode, LLM gateway with fallback + cache
- [x] Interview room, report screen
- [x] Resume + JD intelligence (deterministic-first parsing)
- [x] Skill verification engine (3-level ladder + rubric)
- [x] Tutor
- [x] Persisted roadmap progress — `learning_paths` / `learning_topics` are written, and a re-plan cannot reset what you finished
- [ ] Resource resolver with URL verification (role gaps are named, not filled)
- [ ] Voice interviews (Whisper STT + local TTS)

## Licence

MIT (planned). Model and resource links belong to their respective owners.
