-- ═══════════════════════════════════════════════════════════════════════════
-- InterviewOS — 001_init.sql
-- Schema of record: extensions, 18 tables, indexes, guards, RLS.
--
-- Mirrors contracts/types.ts and contracts/ENUMS.md exactly. If you change an
-- enum value here without changing ENUMS.md, you have created two sources of
-- truth — don't.
--
-- WHERE TO RUN THIS: Supabase dashboard → SQL Editor → New query → paste the
-- whole file → Run. It is idempotent-ish: it drops and recreates the objects
-- it owns, so re-running on a fresh project is safe. On a project that already
-- holds data it WILL delete that data (see the DROP block below).
--
-- PowerShell note: nothing here is run from your terminal. If you later use
-- psql, the invocation is
--   psql "$env:DATABASE_URL" -f docs\sql\001_init.sql
-- with DATABASE_URL exported as $env:DATABASE_URL = "postgresql://...".
-- ═══════════════════════════════════════════════════════════════════════════

-- ── Extensions ─────────────────────────────────────────────────────────────
-- vector: pgvector, for the 384-dim bge-small embeddings on resources and
--         subtopics (resolver score = 0.45 * cosine similarity).
-- pgcrypto: digest() for llm_cache keys.
-- pg_trgm: fuzzy fallback when an alias match fails during skill resolution.
create extension if not exists vector;
create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

-- ── Teardown (reverse dependency order) ────────────────────────────────────
drop table if exists public.llm_cache cascade;
drop table if exists public.jobs cascade;
drop table if exists public.interview_reports cascade;
drop table if exists public.interview_messages cascade;
drop table if exists public.interview_sessions cascade;
drop table if exists public.resource_checks cascade;
drop table if exists public.topic_resources cascade;
drop table if exists public.resources cascade;
drop table if exists public.learning_topics cascade;
drop table if exists public.learning_paths cascade;
drop table if exists public.assessment_answers cascade;
drop table if exists public.assessments cascade;
drop table if exists public.candidate_skills cascade;
drop table if exists public.skill_subtopics cascade;
drop table if exists public.skills cascade;
drop table if exists public.job_descriptions cascade;
drop table if exists public.resumes cascade;
drop table if exists public.profiles cascade;

drop type if exists public.skill_status cascade;
drop type if exists public.proficiency_level cascade;
drop type if exists public.verified_level cascade;
drop type if exists public.priority_band cascade;
drop type if exists public.requirement_type cascade;
drop type if exists public.evidence_type cascade;
drop type if exists public.assessment_level cascade;
drop type if exists public.question_type cascade;
drop type if exists public.interview_mode cascade;
drop type if exists public.channel cascade;
drop type if exists public.resource_role cascade;
drop type if exists public.resource_kind cascade;
drop type if exists public.parse_status cascade;
drop type if exists public.readiness_label cascade;
drop type if exists public.topic_status cascade;
drop type if exists public.topic_depth cascade;
drop type if exists public.seniority cascade;
drop type if exists public.assessment_status cascade;
drop type if exists public.session_status cascade;
drop type if exists public.message_role cascade;
drop type if exists public.path_status cascade;
drop type if exists public.job_status cascade;

-- ── Enums — one per distinct vocabulary in contracts/ENUMS.md ──────────────
create type public.skill_status as enum
  ('claimed', 'unverified', 'weak', 'developing', 'verified', 'needs_revision');

create type public.proficiency_level as enum
  ('none', 'listed', 'beginner', 'intermediate', 'advanced', 'expert');

-- verified_level may never be 'listed': the resume never sets a verified level.
create type public.verified_level as enum
  ('none', 'beginner', 'intermediate', 'advanced', 'expert');

create type public.priority_band as enum ('critical', 'high', 'medium', 'low');
create type public.requirement_type as enum ('required', 'preferred');

create type public.evidence_type as enum
  ('resume_skill_list', 'resume_project', 'resume_experience',
   'assessment_answer', 'interview_answer', 'user_correction');

create type public.assessment_level as enum ('conceptual', 'practical', 'applied');
create type public.assessment_status as enum ('in_progress', 'completed');

create type public.question_type as enum
  ('fundamentals', 'advanced', 'coding', 'debugging',
   'project_deep_dive', 'scenario', 'system_design', 'behavioral');

create type public.interview_mode as enum
  ('beginner_practice', 'intermediate_technical', 'advanced_technical',
   'resume_based', 'jd_based', 'full_mock');

