# Database handover — InterviewOS

Notebook-to-production in four files, in this order. Total run time on a fresh
Supabase project: about fifteen seconds.

| file | what it does | Supabase | plain Postgres |
|---|---|---|---|
| `001_init.sql` | extensions, 22 enums, **18 tables**, indexes, evidence guard, RLS, new-user trigger | yes | yes, after the stub |
| `002_seed.sql` | 31 skills, 100 subtopics, 39 curated resources (tier 0) | yes | yes |
| `003_storage.sql` | private `resumes` bucket + per-user folder policies | yes | **no** (needs `storage` schema) |
| `000_local_only_stub.sql` | fakes `auth.users` / `auth.uid()` for local testing | **never run** | yes |

---

## Path A — Supabase SQL editor (what you will actually do)

1. Open the project → **SQL Editor** → **New query**.
2. Paste all of `001_init.sql` → **Run**. Expect the notice
   `public tables: 18 (expected 18)` at the bottom.
3. New query → paste `002_seed.sql` → **Run**. Expect
   `seeded: 31 skills, 100 subtopics, 39 resources`.
4. New query → paste `003_storage.sql` → **Run**, then check
   **Storage → Buckets** for a private bucket named `resumes`.
5. **Database → Extensions** should now list `vector`, `pgcrypto`, `pg_trgm`.
6. Copy the two connection strings into `.env` (never into a commit):

   | variable | where | port |
   |---|---|---|
   | `DATABASE_URL` | Connect → **Transaction pooler** (used by the app at runtime) | 6543 |
   | `DIRECT_URL` | Connect → **Direct connection** (used by migrations) | 5432 |

7. Confirm the seed landed — SQL editor:

   ```sql
   select
     (select count(*) from public.skills)           as skills,
     (select count(*) from public.skill_subtopics)  as subtopics,
     (select count(*) from public.resources)        as resources;
   -- 31 | 100 | 39
   ```

8. Turn off public signup if you are demoing before launch:
   **Authentication → Providers → Email → disable "Allow new users to sign up"**
   once your demo account exists.

### Re-running

`001_init.sql` starts with a `drop table` block — re-running it **deletes all
data**. Run it once on a fresh project, or clear the drop block deliberately.
`002_seed.sql` is a pure upsert and is safe to re-run whenever
`data/taxonomy.yaml` or `data/curated.yaml` changes.

---

## Path B — psql from Windows PowerShell

PowerShell does not have `&&`; use `;` and `curl.exe`. The direct connection on
port **5432** is the one to use for DDL — the transaction pooler on 6543 does
not hold a session long enough for some of it.

```powershell
$env:DIRECT_URL = "postgresql://postgres.<ref>:<password>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
psql $env:DIRECT_URL -f docs\sql\001_init.sql
psql $env:DIRECT_URL -f docs\sql\002_seed.sql
psql $env:DIRECT_URL -f docs\sql\003_storage.sql
```

If `psql` is not on `PATH`, use the full path
`"C:\Program Files\PostgreSQL\17\bin\psql.exe"`. If the password contains `@`
or `:`, percent-encode it (`@` → `%40`) or psql will parse the URI wrong.

---

## Path C — run it locally before trusting it

This is exactly how the files in this folder were checked, on Postgres 17 with
pgvector installed:

```bash
createdb ios_local
psql -d ios_local -f docs/sql/000_local_only_stub.sql   # auth.users + auth.uid() + roles
psql -d ios_local -f docs/sql/001_init.sql
psql -d ios_local -f docs/sql/002_seed.sql
```

---

## What has actually been verified

Run against Postgres 17.11 + pgvector, not assumed:

**Schema and seeds**

- `001_init.sql` executes with `ON_ERROR_STOP=1`; the closing check prints
  `public tables: 18 (expected 18)`.
- `002_seed.sql` inserts 31 skills, 100 subtopics, 39 resources; 33 of the 39
  carry `verified_at` from `curated.yaml`'s `verified: true`, the other 6 are
  left null for the link-check job. Re-running it keeps the counts at 31/100/39.

**Guards (each one deliberately attempted, each one refused)**

| attempt | result |
|---|---|
| `claimed → verified` with empty `evidence[]` | `ERROR: status change claimed -> verified requires evidence[]` |
| `verified → developing` (illegal edge) | `ERROR: illegal transition verified -> developing` |
| `status = 'verified'` with `verified_level = null` | refused by `verified_needs_level` |
| blank / whitespace `explanation` | refused by check constraint |
| `priority = 1.4` | refused by range check |
| second `active` learning path for one user | refused by `learning_paths_one_active_idx` |
| second open assessment for the same skill | refused by `assessments_one_open_idx` |
| resource URL not `http(s)://` | refused by `resources_url_check` |
| curated resource pointing at a non-existent subtopic | refused by the composite FK |

Legal transitions with evidence were accepted: `claimed → verified`, then
`verified → needs_revision`, and deleting the auth user cascaded their rows away
while leaving the shared catalogue intact.

**RLS (two users, acting through the `authenticated` role with real JWTs)**

| check | result |
|---|---|
| user 1 sees own `candidate_skills` / `resumes` / `profiles` | 1 / 1 / 1 |
| user 1 sees the shared catalogue | 31 skills, 39 resources |
| user 1 sees `llm_cache` | 0 — no policy, and prompts can contain resume text |
| user 1 reads user 2's row by id | 0 rows |
| user 1 inserts a row into user 2's account | `ERROR: new row violates row-level security policy` |
| user 1 updates / deletes user 2's rows | `UPDATE 0` / `DELETE 0` |
| user 1 writes to the global `skills` catalogue | `ERROR: violates row-level security policy` |
| user 2 sees user 1's resumes | 0 |

---

## Things this schema deliberately enforces

- **No status change without evidence.** `enforce_skill_transition()` raises on
  any `candidate_skills.status` update whose `evidence[]` is empty, and on any
  edge the state machine does not allow. The product claim lives in the
  database, not in one Python method someone can bypass.
- **The resume never sets a verified level.** `verified_level` has no `listed`
  value, and `verified_needs_level` requires a level as soon as status is
  `verified`.
- **One active path, one open assessment per skill** — enforced by partial
  unique indexes, so a retry cannot fork a user's state.
- **`llm_cache` is service-role only.** It has RLS on and no policies.
- **Resources are shared by URL.** Link health is global; `resources` is keyed by
  URL, and `curated_skill_id` / `curated_subtopic_id` / `tier` record that a row
  is the tier-0 answer for a specific subtopic without a nineteenth table.

## Not done here, on purpose

- No `pg_cron` link-check schedule (the job runner owns that in phase 4).
- No read replica, no partitioning, no full-text search table — none of it earns
  its keep at demo scale.
- Embeddings are declared `vector(384)` (bge-small) and left null until the
  resolver starts writing them; the HNSW indexes are already in place so no
  migration is needed later.
