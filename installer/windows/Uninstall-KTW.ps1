#requires -Version 5.1
# SPDX-License-Identifier: GPL-2.0-or-later
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$InstallRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Assert-NoReparse([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing to follow a link or junction during uninstall.' }
        }
        $next = Split-Path -Parent $current
        if ($next -eq $current) { break }; $current=$next
    }
}
try {
    $root = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
    if ([IO.Path]::GetPathRoot($root).TrimEnd('\') -eq $root) { throw 'Refusing a drive-root uninstall.' }
    Assert-NoReparse $root
    $marker = Join-Path $root 'KTW_INSTALL.json'
    $record = Get-Content -LiteralPath $marker -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($record.schema -ne 1 -or $record.product -cne 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR' -or $record.install_id -notmatch '^[0-9a-f]{32}$' -or [IO.Path]::GetFullPath($record.install_root).TrimEnd('\') -cne $root) { throw 'Invalid product ownership record; nothing was removed.' }
    $seen=@{}; $plan=@(); $preserved=0
    foreach ($row in $record.owned_files) {
        $name=[string]$row.path
        if (-not $name -or $name.Contains('\') -or $name.Contains(':') -or $name.StartsWith('/') -or @($name.Split('/') | Where-Object { $_ -eq '' -or $_ -eq '.' -or $_ -eq '..' }).Count -gt 0 -or $seen.ContainsKey($name)) { throw 'Unsafe or duplicate uninstall path.' }
        $seen[$name]=$true
        if ($name.StartsWith('runtime/binaries/data/saves/',[StringComparison]::OrdinalIgnoreCase) -or $name.StartsWith('runtime/binaries/data/config/',[StringComparison]::OrdinalIgnoreCase)) { $preserved++; continue }
        $path=Join-Path $root $name.Replace('/','\')
        Assert-NoReparse $path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $file=Get-Item -LiteralPath $path -Force
        if ($file.PSIsContainer) { throw 'Expected an installed file, found a directory.' }
        if ($file.Length -ne [long]$row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne [string]$row.sha256) { $preserved++; continue }
        $plan += $path
    }
    # Validate the whole deletion plan before deleting a single file.
    foreach ($path in $plan) { Remove-Item -LiteralPath $path -Force }
    $shell=New-Object -ComObject WScript.Shell
    $paths=@((Join-Path ([Environment]::GetFolderPath('Programs')) 'SAYRAM PLANETA HOLDING\KAZAKH TOTAL WAR.lnk'),(Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'KAZAKH TOTAL WAR.lnk'))
    if ($record.PSObject.Properties.Match('shortcuts').Count -gt 0) { $paths = @($record.shortcuts) }
    foreach ($link in $paths) {
        if (Test-Path -LiteralPath $link) {
            $shortcut=$shell.CreateShortcut($link)
            if ($shortcut.TargetPath -ieq (Join-Path $root 'KazakhTotalWar.exe')) { Remove-Item -LiteralPath $link -Force }
        }
    }
    $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SPH.KazakhTotalWar.'+$record.install_id
    if (Test-Path -LiteralPath $key) {
        $current=Get-ItemProperty -LiteralPath $key
        if ($current.PSObject.Properties.Match('InstallLocation').Count -gt 0 -and $current.InstallLocation -ceq $root) { Remove-Item -LiteralPath $key -Recurse }
    }
    Remove-Item -LiteralPath $marker -Force
    # Empty folders only. Unknown files, modified files, saves, config and caches remain.
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    $queue.Enqueue($root); $directories=@()
    while ($queue.Count -gt 0) {
        $parent=$queue.Dequeue()
        foreach ($directory in @(Get-ChildItem -LiteralPath $parent -Directory -Force)) {
            if (-not ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                Assert-NoReparse $directory.FullName
                $directories += $directory.FullName
                $queue.Enqueue($directory.FullName)
            }
        }
    }
    $directories | Sort-Object { $_.Length } -Descending | ForEach-Object {
        Assert-NoReparse $_
        if (@(Get-ChildItem -LiteralPath $_ -Force).Count -eq 0) { Remove-Item -LiteralPath $_ }
    }
    if (@(Get-ChildItem -LiteralPath $root -Force).Count -eq 0) { Remove-Item -LiteralPath $root }
    Write-Host "Game removed. Saved games, settings and unknown or modified files were preserved ($preserved known entries retained)."
    exit 0
} catch {
    Write-Host ('UNINSTALL FAILED: '+$_.Exception.Message)
    exit 1
}
