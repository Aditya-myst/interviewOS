"""Windows-facing scripts must be pure ASCII.

PowerShell 5.1 reads a BOM-less UTF-8 script as ANSI. An em dash is three bytes
(0xE2 0x80 0x94) and 0x94 decodes to U+201D, which PowerShell treats as a string
terminator -- so a single decorative dash in a comment breaks the whole script with
"the string is missing the terminator". The script that was supposed to repair the
environment failed to parse for exactly that reason.

Keep them ASCII. This test is the tripwire.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WINDOWS_SUFFIXES = {".ps1", ".psm1", ".bat", ".cmd"}


def test_no_windows_script_contains_non_ascii():
    offenders = []
    for path in REPO.rglob("*"):
        if path.suffix.lower() not in WINDOWS_SUFFIXES:
            continue
        if any(part in {".venv", "node_modules", ".git"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        bad = sorted({c for c in text if ord(c) > 127})
        if bad:
            offenders.append(f"{path.relative_to(REPO)}: {bad}")
    assert not offenders, "non-ASCII in a Windows script:\n" + "\n".join(offenders)


def test_windows_scripts_parse_if_powershell_is_available():
    """Skip unless pwsh is installed; when it is, actually parse the .ps1 files."""
    import shutil
    import subprocess

    pwsh = shutil.which("pwsh")
    if pwsh is None:
        import pytest

        pytest.skip("pwsh not installed")

    for path in REPO.rglob("*.ps1"):
        if any(part in {".venv", "node_modules", ".git"} for part in path.parts):
            continue
        cmd = (
            "$e=$null;$t=$null;"
            f"[System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$t,[ref]$e)|Out-Null;"
            "if($e.Count){$e|%{$_.Message};exit 1}else{exit 0}"
        )
        result = subprocess.run([pwsh, "-NoProfile", "-Command", cmd], capture_output=True, text=True, check=False)
        assert result.returncode == 0, f"{path.name}: {result.stdout}{result.stderr}"
