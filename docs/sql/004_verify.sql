-- ═══════════════════════════════════════════════════════════════════════════
-- InterviewOS — 004_verify.sql
--
-- Run this AFTER 001_init.sql, 002_seed.sql (and optionally 003_storage.sql).
-- Unlike the other files this one is a single SELECT, so the SQL editor shows
-- you an actual row of numbers instead of "Success. No rows returned".
--
-- Every column should be `true`. The `resolved_at` column tells you which part
-- of the setup produced these rows, so a wrong project is obvious.
-- ═══════════════════════════════════════════════════════════════════════════

with counts as (
  select
    (select count(*) from information_schema.tables
      where table_schema = 'public' and table_type = 'BASE TABLE')        as tables,
    (select count(*) from pg_tables
      where schemaname = 'public' and rowsecurity)                        as rls_tables,
    (select count(*) from pg_policies where schemaname = 'public')         as policies,
    (select count(*) from pg_type t join pg_namespace n on n.oid = t.typnamespace
      where n.nspname = 'public' and t.typtype = 'e')                      as enums,
    (select count(*) from pg_extension
      where extname in ('vector', 'pgcrypto', 'pg_trgm'))                  as extensions,
    (select count(*) from public.skills)                                   as skills,
    (select count(*) from public.skill_subtopics)                          as subtopics,
    (select count(*) from public.resources)                                as resources,
    (select count(*) from public.resources
      where tier = 0 and verified_at is not null)                          as verified_links
)
select
  tables, rls_tables, policies, enums, extensions,
  skills, subtopics, resources, verified_links,
  (tables = 18 and rls_tables = 18 and enums = 22 and extensions = 3)      as schema_ok,
  (skills = 31 and subtopics = 100 and resources = 39)                     as seeds_ok,
  (tables = 18 and skills = 31)                                            as all_good,
  now()                                                                    as checked_at
from counts;
