"""The environment doctor must run and pass in a healthy environment.

It is the first thing to run when an import fails, so it cannot be the thing that
fails — stdlib only, no app imports.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DOCTOR = Path(__file__).resolve().parent.parent / "scripts" / "doctor.py"


def test_doctor_exists_and_runs_on_a_healthy_environment():
    result = subprocess.run(
        [sys.executable, str(DOCTOR)], capture_output=True, text=True, timeout=180, check=False
    )
    output = result.stdout + result.stderr
    assert "Verdict" in output, output
    assert result.returncode == 0, output


def test_doctor_has_no_third_party_imports():
    """If the doctor needed pydantic, it could not diagnose a broken pydantic."""
    source = DOCTOR.read_text(encoding="utf-8")
    body = source.split('"""', 2)[2]  # skip the module docstring
    for package in ("pydantic", "fastapi", "sqlalchemy"):
        assert f"import {package}" not in body or "importlib" in body
