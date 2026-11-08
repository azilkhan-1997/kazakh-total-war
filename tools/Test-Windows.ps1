# SPDX-License-Identifier: GPL-2.0-or-later
# Windows PowerShell 5.1+ / PowerShell 7. Preflight only, not gameplay acceptance.
#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$ReportPath,
    [ValidateRange(5,300)][int]$LauncherTimeoutSeconds = 30
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$utf8 = New-Object System.Text.UTF8Encoding($false)
$Root = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Root)
$checks = New-Object 'System.Collections.Generic.List[object]'

function Property($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $p = $Object.PSObject.Properties[$Name]
    if ($null -ne $p) { return $p.Value }
    return $null
}
function Add-Check([string]$Id, [string]$Status, $Details) {
    $checks.Add([ordered]@{ id = $Id; status = $Status; details = $Details })
}
function Assert-NoReparseAncestor([string]$Path) {
    $cursor = $Path
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            if (((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse point in QA report destination: $cursor"
            }
        }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Safe-File([string]$Base, [string]$Relative) {
    # Manifests use relative POSIX names. Reject traversal, ADS and junctions.
    if ([string]::IsNullOrEmpty($Relative) -or $Relative -match '[\\:<>"|?*\x00-\x1f]' -or $Relative.StartsWith('/')) {
        throw "Unsafe manifest path: $Relative"
    }
    $parts = $Relative.Split('/')
    foreach ($part in $parts) {
        if (-not $part -or $part -in @('.','..') -or $part.EndsWith('.') -or $part.EndsWith(' ') -or
            $part -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)') {
            throw "Unsafe manifest path: $Relative"
        }
    }
    $path = [IO.Path]::GetFullPath((Join-Path $Base ($Relative.Replace('/', [IO.Path]::DirectorySeparatorChar))))
    $boundary = [IO.Path]::GetFullPath($Base).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $path.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped the manifest root.' }
    $cursor = $path
    while ($cursor -and $cursor.Length -ge $boundary.Length - 1) {
        if (Test-Path -LiteralPath $cursor) {
            if (((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse point in manifest path: $Relative"
            }
        }
        $cursor = Split-Path -Parent $cursor
    }
    return $path
}
function Read-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing JSON: $Path" }
    return ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json)
}
function Verify-Files([string]$Base, $Rows) {
    if ($null -eq $Rows -or @($Rows).Count -eq 0) { throw 'Manifest has no files.' }
    $seen = @{}
    $failures = New-Object 'System.Collections.Generic.List[object]'
    $verified = 0
    foreach ($row in $Rows) {
        $name = [string](Property $row 'path')
        $hash = [string](Property $row 'sha256')
        $size = Property $row 'bytes'
        try {
            $path = Safe-File $Base $name
            if ($seen.ContainsKey($name)) { throw 'Duplicate case-insensitive manifest path.' }
            $seen[$name] = $true
            if ($hash -notmatch '^[0-9a-fA-F]{64}$' -or $null -eq $size -or [string]$size -notmatch '^\d+$') {
                throw 'Invalid SHA-256 or byte count in manifest.'
            }
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'File missing.' }
            if ((Get-Item -LiteralPath $path).Length -ne [long]$size) { throw 'Byte count mismatch.' }
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ine $hash) { throw 'SHA-256 mismatch.' }
            $verified++
        } catch {
            $failures.Add([ordered]@{ path = $name; error = $_.Exception.Message })
        }
    }
    return [ordered]@{ expected = @($Rows).Count; verified = $verified; failures = @($failures.ToArray()) }
}
function Run-Launcher([string]$Exe) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Exe
    $info.Arguments = '--check'
    # Deliberately unrelated cwd: lookup must use the launcher's own directory.
    $info.WorkingDirectory = [Environment]::SystemDirectory
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $info
    try {
        if (-not $p.Start()) { throw 'Launcher process did not start.' }
        # Drain both pipes asynchronously before waiting, including for a GUI EXE.
        $stdout = $p.StandardOutput.ReadToEndAsync()
        $stderr = $p.StandardError.ReadToEndAsync()
        if (-not $p.WaitForExit($LauncherTimeoutSeconds * 1000)) {
            $p.Kill() # Only our --check launcher; no engine is started in this mode.
            $null = $p.WaitForExit(5000)
            throw "Launcher --check timed out after $LauncherTimeoutSeconds seconds."
        }
        $text = $stdout.GetAwaiter().GetResult()
        $errorText = $stderr.GetAwaiter().GetResult()
        $diagnostic = $text | ConvertFrom-Json
        if ($null -eq (Property $diagnostic 'code') -or $null -eq (Property $diagnostic 'launcher_version')) {
            throw "Launcher stdout is not its expected JSON diagnostic: $text"
        }
        return [ordered]@{ exitCode = $p.ExitCode; diagnostic = $diagnostic; stdout = $text; stderr = $errorText }
    } finally { $p.Dispose() }
}

