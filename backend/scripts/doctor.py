"""Environment doctor — run this before debugging anything else.

    python scripts/doctor.py

It answers one question: *is the interpreter that is about to run uvicorn actually
using the packages you think it is?* Almost every "it installed fine but it cannot
import X" on Windows is one of these three:

  1. a *user* site-packages directory (`%APPDATA%\\Python\\Python311\\site-packages`)
     leaking into a venv, so `pydantic` comes from the venv and an older
     `pydantic_core` binary comes from the user directory — which fails with
     `cannot import name 'ArgsKwargs' from 'pydantic_core._pydantic_core' (unknown location)`
  2. a half-installed compiled wheel (interrupted download, antivirus quarantine)
  3. a global install plus a `--user` install layered on top of each other

Stdlib only: this has to work when nothing else imports.

Exit code 0 = usable, 1 = something must be fixed first.
"""
from __future__ import annotations

import importlib.util
import os
import platform
import site
import sys
import sysconfig
from pathlib import Path

REQUIRED = (
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic_core",
    "pydantic_settings",
    "sqlalchemy",
    "psycopg",
    "httpx",
    "yaml",
    "pypdf",
    "docx",
    "multipart",
)

OPTIONAL = ("pytest", "ruff")

PROBLEMS: list[str] = []
NOTES: list[str] = []


def head(text: str) -> None:
    print(f"\n{text}\n" + "-" * len(text))


def ok(text: str) -> None:
    print(f"  OK    {text}")


def warn(text: str) -> None:
    print(f"  WARN  {text}")
    NOTES.append(text)


def bad(text: str) -> None:
    print(f"  FAIL  {text}")
    PROBLEMS.append(text)


def site_dirs() -> list[str]:
    dirs = []
    for path in sys.path:
        if path and ("site-packages" in path or "dist-packages" in path):
            dirs.append(path)
    return dirs


def user_site() -> str:
    try:
        return site.getusersitepackages()
    except Exception:  # noqa: BLE001 — absent user site is not an error
        return ""


def check_interpreter() -> None:
    head("1. Interpreter")
    print(f"  python      {sys.version.split()[0]} ({platform.machine()})")
    print(f"  executable  {sys.executable}")
    print(f"  prefix      {sys.prefix}")
    in_venv = sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV"))
    if in_venv:
        ok("running inside a virtual environment")
    else:
        warn("not inside a virtual environment — installs land in a shared Python")

    if hasattr(sys, "flags") and sys.flags.no_user_site == 0:
        user = user_site()
        if user and os.path.isdir(user):
            entries = [e for e in os.listdir(user) if not e.startswith(("_", "."))][:6]
            warn(
                "the *user* site-packages directory is on this interpreter's path and is "
                f"not empty: {user} ({', '.join(entries) or 'no packages'}). Venvs inherit it "
                "unless PYTHONNOUSERSITE is set — this is the usual cause of a broken "
                "pydantic/pydantic_core pair."
            )


def check_paths() -> None:
    head("2. Import paths")
    dirs = site_dirs()
    if not dirs:
        bad("no site-packages on sys.path at all")
        return
    for path in dirs:
        marker = "this environment" if path.lower().startswith(sys.prefix.lower()) else "OUTSIDE this environment"
        print(f"  {marker:<24} {path}")
    user = user_site()
    leaks = [d for d in dirs if user and os.path.normcase(d) == os.path.normcase(user)]
    if leaks and sys.prefix != sys.base_prefix:
        bad(
            "a venv is active but the user site-packages directory is also being searched — "
            "compiled packages can resolve to two different versions"
        )
    elif leaks:
        warn("user site-packages is being searched (fine for a global install, not for a venv)")


def shadow_copies(*names: str) -> list[str]:
    """Copies of these packages that live outside the running environment.

    They are the suspects when an import fails: a venv can hold pydantic while a
    user-site directory holds an older pydantic_core, and the older binary wins.
    """
    found: list[str] = []
    for entry in sys.path:
        if not entry or entry.lower().startswith(sys.prefix.lower()):
            continue
        for name in names:
            candidate = Path(entry) / name
            if candidate.is_dir() or candidate.with_suffix(".py").exists():
                found.append(str(candidate))
    return found


