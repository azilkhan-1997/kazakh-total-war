# Third-party notices — KAZAKH TOTAL WAR technical prototype

Publisher of this prototype: SAYRAM PLANETA HOLDING. Original project development and integration: Хан Азильхан and team, 2026.

## Original code

The original campaign, simulation integration, GUI, terrain scripts, tests and tools in this package are offered under GPL-2.0-or-later. See `LICENSE`. The entire editable module source is included. The repository is not an assignment of third-party authorship to SAYRAM PLANETA HOLDING.

## 0 A.D. / Pyrogenesis

Copyright Wildfire Games and contributors. Engine version required: **0.28.0**. Source: https://play0ad.com/download/source/ ; development: https://gitea.wildfiregames.com/0ad/0ad . Engine/source terms are primarily GPL-2.0-or-later; the distribution contains components with additional licenses. Exact upstream directory rules are preserved in `LICENSES/0AD-LICENSE.md`.

The module and SPH installer do **not** redistribute the official engine executable, system DLLs, `public.zip` or `mod.zip`. Delivery 0.4 downloads the exact official Release 28 installer directly from Wildfire Games during setup, verifies SHA-256, statically extracts its files and verifies the 140-file manifest. It does not execute the upstream installer. The engine and base assets retain their original notices and authorship. Earlier developer helpers remain in source for compatibility; see `docs/INSTALL_EXE_RU.md` for the current installation flow and `docs/WINDOWS_DISTRIBUTION_NOTICES.md` for the unresolved full-runtime redistribution audit.

## Millennium A.D. artwork

Copyright/attribution: **The Council of Modders, Fallen Empire Studio, Scion Development**, and credited contributors. Source: https://github.com/0ADMods/millenniumad at commit `91636b405ee8d0088ec3a34fba6074dbd5c9d0f3`.

The admitted artwork subset and its adaptations are licensed **Creative Commons Attribution-ShareAlike 3.0 Unported**: https://creativecommons.org/licenses/by-sa/3.0/ ; legal code: https://creativecommons.org/licenses/by-sa/3.0/legalcode . Original artwork notice is preserved at `LICENSES/Millennium-Art.txt` and in the module art directory. File-by-file provenance and hashes: `docs/asset-manifest-millennium.json`.

Modifications: namespaced dependency paths, corrected normal/specular material slots, isolated animated bow skeleton, and five composite unit actors. These are provisional visual assets. Reuse/adaptation of this subset must retain attribution and applicable ShareAlike terms. The importer includes no Millennium audio.

## Medieval A.D.

Inspected at commit `84e5b2d8caad8c8830cb6a3ac5c6d427c0d0462c`: https://github.com/0ADMods/medievalad . No file from this project is redistributed. Concrete migration and per-file license ambiguities are recorded in the source audit. BigTiger and Stan remain the credited upstream artists; they are not represented as contributors to this prototype.

## Historical references and commercial references

Research links and original summarized data are in `research/`. Province control and unit statistics include explicit gameplay assumptions. No source text, art, game files, sound or code from Rome/Medieval/Total War has been copied. The client-supplied working title is not a representation of Creative Assembly or SEGA endorsement. Commercial naming/trademark clearance and Steam review remain outstanding.


## NSIS installer runtime (delivery 0.4)

NSIS 3.09-4 builds the installation wizard and uninstaller, including its runtime/plugin components. Copyright NSIS contributors and the individual authors listed in `LICENSES/NSIS-COPYRIGHT.txt`; that document preserves the component license and compression exception notices. Build inputs and official Ubuntu package hashes are pinned in `docs/installer/nsis-toolchain-lock.json`. NSIS project: https://nsis.sourceforge.io/ . The complete original installer source is in `installer/windows/`; the source archive includes the build script and exact dependency records.

## Temporary installation interpreter and Microsoft prerequisite

The installer downloads the official CPython 3.13.16 embeddable x64 ZIP directly from python.org to the user's computer. It is used privately for setup and removed from temporary execution storage afterward. Python's license is retained in the original downloaded package; a reference copy is at `docs/installer/CPYTHON_3_13_16_LICENSE.txt`. The Python package and its Microsoft DLLs are not embedded in the SPH EXE or copied into the game. If needed, the pinned official Microsoft VC installer is downloaded directly from Microsoft and its original license UI is shown. The game installer does not grant additional redistribution rights for those third-party binaries.
