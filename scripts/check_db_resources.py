#!/usr/bin/env python3
"""
InterviewOS — does the database's resource catalogue match data/curated.yaml?

The seed is generated from the YAML, so after a paste the two should agree exactly.
When they don't, the usual cause is a URL that was *edited* rather than added:
`resources.url` is unique, so an upsert inserting a corrected URL leaves the old row
behind. Two orphan rows look like a data problem and are really a bookkeeping one.

    python scripts/check_db_resources.py            # report only, changes nothing
    python scripts/check_db_resources.py --prune    # delete rows the YAML does not list

The comparison is set-based on `url`, which is the seed's conflict key. Rows whose
URL is not in curated.yaml are reported with the skill/subtopic they claim, so you can
see what a delete would remove before removing it. `--prune` is destructive only for
rows already listed in the report; it prints every URL it deletes.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import yaml
from sqlalchemy import text

CURATED = ROOT / "data" / "curated.yaml"


def catalogue_urls() -> dict[str, tuple[str, str]]:
    """url -> (skill_id, subtopic_id), from the source of truth."""
    data = yaml.safe_load(CURATED.read_text(encoding="utf-8")) or {}
    out: dict[str, tuple[str, str]] = {}
    for skill_id, by_sub in (data.get("catalogue") or {}).items():
        for subtopic_id, entries in by_sub.items():
            for entry in entries:
                out[entry["url"]] = (skill_id, subtopic_id)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prune", action="store_true", help="delete database rows whose URL is not in curated.yaml"
    )
    args = parser.parse_args()

    from app.config import get_settings

    if not get_settings().database_configured:
        print("DATABASE_URL is not set — nothing to compare. (Fixture mode.)")
        return 2

    from app.db import get_session

    expected = catalogue_urls()
    with get_session() as session:
        rows = session.execute(
            text(
                "select url, curated_skill_id, curated_subtopic_id, tier, created_at "
                "from public.resources order by created_at"
            )
        ).mappings().all()

        db_urls = {row["url"] for row in rows}
        extra = [row for row in rows if row["url"] not in expected]
        missing = [url for url in expected if url not in db_urls]

        print(f"curated.yaml : {len(expected)} resources")
        print(f"database     : {len(rows)} resources")
        print(f"matched      : {len(db_urls & set(expected))}")

        if missing:
            print(f"\n{len(missing)} in curated.yaml but NOT in the database "
                  f"— re-paste docs/sql/002_seed.sql:")
            for url in missing[:20]:
                skill, sub = expected[url]
                print(f"  {skill}/{sub}  {url}")
            if len(missing) > 20:
                print(f"  … and {len(missing) - 20} more")

        if not extra:
            print("\nno extra rows — the database matches the catalogue exactly.")
            return 0

        print(f"\n{len(extra)} row(s) in the database that curated.yaml no longer lists:")
        for row in extra:
            where = (
                f"{row['curated_skill_id']}/{row['curated_subtopic_id']}"
                if row["curated_skill_id"]
                else "(not curated)"
            )
            print(f"  tier {row['tier']}  {where}  {row['url']}")

        if not args.prune:
            print("\nnothing deleted. Re-run with --prune to remove exactly the rows above.")
            return 1

        urls = [row["url"] for row in extra]
        deleted = session.execute(
            text("delete from public.resources where url = any(:urls)"), {"urls": urls}
        ).rowcount
        session.commit()
        print(f"\ndeleted {deleted} row(s).")
        for url in urls:
            print(f"  - {url}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
