@echo off
echo This downloads the official 0 A.D. Release 28 installer (about 1.51 GiB) if needed.
echo Its original installation window will open. KTW is a module, not a standalone engine build.
pause
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Install-Windows.ps1" -DownloadEngine -Launch
pause
