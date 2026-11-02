"""Generate docs/sql/002_seed.sql from data/taxonomy.yaml + data/curated.yaml.

The seed used to be hand-maintained, which meant adding one skill was a two-file
edit with a silent failure mode: the YAML says 32 skills, the SQL still inserts 31,
and `/dev/db` reports a mismatch that looks like a database problem. This script
makes the SQL a build artefact of the data.

    python scripts/gen_seed.py            # write docs/sql/002_seed.sql
    python scripts/gen_seed.py --check    # fail if the file is out of date (CI)

The generated file stays idempotent: every insert is an upsert on a natural key, so
re-running it against a seeded project updates rows and never duplicates them.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "data" / "taxonomy.yaml"
CURATED = ROOT / "data" / "curated.yaml"
TARGET = ROOT / "docs" / "sql" / "002_seed.sql"

HEADER = """\
-- ═══════════════════════════════════════════════════════════════════════════
-- InterviewOS — 002_seed.sql
-- Seeds the global vocabulary and the tier-0 resource catalogue.
--
-- GENERATED FILE — do not edit by hand.
--   source: data/taxonomy.yaml ({n_skills} skills / {n_subtopics} subtopics)
--           data/curated.yaml  ({n_resources} hand-curated resources)
--   regenerate: python scripts/gen_seed.py
--
-- Run AFTER 001_init.sql. Safe to re-run: every insert is an upsert on the
-- natural key, and nothing user-owned is touched.
--
-- PowerShell: paste into the Supabase SQL editor like 001. From a terminal:
--   psql "$env:DATABASE_URL" -f docs\\sql\\002_seed.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;
"""


def sql_str(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def sql_text_array(values: list[str]) -> str:
    return "array[" + ", ".join(sql_str(v) for v in values) + "]::text[]"


def sql_or_null(value) -> str:
    return "null" if value in (None, "") else sql_str(value)


def build() -> str:
    taxonomy = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}
    curated = yaml.safe_load(CURATED.read_text(encoding="utf-8")) or {}
    skills = taxonomy.get("skills", [])
    catalogue = curated.get("catalogue", {})
    stamp = str(taxonomy.get("updated", "")).strip()
    n_subtopics = sum(len(s.get("subtopics") or []) for s in skills)
    n_resources = sum(len(rows) for by_sub in catalogue.values() for rows in by_sub.values())

    if not skills:
        raise SystemExit("data/taxonomy.yaml has no skills — refusing to write an empty seed")
    missing_subtopics = [s["id"] for s in skills if not (s.get("subtopics") or [])]
    if missing_subtopics:
        raise SystemExit(
            "every skill needs subtopics or the roadmap has nothing to teach: "
            + ", ".join(missing_subtopics)
        )

    out = [HEADER.format(n_skills=len(skills), n_subtopics=n_subtopics, n_resources=n_resources)]

    # ── skills ───────────────────────────────────────────────────────────────
    out.append("\n-- ── skills ────────────────────────────────────────────────────────────────\n")
    out.append("insert into public.skills (id, name, category, aliases, interview_relevance) values\n")
    rows = [
        f"  ({sql_str(s['id'])}, {sql_str(s['name'])}, {sql_str(s.get('category', 'Other'))}, "
        f"{sql_text_array(s.get('aliases') or [])}, {float(s.get('interview_relevance', 0.5))})"
        for s in skills
    ]
    out.append(",\n".join(rows))
    out.append(
        "\non conflict (id) do update set\n"
        "  name                = excluded.name,\n"
        "  category            = excluded.category,\n"
        "  aliases             = excluded.aliases,\n"
        "  interview_relevance = excluded.interview_relevance;\n"
    )

    # ── subtopics ────────────────────────────────────────────────────────────
    out.append(
        f"\n-- ── skill_subtopics (the curriculum graph; {n_subtopics} rows) ──────────────\n"
    )
    out.append(
        "insert into public.skill_subtopics "
        "(skill_id, subtopic_id, title, level, objective, order_index) values\n"
    )
    rows = []
    for skill in skills:
        for index, subtopic in enumerate(skill.get("subtopics") or []):
            rows.append(
                f"  ({sql_str(skill['id'])}, {sql_str(subtopic['id'])}, "
                f"{sql_str(subtopic['title'])}, "
                f"{sql_str(subtopic.get('level', 'beginner'))}::public.proficiency_level, "
                f"{sql_str(subtopic.get('objective', ''))}, {index})"
            )
    out.append(",\n".join(rows))
    out.append(
        "\non conflict (skill_id, subtopic_id) do update set\n"
        "  title       = excluded.title,\n"
        "  level       = excluded.level,\n"
        "  objective   = excluded.objective,\n"
        "  order_index = excluded.order_index;\n"
    )

    # ── resources ────────────────────────────────────────────────────────────
    out.append(
        "\n-- ── resources: tier 0, the hand-curated catalogue ────────────────────────\n"
        "-- curated_skill_id / curated_subtopic_id record which subtopic each row is the\n"
        "-- canonical answer for. verified_at uses the catalogue's own assembly date\n"
        "f-- (taxonomy.yaml `updated: {stamp}`) for links marked `verified: true` in\n"
        "-- curated.yaml — it is the date the link was hand-checked, not the date this\n"
        "-- file ran. Everything else is stamped by the link-check job.\n".replace("f--", "--")
    )
    out.append(
        "insert into public.resources\n"
        "  (url, title, provider, kind, is_paid, license, tier,\n"
        "   curated_skill_id, curated_subtopic_id, verified_at)\nvalues\n"
    )
    rows = []
    for skill_id, by_subtopic in catalogue.items():
        for subtopic_id, entries in by_subtopic.items():
            for entry in entries:
                verified = entry.get("verified") is True
                stamp_sql = f"timestamptz '{stamp} 00:00:00+00'" if verified and stamp else "null"
                rows.append(
                    f"  ({sql_str(entry['url'])}, {sql_str(entry['title'])}, "
                    f"{sql_or_null(entry.get('provider'))}, "
                    f"{sql_str(entry.get('kind', 'docs'))}::public.resource_kind, "
                    f"{'true' if entry.get('is_paid') else 'false'}, "
                    f"{sql_or_null(entry.get('license'))}, 0, "
                    f"{sql_str(skill_id)}, {sql_str(subtopic_id)}, {stamp_sql})"
                )
    out.append(",\n".join(rows))
    out.append(
        "\non conflict (url) do update set\n"
        "  title               = excluded.title,\n"
        "  provider            = excluded.provider,\n"
        "  kind                = excluded.kind,\n"
        "  is_paid             = excluded.is_paid,\n"
        "  license             = excluded.license,\n"
        "  tier                = least(public.resources.tier, excluded.tier),\n"
        "  curated_skill_id    = excluded.curated_skill_id,\n"
        "  curated_subtopic_id = excluded.curated_subtopic_id,\n"
        "  verified_at         = coalesce(public.resources.verified_at, excluded.verified_at),\n"
        "  updated_at          = now();\n"
    )

    # ── post-seed check ──────────────────────────────────────────────────────
    out.append(
        f"""
