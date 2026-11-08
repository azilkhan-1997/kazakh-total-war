# SPDX-License-Identifier: GPL-2.0-or-later
# Build the actual engine, not the launcher. Run in PowerShell 7 on Windows x64.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkRoot,
    [Parameter(Mandatory = $true)][string]$OutputRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$WorkRoot = [IO.Path]::GetFullPath($WorkRoot)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$evidence = Join-Path $OutputRoot 'evidence'
New-Item -ItemType Directory -Force -Path $WorkRoot, $evidence | Out-Null
$sourceUrl = 'https://releases.wildfiregames.com/0ad-0.28.0-unix-build.tar.xz'
$sourceSha = '27e217755ef76a922fe58dbf593d96e54b6ed2375d23f548c35619aa6bd5a42a'
$scriptSha = 'fa0ada5f2d1363ffd18dadedd355d5b89f3b04dcd5cb08fee49c71686bb4e508'
$premakeSha = '9b29ac24498e92d114da67f7565525c607d1f0bd9c29b164eb3188ac8f804f74'
$sourceDir = Join-Path $WorkRoot '0ad-0.28.0'
$record = [ordered]@{
    schema_version = 1
    purpose = 'Compile and inspect R28 Windows x64; not a player distribution'
    status = 'started'
    started_utc = [DateTime]::UtcNow.ToString('o')
    repository_commit = $env:GITHUB_SHA
    run_url = if ($env:GITHUB_SERVER_URL -and $env:GITHUB_REPOSITORY -and $env:GITHUB_RUN_ID) {
        "$env:GITHUB_SERVER_URL/$env:GITHUB_REPOSITORY/actions/runs/$env:GITHUB_RUN_ID"
    } else { $null }
    runner_image = $env:ImageOS
    runner_image_version = $env:ImageVersion
    engine_source_url = $sourceUrl
    engine_source_sha256 = $sourceSha
    engine_source_revision = 'a2cae4d69f816e9e9d7eecb6bf88f762afc0c90d'
    windows_dependency_url = 'https://svn.wildfiregames.com/public/windows-libs-amd64/trunk@28275'
    windows_dependency_revision = 28275
    engine_flags = @('--without-lobby', '--without-atlas', '--without-tests')
    native_windows_gameplay_tested = $false
    complete_dependency_corresponding_source = $false
    publisher_microsoft_redistribution_entitlement_established = $false
    redistributable_player_release = $false
}

