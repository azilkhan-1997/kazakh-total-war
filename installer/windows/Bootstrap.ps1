#requires -Version 5.1
# SPDX-License-Identifier: GPL-2.0-or-later
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InstallRoot,
    [Parameter(Mandatory=$true)][string]$PayloadRoot,
    [Parameter(Mandatory=$true)][string]$UninstallerPath,
    [Parameter(Mandatory=$true)][string]$PayloadManifestSha,
    [Parameter(Mandatory=$true)][int]$InstallerProcessId
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Product = 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR'
$CacheRoot = Join-Path $env:LOCALAPPDATA 'SAYRAM PLANETA HOLDING\InstallerCache\0.4.0'
$TemporaryRoot = $null
$CacheLock = $null
$installerUrl = 'https://releases.wildfiregames.com/0ad-0.28.0-win64.exe'
$installerSha = '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'
$installerBytes = [long]1616727146
$pythonUrl = 'https://www.python.org/ftp/python/3.13.16/python-3.13.16-embed-amd64.zip'
$pythonSha = '97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'
$pythonBytes = [long]11439094
$vcUrl = 'https://download.visualstudio.microsoft.com/download/pr/ebdab8e5-1d7b-4d9f-a11b-cbb1720c3b12/843068991DAAA1F73AD9F6239BCE4D0F6A07A51F18C37EA2A867E9BECA71295C/VC_redist.x64.exe'
$vcSha = '843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c'
$vcBytes = [long]18731856

