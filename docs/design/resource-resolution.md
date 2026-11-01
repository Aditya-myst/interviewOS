# Picking the one best resource

The requirement: for every subtopic, point the learner at **the best single
resource for that role** — official docs, a maintained open-source repo, a
high-quality blog, and only then video or a search. Never a link we made up.

Two separate problems, often confused:

- **Selection** — which resource is best for this subtopic at this level?
- **Verification** — is that resource still alive, free, and actually about it?

Both have to be mechanical, because a wrong link is the fastest way to lose a
recruiter's trust.

---

## 1. The ladder (where candidates come from)

| tier | source | wins because | trust |
|---|---|---|---|
| T0 | `data/curated.yaml` — hand-picked per subtopic | a human already checked it | highest |
| T1 | official docs slug templates (`fastapi.tiangolo.com/tutorial/<slug>`, `docs.python.org/3/library/<mod>`) | canonical, stable, free | very high |
| T2 | free curricula: freeCodeCamp, roadmap.sh, Kaggle Learn, MIT OCW | structured, free, long-lived | high |
| T3 | GitHub search (topics + stars + recent commits) | often the best practical artefact | high if maintained |
| T4 | YouTube Data API (duration, channel reputation) | good when a visual explanation is required | medium |
| T5 | `ddgs` / self-hosted SearXNG | fills gaps | low |
| T6 | a **labelled search URL** we build from the subtopic name | honest dead end, never a fake link | none |

Resolution stops as soon as a tier produces a candidate that passes the hard
filters **and** scores above the tier threshold. T6 exists so "we have nothing"
is a state the UI can render, not a lie.

## 2. Hard filters (before any scoring)

A candidate is discarded if any of these fail:

- HTTP GET (not HEAD — many docs sites 405 a HEAD) returns 200 after redirects.
- Content type is `text/html`, `application/pdf` or `text/plain`.
- No paywall, login wall, cookie wall or "sign in to continue".
- Not already marked `is_dead`, and not a domain on the death list.
- Repos: not archived, pushed within 18 months, has a licence, `stars >= 50`
  unless the repo is the official one for the tool.
- Docs: the page must mention the subtopic term in its title or h1.
- Videos: <= 90 minutes, published within 4 years, channel allowlisted.
- Language is English (for v1; a language field exists so this can change).

## 3. Scoring

```
score = 0.30 * relevance        # cosine(bge-small(subtopic), bge-small(resource))
      + 0.22 * authority        # tier table below
      + 0.16 * level_match      # beginner resource for a beginner gap
      + 0.12 * maintenance      # repo activity / docs freshness / blog date
      + 0.10 * engagement       # stars, or discussion signal, log-scaled
      + 0.10 * freshness        # how recently a human or bot confirmed it
```

Authority values, so this is not vibes:

| kind | authority |
|---|---|
| official project docs for the exact tool | 1.00 |
| language/runtime reference (MDN, python.org) | 0.95 |
| maintained OSS repo (official) | 0.90 |
| maintained OSS repo (community) | 0.80 |
| recognised free curriculum | 0.78 |
| vetted long-form blog (Real Python, Julia Evans tier) | 0.70 |
| conference talk / reputable video course | 0.55 |
| personal blog | 0.42 |
| aggregator / listicle | 0.25 |
| search results page | 0.05 |

Worked example — subtopic *"Retrieval metrics (recall@k, MRR)"*:

| candidate | rel | auth | level | maint | eng | fresh | score |
|---|---|---|---|---|---|---|---|
| Ragas docs — metrics | .82 | 1.00 | 1.0 | .9 | .3 | 1.0 | **0.81** |
| Blog: "RAG eval from scratch" | .88 | .70 | 1.0 | .6 | .2 | .8 | 0.74 |
| YouTube: "RAG evaluation" | .70 | .55 | .9 | .5 | .8 | .7 | 0.66 |
| ArXiv RAG paper | .62 | .95 | .4 | 1.0 | .9 | .9 | 0.72 |

The paper scores respectably but loses on level match — it is the right
*checkpoint* reading, not the right first read. So the triplet matters: the same
candidate can win one role and lose another.

## 4. The triplet, not a single link

Every topic resolves three roles, which is exactly the teaching loop:

| role | what it must be | tie-break |
|---|---|---|
| `concept` | docs, book chapter, or paper that explains *this* subtopic | prefer official, then shortest |
| `practice` | exercises, a runnable repo, a hands-on tutorial with code | prefer something runnable locally, no signup |
| `checkpoint` | a way to prove it: quiz, test suite, project spec, eval harness | prefer machine-checkable |

Rules:
- **No repeated domain** across the three roles — three links to the same blog
  is one link.
- If a role cannot be filled above threshold, it renders as a labelled search
  ("Not resolved yet — search for X"), which is what the roadmap screenshot
  already does.
- One LLM rerank over the top 12 candidates picks the triplet, and **any URL it
  returns that is not string-identical to a candidate is dropped**. The model
  chooses; it never authors.

## 5. Verification and decay

- `resource_checks` records every HTTP check: timestamp, status, final URL.
- Nightly job re-checks resources not checked in 14 days; sets `is_dead`.
- When a resource dies, affected `topic_resources` are re-resolved immediately,
  and the new pick is announced in the UI ("link replaced 2 days ago").
- Redirects are followed and recorded; a redirect that changes domain is kept
  but flagged, because domain churn often means the resource moved on.
- `verified_at` in the UI is the timestamp of the last successful check — never
  the date it was written into a fixture.

## 6. Cache and cost

- Selection cache key: `(subtopic_id, level, role)` → 90 days. Two users with the
  same gap share the same picks, which is correct: the resource for "recall@k"
  does not depend on who is asking.
- Embeddings are precomputed offline for all 139 catalogue rows and seeded, so
  scoring is one SQL query. No local model runs at request time.
- Per plan: 0–2 searches, 1 rerank, 1 embedding batch. On cached paths: zero
  LLM calls.

## 7. Current status, honestly

- 39 curated resources exist in `data/curated.yaml`; 40 unique URLs once the
  roadmap fixture is included.
- **Audited 2026-11-01 with `scripts/check_links.py`: 40/40 return 200** across
  19 domains. Two redirects worth knowing: `python.langchain.com/docs/tutorials/rag`
  now lands on `docs.langchain.com/oss/python/deepagents/rag`, and
  `postgresqltutorial.com` redirects to `neon.com/postgresql/...`.
- What has **not** happened yet: nothing is checked at runtime, nothing is
  stored in `resources`, and no resolution has ever been run for a real user.
  The badges in the roadmap UI currently reflect the fixture, not a live check.
  Phase 8 makes them true; until then the honest label is "curated", not
  "verified".

## 8. Schema deltas this needs (005_resources.sql)

```sql
alter table public.resources
  add column authority     numeric(3,2) check (authority between 0 and 1),
  add column stars         integer,
  add column last_commit_at timestamptz,
  add column domain        text,
  add column is_paywalled  boolean not null default false,
  add column search_url    text;          -- what T6 renders

create index resources_domain_idx on public.resources (domain);
create index resources_needs_check_idx
  on public.resources (verified_at nulls first);
```
