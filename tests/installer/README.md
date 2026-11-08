# Installer QA

These checks do not execute a Windows installer or prove Windows gameplay.
The recorded results are in `docs/installer/qa/`.

From the project root, run the independent portable contracts with Python 3.12+:

```sh
python3 tests/installer/test_worker_contract.py
```

The test locates the nearest project ancestor. `KTW_GAME_SOURCE` can explicitly
select a different checkout. Its safety fixtures use temporary directories.

For static PowerShell compatibility, use PowerShell 7.4.22 and PSScriptAnalyzer
1.25.0. Exact official URLs and SHA-256 hashes are recorded in
`docs/installer/qa/powershell-qa-tool-provenance.json`. Install or extract those
QA tools separately; they are not game dependencies or part of the installer.

```powershell
pwsh -NoLogo -NoProfile -NonInteractive -File tests/installer/Check-InstallerPowerShell.ps1 -SourceDirectory installer/windows -ReportPath powershell-qa.json -AnalyzerPath /path/to/PSScriptAnalyzer/PSScriptAnalyzer.psd1
```

If PSScriptAnalyzer is already on the module path, omit `-AnalyzerPath`.
The checker verifies parser errors and PowerShell 5.1 syntax, commands and .NET
API availability. `analyzer-probes` deliberately includes an incompatible file:
checking that directory must report a failure for null-coalescing syntax and
`System.IO.Path.GetRelativePath`, and no failures for `compatible.ps1`.

After the final source/documentation freeze and EXE build, verify actual embedded
payload bytes and, optionally, the separately extracted official runtime:

```sh
python3 tests/installer/verify_setup_payload.py \
  --installer dist/KazakhTotalWar_Setup_0.4.0.exe \
  --sevenzip /path/to/7z \
  --build-report dist/installer-build.json \
  --source . \
  --runtime /path/to/verified-official-r28-runtime \
  --output /path/outside/checkout/setup-payload-verification.json
```

Omit `--runtime` when the official 140-file runtime is unavailable; the report
then makes no runtime integration claim. Keep the final artifact report outside
the source tree to avoid changing the payload it describes. This checker hashes
every embedded file and compares it with the frozen source; a documentation edit
after building correctly causes a mismatch and requires another build.

Native Windows 10/11 install, prerequisite UAC, shortcuts, cancel/retry,
uninstall, offline campaign/battle/save and reload still need the actual-machine
procedure in `docs/installer/qa/SINGLE_EXE_ACCEPTANCE.md`.
