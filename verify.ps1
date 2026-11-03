# Convenience shim: run this from anywhere in the repo.
#   powershell -ExecutionPolicy Bypass -File .\verify.ps1
# The real work (and the switches) live in scripts/verify.ps1.
$ErrorActionPreference = "Stop"
$target = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "scripts\verify.ps1"
& $target @args
exit $LASTEXITCODE