$report = [ordered]@{
    schemaVersion = 1
    startedUtc = [DateTime]::UtcNow.ToString('o')
    purpose = 'File integrity and launcher preflight; does not execute Pyrogenesis or prove gameplay.'
    root = $Root
    environment = [ordered]@{
        platform = [Environment]::OSVersion.Platform.ToString()
        osVersion = [Environment]::OSVersion.VersionString
        is64BitOperatingSystem = [Environment]::Is64BitOperatingSystem
        is64BitProcess = [Environment]::Is64BitProcess
        powershellVersion = $PSVersionTable.PSVersion.ToString()
        processorArchitecture = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
        windows = $null; processors = @(); graphicsAdapters = @(); inventoryErrors = @()
    }
    release = $null
    checks = @()
    interactiveAcceptance = @()
    gameplayTested = $false
    nativeEngineExecutionTested = $false
    steamAcceptance = 'not_tested'
    result = 'fail'
}
$nativeWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
if ($nativeWindows -and [Environment]::Is64BitOperatingSystem -and $report.environment.processorArchitecture -eq 'AMD64') {
    Add-Check 'windows_x64_host' 'pass' 'AMD64 Windows detected; Windows version/GPU inventory follows separately.'
    foreach ($query in @(
        @{ class = 'Win32_OperatingSystem'; key = 'windows'; fields = @('Caption','Version','BuildNumber','OSArchitecture','ProductType') },
        @{ class = 'Win32_Processor'; key = 'processors'; fields = @('Name','Architecture','NumberOfCores','NumberOfLogicalProcessors') },
        @{ class = 'Win32_VideoController'; key = 'graphicsAdapters'; fields = @('Name','DriverVersion','DriverDate','VideoProcessor','AdapterRAM') }
    )) {
        try { $report.environment[$query.key] = @(Get-CimInstance -ClassName $query.class | Select-Object -Property $query.fields) }
        catch { $report.environment.inventoryErrors += ($query.class + ': ' + $_.Exception.Message) }
    }
    if (@($report.environment.windows).Count -gt 0 -and $null -ne $report.environment.windows) {
        $os = @($report.environment.windows)[0]
        if ([version]$os.Version -ge [version]'10.0' -and [int]$os.BuildNumber -ge 10240 -and [int]$os.ProductType -eq 1) {
            Add-Check 'windows_target_version' 'pass' 'Windows 10 or later workstation; exact OS version recorded in environment.windows.'
        } else { Add-Check 'windows_target_version' 'fail' 'Windows 10/11 workstation required; older Windows and Windows Server are outside this target.' }
    } else { Add-Check 'windows_target_version' 'fail' 'Windows CIM version could not be obtained; target OS remains unverified.' }
} else { Add-Check 'windows_x64_host' 'fail' 'Run this harness on AMD64 Windows 10/11. ARM64/emulation and Linux/Wine are not target native Windows acceptance.' }

