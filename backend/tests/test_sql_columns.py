"""The SQL in this repo must name columns that exist in docs/sql/001_init.sql.

This test exists because of a real bug: `dashboard_payload` selected
`r.overall_score` (the column is `overall_scores`) and ordered by `s.created_at`
(the column is `started_at`). Postgres raised, the route caught it, served fixtures,
and `X-Data-Source: fixture` looked exactly like "no data yet". The dashboard was
never broken-looking — it was wrong-looking, which is worse.

Fixtures and response models cannot catch a wrong column name. The DDL can.
"""
import importlib.util
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "check_sql_columns.py"
APP = REPO / "backend" / "app"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_sql_columns", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return load_checker()


def test_ddl_parses_into_tables_and_columns(checker):
    tables = checker.schema()
    assert "interview_reports" in tables and "candidate_skills" in tables
    # Spot-check the two columns this test file is named for.
    assert "overall_scores" in tables["interview_reports"]
    assert "started_at" in tables["interview_sessions"]
    assert "created_at" not in tables["interview_sessions"]


def test_every_query_in_the_app_matches_the_schema(checker):
    tables = checker.schema()
    problems = []
    checked = 0
    for path in sorted(APP.rglob("*.py")):
        for sql in checker.sql_strings(path.read_text(encoding="utf-8")):
            checked += 1
            for bad in checker.check(sql, tables):
                problems.append(f"{path.relative_to(REPO)}: {bad}")
    assert checked >= 10, f"only {checked} queries were found — the scanner is not seeing them"
    assert not problems, "queries name columns the schema does not have:\n" + "\n".join(problems)


def test_the_checker_rejects_the_query_that_actually_shipped_broken(checker):
    """Regression, verbatim: the pre-fix dashboard query must fail this check."""
    broken = (
        "select s.id, s.mode, s.channel, r.overall_score, s.duration_minutes, s.created_at "
        "from public.interview_sessions s "
        "left join public.interview_reports r on r.session_id = s.id "
        "where s.user_id = cast(:user_id as uuid) order by s.created_at desc limit 10"
    )
    problems = checker.check(broken, checker.schema())
    assert "r.overall_score (table interview_reports)" in problems
    assert "s.created_at (table interview_sessions)" in problems


def test_the_checker_does_not_flag_valid_sql(checker):
    """A guard that cries wolf gets deleted, so pin the shapes we rely on."""
    good = (
        "select p.target_role, c.status, count(*) as n, "
        "(r.overall_scores->>'overall')::numeric as score "
        "from public.candidate_skills c "
        "join public.profiles p on p.id = c.user_id "
        "left join public.interview_reports r on r.user_id = p.id "
        "where c.user_id = cast(:user_id as uuid) "
        "group by p.target_role, c.status "
        "order by c.status::text"
    )
    assert checker.check(good, checker.schema()) == []


def test_a_string_literal_that_looks_like_a_column_is_ignored(checker):
    sql = "select (r.overall_scores->>'overall')::numeric from public.interview_reports r"
    assert checker.check(sql, checker.schema()) == []
