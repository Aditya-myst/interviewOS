-- ═══════════════════════════════════════════════════════════════════════════
-- InterviewOS — 003_storage.sql   (Supabase only)
--
-- A private bucket for resume files, with one folder per user. Raw bytes live
-- in Storage; Postgres keeps only `resumes.storage_path`, the extracted text
-- and the evidence quotes. Nothing about a resume is ever publicly readable.
--
-- NOT verified against a live Supabase project from here (there is no
-- `storage` schema on a plain Postgres instance, so it cannot be tested the
-- way 001/002 were). Run it after 001/002 and check the bucket exists in
-- Storage → Buckets before wiring uploads.
--
-- Path convention: resumes/{auth.uid()}/{resume_id}.{ext}
-- ═══════════════════════════════════════════════════════════════════════════

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'resumes',
  'resumes',
  false,
  10485760,                                                   -- 10 MB
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ]
)
on conflict (id) do nothing;

drop policy if exists resumes_objects_select_own on storage.objects;
drop policy if exists resumes_objects_insert_own on storage.objects;
drop policy if exists resumes_objects_delete_own on storage.objects;

-- The first path segment must be the caller's uid, so one user can never read
-- or overwrite another user's file even if they guess a filename.
create policy resumes_objects_select_own on storage.objects
  for select to authenticated
  using (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

create policy resumes_objects_insert_own on storage.objects
  for insert to authenticated
  with check (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

create policy resumes_objects_delete_own on storage.objects
  for delete to authenticated
  using (bucket_id = 'resumes' and (storage.foldername(name))[1] = auth.uid()::text);

-- Deliberately no update policy: a resume is replaced, never edited in place.
