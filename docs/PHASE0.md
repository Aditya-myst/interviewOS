# Phase 0 — Environment checklist (Windows / PowerShell / 8 GB laptop / ₹0)

Tick these in order. Each line has a verification; do not move on with an unticked box.

## A. Accounts and keys
- [ ] **Rotate every key that was ever pasted into chat.** Supabase → Settings → API → *Generate new JWT secret* (rotates anon **and** service_role) → then Settings → Database → *Reset database password* (use letters + digits only, no symbols). Gemini and Groq keys: delete and recreate.
  - verify: old keys return 401/403; new keys work in the doctor script.
- [ ] Gemini API key from aistudio.google.com (personal Gmail).
- [ ] Groq API key from console.groq.com (also gives free Whisper STT).
- [ ] Supabase project. **If it is still eu-north-1 and the DB is empty, recreate in Mumbai/Singapore** — you'll feel ~150 ms on every query.
  - verify: `SUPABASE_URL` subdomain == the project ref inside `DATABASE_URL`.
- [ ] SQL Editor: `create extension if not exists vector no schema public;`
- [ ] Storage: bucket `resumes`, **public off**.

## B. Machine (no Docker, no Ollama, no local Postgres)
- [ ] `node -v` ≥ 20, `python3 -V` ≥ 3.11, `pnpm -v`, `uv --version`
- [ ] `uv add "psycopg[binary]" sqlalchemy httpx pyyaml ddgs fastembed`
- [ ] Ollama uninstalled or stopped (it was the heat source; nothing depends on it).
- [ ] Repo lives at `C:\dev\interviewOS`, not in `Downloads` (OneDrive + venv do not mix).

## C. Repo
- [ ] Root `.env` created from `.env.example`, with `DATABASE_URL` (port 6543) **and** `DIRECT_URL` (port 5432).
- [ ] `.env` is in `.gitignore`; `git status` does not show it.
- [ ] `contracts/`, `data/`, `docs/`, `prompts/`, `scripts/` copied in from the Day-0 pack.
- [ ] `types/api.ts` = copy of `contracts/types.ts` (the UI imports from here).

## D. Verify
```powershell
cd C:\dev\interviewOS
uv run python scripts/verify_env.py
```
- [ ] All checks PASS. Typical failures:
  - `password contains a raw '@'` → percent-encode it (`%40`) or reset to a symbol-free password.
  - `pgvector installed: FAIL` → run the `create extension` statement again, then re-run.
  - `gemini 429` → you are on a rate limit; wait 60 s (15 RPM).
  - `web search FAIL` → `uv add ddgs`; if DuckDuckGo blocks the IP, set `SEARCH_BACKEND` later to SearXNG.

## E. Then, in this order
1. `prompts/01-design-system-and-shell.md` → Antigravity → screenshot `/shell-demo` back to me.
2. `prompts/02-landing.md`
3. `prompts/03-dashboard.md`
4. Backend Day 1 (with me): app skeleton, models + migration, `llm_cache`, LLM gateway, `/health`, `/ready`.

## Standing rules
- One Antigravity pack per sitting; its free quota refreshes ~ every 5 hours.
- Never let a builder touch `contracts/`, `data/`, `lib/api.ts` or `backend/`.
- Never paste secrets into chat again — masked values only.
