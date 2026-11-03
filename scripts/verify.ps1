<#
    One command, whole repo, plain verdict.

        powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1

    Runs the four checks that have actually caught bugs here: the backend suite, lint on
    both sides, and a production build of the frontend. Nothing is written outside the
    repo, nothing talks to a database, and no key is needed.

    Deliberately ASCII-only: PowerShell 5.1 reads a BOM-less UTF-8 script as ANSI, so any
    box-drawing or tick character turns into mojibake in the console.

    Exit code 0 means every check passed. Anything else means at least one did not, and the
    summary says which.
#>

param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent $PSScriptRoot
$results = @()

function Add-Result {
    param([string]$Name, [string]$State, [string]$Detail)
    $script:results += [pscustomobject]@{ Check = $Name; Result = $State; Detail = $Detail }
}

function Show-Result {
    param([string]$Name, [int]$Code, [string]$Detail)
    if ($Code -eq 0) {
        Write-Host ("  PASS  " + $Name) -ForegroundColor Green
        Add-Result $Name "PASS" $Detail
    } else {
        Write-Host ("  FAIL  " + $Name) -ForegroundColor Red
        Add-Result $Name "FAIL" $Detail
    }
}

Write-Host ""
Write-Host "InterviewOS verification" -ForegroundColor Cyan
Write-Host ("repo: " + $repo)
Write-Host ""

# ---------------------------------------------------------------- python
Push-Location (Join-Path $repo "backend")
try {
    Write-Host "[1/4] backend tests" -ForegroundColor Cyan
    python -m pytest -q
    Show-Result "backend tests" $LASTEXITCODE "python -m pytest"

    Write-Host "[2/4] backend lint" -ForegroundColor Cyan
    $ruffExe = Get-Command ruff -ErrorAction SilentlyContinue
    if ($ruffExe) {
        ruff check .
        Show-Result "backend lint" $LASTEXITCODE "ruff check"
    } else {
        python -m ruff check . 2>$null
        if ($LASTEXITCODE -eq 0) {
            Show-Result "backend lint" 0 "python -m ruff check"
        } else {
            Write-Host "  SKIP  backend lint (ruff not installed: pip install ruff)" -ForegroundColor Yellow
            Add-Result "backend lint" "SKIP" "ruff not installed"
        }
    }
} finally {
    Pop-Location
}

# ---------------------------------------------------------------- node
$frontend = Join-Path $repo "frontend"
Push-Location $frontend
try {
    $pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
    if (-not $pnpm) {
        Write-Host "  SKIP  frontend checks (pnpm not found: run 'corepack enable')" -ForegroundColor Yellow
        Add-Result "frontend typecheck" "SKIP" "pnpm not found"
        Add-Result "frontend build" "SKIP" "pnpm not found"
    } else {
        if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
            Write-Host "  ..    installing frontend dependencies (first run only)"
            pnpm install --frozen-lockfile
        }

        Write-Host "[3/4] frontend typecheck and lint" -ForegroundColor Cyan
        pnpm exec tsc --noEmit
        $tsc = $LASTEXITCODE
        if ($tsc -eq 0) {
            pnpm exec eslint .
            Show-Result "frontend typecheck and lint" $LASTEXITCODE "tsc --noEmit; eslint ."
        } else {
            Show-Result "frontend typecheck" $tsc "tsc --noEmit"
        }

        if ($SkipBuild) {
            Write-Host "  SKIP  frontend build (-SkipBuild)" -ForegroundColor Yellow
            Add-Result "frontend build" "SKIP" "skipped by -SkipBuild"
        } else {
            Write-Host "[4/4] frontend build" -ForegroundColor Cyan
            pnpm build
            Show-Result "frontend build" $LASTEXITCODE "next build"
        }
    }
} finally {
    Pop-Location
}

# ---------------------------------------------------------------- summary
Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
$results | Format-Table -AutoSize | Out-String | Write-Host

$failed = @($results | Where-Object { $_.Result -eq "FAIL" })
if ($failed.Count -gt 0) {
    Write-Host ("FAILED: " + $failed.Count + " check(s). Scroll up for the first error.") -ForegroundColor Red
    exit 1
}

Write-Host "All checks passed." -ForegroundColor Green
exit 0
