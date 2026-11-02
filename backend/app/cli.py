"""`python -m app.cli parse resume.pdf` — the pipeline, without the API.

Useful for two things: trying the parser on a real document before any upload
flow exists, and showing a sceptic exactly which line produced which claim.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from app.parsing import jd as jd_mod
from app.parsing import resume as resume_mod
from app.parsing.extract import UnparseableDocument, extract
from app.prep import priority
from app.prep.profile import build_profile


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


def cmd_analyze(resume_path: str, jd_path: str, as_json: bool) -> int:
    """resume + JD → scored profile. No model, no database, no network."""
    try:
        resume_doc = extract(pathlib.Path(resume_path).name, pathlib.Path(resume_path).read_bytes())
        jd_text = pathlib.Path(jd_path).read_text()
    except (OSError, UnparseableDocument) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2

    parsed_resume = resume_mod.parse(resume_doc)
    parsed_jd = jd_mod.parse(jd_text)
    rows = priority.score(parsed_resume, parsed_jd)
    payload = build_profile(rows)

    if as_json:
        print(json.dumps({
            "resume": {"filename": resume_doc.filename, "sha256": resume_doc.sha256,
                       "stats": parsed_resume.stats},
            "jd": parsed_jd.as_json(),
            "profile": payload,
        }, indent=2))
        return 0

    print(f"resume: {resume_doc.filename} · {parsed_resume.stats['skills_found']} skills · "
          f"{parsed_resume.stats['quotes']} quotes")
    print(f"jd: {parsed_jd.title or '(untitled)'} · {parsed_jd.stats['requirements_found']} "
          f"requirements ({parsed_jd.stats['required']} required, "
          f"{parsed_jd.stats['preferred']} preferred) · rounds {parsed_jd.interview_rounds}"
          f" (inferred)")
    print(f"counts: {payload['counts']}")
    print()
    print(f"{'#':>2} {'skill':16}{'band':10}{'prio':>6}{'gap':>6}{'jd':>5}{'you':>14}  why")
    print("-" * 118)
    for index, row in enumerate(payload["skills"][:14], start=1):
        print(f"{index:>2} {row['skill_id']:16}{row['priority_band']:10}{row['priority']:>6.3f}"
              f"{row['gap']:>6}{row['jd_importance']:>5}  {row['claimed_level'] or '-':>12}"
              f"  {row['explanation'][:64]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="InterviewOS pipelines")
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="extract + match a resume (no model, no network)")
    parse_cmd.add_argument("path")
    parse_cmd.add_argument("--json", action="store_true")

    analyze = sub.add_parser("analyze", help="resume + JD → scored profile (no model, no network)")
    analyze.add_argument("resume")
    analyze.add_argument("jd")
    analyze.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "parse":
        return cmd_parse(args.path, args.json)
    if args.command == "analyze":
        return cmd_analyze(args.resume, args.jd, args.json)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
