# Offline runtime resolution — exact R28 evidence

Checked 2026-11-08. Scope: read-only inspection and isolated research; no production source/site changes, no engine rebuild, no Microsoft license accepted, and no native Windows execution.

## Decision

There is a concrete source-based route to a full offline installer. The existing official EXE cannot yet be relabelled and republished as a cleared package. The most predictable route is an R28 Windows rebuild with `--without-lobby`, an eligible free Visual Studio Community development environment, explicit dependency/source notices, and clean offline Windows acceptance testing. Paid Visual Studio is not intrinsically required for this OSI-licensed project.

This is a feasible engineering route, not a completed build or legal clearance. No missing runtime permission has been guessed; no source snapshot has been labelled corresponding merely because its version string is similar.

## Verified artifacts

| Artifact | Evidence |
|---|---|
| Official R28 Windows installer | `/tmp/ktw-official-download-4xfhv88f/0ad-0.28.0-win64.exe`; 1,616,727,146 bytes; SHA-256 `9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1` |
| Extracted original runtime | `/tmp/ktw-runtime-qa-9oi_z6u5`; 140 files / 4,217,782,703 bytes in previous manifest verification |
| Actual engine EXE | SHA-256 `11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f` |
| Fresh official R28 source | `0ad-0.28.0-unix-build.tar.xz`; 164,975,536 bytes; SHA-256 `27e217755ef76a922fe58dbf593d96e54b6ed2375d23f548c35619aa6bd5a42a` |
| Machine-readable proof | `exact-r28-rebuild-proof.json` |

Source archive: https://releases.wildfiregames.com/0ad-0.28.0-unix-build.tar.xz

## Gloox: actual resolution path

The shipped `gloox-1.0.dll` identifies itself as **1.1-svn**, GPLv3, and was built 2025-07-22. Official engine PE imports include `gloox-1.0.dll`; deleting that DLL from the existing release is not a valid fix. The shipped PDB contains build paths but no recovered source-server or SVN-revision mapping in the inspected strings.

The author's official download page offers stable 1.0.28 and identifies 1.1 as unreleased SVN trunk. Wildfire's public dependency directory offers 1.0.28, not a demonstrated corresponding 1.1 snapshot. Neither proves the exact source used for the shipped DLL. The SVN hostname could not be resolved in this environment; this is an observed access limitation, not a conclusion that no source exists.

The **actual R28 archive**, not just current master, provides a direct alternative:

- `build/premake/premake5.lua:59`: `--without-lobby` is declared.
- Line 278 block: sets `CONFIG2_LOBBY=0`.
- Lines 772–806: excludes gloox from the link dependencies and keeps lobby stub interfaces.
- The inspected file SHA-256 is `9b29ac24498e92d114da67f7565525c607d1f0bd9c29b164eb3188ac8f804f74`.

Rebuilding that configuration removes the lobby dependency while preserving the intended single-player offline role. It changes engine bytes and requires a new runtime manifest, appropriate source release, and actual gameplay tests. It is not achieved by an installer checkbox or deleting the DLL.

Primary sources: https://camaya.net/gloox/download/ ; https://camaya.net/gloox/roadmap/ ; https://releases.wildfiregames.com/libs/

## Microsoft: a free route exists

`ms-rights/RESOLUTION.md` and `ms-rights/provenance.json` preserve the actual downloaded Microsoft agreements, exact hashes and findings. Community 2026 expressly permits organizational development/testing of OSI-licensed applications and grants distribution of listed object code subject to conditions. The REDIST list includes Community. An eligible real Community acquisition/use record has not been observed for the publisher in this workspace; no purchase is automatically required.

Build Tools alone is a weaker basis: the actual agreement's no-license exception covers compiling third-party OSS dependencies and has no Distributable Code clause. The separate public VC runtime download does not itself grant developer redistribution rights. Do not infer entitlement simply from an available binary or hosted compiler.

Use the unmodified release VC runtime package covered by the developer's applicable grant, preserve its terms, and verify offline prerequisite installation. The current engine actually imports `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` and `MSVCP140.dll`, so removing runtime files without replacing/rebuilding the dependency chain is not valid.

Primary sources:

- https://visualstudio.microsoft.com/wp-content/uploads/2025/10/Visual_Studio_2026-License-Community_ENU.docx
- https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution
- https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170

## DbgHelp / DbgCore require a separate decision

The original `license_dbghelp.txt` does contain a distribution grant, conditional on files being listed in the applicable REDIST.TXT and on its distribution requirements. This is not proof that every Microsoft debug binary is prohibited, and these DLL names must not be confused with Visual Studio `debug_nonredist` runtimes. The matching package/list provenance for the shipped copies remains unestablished here.

Microsoft's DbgHelp documentation distinguishes Debugging Tools package redistribution from the Windows system copy, which is not redistributable. Obtain matching permitted SDK/Debugging Tools package provenance and terms, or validate a configuration using OS-supplied functionality without shipping those DLLs. Do not copy DLLs from Windows system directories into the installer.

The actual `mozjs128-release.dll` imports seven DbgHelp functions: `EnumerateLoadedModules64`, `SymFromAddr`, `SymGetLineFromAddr64`, `SymGetModuleInfo64`, `SymInitialize`, `SymLoadModule64`, `SymSetOptions`. R28 also dynamically uses DbgHelp for diagnostics. Therefore omission needs real Windows loader/startup/crash-report testing; this research does not certify it.

Primary sources: https://learn.microsoft.com/en-us/windows/win32/debug/dbghelp-versions ; https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/debugger-download-tools

## Environment and remaining close-out

The R28 source selects v143 for the VS2022 action and expects Windows dependency libraries. This Linux environment has inspection tooling and a launcher cross-compiler, but does not establish a working Windows/MSVC engine build. The Unix source archive omits the Windows workspace batch script and prebuilt Windows libraries. An existing MinGW-built launcher is not proof that the engine plus MSVC C++ and SpiderMonkey dependencies can be relinked with it.

A practical close-out sequence is:

1. Use a real eligible stable Community Windows build environment and retain its licensing/version evidence.
2. Obtain the exact R28 source and compatible Windows dependencies with their source/build/license mapping; generate a release workspace with `--without-lobby`.
3. Build and inspect the resulting PE imports to confirm gloox is absent. Bundle only required permitted runtime components.
4. Resolve the debug DLL package/list provenance or test and document an OS-runtime alternative.
5. Complete remaining LGPL/source and per-file notice mappings already listed in the project's distribution audit; this focused research has not cleared them.
6. Build a single offline installer from a local payload, run clean Windows 10/11 installation with network disabled, launch campaign, battle and save/reload, then record real bytes/hash.
7. Publish that tested installer and its corresponding source/notices. The button size must be measured, not padded to exactly 1.65 GB.

No public upload or readiness claim is authorized by this report itself. The user has requested publication, but the technical and license facts must first support the package being published.
