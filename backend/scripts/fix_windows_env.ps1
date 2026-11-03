# Repair the backend environment on Windows.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\fix_windows_env.ps1
#
# Deletes a half-removed .venv (the cause of "failed to locate pyvenv.cfg" and
# "Access is denied ... uvicorn.exe"), rebuilds it from the committed uv.lock, then
# runs the doctor and the test suite. Safe to run more than once.

$ErrorActionPreference = "Continue"
$backend = Split-Path -Parent $PSScriptRoot
Set-Location $backend
Write-Host "backend: $backend" -ForegroundColor Cyan

# ── 1. close anything running out of this venv ──────────────────────────────
Write-Host "`n[1/6] closing processes that hold the venv" -ForegroundColor Cyan
$held = Get-CimInstance Win32_Process |
    Where-Object { $_.ExecutablePath -and $_.ExecutablePath -like "*$backend*" }
if ($held) {
    foreach ($proc in $held) {
        Write-Host "      stopping $($proc.Name) ($($proc.ProcessId))"
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "      nothing running from this folder"
}

# ── 2. remove the broken venv; rename first when a file is locked ───────────
Write-Host "`n[2/6] removing .venv" -ForegroundColor Cyan
if (Test-Path .venv) {
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
}
if (Test-Path .venv) {
    Write-Host "      delete was refused — renaming instead"
    Remove-Item -Recurse -Force .venv-broken -ErrorAction SilentlyContinue
    Rename-Item .venv .venv-broken -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .venv-broken -ErrorAction SilentlyContinue
}
if (Test-Path .venv) {
    Write-Host "      FAILED: .venv is still there." -ForegroundColor Red
    Write-Host "      Close every terminal that ran uvicorn, then run this script again." -ForegroundColor Red
    Write-Host "      If it keeps failing, the folder is protected: move the repo out of Downloads." -ForegroundColor Red
    exit 1
}
Write-Host "      gone"

# ── 3. a stale VIRTUAL_ENV is what makes uv say 'failed to locate pyvenv.cfg' ─
Write-Host "`n[3/6] clearing stale environment variables for this process" -ForegroundColor Cyan
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Write-Host "      done"

# ── 4. rebuild from the committed lock ─────────────────────────────────────
Write-Host "`n[4/6] uv sync --frozen" -ForegroundColor Cyan
uv sync --frozen
if (-not (Test-Path .venv\pyvenv.cfg)) {
    Write-Host "      FAILED: uv did not produce a usable .venv" -ForegroundColor Red
    exit 1
}
Write-Host "      .venv\pyvenv.cfg present — environment is real" -ForegroundColor Green

# ── 5. doctor ──────────────────────────────────────────────────────────────
Write-Host "`n[5/6] doctor" -ForegroundColor Cyan
uv run python scripts/doctor.py
$doctor = $LASTEXITCODE

# ── 6. tests ───────────────────────────────────────────────────────────────
Write-Host "`n[6/6] tests" -ForegroundColor Cyan
uv run python -m pytest -q
$tests = $LASTEXITCODE

Write-Host "`n─────────────────────────────────────────────"
if ($doctor -eq 0 -and $tests -eq 0) {
    Write-Host "READY. Start the API with:" -ForegroundColor Green
    Write-Host "  uv run uvicorn app.main:app --reload --port 8000"
    Write-Host "Watch for: interviewos ready — env=dev data=database llm=none"
} else {
    Write-Host "NOT ready — doctor exit $doctor, tests exit $tests" -ForegroundColor Red
    Write-Host "Copy the FAIL lines above and send them on."
}
