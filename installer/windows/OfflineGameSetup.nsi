; SPDX-License-Identifier: GPL-2.0-or-later
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

!ifndef PAYLOAD_DIR
  !error "PAYLOAD_DIR must point to the verified build staging directory"
!endif
!ifndef COMPONENT_0AD
  !error "COMPONENT_0AD is required"
!endif
!ifndef COMPONENT_PYTHON
  !error "COMPONENT_PYTHON is required"
!endif
!ifndef COMPONENT_VC
  !error "COMPONENT_VC is required"
!endif
!ifndef OUTPUT_FILE
  !error "OUTPUT_FILE is required"
!endif
!ifndef PAYLOAD_SHA
  !error "PAYLOAD_SHA is required"
!endif
Name "KAZAKH TOTAL WAR — Offline QA"
OutFile "${OUTPUT_FILE}"
InstallDir "$LOCALAPPDATA\Programs\SAYRAM PLANETA HOLDING\Kazakh Total War Offline QA"
RequestExecutionLevel user
SetCompressor lzma
SetCompressorDictSize 16
CRCCheck on
ShowInstDetails show
ShowUninstDetails show
BrandingText "SAYRAM PLANETA HOLDING"
VIProductVersion "0.4.0.0"
VIAddVersionKey "ProductName" "KAZAKH TOTAL WAR Setup"
VIAddVersionKey "CompanyName" "SAYRAM PLANETA HOLDING"
VIAddVersionKey "FileDescription" "KAZAKH TOTAL WAR offline QA - redistribution not cleared"
VIAddVersionKey "FileVersion" "0.4.0"
VIAddVersionKey "LegalCopyright" "SAYRAM PLANETA HOLDING contributors; original code GPL-2.0-or-later"

!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "KAZAKH TOTAL WAR"
!define MUI_WELCOMEPAGE_TEXT "KAZAKH TOTAL WAR — локальная офлайн-сборка для испытаний.$\r$\n$\r$\nВсе компоненты находятся внутри этого EXE. Загрузка из интернета при установке не выполняется.$\r$\n$\r$\nТребуются Windows 10/11 x64, 8 ГиБ на диске игры и 2 ГиБ на диске временных файлов.$\r$\n$\r$\nПубликация этой QA-сборки не разрешена: лицензии полного комплекта и запуск на Windows ещё не проверены."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD_DIR}\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\KazakhTotalWar.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Запустить KAZAKH TOTAL WAR"
!define MUI_FINISHPAGE_TEXT "Файлы игры установлены и проверены. Ярлыки созданы на рабочем столе и в меню «Пуск».$\r$\n$\r$\nЗапускайте KAZAKH TOTAL WAR с ярлыка. Для игры интернет не нужен.$\r$\n$\r$\nСохранения находятся в runtime\binaries\data\saves внутри папки игры."
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Russian"

Var ParentPid
Var SetupExit

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Нужна Windows 10/11 x64."
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "Нужна Windows 10 или Windows 11."
    Abort
  ${EndIf}
  SetShellVarContext current
  System::Call 'kernel32::GetCurrentProcessId() i.r0'
  StrCpy $ParentPid $0
FunctionEnd

Section "KAZAKH TOTAL WAR" MainSection
  InitPluginsDir
  SetOutPath "$PLUGINSDIR\payload"
  File /r "${PAYLOAD_DIR}\*"
  WriteUninstaller "$PLUGINSDIR\Uninstall.exe"
  ; Already-compressed upstream packages stay outside PAYLOAD_MANIFEST and
  ; outside the copied game source tree. Total input remains below 2 GiB.
  SetOutPath "$PLUGINSDIR\components"
  SetCompress off
  File /oname=0ad-0.28.0-win64.exe "${COMPONENT_0AD}"
  File /oname=python-3.13.16-embed-amd64.zip "${COMPONENT_PYTHON}"
  File /oname=VC_redist.x64.exe "${COMPONENT_VC}"
  SetCompress auto
  DetailPrint "Проверка встроенных компонентов и установка игры без загрузки из сети."
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PLUGINSDIR\payload\installer\windows\OfflineBootstrap.ps1" -ComponentRoot "$PLUGINSDIR\components" -InstallRoot "$INSTDIR" -PayloadRoot "$PLUGINSDIR\payload" -UninstallerPath "$PLUGINSDIR\Uninstall.exe" -PayloadManifestSha "${PAYLOAD_SHA}" -InstallerProcessId $ParentPid'
  Pop $SetupExit
  ${If} $SetupExit != 0
    MessageBox MB_ICONSTOP "Установка не завершена.$\r$\n$\r$\nПричина показана в журнале установки. Проверьте целостность EXE и свободное место. Загрузка из сети не используется. Если папка уже содержит игру или сохранения, выберите другую пустую папку. При запросе перезапуска Windows перезагрузите компьютер и запустите этот EXE снова.$\r$\n$\r$\nСуществующие игры и сохранения не заменялись."
    SetErrorLevel 1
    Abort
  ${EndIf}
  IfFileExists "$INSTDIR\KTW_INSTALL.json" +3 0
    SetErrorLevel 1
    Abort "Не найден результат успешной установки."
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  IfFileExists "$INSTDIR\KTW_INSTALL.json" +3 0
    MessageBox MB_ICONSTOP "Не найден документ установленной игры. Автоматическое удаление отменено."
    Abort
  nsExec::ExecToLog '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$INSTDIR\installer\windows\Uninstall-KTW.ps1" -InstallRoot "$INSTDIR"'
  Pop $SetupExit
  ${If} $SetupExit != 0
    MessageBox MB_ICONSTOP "Удаление не завершено. Причина показана в журнале. Сохранения не удалялись."
    SetErrorLevel 1
    Abort
  ${EndIf}
  DetailPrint "Игра удалена. Сохранения, настройки и изменённые файлы сохранены."
SectionEnd
