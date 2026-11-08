# SPDX-License-Identifier: GPL-2.0-or-later
param(
    [Parameter(Mandatory=$true)][string]$SourceDirectory,
    [Parameter(Mandatory=$true)][string]$ReportPath,
    [string]$AnalyzerPath = 'PSScriptAnalyzer'
)
$ErrorActionPreference = 'Stop'
Import-Module -Name $AnalyzerPath -ErrorAction Stop
$profile = 'win-48_x64_10.0.17763.0_5.1.17763.316_x64_4.0.30319.42000_framework'
$settings = @{
    IncludeRules = @('PSUseCompatibleSyntax','PSUseCompatibleCommands','PSUseCompatibleTypes')
    Rules = @{
        PSUseCompatibleSyntax = @{Enable=$true; TargetVersions=@('5.1')}
        PSUseCompatibleCommands = @{Enable=$true; TargetProfiles=@($profile)}
        PSUseCompatibleTypes = @{Enable=$true; TargetProfiles=@($profile)}
    }
}
$rows = @()
foreach ($file in @(Get-ChildItem -LiteralPath $SourceDirectory -Filter '*.ps1' -File -Recurse | Sort-Object FullName)) {
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$parseErrors) | Out-Null
    $diagnostics = @(Invoke-ScriptAnalyzer -Path $file.FullName -Settings $settings)
    $rows += [ordered]@{
        path = $file.FullName
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        parse_errors = @($parseErrors | ForEach-Object { [ordered]@{message=$_.Message;line=$_.Extent.StartLineNumber} })
        compatibility_diagnostics = @($diagnostics | ForEach-Object { [ordered]@{rule=$_.RuleName;message=$_.Message;severity=$_.Severity.ToString();line=$_.Line} })
    }
}
$failures = @($rows | Where-Object { $_.parse_errors.Count -gt 0 -or $_.compatibility_diagnostics.Count -gt 0 })
$report = [ordered]@{
    host = $PSVersionTable.OS
    powershell_version = $PSVersionTable.PSVersion.ToString()
    analyzer_version = (Get-Module PSScriptAnalyzer).Version.ToString()
    target_syntax = '5.1'
    target_api_profile = $profile
    files = $rows
    pass = ($rows.Count -gt 0 -and $failures.Count -eq 0)
    native_windows_execution = 'NOT TESTED'
    scope = 'Parser and static compatibility analysis only. No installer, UAC, COM, registry or game was executed.'
}
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReportPath -Encoding utf8
$report | ConvertTo-Json -Depth 10
if (-not $report.pass) { exit 1 }
