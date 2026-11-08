# One-EXE installation: source and redistribution audit

SAYRAM PLANETA HOLDING • KAZAKH TOTAL WAR • 2026-11-08

## Decision

A single native installer EXE can automate installation without requiring the player to install Python or unpack a ZIP. The currently supported distribution route is an **online installer**: it carries the original SPH module/launcher/setup code and fetches pinned, unmodified component packages from their official publishers on the user's computer. After installation, gameplay has no Python or online-service dependency. Actual Windows acceptance is a separate test and has not been inferred from packaging.

An EXE containing the entire upstream runtime is **not cleared for public redistribution by this audit**. Keeping the official installer unmodified inside a wrapper does not, by itself, prove that this publisher has satisfied every bundled component's source, notice and proprietary-license conditions.

## Full offline bundle: unresolved items

| Item | Current evidence | Decision |
|---|---|---|
| 0 A.D. itself | Wildfire Games permits redistribution under the applicable GPL/art licenses. Its R28 source page publishes the Unix code/data tarballs. | Preserve engine notices, editable SPH source and art attribution. This general permission is not a complete per-library source map. |
| gloox | Actual prior binary audit identifies `1.1-svn`. The current official download page still supplies stable `1.0.28`; the roadmap calls 1.1 development trunk. | No exact SVN revision/build correspondence was found. Do not present 1.0.28 or today's arbitrary trunk as matching source. |
| Microsoft runtime/debug components | Current Microsoft developer documentation limits redistribution to licensed Visual Studio users under applicable terms. The project does not establish such entitlement. | A public-download link, verified signature, or presence in another publisher's package is not a new redistribution grant for SPH. Direct publisher downloads on the end-user PC avoid republishing those files. |
| Windows execution | Existing native game evidence is Linux; previous Wine startup was blocked before Windows commands ran. | Do not mark Windows install/play/Steam accepted from archive hashes or PE headers. |

The original detailed component audit remains authoritative at `docs/WINDOWS_DISTRIBUTION_NOTICES.md` in the game source. This follow-up does not remove its open Windows dependency items.

## CPython 3.13.16: verified exact package

- URL: https://www.python.org/ftp/python/3.13.16/python-3.13.16-embed-amd64.zip
- Size: **11,439,094 bytes**.
- SHA-256: **97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297**.
- The local digest matches the checksum published on the official release page. ZIP CRC passes for every file. No Windows execution or signature verification is claimed here.
- Actual contents include `vcruntime140.dll` **and** `vcruntime140_1.dll`. Do not assume every file is covered by PSF-2.0 merely because the archive is a Python distribution.
- Complete `LICENSE.txt` is retained as `CPYTHON_3_13_16_LICENSE.txt`; the official SPDX document and a per-file hash inventory are stored alongside this report.

Official Python documentation describes the embeddable environment as a private application component. PSF licensing permits Python redistribution with retained license/copyright and a changes summary for derivatives; incorporated components have their own terms. The chosen implementation downloads the unmodified archive directly during setup, uses it privately for extraction, and removes its temporary environment afterward. No Python/MS binary is placed in the SPH distribution. The player does not install Python or run Python commands.

Do not copy Microsoft DLLs out of the embedded Python archive into the game as an improvised runtime redistribution. The engine prerequisite is handled separately by the original Microsoft installer on the user's machine, preserving its license/UAC interaction. Microsoft's documentation describes bootstrapper execution and the `/install`, `/passive`, and `/norestart` options; calling those switches does not itself establish redistribution rights.

## Product instructions

The site can accurately say: download one EXE, run installation, wait for automatic downloads, launch the game from its shortcut. Explain that internet is required during the first installation (approximately **1.65 GB** of component downloads when all prerequisites are missing) and is not intended to be required for subsequent gameplay. Keep native-Windows test status explicit until it is measured. Do not call this installer fully offline or say every game resource is embedded in the downloaded EXE.

## Primary sources read

1. https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170
2. https://learn.microsoft.com/en-us/cpp/windows/choosing-a-deployment-method?view=msvc-170
3. https://learn.microsoft.com/en-us/visualstudio/releases/2026/redistribution
4. https://play0ad.com/game-info/project-overview/
5. https://play0ad.com/download/source/
6. https://camaya.net/gloox/download/
7. https://camaya.net/gloox/roadmap/
8. https://www.python.org/downloads/release/python-31316/
9. https://www.python.org/ftp/python/3.13.16/
10. https://docs.python.org/3.13/using/windows.html#the-embeddable-package
11. https://docs.python.org/3.13/license.html

Public current pages did not close the precise gloox source revision. The Gitea domain was blocked by the browsing tool's robots policy; it was not accessed through an alternative method. A primary SVN URL was inaccessible through the browsing tool. No matching-source claim is made from those unavailable resources.
