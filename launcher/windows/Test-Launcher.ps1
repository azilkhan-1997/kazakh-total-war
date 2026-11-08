# SPDX-License-Identifier: GPL-2.0-or-later
# Native Windows error-path tests. No fixture engine is ever executed.
param([Parameter(Mandatory=$true)][string]$Launcher)
$ErrorActionPreference = 'Stop'
$launcherSource = (Resolve-Path -LiteralPath $Launcher).Path
$kazakh = [string][char]0x049a + [char]0x0430 + [char]0x0437 + [char]0x0430 + [char]0x049b
$work = Join-Path ([IO.Path]::GetTempPath()) ('KTW Launcher Tests ' + $kazakh + ' ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
$base = '{"name":"0ad","version":"0.28.0"}'
$module = '{"name":"kazakh_total_war","version":"0.2.0","dependencies":["0ad=0.28.0"]}'
$passed = 0
function Fixture([string]$name, [string]$baseJson, [string]$moduleJson) {
    $folder = Join-Path $work $name
    New-Item -ItemType Directory -Path $folder | Out-Null
    Copy-Item -LiteralPath $launcherSource -Destination (Join-Path $folder 'KazakhTotalWar.exe')
    foreach ($file in @('runtime\binaries\data\mods\public\public.zip',
        'runtime\binaries\data\mods\mod\mod.zip',
        'runtime\binaries\data\mods\kazakh_total_war\gui\page_pregame.xml',
        'runtime\binaries\data\mods\kazakh_total_war\maps\random\ktw_campaign.js',
        'runtime\binaries\data\mods\kazakh_total_war\simulation\components\KtwController.js')) {
        $target = Join-Path $folder $file
        New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
        [IO.File]::WriteAllText($target, 'TEST ONLY - never launch these fixtures', $utf8)
    }
    $engineFolder = Join-Path $folder 'runtime\binaries\system'
    New-Item -ItemType Directory -Path $engineFolder | Out-Null
    # Copy an AMD64 PE only to reach metadata error branches. This is NOT
    # Pyrogenesis and must never be used as a playable-game runtime.
    Copy-Item -LiteralPath $launcherSource -Destination (Join-Path $engineFolder 'pyrogenesis.exe')
    [IO.File]::WriteAllText((Join-Path $folder 'runtime\binaries\data\mods\public\mod.json'), $baseJson, $utf8)
    [IO.File]::WriteAllText((Join-Path $folder 'runtime\binaries\data\mods\kazakh_total_war\mod.json'), $moduleJson, $utf8)
    return (Join-Path $folder 'KazakhTotalWar.exe')
}
function Expect([string]$exe, [string]$arguments, [int]$code) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $exe
    $info.Arguments = $arguments
    # Intentionally unrelated cwd: lookup must be relative to the launcher.
    $info.WorkingDirectory = [Environment]::SystemDirectory
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.CreateNoWindow = $true
    $process = [Diagnostics.Process]::Start($info)
    $text = $process.StandardOutput.ReadToEnd()
    $process.WaitForExit()
    $result = $text | ConvertFrom-Json
    if ($process.ExitCode -ne $code -or $result.code -ne $code) {
        throw "Expected exit $code, got $($process.ExitCode): $text"
    }
    $process.Dispose()
    $script:passed++
    Write-Output "PASS code=$code $($result.message)"
}
try {
    $bare = Join-Path $work 'KazakhTotalWar.exe'
    Copy-Item -LiteralPath $launcherSource -Destination $bare
    Expect $bare '--check' 10
    Expect $bare '--check --unknown' 2
    Expect (Fixture 'wrong engine version' '{"name":"0ad","version":"0.0.26"}' $module) '--check' 11
    Expect (Fixture 'wrong module dependency' $base '{"name":"kazakh_total_war","dependencies":["0ad=0.0.26"]}') '--check' 11
    Expect (Fixture 'truncated metadata' '{"name":"0ad",' $module) '--check' 11
    Expect (Fixture 'duplicate metadata field' '{"name":"0ad","version":"0.0.26","version":"0.28.0"}' $module) '--check' 11
    $invalid = Fixture 'invalid engine PE' $base $module
    [IO.File]::WriteAllText((Join-Path (Split-Path -Parent $invalid) 'runtime\binaries\system\pyrogenesis.exe'), 'not a PE', $utf8)
    Expect $invalid '--check' 11
    Write-Output "$passed native launcher error-path tests passed. Gameplay was NOT tested."
} finally {
    # This is the unique directory created above, never the user's game folder.
    Remove-Item -LiteralPath $work -Recurse -Force
}