function Assert-ParentAlive {
    if (-not (Get-Process -Id $InstallerProcessId -ErrorAction SilentlyContinue)) { throw 'Setup was closed. Installation cancelled.' }
}
function Assert-NoReparse([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Choose a physical folder without links or junctions: $current" }
        }
        $next = Split-Path -Parent $current
        if ($next -eq $current) { break }
        $current = $next
    }
}
function Assert-File([string]$Path, [string]$Sha, [long]$Bytes=-1) {
    Assert-NoReparse $Path
    $item = Get-Item -LiteralPath $Path
    if ($item.PSIsContainer -or ($Bytes -ge 0 -and $item.Length -ne $Bytes)) { throw "Unexpected downloaded file size: $Path" }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Sha) { throw "SHA-256 verification failed: $Path" }
}
function Get-VerifiedFile([string]$Url, [string]$Name, [string]$Sha, [long]$Bytes, [string]$Label) {
    Assert-ParentAlive
    $dest = Join-Path $CacheRoot $Name
    if (Test-Path -LiteralPath $dest) {
        try { Assert-File $dest $Sha $Bytes; Write-Host "$Label : verified cached download"; return $dest }
        catch {
            # Only this product's known cache filename is replaced, never user data.
            Assert-NoReparse $dest
            Remove-Item -LiteralPath $dest -Force
        }
    }
    $partial = $dest + '.partial.' + [guid]::NewGuid().ToString('N')
    $web = New-Object Net.WebClient
    $oldProtocol = [Net.ServicePointManager]::SecurityProtocol
    try {
        [Net.ServicePointManager]::SecurityProtocol = $oldProtocol -bor [Net.SecurityProtocolType]::Tls12
        Write-Host "$Label : downloading from the official publisher..."
        $task = $web.DownloadFileTaskAsync([uri]$Url, $partial)
        $timer = [Diagnostics.Stopwatch]::StartNew()
        $lastProgress = -10
        while (-not $task.IsCompleted) {
            if (-not (Get-Process -Id $InstallerProcessId -ErrorAction SilentlyContinue)) { $web.CancelAsync(); throw 'Setup was closed. Download cancelled.' }
            if ($timer.Elapsed.TotalSeconds -ge $lastProgress + 5) {
                $length = if (Test-Path -LiteralPath $partial) { (Get-Item -LiteralPath $partial).Length } else { 0 }
                $percent = [Math]::Min(99, [Math]::Floor(100.0 * $length / $Bytes))
                Write-Host "$Label : $percent%"
                $lastProgress = $timer.Elapsed.TotalSeconds
            }
            Start-Sleep -Milliseconds 300
        }
        $task.GetAwaiter().GetResult()
        Assert-ParentAlive
        Assert-File $partial $Sha $Bytes
        [IO.File]::Move($partial, $dest)
        Write-Host "$Label : download verified"
        return $dest
    } finally {
        $web.Dispose()
        [Net.ServicePointManager]::SecurityProtocol = $oldProtocol
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue }
    }
}
function Test-VcRuntime {
    $dll = Join-Path ([Environment]::SystemDirectory) 'VCRUNTIME140_1.dll'
    if (-not (Test-Path -LiteralPath $dll -PathType Leaf)) { return $false }
    $info = [Diagnostics.FileVersionInfo]::GetVersionInfo($dll)
    $version = [version]::new($info.FileMajorPart, $info.FileMinorPart, $info.FileBuildPart, $info.FilePrivatePart)
    return $version -ge [version]'14.44.35211.0'
}
function Register-Game([string]$Root) {
    $record = Get-Content -LiteralPath (Join-Path $Root 'KTW_INSTALL.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($record.product -ne $Product -or $record.install_id -notmatch '^[0-9a-f]{32}$') { throw 'Invalid installed-product record.' }
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SPH.KazakhTotalWar.' + $record.install_id
    $programs = [Environment]::GetFolderPath('Programs')
    $desktop = [Environment]::GetFolderPath('DesktopDirectory')
    $folder = Join-Path $programs 'SAYRAM PLANETA HOLDING'
    [IO.Directory]::CreateDirectory($folder) | Out-Null
    $shell = New-Object -ComObject WScript.Shell
    $createdLinks = @()
    foreach ($requestedPath in @((Join-Path $folder 'KAZAKH TOTAL WAR.lnk'), (Join-Path $desktop 'KAZAKH TOTAL WAR.lnk'))) {
        $linkPath = $requestedPath
        if (Test-Path -LiteralPath $linkPath) {
            $oldTarget = ''
            try { $oldTarget = $shell.CreateShortcut($linkPath).TargetPath } catch { $oldTarget = '' }
            $owned = $oldTarget -ieq (Join-Path $Root 'KazakhTotalWar.exe')
            if (-not $owned -and $oldTarget) {
                $oldMarker = Join-Path (Split-Path -Parent $oldTarget) 'KTW_INSTALL.json'
                if (Test-Path -LiteralPath $oldMarker -PathType Leaf) {
                    try { $oldRecord = Get-Content -LiteralPath $oldMarker -Raw -Encoding UTF8 | ConvertFrom-Json; $owned = $oldRecord.product -ceq $Product } catch { $owned = $false }
                }
            }
            if (-not $owned) {
                $linkPath = Join-Path (Split-Path -Parent $requestedPath) ('KAZAKH TOTAL WAR (' + $record.install_id.Substring(0,8) + ').lnk')
                if (Test-Path -LiteralPath $linkPath) {
                    $alternateTarget = ''
                    try { $alternateTarget = $shell.CreateShortcut($linkPath).TargetPath } catch { $alternateTarget = '' }
                    if ($alternateTarget -ine (Join-Path $Root 'KazakhTotalWar.exe')) { throw 'A shortcut with this name already exists and was preserved.' }
                }
            }
        }
        $link = $shell.CreateShortcut($linkPath)
        $link.TargetPath = Join-Path $Root 'KazakhTotalWar.exe'
        $link.WorkingDirectory = $Root
        $link.Description = 'KAZAKH TOTAL WAR - SAYRAM PLANETA HOLDING'
        $link.IconLocation = (Join-Path $Root 'KazakhTotalWar.exe') + ',0'
        $link.Save()
        if (-not (Test-Path -LiteralPath $linkPath)) { throw 'Could not create a game shortcut.' }
        $createdLinks += $linkPath
    }
    New-Item -Path $key -Force | Out-Null
    $values = @{DisplayName='KAZAKH TOTAL WAR: LEGACY OF THE STEPPE';DisplayVersion='0.4.0';Publisher='SAYRAM PLANETA HOLDING';InstallLocation=$Root;DisplayIcon=(Join-Path $Root 'KazakhTotalWar.exe');UninstallString=('"' + (Join-Path $Root 'Uninstall.exe') + '"');URLInfoAbout='https://sayramplaneta.com/games/kazakh-total-war/legacy-of-the-steppe'}
    foreach ($name in $values.Keys) { New-ItemProperty -Path $key -Name $name -Value $values[$name] -PropertyType String -Force | Out-Null }
    New-ItemProperty -Path $key -Name NoModify -Value 1 -PropertyType DWord -Force | Out-Null
    New-ItemProperty -Path $key -Name NoRepair -Value 1 -PropertyType DWord -Force | Out-Null
    $record | Add-Member -NotePropertyName shortcuts -NotePropertyValue $createdLinks -Force
    $record | Add-Member -NotePropertyName registration_complete -NotePropertyValue $true -Force
    $marker = Join-Path $Root 'KTW_INSTALL.json'
    $temporary = $marker + '.registration.' + [guid]::NewGuid().ToString('N')
    [IO.File]::WriteAllText($temporary, ($record | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
    [IO.File]::Replace($temporary, $marker, $null)
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT -or -not [Environment]::Is64BitProcess) { throw 'Windows10/11 x64 is required.' }
    if ([Environment]::OSVersion.Version.Major -lt 10) { throw 'Windows10 or newer is required.' }
    $InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
    Assert-NoReparse $InstallRoot
    if (Test-Path -LiteralPath $InstallRoot) {
        if (-not (Test-Path -LiteralPath $InstallRoot -PathType Container)) { throw 'Choose an empty installation folder.' }
        if (@(Get-ChildItem -LiteralPath $InstallRoot -Force).Count -ne 0) {
            $existingMarker = Join-Path $InstallRoot 'KTW_INSTALL.json'
            if (Test-Path -LiteralPath $existingMarker -PathType Leaf) {
                $existing = Get-Content -LiteralPath $existingMarker -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($existing.product -ceq $Product -and $existing.delivery_version -ceq '0.4.0' -and [IO.Path]::GetFullPath($existing.install_root) -ceq $InstallRoot) {
                    $existingLauncher = Join-Path $InstallRoot 'KazakhTotalWar.exe'
                    Assert-File $existingLauncher '3c1906f7b2c384d2470c4ddcdf35b1da01697f61260fdb3033e44d9c3e12f969'
                    Assert-File (Join-Path $InstallRoot 'runtime\binaries\system\pyrogenesis.exe') '11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f'
                    & $existingLauncher --check
                    if ($LASTEXITCODE -ne 0) { throw 'The existing installation needs repair. Choose a new empty folder; existing saves remain untouched.' }
                    Register-Game $InstallRoot
                    Write-Host 'The existing verified installation is ready. Shortcuts have been restored.'
                    exit 0
                }
            }
            throw 'The selected folder contains files or saved games. Choose another empty folder. Existing game files and saves are preserved.'
        }
    }
    $drive = New-Object IO.DriveInfo([IO.Path]::GetPathRoot($InstallRoot))
    if ($drive.AvailableFreeSpace -lt 8GB) { throw 'At least8GiB free disk space is required.' }
    Assert-NoReparse $CacheRoot
    $cacheMarker = Join-Path $CacheRoot 'OWNER.txt'
    if (Test-Path -LiteralPath $CacheRoot) {
        if (-not (Test-Path -LiteralPath $cacheMarker) -or (Get-Content -LiteralPath $cacheMarker -Raw) -ne $Product) { throw 'The installer cache is not owned by this product. Contact support; no files were changed.' }
    } else {
        [IO.Directory]::CreateDirectory($CacheRoot) | Out-Null
        [IO.File]::WriteAllText($cacheMarker, $Product)
    }
    $CacheLock = [IO.File]::Open((Join-Path $CacheRoot 'setup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $cacheDrive = New-Object IO.DriveInfo([IO.Path]::GetPathRoot($CacheRoot))
    if ($cacheDrive.AvailableFreeSpace -lt 2GB) { throw 'At least2GiB free space is required on the Windows user-profile drive for verified setup downloads.' }
    Assert-File (Join-Path $PayloadRoot 'PAYLOAD_MANIFEST.json') $PayloadManifestSha
    $manifest = Get-Content -LiteralPath (Join-Path $PayloadRoot 'PAYLOAD_MANIFEST.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $workerRecord = @($manifest.files | Where-Object { $_.path -ceq 'installer/windows/setup_worker.py' })
    if ($manifest.product -ne $Product -or $workerRecord.Count -ne 1) { throw 'Installer payload is incomplete.' }
    $worker = Join-Path $PayloadRoot 'installer\windows\setup_worker.py'
    Assert-File $worker $workerRecord[0].sha256 $workerRecord[0].bytes
    # Direct publisher downloads remain in a product-owned cache for retry.
    # No system Python installation, PATH/registry edits or Python package installs.
    $pythonZip = Get-VerifiedFile $pythonUrl 'python-3.13.16-embed-amd64.zip' $pythonSha $pythonBytes 'Preparing setup tools'
    $TemporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ('SPH-KTW-tools-' + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($TemporaryRoot) | Out-Null
    Expand-Archive -LiteralPath $pythonZip -DestinationPath $TemporaryRoot
    $python = Join-Path $TemporaryRoot 'python.exe'
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Private setup tools are incomplete.' }
    if (-not (Test-VcRuntime)) {
        $vc = Get-VerifiedFile $vcUrl 'VC_redist.x64.exe' $vcSha $vcBytes 'Microsoft prerequisite'
        Write-Host 'The official Microsoft prerequisite installer will open. Review its license and choose Install.'
        Assert-ParentAlive
        # Visible original license UI; elevation applies only to this publisher installer.
        $vcProcess = Start-Process -FilePath $vc -ArgumentList @('/install','/norestart') -Verb RunAs -Wait -PassThru
        if ($vcProcess.ExitCode -eq 3010 -or $vcProcess.ExitCode -eq 1641) { throw 'Microsoft requires a restart. Restart Windows and run this installer again; verified downloads are retained.' }
        if ($vcProcess.ExitCode -ne 0 -and -not (@(1638, -2147023258) -contains $vcProcess.ExitCode -and (Test-VcRuntime))) { throw ('Microsoft prerequisite was cancelled or failed (exit ' + $vcProcess.ExitCode + '). The game was not installed.') }
        if (-not (Test-VcRuntime)) { throw 'Required Microsoft runtime is still unavailable. Restart Windows and retry setup.' }
    }
    $official = Get-VerifiedFile $installerUrl '0ad-0.28.0-win64.exe' $installerSha $installerBytes 'Game files'
    Assert-ParentAlive
    Write-Host 'All downloads verified. Installing the game...'
    & $python -I $worker --payload $PayloadRoot --target $InstallRoot --runtime-installer $official --uninstaller $UninstallerPath --payload-manifest-sha $PayloadManifestSha --parent-pid $InstallerProcessId
    if ($LASTEXITCODE -ne 0) { throw ('Game installation failed (worker exit ' + $LASTEXITCODE + '). Existing installs and saves were not replaced.') }
    Register-Game $InstallRoot
    Write-Host 'Installation complete. Start KAZAKH TOTAL WAR from your desktop or the Start menu.'
    exit 0
} catch {
    Write-Host ('SETUP FAILED: ' + $_.Exception.Message)
    exit 1
} finally {
    if ($CacheLock) { $CacheLock.Dispose() }
    if ($TemporaryRoot -and (Test-Path -LiteralPath $TemporaryRoot)) {
        Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
