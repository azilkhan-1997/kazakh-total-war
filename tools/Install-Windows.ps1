# SPDX-License-Identifier: GPL-2.0-or-later
# Installs only the KTW module. Requires the genuine 0 A.D. 0.28.0 Windows runtime.
[CmdletBinding()]
param([string]$EngineExe, [switch]$DownloadEngine, [switch]$Launch)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows 64-bit is required.' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$moduleSource = Join-Path $projectRoot 'mods\kazakh_total_war'
if (-not (Test-Path (Join-Path $moduleSource 'mod.json'))) { throw 'Extract the complete ZIP before running this script.' }
function Find-Engine {
    $roots = @((Join-Path $env:LOCALAPPDATA '0 A.D. Empires Ascendant'))
    foreach ($key in @('HKCU:\Software\0 A.D.','HKLM:\Software\0 A.D.','HKLM:\Software\WOW6432Node\0 A.D.')) {
        if (Test-Path $key) {
            $value = (Get-Item $key).GetValue('')
            if ($value) { $roots += [string]$value }
        }
    }
    foreach ($root in $roots) {
        $candidate = Join-Path $root 'binaries\system\pyrogenesis.exe'
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}
if (-not $EngineExe) { $EngineExe = Find-Engine }
if (-not $EngineExe -and $DownloadEngine) {
    $installer = Join-Path $PSScriptRoot '0ad-0.28.0-win64.exe'
    if (-not (Test-Path $installer)) {
        Write-Host 'Downloading official 0 A.D. Release 28 (about 1.51 GiB)...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $partial = "$installer.partial"
        Invoke-WebRequest -UseBasicParsing -Uri 'https://releases.wildfiregames.com/0ad-0.28.0-win64.exe' -OutFile $partial
        Move-Item -LiteralPath $partial -Destination $installer -Force
    }
    $expected = '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $installer).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Installer checksum mismatch. Installation stopped.'
    }
    # Opens the original interactive installer. No silent system changes.
    Start-Process -FilePath $installer -Wait
    $EngineExe = Find-Engine
}
if (-not $EngineExe -or -not (Test-Path $EngineExe)) {
    throw 'Install 0 A.D. Release 28 from https://play0ad.com/download/win/ or run with -DownloadEngine; alternatively specify -EngineExe.'
}
$EngineExe = (Resolve-Path -LiteralPath $EngineExe).Path
$binaryDir = Split-Path -Parent $EngineExe
$publicInfo = Join-Path (Split-Path -Parent $binaryDir) 'data\mods\public\mod.json'
if (-not (Test-Path $publicInfo)) { throw 'Cannot verify the installed engine version: public/mod.json is missing.' }
if ((Get-Content -LiteralPath $publicInfo -Raw | ConvertFrom-Json).version -ne '0.28.0') {
    throw 'This module requires exactly 0 A.D. 0.28.0. No dependency override will be applied.'
}
$documents = [Environment]::GetFolderPath('MyDocuments')
$userData = Join-Path $documents 'My Games\0ad'
$target = Join-Path $userData 'mods\kazakh_total_war'
New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
if (Test-Path $target) {
    $backup = Join-Path $userData ('ktw-backups\kazakh_total_war-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
    Move-Item -LiteralPath $target -Destination $backup
    Write-Host "Previous module retained at $backup"
}
Copy-Item -LiteralPath $moduleSource -Destination $target -Recurse
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'KAZAKH TOTAL WAR - Prototype.lnk'))
$shortcut.TargetPath = $EngineExe
$shortcut.Arguments = '-mod=public -mod=kazakh_total_war'
$shortcut.WorkingDirectory = $binaryDir
$shortcut.Description = 'SAYRAM PLANETA HOLDING - native Pyrogenesis technical prototype'
$shortcut.Save()
Write-Host "Installed module: $target"
Write-Host 'The official engine remains Wildfire Games software. KTW is an experimental module, not a Steam release.'
if ($Launch) { Start-Process -FilePath $EngineExe -WorkingDirectory $binaryDir -ArgumentList '-mod=public','-mod=kazakh_total_war' }