$bundleOk = $false
$build = $null
try {
    $build = Read-Json (Safe-File $Root 'BUILD_MANIFEST.json')
    if ((Property $build 'engineVersion') -ne '0.28.0') { throw 'BUILD_MANIFEST engineVersion must be exactly 0.28.0.' }
    $rows = Property $build 'files'
    $required = @('KazakhTotalWar.exe', 'docs/windows-runtime-manifest.json', 'tools/Test-Windows.ps1')
    foreach ($name in $required) {
        if (@($rows | Where-Object { (Property $_ 'path') -ceq $name }).Count -ne 1) { throw "Build manifest must include $name exactly once." }
    }
    $report.release = [ordered]@{
        releaseVersion = Property $build 'releaseVersion'; moduleVersion = Property $build 'moduleVersion'
        engineVersion = Property $build 'engineVersion'; sourceRevision = Property $build 'sourceRevision'
        deliveryType = Property $build 'deliveryType'
        buildManifestSha256 = (Get-FileHash -LiteralPath (Join-Path $Root 'BUILD_MANIFEST.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $verification = Verify-Files $Root $rows
    $bundleOk = $verification.failures.Count -eq 0
    $status = if ($bundleOk) { 'pass' } else { 'fail' }
    Add-Check 'bundle_manifest_files' $status $verification
} catch { Add-Check 'bundle_manifest_files' 'fail' $_.Exception.Message }

if ($bundleOk) {
    try {
        $runtimeManifest = Read-Json (Safe-File $Root 'docs/windows-runtime-manifest.json')
        $runtimeRows = Property $runtimeManifest 'files'
        if ((Property $runtimeManifest 'source_sha256') -ne '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1' -or
            (Property $runtimeManifest 'file_count') -ne 140 -or @($runtimeRows).Count -ne 140) {
            throw 'Unexpected official Release 28 runtime manifest identity or file count.'
        }
        Write-Host 'Hashing all 140 official runtime files, including large asset archives...'
        $verification = Verify-Files (Join-Path $Root 'runtime') $runtimeRows
        $status = if ($verification.failures.Count -eq 0) { 'pass' } else { 'fail' }
        Add-Check 'official_runtime_files' $status $verification
    } catch { Add-Check 'official_runtime_files' 'fail' $_.Exception.Message }
    try {
        # Setup copies the packaged module into the portable runtime. Check that copy too.
        $modulePrefix = 'mods/kazakh_total_war/'
        if ((Property $build 'deliveryType') -ne 'bootstrap') { $modulePrefix = 'runtime/binaries/data/mods/kazakh_total_war/' }
        $moduleRows = @((Property $build 'files') | Where-Object { ([string](Property $_ 'path')).StartsWith($modulePrefix, [StringComparison]::Ordinal) } | ForEach-Object {
            [pscustomobject]@{ path = $_.path.Substring($modulePrefix.Length); bytes = $_.bytes; sha256 = $_.sha256 }
        })
        if (@($moduleRows | Where-Object { $_.path -eq 'mod.json' }).Count -ne 1) { throw 'No complete KTW module inventory in BUILD_MANIFEST.' }
        $verification = Verify-Files (Join-Path $Root 'runtime/binaries/data/mods/kazakh_total_war') $moduleRows
        $status = if ($verification.failures.Count -eq 0) { 'pass' } else { 'fail' }
        Add-Check 'installed_ktw_module_files' $status $verification
    } catch { Add-Check 'installed_ktw_module_files' 'fail' $_.Exception.Message }
} else {
    Add-Check 'official_runtime_files' 'skipped' 'Bundle integrity failed; runtime manifest is not trusted.'
    Add-Check 'installed_ktw_module_files' 'skipped' 'Bundle integrity failed.'
}

if ($nativeWindows -and $bundleOk) {
    try {
        $launcher = Run-Launcher (Safe-File $Root 'KazakhTotalWar.exe')
        $status = if ($launcher.exitCode -eq 0 -and $launcher.diagnostic.code -eq 0) { 'pass' } else { 'fail' }
        Add-Check 'launcher_check' $status $launcher
    } catch { Add-Check 'launcher_check' 'fail' $_.Exception.Message }
} else { Add-Check 'launcher_check' 'skipped' 'Requires native Windows and successful bundle integrity check.' }

foreach ($id in @('menu_ru_kk','campaign_movement_recruitment_turn','campaign_to_tactical_battle',
    'mounted_archery_and_unit_commands','natural_victory_defeat','battle_to_campaign_casualties',
    'commander_death_and_succession','manual_save_restart_load','midbattle_save_restart_load',
    'legacy_save_import','spaces_and_kazakh_path','offline_launch','audio','hardware_performance')) {
    $report.interactiveAcceptance += [ordered]@{ id = $id; status = 'not_tested'; evidence = $null }
}
$report.checks = @($checks.ToArray())
$failed = @($report.checks | Where-Object { $_.status -ne 'pass' }).Count -gt 0
$report.result = if ($failed) { 'preflight_failed' } else { 'preflight_passed_gameplay_not_tested' }
$report.finishedUtc = [DateTime]::UtcNow.ToString('o')
if (-not $ReportPath) {
    $ReportPath = Join-Path $Root ('qa-reports/windows-preflight-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N') + '.json')
}
$ReportPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ReportPath)
$runtimeBoundary = [IO.Path]::GetFullPath((Join-Path $Root 'runtime')).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if ($ReportPath.StartsWith($runtimeBoundary, [StringComparison]::OrdinalIgnoreCase)) { throw 'Write QA reports outside runtime; keep the play profile separate.' }
Assert-NoReparseAncestor $ReportPath
if (Test-Path -LiteralPath $ReportPath) { throw 'Report destination already exists; choose a new filename to retain prior evidence.' }
$null = New-Item -ItemType Directory -Path (Split-Path -Parent $ReportPath) -Force
[IO.File]::WriteAllText($ReportPath, ($report | ConvertTo-Json -Depth 16), $utf8)
Write-Host ($report.result + ': ' + $ReportPath)
Write-Host 'No game was launched. Complete docs/windows-acceptance-checklist.md on this Windows PC.'
if ($failed) { exit 1 }
exit 0
