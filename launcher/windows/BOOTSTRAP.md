# Windows installation kit (engine downloaded during setup)

The installation kit is **not a fully installed offline game**. It contains the
native launcher, our game module, original source, audited extraction tool and
manifests. It obtains the official unmodified engine directly from Wildfire
Games during the user's setup. It does not redistribute that binary runtime.

First setup requires Windows 10/11 x64, 64-bit PowerShell 5.1 or newer,
**installed 64-bit CPython 3.11+ including `lzma`**, Internet access and at least
8 GiB free space. Python is only a setup tool; it is not needed to play after
installation. Obtain Python from <https://www.python.org/downloads/windows/>.
Interpreter behavior is documented at
<https://docs.python.org/3.11/using/windows.html>.

Extract the entire kit into a short, writable path such as
`C:\Users\YourName\Games\KazakhTotalWar`. Double-click `Setup-Windows.cmd`, or
run from its root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install-WindowsRuntime.ps1
```

If Python is not found automatically, select its existing executable explicitly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install-WindowsRuntime.ps1 -PythonExe 'C:\Path\To\python.exe'
```

The script looks for installed `py.exe -3` and then `python.exe`, skips Windows
Store execution aliases, and tests Windows/architecture/version and `lzma`
before any large download. During detection, the legacy launcher's install-on-demand
variables are cleared and the current Python install manager's documented
`PYTHON_MANAGER_AUTOMATIC_INSTALL` setting is disabled, then the user's settings
are restored. It does not install Python or run pip.

The required kit layout is:

| Path | Purpose |
| --- | --- |
| `KazakhTotalWar.exe` | Native launcher |
| `mods/kazakh_total_war/` | Complete game module |
| `tools/Install-WindowsRuntime.ps1` | This setup entry point |
| `tools/extract_r28_nsisbi.py` | Pinned original static extractor |
| `docs/windows-runtime-manifest.json` | Pinned 140-file official payload manifest |

Setup downloads the exact R28 installer from
<https://releases.wildfiregames.com/0ad-0.28.0-win64.exe>, verifies its
1,616,727,146-byte size and SHA-256
`9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1`,
then extracts it as data. **The official installer executable is never run.**
The extractor verifies the embedded CRCs; an independent validation pass checks
all 140 file sizes and hashes, both internal ZIP CRCs, AMD64 engine header and
Release 28/module metadata. It copies our module only into the staging runtime,
then publishes `runtime/` through a same-directory rename. No engine or gameplay
execution is claimed by these validation steps.

If Microsoft `VCRUNTIME140_1.dll` is absent from the Windows system directory,
setup also downloads Microsoft Visual C++ x64 Redistributable 14.51.36247 to
`prerequisites/VC_redist.x64.exe`. The URL is a pinned official Microsoft CDN
location recorded in the script; size is 18,731,856 bytes and SHA-256 is
`843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`.
It is **never executed automatically**. Run it manually before starting the
game if instructed; Microsoft's installer may request administrator approval.
The setup script and game launcher do not request elevation.

After setup, start `KazakhTotalWar.exe`. Game configuration, cache and saves
remain in this installation's portable runtime, as described in `README.md`.
The cached original installer in `downloads/` can be removed manually after
successful setup if disk space is needed. It is not used during play.

For a machine without Internet, first obtain the exact official files on
another machine and pass their local paths. The same hashes are enforced:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install-WindowsRuntime.ps1 -PythonExe 'C:\Python313\python.exe' -InstallerPath 'D:\Installers\0ad-0.28.0-win64.exe' -VcRedistPath 'D:\Installers\VC_redist.x64.exe'
```

No checksum bypass exists. Existing cached files with wrong hashes cause an
error and are preserved for inspection. Incomplete downloads use separate
temporary filenames. Failed extraction/validation does not publish `runtime/`;
only that invocation's private staging folder is removed. A valid cached
installer can be reused by the next attempt. If `runtime/` already exists,
setup refuses to overwrite it or its saves; launch it or use a separate kit
directory. This is a first-install tool, not an in-place updater.

Success leaves `runtime/KTW_SETUP_VALIDATION.json` and
`runtime/OFFICIAL_RUNTIME_PROVENANCE.json`. These record content validation,
not successful native gameplay. The PowerShell wrapper has **not been executed
on native Windows in this development environment**. The embedded validator
passed against the real 140-file R28 payload and current game module on the
Linux host. It also rejected a corrupted payload file and a duplicate/missing
extraction-manifest entry. This does not establish PowerShell 5.1 or Windows
acceptance. Full first-setup and campaign/battle tests on a clean
Windows 10/11 machine remain required.
