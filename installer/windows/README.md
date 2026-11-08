# Single EXE installation — delivery 0.4.0

This continues the existing KAZAKH TOTAL WAR project, with unchanged gameplay
module 0.2.0 and save schema 2. The distribution is a native NSIS installation
wizard for Windows 10/11 x64. Its standard x86 NSIS bootstrap starts 64-bit
Windows PowerShell through `Sysnative`; the game and private setup interpreter
are AMD64. It is an **online installer**, not an offline full-runtime bundle.

The player downloads one `KazakhTotalWar_Setup_0.4.0.exe`, chooses a new/empty
writable installation folder, and follows the wizard. No installed Python,
manual ZIP extraction or manual scripts are required. The first installation
needs internet and downloads at most 1,646,898,096 bytes from the official
publishers (engine, isolated setup tools and optional Microsoft prerequisite).
Offline gameplay is the intended post-installation mode; native Windows
installation/gameplay acceptance has not yet been performed.

## Build

From the game source root, using the separately acquired pinned NSIS 3.09-4
compiler and the existing reproducibly built AMD64 launcher:

```bash
python3 tools/build_windows_launcher.py \
  --toolchain .build/launcher-toolchain --fetch-toolchain \
  --output dist/windows/KazakhTotalWar.exe

python3 installer/windows/build_installer.py \
  --launcher dist/windows/KazakhTotalWar.exe \
  --makensis /absolute/nsis-root/usr/bin/makensis \
  --nsis-dir /absolute/nsis-root/usr/share/nsis \
  --output dist/KazakhTotalWar_Setup_0.4.0.exe
```

The launcher toolchain lock is `launcher/windows/toolchain-lock.json`.
NSIS acquisition records are in `docs/installer/`. Build prerequisites are
Python 3 on the build host and the NSIS Linux compiler; they are not end-user
requirements. `build_installer.py --help` lists all options, including an
alternate `--project` source tree. No Windows runtime, Microsoft redistributable
or private Python binary is embedded in the EXE. The EXE carries the original
launcher, editable game/source files, notices and installation scripts.

The builder creates an isolated snapshot, converts the PowerShell payload to
UTF-8 with BOM for Windows PowerShell 5.1, hashes each included file, invokes
NSIS with warnings treated as errors, verifies the PE header, fsyncs the result,
and atomically publishes it. It writes `installer-build.json`,
`installer-payload-manifest.json` and `installer-build.log` beside the EXE.
File timestamps are normalized with `SOURCE_DATE_EPOCH` (default: 2026-11-08
UTC). The Git source revision and dirty state are recorded in the payload
manifest and build report. Changing source or documentation requires a fresh
build and changes the installer digest.
Temporary absolute paths in the build log do not denote runtime dependencies.

## Installation flow

1. NSIS displays the welcome/license/destination pages and extracts its own
   verified package into its private temporary directory. It runs as the user.
2. `Bootstrap.ps1` checks Windows x64, destination ownership, free disk space,
   a product-owned cache, exclusive cache access and the pinned payload manifest.
3. It obtains the pinned official CPython embeddable ZIP into an isolated
   temporary directory. It never installs Python globally, changes PATH, uses
   the user's interpreter or installs Python packages.
4. If the minimum Microsoft VC runtime is missing, it obtains the pinned
   original Microsoft installer and opens its visible license UI with its own
   normal elevation request. Cancellation, failure or a required restart stop
   game installation. A newer-runtime result is accepted only after the DLL
   version check passes.
5. It downloads the pinned official 0 A.D. Release 28 installer as data. That
   installer is **never executed**, so the user's global 0 A.D. installation,
   registry entries and shortcuts are untouched.
6. `setup_worker.py` runs the existing unchanged NSISBI extractor, independently
   verifies all 140 runtime files against the pinned manifest, checks both data
   ZIPs, installs the unchanged module and runs the launcher's `--check` preflight.
   Preflight does not run the game and is not a native gameplay acceptance test.
7. A sibling staging directory is atomically renamed into the selected target
   only after verification. Product ownership and exact owned-file hashes are
   recorded in `KTW_INSTALL.json`. Start-menu/desktop links and a unique HKCU
   uninstall entry are created afterward. Unknown same-named shortcuts are
   preserved, with a per-install alternate name used when necessary.