create type public.channel as enum ('text', 'voice');
create type public.session_status as enum ('active', 'completed');
create type public.message_role as enum ('interviewer', 'candidate', 'system');

create type public.resource_role as enum ('concept', 'practice', 'checkpoint');
create type public.resource_kind as enum
  ('docs', 'article', 'video', 'course', 'exercise', 'repo', 'paper', 'book');

create type public.parse_status as enum ('ok', 'degraded');
create type public.readiness_label as enum
  ('not_ready', 'early', 'approaching', 'interview_ready');
create type public.topic_status as enum
  ('not_started', 'in_progress', 'checkpoint_passed', 'done');
create type public.topic_depth as enum ('refresh', 'core', 'deep_dive');
create type public.path_status as enum ('active', 'completed');
create type public.seniority as enum ('intern', 'junior', 'mid', 'senior', 'lead');
create type public.job_status as enum ('queued', 'running', 'done', 'failed');

-- ── Shared helper: updated_at ──────────────────────────────────────────────
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $fn$
begin
  new.updated_at := now();
  return new;
end;
$fn$;

-- ── 1. profiles ────────────────────────────────────────────────────────────
-- One row per auth user. `id` IS the auth uid — that is what every RLS policy
-- compares against.
create table public.profiles (
  id             uuid primary key references auth.users (id) on delete cascade,
  email          text,
  full_name      text,
  target_role    text,
  target_company text,
  seniority      public.seniority,
  interview_date date,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create trigger trg_profiles_touch
  before update on public.profiles
  for each row execute function public.touch_updated_at();

-- ── 2. resumes ─────────────────────────────────────────────────────────────
create table public.resumes (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references public.profiles (id) on delete cascade,
  filename         text,
  mime_type        text,
  size_bytes       bigint check (size_bytes is null or size_bytes between 0 and 10485760),
  storage_path     text,                        -- Supabase Storage object path; raw bytes never in Postgres
  raw_text         text,                        -- extracted text, used for quote location
  parse_status     public.parse_status not null default 'ok',
  parse_meta       jsonb not null default '{}'::jsonb,   -- {model, prompt_hash, parse_version, warn}
  skills           jsonb not null default '[]'::jsonb,   -- ExtractedSkill[]
  projects         jsonb not null default '[]'::jsonb,   -- ParsedProject[]
  experience_years numeric(4, 1) check (experience_years is null or experience_years >= 0),
  achievements     text[] not null default '{}',
  unsupported_claims text[] not null default '{}',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create index resumes_user_created_idx on public.resumes (user_id, created_at desc);

create trigger trg_resumes_touch
  before update on public.resumes
  for each row execute function public.touch_updated_at();

-- ── 3. job_descriptions ────────────────────────────────────────────────────
create table public.job_descriptions (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references public.profiles (id) on delete cascade,
  title              text,
  company            text,
  role               text,
  seniority          public.seniority,
  min_years_experience numeric(4, 1) check (min_years_experience is null or min_years_experience >= 0),
  body               text not null check (length(body) > 0),
  parse_status       public.parse_status not null default 'ok',
  requirements       jsonb not null default '[]'::jsonb,  -- JDRequirement[]
  interview_rounds   text[] not null default '{}',
  rounds_inferred    boolean not null default true,
  topics             text[] not null default '{}',
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index job_descriptions_user_created_idx
  on public.job_descriptions (user_id, created_at desc);

create trigger trg_job_descriptions_touch
  before update on public.job_descriptions
  for each row execute function public.touch_updated_at();

-- ── 4. skills (global vocabulary, seeded from data/taxonomy.yaml) ──────────
create table public.skills (
  id                  text primary key,
  name                text not null,
  category            text,
  aliases             text[] not null default '{}',
  interview_relevance numeric(3, 2) not null default 0.5
                      check (interview_relevance between 0 and 1),
  created_at          timestamptz not null default now()
);

create index skills_category_idx on public.skills (category);
-- alias lookups + typo fallback during parsing
create index skills_aliases_gin_idx on public.skills using gin (aliases);
create index skills_name_trgm_idx on public.skills using gin (name gin_trgm_ops);

-- ── 5. skill_subtopics (the curriculum graph the tutor is not allowed to
--       invent around) ────────────────────────────────────────────────────
create table public.skill_subtopics (
  skill_id    text not null references public.skills (id) on delete cascade,
  subtopic_id text not null,
  title       text not null,
  level       public.proficiency_level not null default 'beginner',
  objective   text,
  order_index integer not null default 0,
  embedding   vector(384),
  primary key (skill_id, subtopic_id)
);

create index skill_subtopics_order_idx
  on public.skill_subtopics (skill_id, order_index);
create index skill_subtopics_embedding_idx
  on public.skill_subtopics using hnsw (embedding vector_cosine_ops);

-- ── 6. candidate_skills — the heart of the product ────────────────────────
-- status + the three priority factors + priority + band + the server-written
-- explanation. The UI renders `explanation` verbatim; it never recomputes it.
create table public.candidate_skills (
  id                 uuid primary key default gen_random_uuid(),
  user_id            uuid not null references public.profiles (id) on delete cascade,
  skill_id           text not null references public.skills (id),
  status             public.skill_status not null default 'claimed',
  claimed_level      public.proficiency_level,
  verified_level     public.verified_level,
  expected_level     public.verified_level,
  confidence         numeric(3, 2) not null default 0 check (confidence between 0 and 1),
  jd_importance      numeric(3, 2) not null default 0 check (jd_importance between 0 and 1),
  interview_relevance numeric(3, 2) not null default 0.5
                     check (interview_relevance between 0 and 1),
  gap                numeric(3, 2) not null default 0 check (gap between 0 and 1),
  priority           numeric(4, 3) not null default 0 check (priority between 0 and 1),
  priority_band      public.priority_band not null default 'low',
  explanation        text not null check (length(btrim(explanation)) > 0),
  in_resume          boolean not null default false,
  in_jd              boolean not null default false,
  evidence           jsonb not null default '[]'::jsonb,  -- Evidence[]
  last_assessed_at   timestamptz,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (user_id, skill_id),
  -- the state machine's floor: no verified status without a verified level
  constraint verified_needs_level check (
    status <> 'verified' or verified_level is not null
  )
);

create index candidate_skills_user_priority_idx
  on public.candidate_skills (user_id, priority desc);
create index candidate_skills_user_status_idx
  on public.candidate_skills (user_id, status);
create index candidate_skills_user_band_idx
  on public.candidate_skills (user_id, priority_band);

create trigger trg_candidate_skills_touch
  before update on public.candidate_skills
  for each row execute function public.touch_updated_at();

-- Guard: every status change must carry evidence, and only legal edges of the
-- state machine are allowed. This is the rule the whole product claim rests on,
-- so it lives in the database rather than in one service method.
create or replace function public.enforce_skill_transition()
returns trigger
language plpgsql
as $fn$
declare
  legal boolean;
begin
  if new.status = old.status then
    return new;
  end if;

  if coalesce(jsonb_array_length(new.evidence), 0) = 0 then
    raise exception
      'skill %: status change % -> % requires evidence[]',
      new.skill_id, old.status, new.status
      using errcode = 'check_violation';
  end if;

  legal := case
    when old.status in ('claimed', 'unverified')
      then new.status in ('weak', 'developing', 'verified')
    when old.status = 'weak'
      then new.status in ('developing', 'verified')
    when old.status = 'developing'
      then new.status in ('verified', 'weak')
    when old.status = 'verified'
      then new.status in ('needs_revision')
    when old.status = 'needs_revision'
      then new.status in ('developing', 'verified')
    else false
  end;

  if not legal then
    raise exception 'skill %: illegal transition % -> %',
      new.skill_id, old.status, new.status
      using errcode = 'check_violation';
  end if;

  return new;
end;
$fn$;

create trigger trg_candidate_skills_transition
  before update on public.candidate_skills
  for each row execute function public.enforce_skill_transition();

-- ── 7. assessments ─────────────────────────────────────────────────────────
create table public.assessments (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references public.profiles (id) on delete cascade,
  skill_id       text not null references public.skills (id),
  level          public.assessment_level not null default 'conceptual',
  status         public.assessment_status not null default 'in_progress',
  question_index integer not null default 1 check (question_index >= 1),
  question_total integer not null default 3 check (question_total between 2 and 4),
  plan           jsonb not null default '[]'::jsonb,   -- [{question, question_type, rubric, hint}]
  inferred_level public.verified_level,
  status_after   public.skill_status,
  confidence     numeric(3, 2) check (confidence is null or confidence between 0 and 1),
  started_at     timestamptz not null default now(),
  completed_at   timestamptz,
  check (status <> 'completed' or status_after is not null)
);

create index assessments_user_skill_idx
  on public.assessments (user_id, skill_id, started_at desc);
create unique index assessments_one_open_idx
  on public.assessments (user_id, skill_id)
  where status = 'in_progress';

-- ── 8. assessment_answers ──────────────────────────────────────────────────
create table public.assessment_answers (
  id              uuid primary key default gen_random_uuid(),
  assessment_id   uuid not null references public.assessments (id) on delete cascade,
  user_id         uuid not null references public.profiles (id) on delete cascade,
  question_index  integer not null check (question_index >= 1),
  question_text   text not null,
  question_type   public.question_type not null,
  answer_text     text not null default '',
  scores          jsonb not null default '{}'::jsonb,   -- RubricScores
  missing_concepts text[] not null default '{}',
  feedback        text,
  created_at      timestamptz not null default now(),
  unique (assessment_id, question_index)
);

create index assessment_answers_user_idx on public.assessment_answers (user_id);

-- ── 9. learning_paths ──────────────────────────────────────────────────────
create table public.learning_paths (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.profiles (id) on delete cascade,
  title           text not null default 'Your preparation path',
  summary         text not null default '',             -- server-written, rendered verbatim
  status          public.path_status not null default 'active',
  target_role     text,
  readiness       numeric(5, 2) not null default 0 check (readiness between 0 and 100),
  readiness_label public.readiness_label not null default 'not_ready',
  generated_at    timestamptz not null default now(),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index learning_paths_user_status_idx on public.learning_paths (user_id, status);
create unique index learning_paths_one_active_idx
  on public.learning_paths (user_id) where status = 'active';

create trigger trg_learning_paths_touch
  before update on public.learning_paths
  for each row execute function public.touch_updated_at();

-- ── 10. learning_topics ────────────────────────────────────────────────────
create table public.learning_topics (
  id                uuid primary key default gen_random_uuid(),
  path_id           uuid not null references public.learning_paths (id) on delete cascade,
  user_id           uuid not null references public.profiles (id) on delete cascade,
  skill_id          text references public.skills (id),  -- null = cross-skill topic
  title             text not null,
  objective         text,
  subtopics         text[] not null default '{}',
  depth             public.topic_depth not null default 'core',
  status            public.topic_status not null default 'not_started',
  order_index       integer not null default 0,
  estimated_minutes integer check (estimated_minutes is null or estimated_minutes > 0),
  progress          numeric(5, 2) not null default 0 check (progress between 0 and 100),
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (path_id, order_index)
);

create index learning_topics_path_order_idx
  on public.learning_topics (path_id, order_index);
create index learning_topics_user_status_idx
  on public.learning_topics (user_id, status);

create trigger trg_learning_topics_touch
  before update on public.learning_topics
  for each row execute function public.touch_updated_at();

-- ── 11. resources (shared: keyed by URL so link health is global) ──────────
-- tier 0 rows are the hand-curated catalogue from data/curated.yaml; tiers 1..6
-- are the resolver ladder (docs slug templates → free curricula → GitHub →
-- YouTube → SearXNG → labelled search URL). curated_* columns record which
-- subtopic a T0 row is the canonical answer for.
create table public.resources (
  id                  uuid primary key default gen_random_uuid(),
  url                 text not null unique check (url ~ '^https?://'),
  title               text not null,
  provider            text,
  author              text,
  kind                public.resource_kind,
  duration_minutes    integer check (duration_minutes is null or duration_minutes > 0),
  is_paid             boolean not null default false,
  license             text,
  tier                smallint not null default 6 check (tier between 0 and 6),
  curated_skill_id    text,
  curated_subtopic_id text,
  embedding           vector(384),
  http_status         integer,
  is_dead             boolean not null default false,
  verified_at         timestamptz,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  foreign key (curated_skill_id, curated_subtopic_id)
    references public.skill_subtopics (skill_id, subtopic_id)
    on delete set null
);

create index resources_catalogue_idx
  on public.resources (tier, curated_skill_id, curated_subtopic_id);
create index resources_live_idx on public.resources (is_dead, verified_at desc);
create index resources_embedding_idx
  on public.resources using hnsw (embedding vector_cosine_ops);

create trigger trg_resources_touch
  before update on public.resources
  for each row execute function public.touch_updated_at();

-- ── 12. topic_resources — what a user's topic actually points at ───────────
create table public.topic_resources (
  id          uuid primary key default gen_random_uuid(),
  topic_id    uuid not null references public.learning_topics (id) on delete cascade,
  resource_id uuid not null references public.resources (id) on delete cascade,
  role        public.resource_role not null,
  score       numeric(4, 3) not null default 0 check (score between 0 and 1),
  why         text,
  created_at  timestamptz not null default now(),
  unique (topic_id, role, resource_id)
);

create index topic_resources_topic_idx on public.topic_resources (topic_id);

-- ── 13. resource_checks — link health, one row per HTTP check ──────────────
create table public.resource_checks (
  id          bigserial primary key,
  resource_id uuid not null references public.resources (id) on delete cascade,
  checked_at  timestamptz not null default now(),
  http_status integer,
  final_url   text,
  ok          boolean not null default false,
  note        text
);

create index resource_checks_resource_idx
  on public.resource_checks (resource_id, checked_at desc);

-- ── 14. interview_sessions ─────────────────────────────────────────────────
create table public.interview_sessions (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references public.profiles (id) on delete cascade,
  mode             public.interview_mode not null default 'jd_based',
  channel          public.channel not null default 'text',
  status           public.session_status not null default 'active',
  target_role      text,
  skill_focus      text[] not null default '{}',
  asked            integer not null default 0 check (asked >= 0),
  total            integer not null default 6 check (total between 1 and 20),
  score            numeric(5, 2) check (score is null or score between 0 and 100),
  duration_minutes integer check (duration_minutes is null or duration_minutes >= 0),
  started_at       timestamptz not null default now(),
  completed_at     timestamptz
);

create index interview_sessions_user_created_idx
  on public.interview_sessions (user_id, started_at desc);

-- ── 15. interview_messages ─────────────────────────────────────────────────
create table public.interview_messages (
  id            bigserial primary key,
  session_id    uuid not null references public.interview_sessions (id) on delete cascade,
  user_id       uuid not null references public.profiles (id) on delete cascade,
  role          public.message_role not null,
  content       text not null,
  question_type public.question_type,
  skill_id      text references public.skills (id),
  created_at    timestamptz not null default now()
);

create index interview_messages_session_idx
  on public.interview_messages (session_id, id);

-- ── 16. interview_reports ─────────────────────────────────────────────────
create table public.interview_reports (
  id              uuid primary key default gen_random_uuid(),
  session_id      uuid not null unique references public.interview_sessions (id) on delete cascade,
  user_id         uuid not null references public.profiles (id) on delete cascade,
  overall_scores  jsonb not null default '{}'::jsonb,
  -- per_skill carries status_after; the report writeback updates
  -- candidate_skills, it never bypasses the evidence guard above.
  per_skill       jsonb not null default '[]'::jsonb,
  strengths       text[] not null default '{}',
  gaps            text[] not null default '{}',
  weak_answers    jsonb not null default '[]'::jsonb,
  next_actions    text[] not null default '{}',
  created_at      timestamptz not null default now()
);

create index interview_reports_user_created_idx
  on public.interview_reports (user_id, created_at desc);

-- ── 17. llm_cache ─────────────────────────────────────────────────────────
-- Key = sha256(model || canonical prompt || schema_version). Cuts free-tier
-- quota use, makes a demo instant, and removes 429 risk on cached paths.
create table public.llm_cache (
  key           text primary key,          -- hex sha256
  model         text not null,
  schema_version integer not null default 1,
  prompt_snippet text,
  response      jsonb not null,
  prompt_tokens integer,
  output_tokens integer,
  hits          integer not null default 0,
  created_at    timestamptz not null default now(),
  expires_at    timestamptz not null default (now() + interval '90 days')
);

create index llm_cache_expires_idx on public.llm_cache (expires_at);

comment on table public.llm_cache is
  'Service-role only. Never readable by an anon/authenticated key: prompts can contain resume text.';

-- ── 18. jobs — the outbox for slow work (parse, embed, link-check) ────────
create table public.jobs (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references public.profiles (id) on delete cascade,
  kind        text not null,               -- 'parse_resume' | 'resolve_resources' | 'link_check' | ...
  status      public.job_status not null default 'queued',
  payload     jsonb not null default '{}'::jsonb,
  attempts    integer not null default 0 check (attempts >= 0),
  error       text,
  run_after   timestamptz not null default now(),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index jobs_queue_idx on public.jobs (status, run_after);
create index jobs_user_idx on public.jobs (user_id, created_at desc);

create trigger trg_jobs_touch
  before update on public.jobs
  for each row execute function public.touch_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════
-- Row-level security
--
-- Rule: every row that belongs to a person is readable and writable only by
-- that person. The service_role key bypasses RLS entirely and is the ONLY key
-- the backend uses for writes it performs on the user's behalf.
-- ═══════════════════════════════════════════════════════════════════════════

alter table public.profiles           enable row level security;
alter table public.resumes            enable row level security;
alter table public.job_descriptions   enable row level security;
alter table public.skills             enable row level security;
alter table public.skill_subtopics    enable row level security;
alter table public.candidate_skills   enable row level security;
alter table public.assessments        enable row level security;
alter table public.assessment_answers enable row level security;
alter table public.learning_paths     enable row level security;
alter table public.learning_topics    enable row level security;
alter table public.resources          enable row level security;
alter table public.topic_resources    enable row level security;
alter table public.resource_checks    enable row level security;
alter table public.interview_sessions enable row level security;
alter table public.interview_messages enable row level security;
alter table public.interview_reports  enable row level security;
alter table public.llm_cache          enable row level security;
alter table public.jobs               enable row level security;

-- profiles: the row IS the user
create policy profiles_select_own on public.profiles
  for select using (auth.uid() = id);
create policy profiles_update_own on public.profiles
  for update using (auth.uid() = id) with check (auth.uid() = id);
create policy profiles_insert_own on public.profiles
  for insert with check (auth.uid() = id);

-- Straight ownership policies for the tables that carry user_id directly.
do $do$
declare
  t text;
  owned text[] := array[
    'resumes', 'job_descriptions', 'candidate_skills', 'assessments',
    'assessment_answers', 'learning_paths', 'learning_topics',
    'interview_sessions', 'interview_messages', 'interview_reports', 'jobs'
  ];
begin
  foreach t in array owned loop
    execute format(
      'create policy %I on public.%I for select using (auth.uid() = user_id)',
      t || '_select_own', t);
    execute format(
      'create policy %I on public.%I for insert with check (auth.uid() = user_id)',
      t || '_insert_own', t);
    execute format(
      'create policy %I on public.%I for update using (auth.uid() = user_id) with check (auth.uid() = user_id)',
      t || '_update_own', t);
    execute format(
      'create policy %I on public.%I for delete using (auth.uid() = user_id)',
      t || '_delete_own', t);
  end loop;
end;
$do$;

-- jobs is written by the backend only; users may read their own but never
-- enqueue arbitrary work. Drop the insert policy the loop just created.
drop policy jobs_insert_own on public.jobs;
drop policy jobs_update_own on public.jobs;
drop policy jobs_delete_own on public.jobs;

-- Global catalogue: readable by any signed-in user, writable by nobody but
-- service_role (which bypasses RLS).
create policy skills_read_all on public.skills
  for select to authenticated using (true);
create policy skill_subtopics_read_all on public.skill_subtopics
  for select to authenticated using (true);
create policy resources_read_all on public.resources
  for select to authenticated using (true);

-- topic_resources: visible only through a topic the caller owns.
create policy topic_resources_select_own on public.topic_resources
  for select using (
    exists (
      select 1 from public.learning_topics lt
      where lt.id = topic_resources.topic_id
        and lt.user_id = auth.uid()
    )
  );

-- resource_checks and llm_cache intentionally have NO policies: service_role
-- only. Prompts contain resume text; link-check history is internal.

-- ═══════════════════════════════════════════════════════════════════════════
-- New-user bootstrap: create the profile row the moment auth.users gets one.
-- ═══════════════════════════════════════════════════════════════════════════
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $fn$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', split_part(new.email, '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$fn$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ═══════════════════════════════════════════════════════════════════════════
-- Grants
--
-- Supabase already applies these as default privileges; stating them explicitly
-- means this file also behaves correctly on a plain Postgres instance, and it
-- documents exactly what the anon and authenticated keys can touch. None of
-- this weakens RLS — a grant without a policy is still a denial.
-- ═══════════════════════════════════════════════════════════════════════════
grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to authenticated, service_role;

-- ═══════════════════════════════════════════════════════════════════════════
-- Table count check — should print 18.
-- ═══════════════════════════════════════════════════════════════════════════
do $do$
declare
  n integer;
begin
  select count(*) into n
  from information_schema.tables
  where table_schema = 'public' and table_type = 'BASE TABLE';
  raise notice 'public tables: % (expected 18)', n;
end;
$do$;
