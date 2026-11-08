# Offline QA installer independent review

Reviewed the source at `/workspace/scratch/a712cf7eed58/offline_game`, preserving all installer/game files. Review date: 2026-11-08.

The three new files are `installer/windows/OfflineBootstrap.ps1`, `OfflineGameSetup.nsi` and `build_offline_qa.py`. Source hashes are recorded in `independent-python-and-source-review.json`.

## Results

- All three installer PowerShell files parse successfully and pass PSScriptAnalyzer 1.25.0 static Windows PowerShell 5.1 syntax/API/type profiles, with no diagnostics. Host interpreter: PowerShell 7.4.22 on Ubuntu; report: `powershell-compatibility.json`.
- Analyzer positive/negative controls behave as expected: the compatible probe has no diagnostics; the deliberately incompatible probe is rejected for the null-coalescing operator and the unavailable .NET Framework `Path.GetRelativePath` method. `analyzer-negative-control.json` therefore intentionally records `pass: false` and exit 1, which confirms the analyzer is active.
- Original helper function definitions were selected with the PowerShell AST and executed in isolation against disposable fixtures. The top-level installer was never executed and its Windows guard was never bypassed. All 13 fixtures pass: original valid local component; missing file; wrong byte count; wrong SHA-256; directory; parent traversal; absolute path; Windows separator; alternate data stream syntax; empty name; component symlink; symlink ancestor; exited installer parent. Report: `embedded-component-helper-tests.json`.
- Fourteen Python helper/source assertions pass. These check input integrity rejection, local-only acquisition logic, rejection of binary packages in the original source payload, all component pins checked before Python extraction/VC execution, exact component inventory, NSIS separation, compressed package handling and unchanged online files. Report: `independent-python-and-source-review.json`.
- `Bootstrap.ps1`, `GameSetup.nsi`, `build_installer.py`, `setup_worker.py` and `Uninstall-KTW.ps1` are byte-unchanged relative to commit `d87603fe71a7f390862bcfb0c0be1aafaf520774`.

## Reviewed behavior

Fresh offline installation resolves no download URL and has no component download/cache/fallback path. Every runtime, embedded Python and VC input has hard-coded bytes/SHA checks before use. A missing, corrupt or unexpected inventory fails closed. NSIS extracts these inputs into `$PLUGINSDIR\components`, separately from `$PLUGINSDIR\payload`; the existing worker copies only the verified payload tree into the installation. The large original 0 A.D. installer is extracted as data rather than executed.

Default installation directory and shortcuts are explicitly marked Offline QA. A selected nonempty destination is refused. The existing verified same-version registration retry preserves the installed game and saves; it checks launcher/engine and runs readiness validation, then restores registration without consuming embedded components. This is a deliberate existing-install branch and is not an integrity bypass for a fresh installation. Existing worker staging ownership checks and same-volume commit behavior remain unchanged. Uninstall preserves save/config paths and unknown or modified files.

The builder explicitly requires `--private-qa-only`, limits output to the host temporary directory, verifies original inputs and records that publication, licensing and native Windows execution are not cleared.

## Tool provenance

Pinned direct GitHub URLs returned HTTP 504. Both exact artifacts were retrieved through their official GitHub release-asset APIs, with release metadata and full-byte SHA-256 matching the existing project provenance. `toolchain-verification.json` records source API URLs, sizes and hashes. Tools remain under `/tmp/ktw-offline-independent-qa` and are not project/game payload.

## Limits and remaining acceptance

No blocking source defect was found within this review scope. This is not native Windows installation or gameplay acceptance, nor legal redistribution clearance. No UAC, COM, registry, prerequisite GUI, installer subprocess, engine, battle or save restart was executed. Windows-specific filesystem/junction semantics still require Windows testing. An offline acceptance run on clean Windows 10/11 x64 with networking disabled is required, including missing prerequisite, existing newer prerequisite, cancellation, insufficient disk, install path containing Cyrillic/spaces, reinstall and uninstall/save preservation. Original Microsoft prerequisite binary behavior, such as optional certificate or telemetry traffic, was not audited; the statement verified here concerns absence of installer-controlled component acquisition/fallback, not a claim of zero traffic from every upstream executable.

The parent agent performs full EXE archive/extraction verification separately. This independent review does not certify the rebuilt EXE or copy/re-publish it. No full candidate or third-party QA tools were uploaded or published.
