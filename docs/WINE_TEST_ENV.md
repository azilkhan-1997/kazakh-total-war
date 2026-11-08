# Windows compatibility test environment — observed blocker

Checked 8 November 2026. This document concerns a Linux compatibility-layer test, **not native Windows 10/11 acceptance**. No game result is inferred from merely obtaining Wine or a Windows executable.

## Isolated setup actually performed

Host: Ubuntu 24.04 x86-64. No Wine, Wine64 or Xvfb executable was initially available on PATH. Ubuntu Noble packages were downloaded into an isolated scratch directory, verified against their SHA-256 values in the host's existing apt metadata, and unpacked with `dpkg-deb -x`. No system package installation or privileged configuration change was made.

Authoritative package reference: https://packages.ubuntu.com/noble/wine64 . Package bytes came from `https://archive.ubuntu.com/ubuntu/` or the existing metadata's pinned official snapshot `https://snapshot.ubuntu.com/ubuntu/20260828T000000Z/`. Where an older update had disappeared from the live archive, the matching snapshot was used. The metadata's hashes were checked; this task did not independently re-verify an Ubuntu Release signature.

| Component | Exact package version | SHA-256 of downloaded Debian package |
|---|---|---|
| wine64 | `9.0~repack-4build3` | `7f4f912b21917f28c281c99e3244ee801be2e20f0a23cd9f6d37acc97f5041ff` |
| libwine amd64 | `9.0~repack-4build3` | `eb421a3660bfdc090d70ce16b06aadfde1c2bce2593292023e520988f45d009e` |
| Xvfb | `2:21.1.12-1ubuntu1.6` | `9188c2ab6394dfe6aa53f782f6bfa22b7eb6febfe51a48e0e36af35cd2f64307` |

Other locally extracted dependencies/tools: fonts-wine, libz-mingw-w64, xserver-common, libxfont2, libfontenc1, xauth, x11-xkb-utils, xdotool, libxdo3. Their full metadata is retained in the scratch environment's `packages.json`. Wine, wineserver and Xvfb have no missing direct ELF dependencies when this local library directory is provided; that is a dependency inspection, not a successful graphical launch.

The Debian `wineserver` wrapper hard-codes `/usr/lib/wine/`. For scratch relocation only, its original file was retained as `wineserver.debian-original` and the local wrapper path replaced with a relative symlink to `wineserver64`. Neither the Wine executables nor the game engine were patched. This local test setup is not part of the Windows game distribution.

## Actual results

`wine64 --version` returned:

```text
wine-9.0 (Ubuntu 9.0~repack-4build3)
```

An isolated prefix and the trivial command `wine64 cmd /c echo KTW_WINE64_READY` were then attempted. The process exited 1 before running the Windows command:

```text
wineserver: socket: Operation not permitted
```

A minimal local socket probe confirmed the environment boundary:

```json
[
  {"family":"AF_UNIX","created":false,"errno":1,"error":"[Errno 1] Operation not permitted"},
  {"family":"AF_INET","created":true}
]
```

Wine requires local Unix-domain IPC sockets to start its server. The execution environment rejects that socket family. This is an observed execution-environment restriction, not evidence of a defect in KTW or Pyrogenesis. No attempt was made to patch Wine's IPC into another transport or bypass the restriction. Xvfb's ability to use TCP would not resolve Wine's separate IPC requirement.

## Reproduction on an ordinary Linux workstation

Use an ordinary installed Wine64 environment with working Unix-domain sockets and a dedicated test prefix. Wine testing remains separate from native Windows acceptance. If reproducing the isolated layout above, let `KTW_WINE_ROOT` denote the extracted package root:

```bash
export WINEPREFIX="$KTW_WINE_ROOT/prefix-test"
export WINEARCH=win64
export WINEDLLPATH="$KTW_WINE_ROOT/usr/lib/x86_64-linux-gnu/wine"
export WINELOADER="$KTW_WINE_ROOT/usr/lib/wine/wine64"
export WINESERVER="$KTW_WINE_ROOT/usr/lib/wine/wineserver64"
export LD_LIBRARY_PATH="$KTW_WINE_ROOT/usr/lib/x86_64-linux-gnu"
"$WINELOADER" cmd /c echo KTW_WINE64_READY
```

The original official 0 A.D. win64 installer has a 32-bit bootstrap. A classic Wine64-only installation is insufficient for that bootstrap even on an unrestricted workstation; it needs suitable Wine32 support or a compatible new-WoW64 Wine build. The actual 64-bit Pyrogenesis engine can be tested separately after extraction. Installing further 32-bit packages in this restricted environment would not fix the demonstrated IPC denial, so it was not pursued.

## Acceptance status

- Verified: package hashes, extraction, Wine version, direct dependency availability, exact IPC blocker.
- **Not verified:** execution of a Windows command, the official Windows installer, the KTW launcher or Pyrogenesis Windows game under Wine.
- **Not verified:** native Windows installation, menu, 3D battle, save/load, driver behavior or Steam acceptance.

Next valid execution target is a real Windows 10/11 test machine or a Windows runner. Static PE/import/package checks may still be performed here, but must remain labelled static checks.
