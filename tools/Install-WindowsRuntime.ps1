#requires -Version 5.1
# SPDX-License-Identifier: GPL-2.0-or-later
# Downloads official files for this user's local installation. The official
# installer is verified and statically extracted; its executable is NEVER run.
[CmdletBinding()]
param(
    [string]$PythonExe,
    [string]$InstallerPath,
    [string]$VcRedistPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$kit = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$runtime = Join-Path $kit 'runtime'
$stageParent = $null
$installerUrl = 'https://releases.wildfiregames.com/0ad-0.28.0-win64.exe'
$installerSha = '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'
$installerBytes = [long]1616727146
$vcUrl = 'https://download.visualstudio.microsoft.com/download/pr/ebdab8e5-1d7b-4d9f-a11b-cbb1720c3b12/843068991DAAA1F73AD9F6239BCE4D0F6A07A51F18C37EA2A867E9BECA71295C/VC_redist.x64.exe'
$vcSha = '843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c'
$vcBytes = [long]18731856
$extractor = Join-Path $PSScriptRoot 'extract_r28_nsisbi.py'
$expectedManifest = Join-Path $kit 'docs\windows-runtime-manifest.json'

function Assert-FileHash([string]$Path, [string]$Sha, [long]$Bytes = -1) {
    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    if ($item.PSIsContainer -or ($Bytes -ge 0 -and $item.Length -ne $Bytes)) {
        throw "Unexpected file size: $Path"
    }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Sha) {
        throw "SHA-256 verification failed: $Path. This file has not been executed or accepted. Obtain the correct file; no checksum override is supported."
    }
}

function Get-VerifiedDownload([string]$Url, [string]$Destination, [string]$Sha, [long]$Bytes) {
    if (Test-Path -LiteralPath $Destination) {
        Assert-FileHash $Destination $Sha $Bytes
        Write-Host "Reusing verified file: $Destination"
        return $Destination
    }
    $parent = Split-Path -Parent $Destination
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $partial = $Destination + '.partial.' + [guid]::NewGuid().ToString('N')
    $web = New-Object Net.WebClient
    $oldProtocol = [Net.ServicePointManager]::SecurityProtocol
    try {
        [Net.ServicePointManager]::SecurityProtocol = $oldProtocol -bor [Net.SecurityProtocolType]::Tls12
        Write-Host "Downloading official file ($Bytes bytes): $Url"
        # Streams to disk rather than loading the 1.6 GB installer into memory.
        $web.DownloadFile($Url, $partial)
        Assert-FileHash $partial $Sha $Bytes
        [IO.File]::Move($partial, $Destination)
        return $Destination
    } finally {
        $web.Dispose()
        [Net.ServicePointManager]::SecurityProtocol = $oldProtocol
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue }
    }
}

