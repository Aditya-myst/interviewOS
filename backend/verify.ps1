# Same check, from the backend folder, because that is where you already are.
# The real work (and the switches) live in scripts/verify.ps1 at the repo root.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& (Join-Path $root "scripts\verify.ps1") @args
exit $LASTEXITCODE
