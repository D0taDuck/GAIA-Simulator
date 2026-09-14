$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$gaiaCandidates = @(
    (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
)
$gaiaPython = $gaiaCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $gaiaPython) {
    $gaiaCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($gaiaCommand) { $gaiaPython = $gaiaCommand.Source }
}
if (-not $gaiaPython) { throw 'Python 3.11 or newer is required. Install Python, then run python launch.py.' }
& $gaiaPython (Join-Path $PSScriptRoot 'launch.py') @args
exit $LASTEXITCODE
