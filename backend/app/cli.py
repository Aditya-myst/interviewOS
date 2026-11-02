"""`python -m app.cli parse resume.pdf` — the pipeline, without the API.

Useful for two things: trying the parser on a real document before any upload
flow exists, and showing a sceptic exactly which line produced which claim.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from app.parsing import resume as resume_mod
from app.parsing.extract import UnparseableDocument, extract


def cmd_parse(path: str, as_json: bool) -> int:
    file_path = pathlib.Path(path)
    if not file_path.exists():
        print(f"no such file: {path}", file=sys.stderr)
        return 2
    try:
        document = extract(file_path.name, file_path.read_bytes())
    except UnparseableDocument as exc:
        print(json.dumps({"parse_status": "unparseable", "reason": exc.reason,
                          "detail": exc.detail}, indent=2) if as_json
              else f"unparseable — {exc.reason}: {exc.detail}")
        return 1

    parsed = resume_mod.parse(document)
    if as_json:
        print(json.dumps({"parse_status": "ok", "document": {
            "filename": document.filename, "kind": document.kind,
            "chars": len(document.text), "pages": len(document.pages),
            "sha256": document.sha256}, **parsed.as_json()}, indent=2))
        return 0

    stats = parsed.stats
    print(f"{document.filename} · {document.kind} · {stats['chars']} chars · "
          f"{stats['pages']} page(s) · sha256 {document.sha256[:12]}")
    print(f"skills {stats['skills_found']} · quotes {stats['quotes']} · "
          f"levels {stats['by_claimed_level']} · method: {stats['method']}")
    print(f"experience: {parsed.experience_years} ({parsed.experience_basis})")
    if document.warnings:
        print("warnings: " + "; ".join(document.warnings))
    print()
    id_width = max([len(c.skill_id) for c in parsed.skills] + [5]) + 2
    cat_width = max([len(c.category) for c in parsed.skills] + [8]) + 2
    print(f"{'skill':{id_width}}{'category':{cat_width}}{'claimed':14}{'conf':>5}  quote")
    print("-" * (id_width + cat_width + 14 + 5 + 78))
    for claim in parsed.skills:
        first = claim.mentions[0]
        quote = " ".join(first.quote.split())
        print(f"{claim.skill_id:{id_width}}{claim.category:{cat_width}}"
              f"{claim.claimed_level:14}{claim.confidence:>5}  [{first.section}] {quote[:60]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="InterviewOS pipelines")
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="extract + match a resume (no model, no network)")
    parse_cmd.add_argument("path")
    parse_cmd.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "parse":
        return cmd_parse(args.path, args.json)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
