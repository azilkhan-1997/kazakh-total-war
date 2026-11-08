# SPDX-License-Identifier: GPL-2.0-or-later
[CmdletBinding()]
param([string]$Source, [string]$PythonExe)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $Source) { $Source = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\0ad\saves' }
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root 'runtime\binaries\data\saves'
if (-not (Test-Path -LiteralPath (Join-Path $root 'runtime\binaries\system\pyrogenesis.exe'))) {
    throw 'Complete Install-WindowsRuntime.ps1 before importing saves.'
}
Write-Host 'Close KAZAKH TOTAL WAR before importing. Original files are never changed.'
$prefix = @()
if (-not $PythonExe) {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) { $PythonExe = 'py.exe'; $prefix = @('-3') }
    elseif (Get-Command python.exe -ErrorAction SilentlyContinue) { $PythonExe = 'python.exe' }
    else { throw 'CPython 3.11+ required for this optional import tool; specify -PythonExe.' }
}
& $PythonExe @prefix (Join-Path $PSScriptRoot 'import_legacy_saves.py') --source $Source --destination $target
if ($LASTEXITCODE -ne 0) { throw "Save import failed, Python exit code $LASTEXITCODE" }
