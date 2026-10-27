$ErrorActionPreference = 'Stop'
$taskProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskPython = Join-Path $taskProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Create the project virtual environment first.' }
$taskWorkRoot = Join-Path $taskProjectRoot 'work'
New-Item -ItemType Directory -Force -Path $taskWorkRoot | Out-Null
$taskTestDirectory = Join-Path $taskWorkRoot ('pytest-' + [guid]::NewGuid().ToString('N'))
Push-Location $taskProjectRoot
try {
    & $taskPython -m ruff check src tests scripts
    if ($LASTEXITCODE -ne 0) { throw 'Ruff failed.' }
    & $taskPython -m pytest --basetemp $taskTestDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
} finally {
    Pop-Location
}