def check_imports() -> None:
    head("3. Dependencies")
    for name in REQUIRED:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 — the error text is the finding
            bad(f"{name}: {type(exc).__name__}: {exc}")
            suspects = shadow_copies(name, "pydantic_core")
            for suspect in dict.fromkeys(suspects):
                print(f"        suspect copy outside this environment: {suspect}")
            continue
        path = getattr(module, "__file__", None) or "(built-in / namespace)"
        version = None
        for attr in ("__version__", "VERSION"):
            version = getattr(module, attr, None)
            if isinstance(version, str):
                break
            version = None
        label = f"{name} {version}" if version else name
        print(f"  OK    {label:<34} {path}")
        if path != "(built-in / namespace)" and not path.lower().startswith(sys.prefix.lower()):
            warn(f"{name} is imported from outside this environment ({path})")

    for name in OPTIONAL:
        if importlib.util.find_spec(name) is None:
            warn(f"{name} is not installed — the test suite and linter need it")
        else:
            ok(f"{name} present")


def check_pydantic_pair() -> None:
    head("4. pydantic / pydantic-core pair")
    try:
        import pydantic
        import pydantic_core
    except Exception as exc:  # noqa: BLE001
        bad(f"cannot import the pair: {type(exc).__name__}: {exc}")
        if "ArgsKwargs" in str(exc) or "unknown location" in str(exc):
            bad(
                "the two halves disagree — reinstall them together: "
                "pip install --force-reinstall --no-cache-dir pydantic pydantic-core"
            )
        return
    print(f"  pydantic       {pydantic.VERSION}")
    print(f"  pydantic_core  {pydantic_core.__version__}")
    print(f"  core file      {getattr(pydantic_core, '__file__', '?')}")
    same_dir = Path(pydantic.__file__).parent.parent == Path(pydantic_core.__file__).parent.parent
    if same_dir:
        ok("both installed in the same environment")
    else:
        bad("pydantic and pydantic_core come from different site-packages directories")


def check_project() -> None:
    head("5. Project")
    backend = Path(__file__).resolve().parent.parent
    repo = backend.parent
    fixtures = repo / "contracts" / "fixtures"
    if fixtures.is_dir():
        count = len(list(fixtures.glob("*.json")))
        ok(f"contracts/fixtures present ({count} json files)")
    else:
        bad(f"missing {fixtures} — is the repository complete?")

    env_file = repo / ".env"
    print(f"  .env          {'present' if env_file.exists() else 'absent (defaults apply)'}")

    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        try:
            from dotenv import dotenv_values  # type: ignore

            url = str(dotenv_values(env_file).get("DATABASE_URL") or "").strip()
            source = ".env"
        except Exception:  # noqa: BLE001
            source = "environment"
    else:
        source = "environment"

    if not url:
        ok("DATABASE_URL empty — the API will serve contracts/fixtures (fine for a demo)")
    else:
        scheme = url.split("://", 1)[0]
        print(f"  DATABASE_URL  set in {source}, scheme {scheme!r}")
        if scheme in ("postgres", "postgresql"):
            ok("bare postgres URL — the app rewrites it to postgresql+psycopg:// (psycopg 3)")
        if "%40" not in url and url.count("@") > 3:
            warn("the password may contain an unescaped '@' — encode it as %40")
        try:
            import psycopg  # noqa: F401

            ok("psycopg importable — the database should connect")
        except Exception as exc:  # noqa: BLE001
            bad(f"DATABASE_URL is set but psycopg is missing: {exc}")


def check_writable() -> None:
    head("6. Caches")
    for name in (".pytest_cache", ".ruff_cache"):
        target = Path(__file__).resolve().parent.parent / name
        try:
            target.mkdir(exist_ok=True)
            ok(f"{name} writable")
        except OSError as exc:
            warn(f"{name} not writable: {exc}")


def main() -> int:
    print("InterviewOS environment doctor")
    print(f"platform: {platform.platform()}")
    print(f"python  : {sysconfig.get_python_version()} ({'64-bit' if sys.maxsize > 2**32 else '32-bit'})")

    check_interpreter()
    check_paths()
    check_imports()
    check_pydantic_pair()
    check_project()
    check_writable()

    head("Verdict")
    if PROBLEMS:
        print(f"  {len(PROBLEMS)} problem(s) to fix before starting the API:")
        for item in PROBLEMS:
            print(f"    - {item}")
        print(
            "\n  Rebuilding cleanly is usually faster than repairing:\n"
            "    Remove-Item -Recurse -Force .venv\n"
            "    python -m venv .venv\n"
            "    .\\.venv\\Scripts\\Activate.ps1\n"
            '    $env:PYTHONNOUSERSITE = "1"\n'
            "    python -m pip install -U pip\n"
            "    pip install --no-cache-dir -e .\n"
            "    python scripts\\doctor.py"
        )
        return 1

    if NOTES:
        print(f"  usable, with {len(NOTES)} note(s) worth reading above")
    else:
        print("  usable — no problems found")
    print("\n  Next:  python -m pytest -q   then   python -m uvicorn app.main:app --reload --port 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
