-- ═══════════════════════════════════════════════════════════════════════════
-- LOCAL TEST STUB — never run this on Supabase.
--
-- 001_init.sql assumes Supabase's `auth` schema: `auth.users` for the profile
-- foreign key, `auth.uid()` inside every RLS policy. A plain Postgres instance
-- has neither, so this file fakes them just well enough to run and test the
-- schema locally.
--
-- On Supabase: skip this file entirely. Their auth.uid() reads the verified JWT
-- and you must never shadow it.
-- ═══════════════════════════════════════════════════════════════════════════

create schema if not exists auth;

create table if not exists auth.users (
  id                 uuid primary key,
  email              text,
  raw_user_meta_data jsonb default '{}'::jsonb
);

-- Mirrors Supabase's contract: the current user id comes from the request's
-- JWT claims, which tests set with
--   set request.jwt.claims = '{"sub":"<uuid>"}';
create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')::uuid
$$;

-- Supabase's three roles, minus their policies.
do $$
begin
  if not exists (select from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
  if not exists (select from pg_roles where rolname = 'anon') then
    create role anon nologin;
  end if;
  if not exists (select from pg_roles where rolname = 'service_role') then
    create role service_role nologin bypassrls;
  end if;
end $$;

grant usage on schema auth to authenticated, anon, service_role;
grant select on auth.users to authenticated, anon, service_role;
grant execute on function auth.uid() to authenticated, anon, service_role;
