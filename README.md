# InterviewOS

**Your resume claims skills. This tells you which ones you can actually defend.**

InterviewOS takes three inputs — your resume, a target job description, and short adaptive
skill checks — and produces a preparation plan ordered by *interview impact*, not by what
happens to be on your CV. Every priority it shows cites the evidence behind it.

> **Status:** frontend foundation + marketing site in progress; backend starts next.
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
data/        taxonomy.yaml (31 skills / 100 subtopics), curated.yaml (resource seeds)
docs/        architecture.md, PHASE0.md
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

# 2. frontend
cd frontend && pnpm install && pnpm dev     # http://localhost:3000

# 3. backend (once implemented)
cd backend && uv run uvicorn app.main:app --reload
```

## Design system

Cream canvas, ink slabs for contrast, one green accent. Green `#22C55E` is used for
**fills only** — text on cream uses `#15803D` so it passes contrast. Status colours are
contrast-corrected variants, not the decorative tones.

## Roadmap

- [x] Contract pack, taxonomy, curated resources, environment doctor
- [x] Design system, marketing page
- [ ] Dashboard, gap map, roadmap, interview room
- [ ] Resume + JD intelligence (deterministic-first parsing)
- [ ] Skill verification engine (3-level ladder + rubric)
- [ ] Resource resolver with URL verification
- [ ] Voice interviews (Whisper STT + local TTS)

## Licence

MIT (planned). Model and resource links belong to their respective owners.
