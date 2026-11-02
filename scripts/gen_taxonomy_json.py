#!/usr/bin/env python3
"""
InterviewOS — build contracts/taxonomy.json from data/.

The marketing page shows the real curriculum: how many skills the graph holds, how
many subtopics each has, and how many of them have a curated, HTTP-checked resource.
Those numbers already exist in data/taxonomy.yaml and data/curated.yaml — this
publishes them as JSON the frontend can read at build time instead of hardcoding
"41 skills" in a headline and letting it drift.

    python scripts/gen_taxonomy_json.py

Exit code is not zero if the files are missing; the frontend shows a labelled empty
state rather than inventing numbers.
"""

from __future__ import annotations

import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "data" / "taxonomy.yaml"
CURATED = ROOT / "data" / "curated.yaml"
OUT = ROOT / "contracts" / "taxonomy.json"


def build() -> dict:
    taxonomy = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8")) or {}
    curated = (yaml.safe_load(CURATED.read_text(encoding="utf-8")) or {}).get("catalogue") or {}

    skills = []
    for skill in taxonomy.get("skills") or []:
        subtopics = skill.get("subtopics") or []
        taught = curated.get(skill["id"]) or {}
        skills.append(
            {
                "id": skill["id"],
                "name": skill["name"],
                "category": skill.get("category", "Other"),
                "subtopics": len(subtopics),
                "resources": sum(len(rows) for rows in taught.values()),
                "teach": sum(1 for sub in subtopics if taught.get(sub["id"])),
            }
        )

    skills.sort(key=lambda s: (-s["resources"], s["name"]))
    return {
        "_comment": (
            "GENERATED from data/taxonomy.yaml and data/curated.yaml by "
            "scripts/gen_taxonomy_json.py — do not edit by hand."
        ),
        "updated": taxonomy.get("updated"),
        "totals": {
            "skills": len(skills),
            "subtopics": sum(s["subtopics"] for s in skills),
            "resources": sum(s["resources"] for s in skills),
            "skills_with_resources": sum(1 for s in skills if s["resources"]),
        },
        "skills": skills,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    totals = payload["totals"]
    print(
        f"wrote {OUT.relative_to(ROOT)}: {totals['skills']} skills, "
        f"{totals['subtopics']} subtopics, {totals['resources']} resources"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