function Find-SetupPython {
    $probe = @'
import sys, json, lzma, hashlib, zipfile, struct, shutil
if sys.platform != 'win32' or sys.implementation.name != 'cpython' or sys.version_info < (3, 11) or struct.calcsize('P') != 8:
    raise SystemExit('Setup requires 64-bit Windows CPython 3.11 or newer with lzma support.')
print(json.dumps({'executable': sys.executable, 'version': sys.version.split()[0]}))
'@
    $candidates = @()
    if ($PythonExe) {
        $selected = (Resolve-Path -LiteralPath $PythonExe).Path
        if ($selected -match '\\Microsoft\\WindowsApps\\') {
            throw 'Select the actual installed python.exe with -PythonExe, not a Windows Store execution alias.'
        }
        $candidates += @{ Path = $selected; Prefix = @() }
    } else {
        # Restrict lookup to existing applications; do not invoke aliases,
        # functions or the Microsoft Store application-execution stubs.
        foreach ($name in @('py.exe', 'python.exe')) {
            $command = Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($command -and $command.Source -notmatch '\\Microsoft\\WindowsApps\\') {
                $prefix = @()
                if ($name -eq 'py.exe') { $prefix = @('-3') }
                $candidates += @{ Path = $command.Source; Prefix = $prefix }
            }
        }
    }
    foreach ($candidate in $candidates) {
        $savedAllowInstall = [Environment]::GetEnvironmentVariable('PYLAUNCHER_ALLOW_INSTALL', 'Process')
        $savedAlwaysInstall = [Environment]::GetEnvironmentVariable('PYLAUNCHER_ALWAYS_INSTALL', 'Process')
        $savedManagerInstall = [Environment]::GetEnvironmentVariable('PYTHON_MANAGER_AUTOMATIC_INSTALL', 'Process')
        try {
            # Disable both legacy py.exe install-on-demand and the current
            # Python install manager's documented automatic-install setting.
            [Environment]::SetEnvironmentVariable('PYLAUNCHER_ALLOW_INSTALL', $null, 'Process')
            [Environment]::SetEnvironmentVariable('PYLAUNCHER_ALWAYS_INSTALL', $null, 'Process')
            [Environment]::SetEnvironmentVariable('PYTHON_MANAGER_AUTOMATIC_INSTALL', 'false', 'Process')
            $commandPath = $candidate.Path
            $commandArgs = @($candidate.Prefix) + @('-I', '-')
            # Source travels over stdin, avoiding PowerShell 5.1's native
            # double-quote escaping differences for python -c arguments.
            $answer = $probe | & $commandPath @commandArgs 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $info = ($answer -join "`n") | ConvertFrom-Json
            if (-not (Test-Path -LiteralPath $info.executable -PathType Leaf)) { continue }
            Write-Host "Using installed CPython $($info.version): $($info.executable)"
            return [string]$info.executable
        } catch {
            # Try the next already-installed interpreter; never download Python.
        } finally {
            [Environment]::SetEnvironmentVariable('PYLAUNCHER_ALLOW_INSTALL', $savedAllowInstall, 'Process')
            [Environment]::SetEnvironmentVariable('PYLAUNCHER_ALWAYS_INSTALL', $savedAlwaysInstall, 'Process')
            [Environment]::SetEnvironmentVariable('PYTHON_MANAGER_AUTOMATIC_INSTALL', $savedManagerInstall, 'Process')
        }
    }
    throw 'Install 64-bit CPython 3.11 or newer from https://www.python.org/downloads/windows/ (including the standard lzma module), then retry. Alternatively pass -PythonExe "C:\Path\To\python.exe". Python is needed only for this setup, not for playing the game.'
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT -or -not [Environment]::Is64BitProcess) {
        throw 'Run this script in 64-bit Windows PowerShell 5.1 or newer on Windows 10/11 x64.'
    }
    if (Test-Path -LiteralPath $runtime) {
        throw "The runtime folder already exists: $runtime. This setup will not overwrite an existing game or its saves. Launch KazakhTotalWar.exe, or extract a new installation kit into a different directory."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $kit 'KazakhTotalWar.exe') -PathType Leaf)) {
        throw 'The kit is incomplete: KazakhTotalWar.exe is missing. Extract the entire installation kit before running setup.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $kit 'mods\kazakh_total_war\mod.json') -PathType Leaf)) {
        throw 'The kit is incomplete: mods\kazakh_total_war\mod.json is missing.'
    }
    # These hashes pin the audited source extractor and its independent payload
    # manifest, not a dynamically obtained checksum from the download server.
    Assert-FileHash $extractor 'c9c109967d74128e6d61c0cb285e397518a89e79d6899e87bb211c67018b3570'
    Assert-FileHash $expectedManifest '6acc32df690bb3a0547a0c64818f91a2951aa24c8c1bd216b84a9d40cb1aad7d'
    $python = Find-SetupPython

    # Same-directory staging allows a rename after all validation succeeds.
    # Directory creation is also an early check of writable installation space.
    $stageParent = Join-Path $kit ('setup-staging-' + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($stageParent) | Out-Null
    $candidate = Join-Path $stageParent 'candidate-runtime'
    $driveRoot = [IO.Path]::GetPathRoot($kit)
    if ($driveRoot -match '^[A-Za-z]:\\$') {
        $drive = New-Object IO.DriveInfo($driveRoot)
        if ($drive.AvailableFreeSpace -lt 8GB) {
            throw 'At least 8 GiB of free space is required for the downloaded installer, extracted runtime and temporary setup files.'
        }
    }

    if ($InstallerPath) {
        $installer = (Resolve-Path -LiteralPath $InstallerPath).Path
        Assert-FileHash $installer $installerSha $installerBytes
    } else {
        $installer = Get-VerifiedDownload $installerUrl (Join-Path $kit 'downloads\0ad-0.28.0-win64.exe') $installerSha $installerBytes
    }

    $vcSystem = Join-Path ([Environment]::SystemDirectory) 'VCRUNTIME140_1.dll'
    if ($VcRedistPath -or -not (Test-Path -LiteralPath $vcSystem -PathType Leaf)) {
        $vcDestination = Join-Path $kit 'prerequisites\VC_redist.x64.exe'
        if ($VcRedistPath) {
            $vcSource = (Resolve-Path -LiteralPath $VcRedistPath).Path
            Assert-FileHash $vcSource $vcSha $vcBytes
            if (Test-Path -LiteralPath $vcDestination) {
                Assert-FileHash $vcDestination $vcSha $vcBytes
            } else {
                [IO.Directory]::CreateDirectory((Split-Path -Parent $vcDestination)) | Out-Null
                $vcTemporary = $vcDestination + '.partial.' + [guid]::NewGuid().ToString('N')
                try {
                    Copy-Item -LiteralPath $vcSource -Destination $vcTemporary
                    Assert-FileHash $vcTemporary $vcSha $vcBytes
                    [IO.File]::Move($vcTemporary, $vcDestination)
                } finally {
                    if (Test-Path -LiteralPath $vcTemporary) { Remove-Item -LiteralPath $vcTemporary -Force -ErrorAction SilentlyContinue }
                }
            }
        } else {
            $null = Get-VerifiedDownload $vcUrl $vcDestination $vcSha $vcBytes
        }
    }

    Write-Host 'Extracting the verified official installer as data. Its installer program will not be executed.'
    & $python -I $extractor $installer $candidate
    if ($LASTEXITCODE -ne 0) { throw "Static extraction failed (Python exit $LASTEXITCODE). No runtime was published." }

    # This validator is deliberately separate from the extractor. It checks
    # every extracted byte against the independently recorded 140-file manifest
    # and checks internal ZIP CRCs before copying our module and publishing.
    $validator = @'
import hashlib, json, os, pathlib, shutil, struct, sys, zipfile
root, expected_path, mod = map(pathlib.Path, sys.argv[1:])
def require(ok, message):
    if not ok:
        raise ValueError(message)
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
def regular_tree(directory):
    result = []
    for p in [directory, *directory.rglob('*')]:
        require(not p.is_symlink() and not (getattr(p.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse point not permitted: ' + str(p))
        if p.is_file():
            result.append(p)
    return result
expected = json.loads(expected_path.read_text(encoding='utf-8'))
actual = json.loads(root.with_name(root.name + '-manifest.json').read_text(encoding='utf-8'))
require(expected['source_sha256'] == actual['source_sha256'] == '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1', 'Installer provenance mismatch')
require(expected['source_bytes'] == actual['source_bytes'] == 1616727146, 'Installer byte count mismatch')
require(expected['file_count'] == actual['file_count'] == 140, 'Unexpected payload count')
for flag in ('all_file_crc_verified', 'header_crc_verified', 'installer_stub_crc_verified'):
    require(actual[flag] is True, 'Extractor did not verify ' + flag)
require(actual['installer_execution'] is False, 'Unexpected installer execution report')
lookup = {item['path']: item for item in expected['files']}
require(len(lookup) == 140 and len(actual['files']) == 140, 'Duplicate manifest paths')
require({item['path'] for item in actual['files']} == set(lookup), 'Unexpected, missing or duplicate extraction manifest paths')
require({p.relative_to(root).as_posix() for p in regular_tree(root)} == set(lookup), 'Unexpected or missing runtime file')
for item in actual['files']:
    name = item['path']
    p = pathlib.PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name, 'Unsafe payload path')
    require(name in lookup, 'Unexpected payload: ' + name)
    reference = lookup[name]
    require(all(item[k] == reference[k] for k in ('bytes', 'sha256', 'crc32')) and item['crc_verified'] is True, 'Extraction manifest mismatch: ' + name)
    target = root / p
    require(target.stat().st_size == reference['bytes'] and sha(target) == reference['sha256'], 'Runtime size/hash mismatch: ' + name)
for name in ('mod', 'public'):
    with zipfile.ZipFile(root / 'binaries/data/mods' / name / (name + '.zip')) as archive:
        require(archive.testzip() is None, 'ZIP CRC validation failed: ' + name)
base = json.loads((root / 'binaries/data/mods/public/mod.json').read_text(encoding='utf-8'))
game = json.loads((mod / 'mod.json').read_text(encoding='utf-8'))
require(base['name'] == '0ad' and base['version'] == '0.28.0', 'Not Release 28')
require(game['name'] == 'kazakh_total_war' and game['dependencies'] == ['0ad=0.28.0'], 'Incompatible game module')
engine = root / 'binaries/system/pyrogenesis.exe'
require(sha(engine) == '11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f', 'Engine executable mismatch')
with engine.open('rb') as f:
    header = f.read(64)
    require(header[:2] == b'MZ', 'Missing MZ header')
    f.seek(struct.unpack_from('<I', header, 60)[0])
    pe = f.read(26)
require(pe[:4] == b'PE\0\0' and struct.unpack_from('<H', pe, 4)[0] == 0x8664 and struct.unpack_from('<H', pe, 24)[0] == 0x20b, 'Engine must be AMD64 PE32+')
regular_tree(mod)
destination = root / 'binaries/data/mods/kazakh_total_war'
shutil.copytree(mod, destination)
for source in regular_tree(mod):
    require(sha(source) == sha(destination / source.relative_to(mod)), 'Copied game module hash mismatch')
for directory in ('binaries/data/config', 'binaries/data/cache', 'binaries/data/saves', 'binaries/logs'):
    (root / directory).mkdir(parents=True, exist_ok=True)
report = dict(engineVersion='0.28.0', moduleVersion=game['version'], officialInstallerSha256=actual['source_sha256'],
              runtimeFilesVerified=140, archiveCrcVerified=True, nativeWindowsExecutionTested=False,
              gameplayTested=False, installerExecuted=False, pythonRequiredForGameplay=False,
              moduleFiles=[dict(path=p.relative_to(mod).as_posix(), sha256=sha(p)) for p in sorted(regular_tree(mod))])
(root / 'KTW_SETUP_VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(root.with_name(root.name + '-manifest.json'), root / 'OFFICIAL_RUNTIME_PROVENANCE.json')
print('Validated all 140 official payload files, both data ZIP CRCs, AMD64 engine and copied game module. No engine execution was performed.')
'@
    $validator | & $python -I - $candidate $expectedManifest (Join-Path $kit 'mods\kazakh_total_war')
    if ($LASTEXITCODE -ne 0) { throw "Runtime validation failed (Python exit $LASTEXITCODE). No runtime was published." }
    # Directory.Move will fail if another setup has already created runtime;
    # it never merges with or overwrites an existing folder/save profile.
    [IO.Directory]::Move($candidate, $runtime)
    Write-Host "Runtime installed and verified: $runtime"
    Write-Host 'Start KazakhTotalWar.exe to play. Python is no longer required. Windows gameplay still needs to be tested on this machine.'
    if (-not (Test-Path -LiteralPath $vcSystem -PathType Leaf)) {
        Write-Warning ('Before launching, manually run the verified Microsoft prerequisite: ' + (Join-Path $kit 'prerequisites\VC_redist.x64.exe') + '. Its own installer may request administrator approval. This script has not run it.')
    }
} catch {
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
} finally {
    if ($stageParent -and (Test-Path -LiteralPath $stageParent)) {
        # Only this invocation's newly created staging directory is removed.
        # Existing runtime, downloads, prerequisites and user saves are retained.
        Remove-Item -LiteralPath $stageParent -Recurse -Force -ErrorAction SilentlyContinue
    }
}