commit;

-- ── Post-seed sanity check ────────────────────────────────────────────────
do $do$
declare
  n_skills integer;
  n_subtopics integer;
  n_resources integer;
begin
  select count(*) into n_skills from public.skills;
  select count(*) into n_subtopics from public.skill_subtopics;
  select count(*) into n_resources from public.resources;
  raise notice 'seeded: % skills, % subtopics, % resources', n_skills, n_subtopics, n_resources;
  if n_skills <> {len(skills)} then
    raise warning 'expected {len(skills)} skills, found % — is the seed out of date? '
      'Run: python scripts/gen_seed.py', n_skills;
  end if;
  if n_subtopics < {n_subtopics} then
    raise warning 'expected at least {n_subtopics} subtopics, found % — is the seed out of date?',
      n_subtopics;
  end if;
end;
$do$;
"""
    )
    return "".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the seed SQL from the YAML data files")
    parser.add_argument("--check", action="store_true", help="verify the file is up to date")
    args = parser.parse_args(argv)

    generated = build()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current.strip() != generated.strip():
            print(
                f"{TARGET.relative_to(ROOT)} is out of date with data/. "
                "Run: python scripts/gen_seed.py",
                file=sys.stderr,
            )
            return 1
        print(f"{TARGET.relative_to(ROOT)} matches data/taxonomy.yaml + data/curated.yaml")
        return 0

    TARGET.write_text(generated, encoding="utf-8")
    taxonomy = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}
    skills = taxonomy.get("skills", [])
    print(
        f"wrote {TARGET.relative_to(ROOT)}: {len(skills)} skills, "
        f"{sum(len(s.get('subtopics') or []) for s in skills)} subtopics"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
