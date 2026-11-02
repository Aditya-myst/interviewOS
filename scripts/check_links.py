#!/usr/bin/env python3
"""
InterviewOS — resource link check.

The product claim is "every learning link is HTTP-verified before you see it".
This is that check, as a script you can run instead of trusting a screenshot.

    uv run python scripts/check_links.py                 # curated catalogue
    uv run python scripts/check_links.py --fixtures      # + roadmap fixture URLs
    uv run python scripts/check_links.py --json out.json

Exit code is 1 if anything is dead, so CI or a nightly job can fail on it.
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import pathlib
import sys
import time

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = (
    "Mozilla/5.0 (compatible; InterviewOS link-check/0.1; "
    "+https://github.com/Aditya-myst/interviewOS)"
)
HEADERS = {"User-Agent": UA}

# A link is only usable if it is a real page a human can read for free.
REQUIRED_CONTENT_TYPES = ("text/html", "application/pdf", "text/plain")


def collect(fixtures: bool) -> dict[str, list[str]]:
    """url -> list of "where it is referenced" strings."""
    found: dict[str, list[str]] = {}

    catalogue = yaml.safe_load((ROOT / "data" / "curated.yaml").read_text())["catalogue"]
    for skill, subtopics in catalogue.items():
        for subtopic, resources in subtopics.items():
            for r in resources:
                found.setdefault(r["url"], []).append(f"curated:{skill}/{subtopic}")

    if fixtures:
        path = ROOT / "contracts" / "fixtures" / "roadmap.json"
        if path.exists():
            roadmap = json.loads(path.read_text())
            for topic in roadmap.get("topics", []):
                for r in topic.get("resources", []):
                    found.setdefault(r["url"], []).append(f"fixture:{topic['title']}")

    return found


def check(url: str) -> dict:
    started = time.monotonic()
    try:
        r = requests.get(
            url, headers=HEADERS, timeout=20, allow_redirects=True, stream=True
        )
        ctype = r.headers.get("content-type", "").split(";")[0].strip().lower()
        ok = r.status_code == 200 and (
            not ctype or ctype in REQUIRED_CONTENT_TYPES
        )
        return {
            "url": url,
            "status": r.status_code,
            "final_url": r.url,
            "content_type": ctype,
            "ok": ok,
            "ms": int((time.monotonic() - started) * 1000),
            "note": "" if ok else f"unusable content-type: {ctype or 'none'}",
        }
    except requests.RequestException as e:
        return {
            "url": url,
            "status": None,
            "final_url": None,
            "content_type": None,
            "ok": False,
            "ms": int((time.monotonic() - started) * 1000),
            "note": type(e).__name__,
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", action="store_true", help="also check fixture URLs")
    ap.add_argument("--json", metavar="PATH", help="write full results as JSON")
    args = ap.parse_args()

    urls = collect(args.fixtures)
    print(f"checking {len(urls)} unique URLs…\n")

    with futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(check, urls))

    for res in sorted(results, key=lambda r: (not r["ok"], r["url"])):
        mark = "ok  " if res["ok"] else "DEAD"
        status = res["status"] if res["status"] is not None else "---"
        extra = ""
        if res["final_url"] and res["final_url"] != res["url"]:
            extra = f" -> {res['final_url']}"
        if res["note"]:
            extra += f"  [{res['note']}]"
        print(f"{mark} {str(status):>3}  {res['ms']:>4}ms  {res['url']}{extra}")

    bad = [r for r in results if not r["ok"]]
    by_domain: dict[str, int] = {}
    for res in results:
        domain = res["url"].split("/")[2]
        by_domain[domain] = by_domain.get(domain, 0) + 1

    print(
        f"\n{len(results) - len(bad)}/{len(results)} alive"
        f" across {len(by_domain)} domains"
    )
    if bad:
        print("dead:", ", ".join(r["url"] for r in bad))

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(
                {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "results": results},
                indent=1,
            )
        )
        print(f"wrote {args.json}")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
