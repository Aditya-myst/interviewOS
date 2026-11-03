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
    # Prefer uv: ruff and pytest-asyncio live in uv.lock, so `uv run` gives the same
    # environment the lockfile describes. Bare `python -m pytest` on a machine that never
    # ran `uv sync` skips lint entirely, which is how a lint failure ships unnoticed.
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) { $py = "uv"; $pyArgs = @("run", "python") } else { $py = "python"; $pyArgs = @() }
    if (-not $uv) {
        Write-Host "  note  uv not found, using whatever python is on PATH (pip install uv to match the lockfile)" -ForegroundColor Yellow
    }

    Write-Host "[1/4] backend tests" -ForegroundColor Cyan
    & $py @pyArgs -m pytest -q
    Show-Result "backend tests" $LASTEXITCODE ($py + " -m pytest")

    Write-Host "[2/4] backend lint" -ForegroundColor Cyan
    # Ask whether the module exists before running it. `python -m ruff` when ruff is absent
    # exits 1 with "No module named ruff", which is the same code as "found violations" -- so
    # the naive version reported a lint failure on a clean tree.
    & $py @pyArgs -c "import ruff" 2>$null
    $lintRan = $false
    $lintCode = 0
    $lintDetail = ""
    if ($LASTEXITCODE -eq 0) {
        $lintRan = $true
        $lintDetail = $py + " -m ruff check"
        & $py @pyArgs -m ruff check .
        $lintCode = $LASTEXITCODE
    } elseif ($ruffExe) {
        $lintRan = $true
        $lintDetail = "ruff check"
        ruff check .
        $lintCode = $LASTEXITCODE
    }

    if ($lintRan) {
        Show-Result "backend lint" $lintCode $lintDetail
    } else {
        Write-Host "  SKIP  backend lint (install it: pip install ruff, or use uv)" -ForegroundColor Yellow
        Add-Result "backend lint" "SKIP" "ruff not installed"
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

        # `pnpm typecheck` is `next typegen && tsc --noEmit`. The typegen step is not
        # decoration: .next/types/validator.ts is generated, and one left over from a build
        # before a route was deleted keeps pointing at that route, so a plain `tsc` fails on
        # a file nobody wrote, pointing at a page that no longer exists.
        Write-Host "[3/4] frontend typecheck and lint" -ForegroundColor Cyan
        pnpm run typecheck
        $tsc = $LASTEXITCODE
        if ($tsc -eq 0) {
            pnpm exec eslint .
            Show-Result "frontend typecheck and lint" $LASTEXITCODE "pnpm typecheck; eslint ."
        } else {
            Show-Result "frontend typecheck" $tsc "pnpm typecheck"
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
