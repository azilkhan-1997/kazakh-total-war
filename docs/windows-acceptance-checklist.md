# Windows 10/11 acceptance — v0.3 launcher / v0.2 gameplay

This is a test procedure, not a record of a successful Windows run. The real
campaign/battle loop was previously observed on Linux; see
`docs/native-qa-v0.2.md` in the accompanying source archive. Native Windows
gameplay, GPU performance and Steam acceptance remain **not tested** until
the corresponding evidence is collected on a Windows PC.

## 1. Prepare and verify the bootstrap kit

Extract the entire ZIP into a short writable directory, for example
`C:\Games\KTW-Test`. Close the game before verification. Complete runtime
setup using the included installation instructions. The bootstrap ZIP itself
does not contain the engine; missing runtime files before setup are expected,
but they are a failed readiness check, never a successful game test.

From the extracted kit, run Windows PowerShell 5.1 or PowerShell 7:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Test-Windows.ps1
$LASTEXITCODE
```

The script reads `BUILD_MANIFEST.json`, verifies every listed size/SHA-256,
verifies all **140** official runtime files against
`docs/windows-runtime-manifest.json` (including PDB symbols and both large
asset archives), and verifies the installed KTW module against the packaged
module hashes. It waits for `KazakhTotalWar.exe --check`, captures its UTF-8
JSON diagnostic and exit code, and records Windows version, GPU driver and
processor information where Windows CIM permits it. A missing Visual C++
runtime is a prerequisite failure; follow the installer's instructions and
run the preflight again afterward.

Reports go into a unique `qa-reports/windows-preflight-*.json`. An alternate
new path can be supplied with `-ReportPath`. No existing report is overwritten.
Exit `0` means **preflight passed only**; exit `1` means a readiness check
failed or could not run. A script-level error is also a failed test, even if
no report was written. The launcher is not executed when package integrity
fails. No game or automatic headless battle is started.

The launcher check creates portable directories if necessary and writes then
removes temporary permission probes. It does not load or modify saves. The
harness never imports saves, installs a QA mod, downloads dependencies, runs
an installer, or alters game configuration. Hashes cover manifest-listed
files, not an exhaustive scan of arbitrary extra files, and do not establish
publisher authenticity: verify the distributed archive checksum separately.
The report is unsigned diagnostic evidence, not a certificate.

## 2. Native interactive acceptance

Use a **separate fresh extraction** for acceptance, so failures and test saves
do not affect an existing campaign. Keep its `runtime/binaries/data` and
`runtime/binaries/logs` together. Start with `KazakhTotalWar.exe`, never with
an unrelated installed 0 A.D. executable. Record build/source revision from
the preflight report, Windows version, GPU/driver, display resolution, graphics
preset, tester, date and each test's observed result.

For each row use `PASS`, `FAIL`, or `NOT TESTED`; link screenshots, logs and
copied test saves. Do not change the preflight's automatically generated
`not_tested` entries to suggest that the script ran these tests. Keep manual
results in a separate acceptance record.

| Test | Required observable result / evidence | Current status |
| --- | --- | --- |
| Fresh launch | Original KTW menu opens without engine/JS errors; exit closes the process. | NOT TESTED |
| RU / KK | Change language; capture menu and political council, including Ә Ғ Қ Ң Ө Ұ Ү Һ І. No missing glyphs. | NOT TESTED |
| Campaign | New campaign shows the 3D province map; select army, recruit, move to a legal neighbour, end turn; money and army counts change consistently. | NOT TESTED |
| Battle transition | Move from Shu to Sarysu and progress to contact; encounter shows both armies; choosing battle loads a separate real 3D battlefield with matching composition. | NOT TESTED |
| Commands | Select multiple units; order movement, attack, hold and a formation. Observe infantry combat and mounted archer movement/shooting; record actual animation defects. | NOT TESTED |
| Outcome | Let combat resolve normally; separately exercise defeat. Record winner, starting/remaining unit counts and commander outcomes; do not alter health or force a synthetic victory. | NOT TESTED |
| Return | Battle returns to campaign with the same result applied once; losses persist and ownership follows the outcome. Another turn/load must not apply casualties again. | NOT TESTED |
| Political consequence | If a commander dies, retain the archived character and record successor/vacancy and explained political events. A different battle outcome need not kill a commander. | NOT TESTED |
| Save after battle | Save, close the entire process, relaunch, load; compare campaign date, money, army composition, ruler, event journal and pending battle state. | NOT TESTED |
| Save during battle | Save, close, relaunch, load; surviving unit identities and commander links remain consistent; combat resumes. Normal subsequent time/health changes are expected. | NOT TESTED |
| Interrupted outcome | In a disposable test copy, restart from a pre-result save; confirm a valid campaign or resumable battle, never duplicated losses or partially updated character state. Preserve both saves/logs. | NOT TESTED |
| Legacy saves | Use the supplied explicit legacy-import workflow and separate test copies; load v0.1 campaign and battle saves; originals stay intact and migration does not invent old commander identities. | NOT TESTED |
| Alternate path | Repeat launch and save/load from a short directory containing spaces and Kazakh letters, e.g. `C:\Games\Қазақ сынақ`. Native API implementation alone does not prove this. | NOT TESTED |
| Offline | After setup, disconnect network and repeat launch, campaign, battle and save/load. | NOT TESTED |
| Audio / controls | On real audio hardware verify effects, volume controls and hotkeys. Record missing content separately from playback defects. | NOT TESTED |
| Performance | Record hardware, renderer, resolution/preset, warrior count, measured FPS/frame times and method. Do not infer 60 FPS or 1,000–5,000 warriors from successful startup. | NOT TESTED |

Copy `runtime/binaries/logs` after each failed run before another launch can
replace logs. Screenshots must be actual game output; evidence must state if
software rendering, debug overlays, accelerated simulation or test fixtures
were used. Keep personal paths out of publicly posted reports when needed.

## 3. Optional headless QA is separate

`Test-Windows.ps1` intentionally has no `-Headless` switch. The archived
v0.2 fixture is under `evidence/v0.2/native-fixture` in the source kit; its
`mod.json` names it `ktw_qa_v02`. If manually testing it, create a second
complete runtime, install the production module and fixture under that
runtime's `binaries/data/mods`, and use `-writableRoot` from its
`binaries/system` directory. Do not add the fixture to the normal play runtime
or the user's existing 0 A.D. profile. Follow `docs/native-qa-v0.2.md` for
commands and the full `KTW_V02_HEADLESS` outcome checks. A timeout or a process
exit alone is not a successful battle; headless success does not validate
graphics, input, mounted animations or native save/load.

## Harness validation status

The harness was authored and peer reviewed in Linux. The PowerShell parser
reported no syntax errors. PowerShell on Linux passed 15 helper checks for
legal spaces, unsafe manifest paths, size/SHA-256 verification, equal-size
tampering, duplicate entries and report-path symlinks. An end-to-end negative
run verified its fixture bundle, recorded all 140 missing runtime files,
skipped launcher execution, returned failure and retained every gameplay
entry as `not_tested`. This exercises error reporting without a fake success.

Native Windows PowerShell 5.1, WinAPI process execution, CIM inventory and
this complete Windows procedure have **not** been run in the current
development environment. The separate
Wine attempt failed before any Windows process could start because the host
denied wineserver's Unix socket creation; it is not evidence of Windows game
compatibility. See `docs/WINE_TEST_ENV.md` and the launcher README in the source
kit. Preserve unsuccessful reports and outstanding checks in the project
state; do not mark Part 1 or Steam readiness complete from preflight alone.
