param([Parameter(Mandatory=$true)][string]$SourcePath,[Parameter(Mandatory=$true)][string]$ReportPath)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($SourcePath,[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) { throw 'Source parser errors.' }
$selected = @('Assert-ParentAlive','Assert-NoReparse','Assert-File','Get-EmbeddedComponent')
foreach ($name in $selected) {
    $definitions = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name },$true))
    if ($definitions.Count -ne 1) { throw ('Expected one original helper: ' + $name) }
    # Evaluate only an AST-selected function definition. No top-level installer code,
    # OS guards, installation worker, Windows registry or executable is invoked.
    Invoke-Expression $definitions[0].Extent.Text
}
$InstallerProcessId = $PID
$FixtureRoot = Join-Path (Split-Path -Parent ([IO.Path]::GetFullPath($ReportPath))) ('fixtures-' + [guid]::NewGuid().ToString('N'))
$ComponentRoot = Join-Path $FixtureRoot 'components'
[IO.Directory]::CreateDirectory($ComponentRoot) | Out-Null
$bytes = [Text.Encoding]::UTF8.GetBytes('original verified component fixture')
$goodPath = Join-Path $ComponentRoot 'good.bin'
[IO.File]::WriteAllBytes($goodPath,$bytes)
$digest = (Get-FileHash -LiteralPath $goodPath -Algorithm SHA256).Hash.ToLowerInvariant()
$rows = [Collections.Generic.List[object]]::new()
function Expect-Rejected([string]$Name,[scriptblock]$Action,[string]$Pattern) {
    $message = $null
    try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    $passed = $null -ne $message -and $message -match $Pattern
    $rows.Add([ordered]@{name=$Name;pass=$passed;expected_rejection=$Pattern;actual_error=$message})
}
try {
    $returned = Get-EmbeddedComponent 'good.bin' $digest $bytes.Length
    $rows.Add([ordered]@{name='good component returns exact local path';pass=($returned -ceq $goodPath)})
    Expect-Rejected 'missing component fails closed' { Get-EmbeddedComponent 'missing.bin' $digest $bytes.Length } 'Offline component missing:.*No network fallback is permitted'
    Expect-Rejected 'wrong byte count fails closed' { Get-EmbeddedComponent 'good.bin' $digest ($bytes.Length + 1) } 'Unexpected (downloaded|embedded) file size'
    Expect-Rejected 'wrong SHA-256 fails closed' { Get-EmbeddedComponent 'good.bin' ('0'*64) $bytes.Length } 'SHA-256 verification failed'
    [IO.Directory]::CreateDirectory((Join-Path $ComponentRoot 'directory.bin')) | Out-Null
    Expect-Rejected 'directory is not a component' { Get-EmbeddedComponent 'directory.bin' $digest $bytes.Length } 'Offline component missing'
    Expect-Rejected 'parent traversal refused' { Get-EmbeddedComponent '../good.bin' $digest $bytes.Length } 'Invalid embedded component name'
    Expect-Rejected 'absolute path refused' { Get-EmbeddedComponent $goodPath $digest $bytes.Length } 'Invalid embedded component name'
    Expect-Rejected 'Windows path separator refused' { Get-EmbeddedComponent '..\good.bin' $digest $bytes.Length } 'Invalid embedded component name'
    Expect-Rejected 'Windows alternate data stream refused' { Get-EmbeddedComponent 'good.bin:stream' $digest $bytes.Length } 'Invalid embedded component name'
    Expect-Rejected 'empty component name refused' { Get-EmbeddedComponent '' $digest $bytes.Length } 'Invalid embedded component name'
    New-Item -ItemType SymbolicLink -Path (Join-Path $ComponentRoot 'link.bin') -Target $goodPath | Out-Null
    Expect-Rejected 'symlink component refused' { Get-EmbeddedComponent 'link.bin' $digest $bytes.Length } 'physical folder without links or junctions'
    $physicalRoot = $ComponentRoot
    $linkedRoot = Join-Path $FixtureRoot 'linked-components'
    New-Item -ItemType SymbolicLink -Path $linkedRoot -Target $physicalRoot | Out-Null
    $ComponentRoot = $linkedRoot
    Expect-Rejected 'symlink component ancestor refused' { Get-EmbeddedComponent 'good.bin' $digest $bytes.Length } 'physical folder without links or junctions'
    $ComponentRoot = $physicalRoot
    $InstallerProcessId = [int]::MaxValue
    Expect-Rejected 'closed installer cancels component access' { Get-EmbeddedComponent 'good.bin' $digest $bytes.Length } 'Setup was closed. Installation cancelled.'
    $InstallerProcessId = $PID
} finally {
    if (Test-Path -LiteralPath $FixtureRoot) { Remove-Item -LiteralPath $FixtureRoot -Recurse -Force }
}
$failures = @($rows | Where-Object { -not $_.pass })
$report = [ordered]@{
    source=$SourcePath
    source_sha256=(Get-FileHash -LiteralPath $SourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
    extracted_function_definitions=$selected
    powershell_version=$PSVersionTable.PSVersion.ToString()
    host=$PSVersionTable.OS
    pass=($rows.Count -eq 13 -and $failures.Count -eq 0)
    cases=@($rows.ToArray())
    installation_executed=$false
    os_guard_bypassed=$false
    windows_native_execution='NOT TESTED'
    scope='Actual helper definitions executed on Linux fixtures. Windows-specific path semantics, junctions, UAC, registry, COM, prerequisite install and gameplay remain untested.'
}
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReportPath -Encoding utf8
$report | ConvertTo-Json -Depth 10
if (-not $report.pass) { exit 1 }
