# Independent installer review — delivery 0.4.0

Reviewed on Linux on 2026-11-08. This report does not certify Windows installation
or gameplay. The deliverable is a real NSIS setup executable that downloads
official prerequisites automatically; it is not a complete offline installer.

## Verified source

| Component | SHA-256 | Result |
|---|---|---|
| `installer/windows/setup_worker.py` | `477a780da6980c6476250508a2a4ae98db5bf5e14c5dde419e2e4a176e0365e7` | 16 independent portable tests passed; actual 140-file runtime accepted |
| `installer/windows/Bootstrap.ps1` | `7b0750fafdad6c0ae5f3e353a075931ac81d9252208d6651f93ec6709fabe8ca` | Parser and PowerShell 5.1 syntax/API analysis passed |
| `installer/windows/Uninstall-KTW.ps1` | `fd40d8bd2c85c4fccc9844d617ffb513fe5ab16f01637c96ffd2d87f61991030` | Parser and PowerShell 5.1 syntax/API analysis passed |

PowerShell validation used the official Linux PowerShell 7.4.22 parser and
PSScriptAnalyzer 1.25.0 with the Windows PowerShell 5.1 / .NET Framework API
profile. The checker was verified against one compatible sample and one sample
using incompatible null-coalescing syntax and an unavailable .NET method. This
checks source compatibility; it does not execute Windows COM, UAC or registry APIs.

The 16 portable tests cover nonempty target preservation, destination symlinks,
linked ancestors, ownership-restricted staging cleanup, cleanup of child links,
destination races, atomic rename success, injected rename failure, same-size
tampering, missing/extra payload files, case-insensitive manifest collisions,
path/alternate-stream rejection and cancellation during hashing. The worker
also directly verified all 140 freshly extracted official runtime files,
4,217,782,703 bytes total, against the pinned manifest. No Windows guard was
disabled and no Windows executable was run for these tests.

## Packaging review

- Standard x86 NSIS stub explicitly requires Windows 10/11 x64 and invokes
  64-bit Windows PowerShell through `Sysnative`.
- Installation is per user. Only the original verified Microsoft prerequisite
  installer is elevated; its own license UI remains visible.
- Pinned publisher downloads are checked before use. Private embeddable Python
  is temporary and isolated; no user Python installation or PATH change is needed.
- The original 0 A.D. installer is not executed. Its pinned payload is statically
  extracted into the game's private runtime, preserving an independent 0 A.D.
  installation's registry and shortcuts.
- Staging and publication are on the same volume. Existing unowned nonempty
  targets are refused. Matching ownership is required before staging cleanup.
- Parent-process cancellation is checked during download, extraction polling,
  hashing and before publication. Actual NSIS cancellation interaction is untested.
- VC exit 3010/1641 defers game installation until reboot. Exit 1638 or its signed
  HRESULT is accepted only when the runtime post-check succeeds. Cancellation
  and other failures do not publish the game.
- Both target and download-cache volume space are checked. Cache use is locked
  against simultaneous setup downloads.
- Same-version registration retry verifies the launcher, engine and launcher
  preflight; it restores shortcuts without replacing game files or saves.
- Uninstall validates the entire deletion plan, deletes only unchanged owned
  files and matching shortcuts/registry entries, and preserves saves, config,
  unknown or modified files. Directory traversal skips reparse points.

Review found and the engineer fixed a registration retry defect: a previously
created per-install alternate shortcut was rejected on rerun. The final branch
allows that alternate only when its target matches this installation.

## Remaining limitations

- No native Windows host or identified existing project Windows CI was available.
  Read-only connected-repository searches for `kazakh` and `TotalWar` found no
  matching project repository. No runner was created or paid for.
- The earlier Wine attempt failed before Windows command execution because an
  AF_UNIX socket was prohibited. That restriction was not bypassed or retried.
- Real installation, UAC decisions, desktop/Start-menu shortcuts, Windows
  uninstallation, GPU rendering, offline campaign/battle/save loop and restart
  recovery remain **NOT TESTED**.
- After uninstall, preserved saves/config leave a nonempty folder. Automatic
  reinstall into that folder, in-place upgrade and profile migration are absent.
  A fresh empty installation and explicit saved-game transfer are required.
- There is no assertion that this is a signed production release, Steam-approved
  game, offline full installer or completed large-scale game specification.

Exact-artifact extraction/hash results are written to `setup-payload-verification.json`
after the final documentation freeze and rebuild. The reproducible checker is
`verify_setup_payload.py`; it performs no Windows execution.

## Evidence

- `worker-contract-tests.json` and `worker-contract-tests.log`
- `worker-runtime-integration.json`
- `powershell-installer-compatibility.json`
- `powershell-qa-tool-provenance.json`
- `analyzer-probe-results.json`
- `environment-capabilities.json`
- `SINGLE_EXE_ACCEPTANCE.md`

QA tool binaries under `vendor` are not game payload and should not be included
in the source or public game distribution.