function Save-Record {
    $record | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 (Join-Path $evidence 'build-provenance.json')
}
function Invoke-Logged {
    param([string]$Program, [string[]]$Arguments, [string]$LogName)
    Write-Host "Running: $Program $($Arguments -join ' ')"
    & $Program @Arguments 2>&1 | Tee-Object -FilePath (Join-Path $evidence $LogName) | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE (see $LogName)" }
}
function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Require-Hash([string]$Path, [string]$Expected) {
    $actual = Get-Sha256 $Path
    if ($actual -ne $Expected) { throw "SHA256 mismatch for $Path : $actual" }
}
function Get-FileRecord([IO.FileInfo]$File, [string]$Base) {
    [ordered]@{
        path = [IO.Path]::GetRelativePath($Base, $File.FullName).Replace('\', '/')
        bytes = $File.Length
        sha256 = Get-Sha256 $File.FullName
        file_version = $File.VersionInfo.FileVersion
        product_version = $File.VersionInfo.ProductVersion
    }
}
Save-Record

try {
    if (-not $IsWindows -or -not [Environment]::Is64BitOperatingSystem) {
        throw 'This script requires Windows x64 and PowerShell 7.'
    }
    if (Test-Path $sourceDir) { throw "Use a fresh WorkRoot: $sourceDir already exists." }
    $svn = (Get-Command svn.exe -ErrorAction Stop).Source
    $tar = (Get-Command tar.exe -ErrorAction Stop).Source
    $curl = (Get-Command curl.exe -ErrorAction Stop).Source
    Invoke-Logged $svn @('--version', '--quiet') 'svn-version.txt'
    Invoke-Logged $tar @('--version') 'tar-version.txt'
    Invoke-Logged $curl @('--version') 'curl-version.txt'

    # Use the runner's actual VS2022 installation. Do not silently switch toolsets.
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    if (-not (Test-Path $vswhere)) { throw 'vswhere.exe is missing.' }
    $vsJson = & $vswhere -latest -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json
    if ($LASTEXITCODE -ne 0) { throw 'vswhere failed.' }
    $vsJson | Set-Content -Encoding utf8 (Join-Path $evidence 'visual-studio.json')
    $installations = @($vsJson | ConvertFrom-Json)
    if ($installations.Count -ne 1) { throw 'A VS2022 installation with x64 C++ tools is required.' }
    $vsPath = $installations[0].installationPath
    & (Join-Path $vsPath 'Common7/Tools/Launch-VsDevShell.ps1') -Arch amd64 -HostArch amd64 -SkipAutomaticLocation
    $msbuild = Join-Path $vsPath 'MSBuild/Current/Bin/MSBuild.exe'
    $dumpbin = (Get-Command dumpbin.exe -ErrorAction Stop).Source
    $compiler = (Get-Command cl.exe -ErrorAction Stop).Source
    $record.toolchain = [ordered]@{
        visual_studio_version = $installations[0].installationVersion
        visual_studio_product = $installations[0].productId
        compiler_path = $compiler
        compiler_version = (Get-Item $compiler).VersionInfo.FileVersion
        compiler_sha256 = Get-Sha256 $compiler
        vctools_version = $env:VCToolsVersion
        windows_sdk_version = $env:WindowsSDKVersion
        msbuild_path = $msbuild
    }
    Invoke-Logged $msbuild @('-version', '-nologo') 'msbuild-version.txt'
    Save-Record

    # No cache is trusted. Exact official source bytes are verified before extraction.
    $archive = Join-Path $WorkRoot '0ad-0.28.0-unix-build.tar.xz'
    Invoke-Logged $curl @('--fail', '--location', '--retry', '3', '--connect-timeout', '30', '--output', $archive, $sourceUrl) 'source-download.txt'
    Require-Hash $archive $sourceSha
    if ((Get-Item $archive).Length -ne 164975536) { throw 'Unexpected source archive length.' }
    Invoke-Logged $tar @('-xf', $archive, '-C', $WorkRoot) 'source-extraction.txt'
    $premakeFile = Join-Path $sourceDir 'build/premake/premake5.lua'
    Require-Hash $premakeFile $premakeSha

    # The Unix source archive omits Windows fetch scripts; restore the audited exact
    # R28 script to its original location so its relative copy paths work correctly.
    $originalScript = Join-Path $repoRoot 'docs/distribution-evidence/get-windows-libs-r28.bat'
    $fetchScript = Join-Path $sourceDir 'libraries/get-windows-libs.bat'
    $scriptText = [IO.File]::ReadAllText($originalScript).Replace("`r`n", "`n")
    [IO.File]::WriteAllText($fetchScript, $scriptText, [Text.UTF8Encoding]::new($false))
    Require-Hash $fetchScript $scriptSha
    Copy-Item $fetchScript (Join-Path $evidence 'get-windows-libs-r28.bat')
    $record.windows_fetch_script_sha256 = $scriptSha
    $record.premake_script_sha256 = $premakeSha
    Save-Record
    Push-Location (Join-Path $sourceDir 'libraries')
    try {
        Invoke-Logged $env:ComSpec @('/d', '/c', 'get-windows-libs.bat', '--amd64') 'windows-dependency-fetch.txt'
    } finally { Pop-Location }

    $winLibs = Join-Path $sourceDir 'libraries/win64'
    # The upstream batch has an export fallback. Record and verify the real result;
    # do not misrepresent an unversioned partial export as a proven checkout.
    if (-not (Test-Path (Join-Path $winLibs '.svn'))) {
        throw 'Dependency script produced no SVN working copy; revision verification required before continuing.'
    }
    Invoke-Logged $svn @('info', '--xml', $winLibs) 'windows-dependency-svn-info.xml'
    [xml]$svnInfo = Get-Content -Raw (Join-Path $evidence 'windows-dependency-svn-info.xml')
    if ([string]$svnInfo.info.entry.revision -ne '28275') { throw 'Windows library checkout is not r28275.' }
    if ([string]$svnInfo.info.entry.url -ne 'https://svn.wildfiregames.com/public/windows-libs-amd64/trunk') {
        throw 'Unexpected Windows dependency repository URL.'
    }
    $dependencyFiles = @(Get-ChildItem -LiteralPath $winLibs -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]\.svn[\\/]' })
    $dependencyInventory = @($dependencyFiles | ForEach-Object { Get-FileRecord $_ $winLibs })
    ConvertTo-Json -InputObject $dependencyInventory -Depth 5 | Set-Content -Encoding utf8 (Join-Path $evidence 'windows-dependency-files.json')
    # Preserve existing texts only; none is inferred to cover a different component.
    $noticeDir = Join-Path $evidence 'dependency-notices'
    foreach ($file in $dependencyFiles | Where-Object { $_.Name -match '(?i)^(license|copying|copyright|notice|authors|readme|redist)' -and $_.Length -lt 2MB -and $_.Extension -notin @('.dll', '.lib', '.pdb', '.exe') }) {
        $target = Join-Path $noticeDir ([IO.Path]::GetRelativePath($winLibs, $file.FullName))
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target
    }
    $systemDir = Join-Path $sourceDir 'binaries/system'
    $importDir = Join-Path $evidence 'dependency-imports'
    New-Item -ItemType Directory -Force -Path $importDir | Out-Null
    foreach ($dll in Get-ChildItem $systemDir -Filter '*.dll' -File) {
        Invoke-Logged $dumpbin @('/nologo', '/dependents', $dll.FullName) "dependency-imports/$($dll.Name).txt"
    }

    # Exact R28 definitions: workspace pyrogenesis; Release; VS2022/v143;
    # pyrogenesis depends on Collada. No need for the omitted workspace batch file.
    $env:HOSTTYPE = 'amd64'
    $premake = Join-Path $sourceDir 'build/bin/premake5.exe'
    if (-not (Test-Path $premake)) { throw 'Pinned Windows libraries did not supply premake5.exe.' }
    $record.premake_executable_sha256 = Get-Sha256 $premake
    $record.premake_arguments = @('--file=premake5.lua', '--outpath=../workspaces/vs2022-ktw', '--without-lobby', '--without-atlas', '--without-tests', 'vs2022')
    Push-Location (Join-Path $sourceDir 'build/premake')
    try { Invoke-Logged $premake $record.premake_arguments 'premake-generation.txt' }
    finally { Pop-Location }
    $workspace = Join-Path $sourceDir 'build/workspaces/vs2022-ktw'
    $solution = Join-Path $workspace 'pyrogenesis.sln'
    $project = Join-Path $workspace 'pyrogenesis.vcxproj'
    if (-not (Test-Path $solution) -or -not (Test-Path $project)) { throw 'Expected engine workspace was not generated.' }
    $projectText = Get-Content -Raw $project
    if ($projectText -notmatch 'CONFIG2_LOBBY=0') { throw 'Generated engine project did not disable lobby.' }
    if ($projectText -match '(?i)gloox[^;<>]*\.lib') { throw 'Generated engine project still links gloox.' }
    if ($projectText -notmatch '<PlatformToolset>v143</PlatformToolset>') { throw 'Generated engine project is not using v143.' }
    $releasePlatforms = @([regex]::Matches((Get-Content -Raw $solution), '(?m)^\s*Release\|([^=\s]+)\s*=\s*Release\|') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
    if ($releasePlatforms.Count -ne 1 -or $releasePlatforms[0] -ne 'x64') {
        throw "Unexpected generated Release platforms: $($releasePlatforms -join ', ')"
    }
    $record.solution_platform = $releasePlatforms[0]
    New-Item -ItemType Directory -Force -Path (Join-Path $evidence 'generated-workspace') | Out-Null
    Get-ChildItem $workspace -File | Where-Object { $_.Extension -in @('.sln', '.vcxproj', '.props') } | Copy-Item -Destination (Join-Path $evidence 'generated-workspace')
    Save-Record
    foreach ($name in @('pyrogenesis.exe', 'Collada.dll')) {
        if (Test-Path (Join-Path $systemDir $name)) { throw "Fresh source unexpectedly contains prebuilt $name." }
    }
    Invoke-Logged $msbuild @($solution, '/t:pyrogenesis', '/p:Configuration=Release', "/p:Platform=$($releasePlatforms[0])", '/m:2', '/nologo', '/v:minimal') 'engine-build.txt'

    $outputs = @('pyrogenesis.exe', 'Collada.dll')
    $builtFiles = @()
    foreach ($name in $outputs) {
        $file = Get-Item -LiteralPath (Join-Path $systemDir $name)
        Invoke-Logged $dumpbin @('/nologo', '/headers', $file.FullName) "$name.headers.txt"
        Invoke-Logged $dumpbin @('/nologo', '/dependents', $file.FullName) "$name.dependents.txt"
        Invoke-Logged $dumpbin @('/nologo', '/imports', $file.FullName) "$name.imports.txt"
        if ((Get-Content -Raw (Join-Path $evidence "$name.headers.txt")) -notmatch '8664 machine \(x64\)') {
            throw "$name is not a verified AMD64 PE."
        }
        if ((Get-Content -Raw (Join-Path $evidence "$name.imports.txt")) -match '(?i)gloox') {
            throw "$name unexpectedly imports gloox."
        }
        $builtFiles += Get-FileRecord $file $systemDir
    }
    $record.built_files = $builtFiles
    # Built binaries remain in WorkRoot on the ephemeral runner. Only text
    # evidence is uploaded while dependency/source distribution review is open.
    $record.status = 'engine-built-imports-checked-gameplay-not-tested'
    $record.completed_utc = [DateTime]::UtcNow.ToString('o')
    Save-Record
} catch {
    $record.status = 'failed'
    $record.failure = $_.Exception.Message
    $record.completed_utc = [DateTime]::UtcNow.ToString('o')
    Save-Record
    $_ | Out-String | Set-Content -Encoding utf8 (Join-Path $evidence 'failure.txt')
    throw
}
