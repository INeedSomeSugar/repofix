$ErrorActionPreference = 'Stop'
$taskProjectRoot = $PSScriptRoot
$taskPython = Join-Path $taskProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Create the project virtual environment first.' }
Push-Location $taskProjectRoot
try {
    Write-Host 'RepoFix: http://127.0.0.1:8011'
    & $taskPython -m repofix.cli serve --port 8011
} finally {
    Pop-Location
}
