# R28 Windows engine build candidate

This workflow performs a real Release x64 compilation of Pyrogenesis and its
Collada converter. It is a step toward the requested offline installer, not that
installer and not a clean-Windows gameplay acceptance result.

## Run

Push these files with the existing
`docs/distribution-evidence/get-windows-libs-r28.bat` into the same game-source
repository, then run **Actions → R28 Windows engine (no lobby) → Run workflow**.
Pushing a change to the workflow or its build files also starts a run. No secrets,
paid runner, repository write token or publishing credentials are requested.

The equivalent local command requires a fresh working directory, PowerShell 7,
Windows x64, VS2022 C++ x64 tools plus SDK, and `svn.exe`, `tar.exe`, `curl.exe`:

```powershell
./build/windows_ci/Build-R28.ps1 -WorkRoot C:/ktw-build/r28-001 -OutputRoot C:/ktw-build/evidence-001
```

The script selects a real installed VS2022 instance using `vswhere`, enters its
x64 developer shell, and records the compiler, SDK and runner image versions.
It fails if required tools are absent. It does not install or accept a new
Microsoft product license.

## Actual R28 inputs and build configuration

| Input | Pin / checked behavior |
|---|---|
| Official source | [0ad-0.28.0-unix-build.tar.xz](https://releases.wildfiregames.com/0ad-0.28.0-unix-build.tar.xz), 164,975,536 bytes, SHA-256 `27e217755ef76a922fe58dbf593d96e54b6ed2375d23f548c35619aa6bd5a42a` |
| Source release revision | `a2cae4d69f816e9e9d7eecb6bf88f762afc0c90d` (v0.28.0) |
| Windows dependencies | Existing upstream fetch script, normalized-LF SHA-256 `fa0ada5f2d1363ffd18dadedd355d5b89f3b04dcd5cb08fee49c71686bb4e508`; SVN working-copy revision must equal 28275 |
| Premake definition | R28 `build/premake/premake5.lua`, SHA-256 `9b29ac24498e92d114da67f7565525c607d1f0bd9c29b164eb3188ac8f804f74` |
| Premake executable | Obtained from the pinned Windows dependency tree; actual executable hash recorded in evidence |
| Flags | `--without-lobby --without-atlas --without-tests`, `HOSTTYPE=amd64`, action `vs2022` |
| Compilation | Generated `pyrogenesis.sln`, `Release`, validated generated `x64` platform, `v143`, MSBuild target `pyrogenesis` (R28 declares a dependency on `Collada`) |
| Outputs | `binaries/system/pyrogenesis.exe` and `binaries/system/Collada.dll`; both must be newly created AMD64 PE files with no gloox imports |

The Unix source tar omits the Windows fetch and workspace batch scripts. The
audited fetch script is restored unchanged (LF normalization only) to its original
`libraries` location; Premake is called directly from `build/premake`, using
options verified in the exact release source. There is no invented replacement
dependency set. The existing fetch script downloads all upstream Windows libs,
including unused lobby/editor files; these are build inputs only. The generated
project and resulting imports must prove the engine excludes gloox.

`--without-tests` disables upstream test-project generation in this first engine
build, not game feature tests. `--without-atlas` leaves out the editor. Audio,
rendering, model conversion, scripting, gameplay and texture support remain in
the build configuration. A passing compile says nothing about current graphics
performance or campaign correctness on Windows.

## Evidence and artifacts

The evidence artifact is uploaded even after failure and contains a structured
status, exact source/build provenance, tool versions, dependency hashes and PE
versions, SVN metadata, existing dependency notices, copied-DLL dependency lists,
generated project files, and command/build logs. The final engine PE headers,
imports and hashes are recorded on success. No full process environment or build
binary log is deliberately captured.

Newly compiled `pyrogenesis.exe` and `Collada.dll` remain in `WorkRoot` on the
ephemeral runner. **No executable or DLL artifact is uploaded**, including the
new engine files, while corresponding-source and redistribution review remains
open. The evidence preserves their hashes, architecture and imports. No
third-party DLLs, Microsoft redistributables, upstream PDBs, game art, website
content or release installer are uploaded by this workflow.

The exact source is checksum-addressed in the provenance; all local build
instructions are versioned in this repository. The dependency tree contains
precompiled libraries, so this is not a claim of rebuilding every dependency from
source or of bit-for-bit reproduction. Runner image and toolchain drift are
recorded, not concealed. A checkout failure, source mismatch, compilation error,
missing Collada output, wrong architecture or remaining gloox import fails the
job instead of producing a successful delivery label.

## Microsoft and dependency source closure

GitHub documents standard public-repository hosted runners as free and supplies
Visual Studio for development/testing. The inspected `windows-2022` image lists
Visual Studio Enterprise 2022. Running this build is ordinary CI use of that
service; this project does not require buying a paid runner or Visual Studio.
This does **not** establish a separate publisher grant to redistribute Microsoft
runtime DLLs. Preinstallation and successful compilation are not that evidence.

- [GitHub-hosted runners](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
- [Runner image software inventory](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md)
- [Actions product terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
- [Microsoft redistribution guidance](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)

An eligible free Visual Studio Community license provides a separate potential
publisher route for OSI-licensed development and listed Distributable Code; its
actual acquisition/use and conditions must be documented. It does not relabel the
hosted Enterprise product as Community. Neither a trial entitlement nor the
public end-user VC runtime download should be claimed as a production
redistribution grant.

Before an all-in-one player package is released, complete the project's existing
`docs/WINDOWS_DISTRIBUTION_NOTICES.md` mappings: matching SpiderMonkey Windows
source/build/patches and third-party notices; OpenAL and libiconv LGPL source and
build closure; exact notices for linked Boost/fmt and runtime dependencies;
matching DbgHelp/DbgCore package REDIST designation if shipping them; and the
publisher's applicable VC runtime distribution basis. This no-lobby configuration
removes the unknown gloox1.1-svn dependency only if the recorded link/import
checks pass. It does not clear unrelated obligations.

After successful compile, the next technical acceptance is to assemble a reviewed
local runtime and data, test on clean Windows 10/11 with networking disabled,
exercise menu → campaign → player-controlled battle → result → save → full
restart/load, and only then build/publish the measured-size single installer.

## Validation status

The files were prepared against the downloaded exact R28 Premake definitions and
the existing pinned Windows dependency script. Local checks are described in
`validation.json` when present. A workflow file alone is not a Windows build:
the definitive status is the actual Actions run and its `build-provenance.json`.
