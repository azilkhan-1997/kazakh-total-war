@echo off
setlocal
echo KAZAKH TOTAL WAR - SAYRAM PLANETA HOLDING
echo First setup requires Windows x64, installed CPython 3.11+ x64 and Internet.
echo The engine is downloaded from Wildfire Games and verified before extraction.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Install-WindowsRuntime.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not complete. Read the error above and README_WINDOWS_RU.md.
  pause
  exit /b 1
)
echo.
echo Read any Microsoft prerequisite instruction above, then start KazakhTotalWar.exe.
pause
exit /b 0
