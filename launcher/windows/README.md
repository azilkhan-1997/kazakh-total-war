# Windows launcher 0.3.0

This directory contains the original GPL-2.0-or-later C++ source for the small
native Windows launcher. It starts the separately bundled official Pyrogenesis
Release 28 engine. The launcher itself is **not the game engine**. Gameplay
module 0.2.0 remains the existing campaign/battle implementation.

For the v0.3 installation kit, first run `Setup-Windows.cmd`; the runtime is
downloaded and verified on the user's computer. Initial setup requires installed
64-bit CPython 3.11+. See `BOOTSTRAP.md` for exact setup requirements. Python
is not required for subsequent game launches.

## Portable bundle contract

Place `KazakhTotalWar.exe` at the top of the extracted game directory. Its
required runtime files are:

| Relative location | Contents |
| --- | --- |
| `runtime/binaries/system/pyrogenesis.exe` | Authentic official R28 AMD64 executable and all its accompanying DLLs |
| `runtime/binaries/data/mods/mod/mod.zip` | Official engine base mod |
| `runtime/binaries/data/mods/public/public.zip` | Official game assets and scripts |
| `runtime/binaries/data/mods/public/mod.json` | Official metadata: name `0ad`, version `0.28.0` |
| `runtime/binaries/data/mods/kazakh_total_war/` | This project's complete module, with `mod.json` |
| `prerequisites/VC_redist.x64.exe` | Official Microsoft Visual C++ prerequisite installer, if supplied with the release |

The executable uses its own location, not the caller's current directory, and
starts this exact command with the working directory set to `runtime/binaries/system`:

```text
"<absolute game directory>\runtime\binaries\system\pyrogenesis.exe" -writableRoot -mod=public -mod=kazakh_total_war
```

**Verified against actual R28 source:**
`source/ps/GameSetup/Paths.cpp`, `Paths::Paths`, `Paths::Root`, and
`Paths::RootData` in the official `0ad-0.28.0-unix-build.tar.xz` source archive
linked at <https://play0ad.com/download/source/>. `-writableRoot` is a flag
without a value. It changes engine directories to the following portable
locations and avoids the ordinary installed 0 A.D. profile:

| Data | Relative location |
| --- | --- |
| Config | `runtime/binaries/data/config/` |
| Saves and game data | `runtime/binaries/data/saves/` and the other engine user-data subdirectories |
| Cache | `runtime/binaries/data/cache/` |
| Engine logs | `runtime/binaries/logs/` |

Extract the entire game into a writable directory. The launcher checks writes
before starting. It never deletes saves, imports another 0 A.D. installation,
requires elevation, downloads files, or runs a prerequisite installer itself.
The supplied Microsoft prerequisite may require administrator approval when
the user runs it. Preserve the portable save/config folders when upgrading.
Do not launch `pyrogenesis.exe` directly if profile isolation is required.

The official R28 engine imports `VCRUNTIME140_1.dll` but omits that DLL from its
installer's application files. The launcher checks for it in the engine folder
or the Windows system directory. If absent, it reports code 17 and the bundled
Microsoft installer location. This existence check does not prove that every
DLL dependency has the correct version or will load; real engine execution
remains a separate acceptance test.

## Reproducible build (Ubuntu 24.04 x86_64)

Prerequisites: Python 3, host `g++`, `dpkg-deb`, glibc 2.39-compatible Linux.
No Python packages are needed. The toolchain is downloaded only when explicitly
requested and extracted locally without a system install:

```bash
python3 tools/build_windows_launcher.py \
  --toolchain .build/launcher-toolchain --fetch-toolchain \
  --output dist/windows/KazakhTotalWar.exe
```

Repeat builds reuse the verified extracted toolchain:

```bash
python3 tools/build_windows_launcher.py \
  --toolchain .build/launcher-toolchain \
  --output dist/windows/KazakhTotalWar.exe
```

The exact seven Ubuntu package URLs, versions, sizes and SHA-256 hashes are
committed in `toolchain-lock.json`. Compiler: GCC MinGW-w64 13.2.0-6ubuntu1+26.1,
Win32 threading variant; headers: mingw-w64 11.0.1-3build1; binutils:
2.41.90.20240122-1ubuntu1+11.4. Every package is size/hash checked before
extraction. The compiler is linked statically; the resulting launcher imports
only Windows system DLLs (`KERNEL32`, `msvcrt`, `SHELL32`, `USER32`). The official
engine has its own separate dependencies.

The build script compiles and runs portable logic tests, embeds version and
`asInvoker`/long-path-aware manifest resources, builds a PE32+ AMD64 GUI
application, checks PE headers and imported DLLs, and emits
`KazakhTotalWar.build.json` with source/output hashes and tool versions. The
linker timestamp is zero for repeatable bytes. The executable is unsigned.
Signing and Steam submission are separate release work.

## Tests and status

Host tests:

```bash
python3 tools/build_windows_launcher.py --tests-only
```

They cover Windows argument quoting (spaces, quotes, trailing slashes, Kazakh
characters), engine command flags, strict root-level metadata validation,
wrong engine versions, wrong/extra module dependencies, duplicate JSON keys,
Unicode escapes, malformed/truncated/deep/oversized JSON. They do not execute
WinAPI calls or prove that the actual engine runs.

Native Windows negative-path tests (PowerShell, no admin required):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File launcher\windows\Test-Launcher.ps1 -Launcher dist\windows\KazakhTotalWar.exe
```

The seven cases use disposable test-only fixtures in a directory containing
spaces and Kazakh characters, with an unrelated current working directory.
They check missing runtime, unsupported arguments, old engine metadata,
incompatible module metadata, truncated/duplicate metadata and invalid PE.
The fixture PE is only a test sentinel; it is never executed as an engine.

Validate a complete bundle without opening the game (a GUI process must be
waited for explicitly):

```powershell
$p = Start-Process -FilePath '.\KazakhTotalWar.exe' -ArgumentList '--check' -Wait -PassThru -NoNewWindow
$p.ExitCode
```

`--check` emits a UTF-8 JSON diagnostic to redirected stdout, checks files,
metadata, AMD64 PE header, the known VC dependency and writable directories;
it does **not** start the engine, test graphics, or validate every archive byte.

| Exit code | Meaning |
| --- | --- |
| 0 | Check passed or game exited normally |
| 2 | Unsupported launcher arguments |
| 10 | Missing/empty bundle file or inaccessible launcher path |
| 11 | Invalid metadata or non-AMD64 engine PE |
| 12 | Portable profile cannot be written |
| 13 | Windows could not create the engine process |
| 14 | Same portable profile is already running, or mutex failed |
| 15 | Waiting for the engine / retrieving its status failed |
| 16 | Engine exited with a nonzero status; inspect engine logs |
| 17 | Missing Microsoft Visual C++ runtime prerequisite |
| 99 | Unexpected launcher exception |

Observed in this development environment: host tests passed; the real AMD64
launcher cross-compiled; PE headers/imports validated; two separate builds
produced identical bytes. **Native Windows tests and engine startup have not
been executed here.** Wine initialization fails in this host's IPC environment
(`wineserver` cannot bind its socket: `Operation not permitted`). Native Windows
10/11 validation, full game launch and campaign/battle acceptance remain open.
Unicode/space handling is implemented with wide Windows APIs. Long-path-aware
launcher manifests and extended file API paths do not establish that the
unmodified engine or all its DLLs support long paths; test complete games in a
short user-writable folder first.
