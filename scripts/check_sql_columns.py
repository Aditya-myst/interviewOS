#!/usr/bin/env python3
"""
InterviewOS — does the SQL in this repo name columns that actually exist?

Why this exists: `dashboard_payload` joined `interview_reports` on `r.overall_score`
and ordered by `s.created_at`. Neither column exists (the schema has `overall_scores`
and `started_at`). Postgres raised, the route caught it and served fixtures — so the
dashboard looked *fine* and the header said `fixture`, which reads exactly like
"this user has no data yet". A wrong column name is silent by default; this makes it
loud.

It reads the DDL from docs/sql/001_init.sql (the file the database was actually
created from) and checks every alias-qualified column reference in a `text(...)`
query against it. No dependencies, no database.

    python scripts/check_sql_columns.py            # every module under backend/app
    python scripts/check_sql_columns.py -v         # list every query it checked

Exit code 1 if a query names a column the schema does not have.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DDL = ROOT / "docs" / "sql" / "001_init.sql"
APP = ROOT / "backend" / "app"

CREATE_TABLE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?public\.(\w+)\s*\((.*?)\n\);",
    re.IGNORECASE | re.DOTALL,
)
# Constraint lines start a column definition but are not columns.
NOT_A_COLUMN = re.compile(r"^\s*(primary|unique|constraint|foreign|check|exclude)\b", re.I)
# `from public.x a` / `join public.x as a` / `from public.x` (alias = table name)
FROM_TABLE = re.compile(
    r"\b(?:from|join)\s+public\.(\w+)(?:\s+(?:as\s+)?(\w+))?",
    re.IGNORECASE,
)
QUALIFIED = re.compile(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", re.IGNORECASE)
SQL_KEYWORDS_AFTER_DOT = {"text", "numeric", "int", "integer", "uuid", "jsonb", "date"}


def schema(ddl_path: pathlib.Path = DDL) -> dict[str, set[str]]:
    """table name -> column names, straight from the DDL."""
    tables: dict[str, set[str]] = {}
    for name, body in CREATE_TABLE.findall(ddl_path.read_text(encoding="utf-8")):
        columns: set[str] = set()
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("--") or NOT_A_COLUMN.match(stripped):
                continue
            column = re.match(r"([a-z_][a-z0-9_]*)", stripped, re.IGNORECASE)
            if column:
                columns.add(column.group(1).lower())
        tables[name.lower()] = columns
    if not tables:
        raise SystemExit(f"no create table statements found in {ddl_path}")
    return tables


def sql_strings(source: str) -> list[str]:
    """Every `text(...)` argument in a module, re-joined from its literals."""
    found: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name != "text" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            found.append(arg.value)
        elif isinstance(arg, ast.JoinedStr):
            pass  # f-strings are not SQL in this codebase; skip rather than guess
        else:
            # text("a" "b" "c") collapses to one Constant; anything else is unusual.
            parts = [n.value for n in ast.walk(arg) if isinstance(n, ast.Constant)]
            found.append(" ".join(p for p in parts if isinstance(p, str)))
    return [s for s in found if s.strip()]


def unquote(sql: str) -> str:
    """Drop string literals so 'overall' inside ->>'overall' is not read as a column."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def check(sql: str, tables: dict[str, set[str]]) -> list[str]:
    """Unknown alias-qualified columns in one query."""
    text = unquote(sql)
    aliases: dict[str, str] = {}
    for table, alias in FROM_TABLE.findall(text):
        table = table.lower()
        aliases[(alias or table).lower()] = table
    problems: list[str] = []
    for qualifier, column in QUALIFIED.findall(text):
        qualifier, column = qualifier.lower(), column.lower()
        if qualifier not in aliases or column in SQL_KEYWORDS_AFTER_DOT:
            continue
        table = aliases[qualifier]
        if column not in tables.get(table, set()):
            problems.append(f"{qualifier}.{column} (table {table})")
    return sorted(set(problems))


def label(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run(paths: list[pathlib.Path], tables: dict[str, set[str]], verbose: bool) -> int:
    failures = 0
    checked = 0
    for path in paths:
        for sql in sql_strings(path.read_text(encoding="utf-8")):
            checked += 1
            problems = check(sql, tables)
            if problems:
                failures += len(problems)
                print(f"\n{label(path)}")
                for problem in problems:
                    print(f"  no such column: {problem}")
                print(f"  in: {' '.join(sql.split())[:200]}")
            elif verbose:
                print(f"ok   {label(path)}  {' '.join(sql.split())[:90]}")
    print(
        f"\n{checked} queries checked against {len(tables)} tables — "
        + ("schema agrees" if not failures else f"{failures} bad column reference(s)")
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=pathlib.Path)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    paths = args.paths or sorted(APP.rglob("*.py"))
    return run(paths, schema(), args.verbose)


if __name__ == "__main__":
    sys.exit(main())
