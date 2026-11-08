# Full offline packaging — private QA only

This is a separate packaging proof for the existing 0.4.0 delivery / 0.2.0 game
module. It does not establish a public release, standalone historical content
completion, native Windows acceptance, or redistribution clearance. The existing
online `GameSetup.nsi`, `Bootstrap.ps1`, builder and setup worker are unchanged.

The builder requires `--private-qa-only` and confines the complete executable to
the host temporary directory. Do not upload that executable, its extracted
components or the runtime to Library, a website, a release, or a Git repository.
Original packaging source and QA reports may be preserved separately.

## Inputs and environment

Build on Python 3.10+ with NSIS 3.09. The verified Linux toolchain packages are
pinned in `docs/installer/nsis-toolchain-lock.json`; extract those two `.deb`
packages into a private tool directory with `dpkg-deb -x`, and set `NSISDIR` to
its `usr/share/nsis`. No privileged package installation is required.

Obtain the original components from their official publishers for local QA.
The builder does not acquire them and rejects a missing or modified input.
The exact official acquisition URLs are recorded in the original online
`Bootstrap.ps1`; using that provenance does not confer redistribution rights.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `0ad-0.28.0-win64.exe` | 1,616,727,146 | `9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1` |
| `python-3.13.16-embed-amd64.zip` | 11,439,094 | `97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297` |
| `VC_redist.x64.exe` | 18,731,856 | `843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c` |
| Original `KazakhTotalWar.exe` launcher | 2,400,523 | `3c1906f7b2c384d2470c4ddcdf35b1da01697f61260fdb3033e44d9c3e12f969` |

## Build

Use absolute paths appropriate to the machine. For the current private QA host:

```bash
python3 installer/windows/build_offline_qa.py --private-qa-only \
  --launcher ../offline_source/restored/KAZAKH_TOTAL_WAR_Source/release/KazakhTotalWar.exe \
  --runtime-installer /tmp/ktw-official-download-4xfhv88f/0ad-0.28.0-win64.exe \
  --python-embed /tmp/ktw-offline-qa-components/python-3.13.16-embed-amd64.zip \
  --vc-redist /tmp/ktw-offline-qa-components/VC_redist.x64.exe \
  --makensis /tmp/ktw-offline-qa-toolchain/root/usr/bin/makensis \
  --nsis-dir /tmp/ktw-offline-qa-toolchain/root/usr/share/nsis \
  --output /tmp/ktw-offline-qa-result/KazakhTotalWar_Offline_QA_0.4.0.exe
```

The three packages are embedded with compression disabled in the separate
NSIS `components` directory. Own game source and the launcher occupy `payload`.
The upstream installers are not copied into the installed game's `source`
directory. This avoids embedding the already-expanded, greater-than-2-GiB
`public.zip` directly in NSIS. Compilation uses warnings as errors. The build
record lists source revision, dirty status, complete EXE size and SHA-256,
payload manifest digest, input package digests and explicit unresolved gates.

## Offline behavior

`OfflineBootstrap.ps1` has no download/cache/network acquisition function. On a
fresh install it validates the exact three-file inventory and every package's
full size and SHA-256 before running the embedded interpreter or prerequisite
installer. Invalid or absent data fails without network fallback. Temporary
Python extraction, the original Microsoft license UI, transactional staging,
runtime manifest validation, shortcuts and save-preserving uninstall reuse the
existing design. The original 0 A.D. installer is parsed as data by the worker,
not executed. A registration retry for an existing verified installation does
not reinstall components.

The default QA directory and shortcuts are labelled `Offline QA`. Plan for at
least 8 GiB free on the installation volume and 2 GiB for temporary extraction;
if these share a volume, reserve at least 10 GiB before setup starts. Compilation
and archive verification also need several GiB of temporary disk space.

## Portable verification

```bash
python3 installer/windows/test_offline_build.py
python3 installer/windows/verify_offline_qa.py \
  --installer /tmp/ktw-offline-qa-result/KazakhTotalWar_Offline_QA_0.4.0.exe \
  --sevenzip /tmp/ktw-offline-qa-toolchain/root/usr/lib/7zip/7z \
  --source "$PWD" \
  --build-report /tmp/ktw-offline-qa-result/offline-qa-build.json \
  --output /tmp/ktw-offline-qa-result/offline-qa-verification.json
```

The verifier extracts the complete NSIS package as data, checks every payload
file against the manifest and current source, checks the full bytes of all three
components, invokes the original worker's payload validation, and inspects the
offline entry point for network acquisition. It never executes a Windows
binary. These checks are packaging and source checks, not an offline Windows
installation or gameplay test. Portable tests cover component corruption,
missing files, size mismatch, symlinks and the private-build/output restrictions.

## Remaining acceptance gates

- Resolve the complete runtime's source, licence and redistribution obligations
  and the Microsoft prerequisite distribution basis before public packaging.
- Test on clean Windows 10/11 x64 with the network disconnected, both with and
  without the required VC runtime: install, prerequisite approval/cancellation,
  restart retry, launch, campaign/battle/save/load, uninstall and reinstall.
- Exercise insufficient disk space, interrupted extraction, invalid package,
  protected/nonempty paths, Cyrillic paths and existing saves on Windows.
- Confirm optional operating-system signature or prerequisite behavior does not
  prevent offline installation. Source absence of download code alone does not
  prove every external Windows behavior.
- Apply the project's native-game acceptance gates before claiming the complete
  game is ready for players. This packaging change adds no gameplay features.