8. The wizard offers to launch the game. The temporary private interpreter is
   removed. Verified downloads remain in the user-owned cache for retries.

The default target is inside the current user's LOCALAPPDATA, because the
existing launcher's `-writableRoot` profile needs a writable runtime directory.
Reserve 8 GiB on the target drive, plus 2 GiB on the user-profile drive when
installing to another drive. No administrator permission is requested for the
game install; only the separate Microsoft prerequisite may need elevation.

## Existing installations, interruption and uninstall

- A matching owned 0.4.0 installation can retry shortcut/registry registration
  after the launcher and engine hashes and `--check` preflight pass. This does
  not overwrite gameplay files or save data.
- Other nonempty destinations are refused. This release does not implement an
  in-place version upgrade or automated migration from an earlier profile.
- Closing the installer is detected during downloads, extraction, hashing and
  before publication. Only marked staging directories belonging to that attempt
  are cleaned. A hard crash may leave an identifiable staging folder or cached
  download; it does not justify deleting arbitrary neighboring directories.
- `Uninstall.exe` calls the native PowerShell uninstall script. The entire
  deletion plan is validated first. Only unchanged, manifest-owned files are
  deleted. Saves, settings, modified/unknown files and directory junctions are
  preserved. Shortcuts are removed only when their target belongs to this install;
  only its own HKCU uninstall entry is removed.
- Because saves/settings remain, uninstalling can leave a nonempty destination.
  A later fresh installation must use another empty folder. Manually deleting
  that preserved folder deletes the user's remaining data; the installer never
  does so automatically.
- Microsoft VC runtime is shared software and is never uninstalled by this game.

## Source and licensing

Original setup code is GPL-2.0-or-later, like the project. Include the complete
source, build scripts, `LICENSE`, existing third-party notices and
`LICENSES/NSIS-COPYRIGHT.txt` with any redistribution. Gameplay art retains its
existing separate attribution/share-alike terms.

Official Python and Microsoft binaries are downloaded directly to the end-user
from their publishers; they are not repackaged into this EXE. The temporary
Python package keeps its original license/notices and runtime DLLs isolated.
Its DLLs are not copied into the game. The original Microsoft license UI is
retained. This online delivery does not claim closure of the separate full
upstream-runtime redistribution audit; see `docs/WINDOWS_DISTRIBUTION_NOTICES.md`.

## Verified scope and remaining acceptance

Build-host checks include source/payload hashes, NSIS compilation, PE format,
PowerShell syntax/API compatibility analysis, portable transaction/path/tamper
contracts and the genuine 140-file runtime manifest. Exact reports are in
`docs/installer/` and the build output. Cross-platform checks do not execute
Windows PowerShell, COM, UAC, NSIS pages or the actual Windows game.

Still required on clean Windows 10/11 x64: setup, Microsoft prerequisite
cancel/reboot, Unicode paths, genuine installation cancellation, shortcut
registration recovery, offline menu/campaign/battle/save/restart, and uninstall
preserving real user data. The EXE is unsigned. No native Windows or Steam
acceptance is implied by a successful compilation or file-integrity result.

## Source distribution

After committing the frozen source and verifying the final EXE, run:

```bash
python3 tools/package_exe_release.py \
  --launcher dist/windows/KazakhTotalWar.exe \
  --installer dist/KazakhTotalWar_Setup_0.4.0.exe \
  --report dist/installer-build.json \
  --report dist/installer-build.log \
  --report /path/to/setup-payload-verification.json \
  --baseline-evidence /path/to/verified-v0.3/evidence \
  --baseline-archive /path/to/KAZAKH_TOTAL_WAR_Pyrogenesis_Prototype_v0.3.zip
```

The full source kit includes Git history, original evidence including four native
saves, both own EXEs and all preferred source. The compact web source omits only
historical evidence images/video, the separately downloadable installer EXE and
the Git bundle. All game art/source, licenses, build tools and native save
fixtures remain. `--baseline-archive` verifies the original evidence against the
pinned authentic 0.3 archive. Packaging creates atomic CRC/hash-verified ZIPs,
per-file inventories and `SOURCE_RELEASE_SHA256.json`. It does not download or
redistribute the engine or Microsoft/Python runtime packages.
