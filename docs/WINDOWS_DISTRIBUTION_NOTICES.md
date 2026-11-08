# Windows distribution audit — KAZAKH TOTAL WAR

Publisher: SAYRAM PLANETA HOLDING. Audit of the Release 28 runtime and the existing `kazakh_total_war` module; this is a distribution record, not a legal opinion or Steam acceptance certificate. The module's existing `THIRD_PARTY_NOTICES.md` remains valid for the module-only source kit. Its statement that no runtime is redistributed does **not** describe a future standalone runtime bundle.

## Verified provenance

| Item | Exact evidence | Status |
|---|---|---|
| Official Windows runtime installer | `https://releases.wildfiregames.com/0ad-0.28.0-win64.exe`; 1,616,727,146 bytes; SHA-256 `9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1` | Download verified; all 140 extracted files passed embedded NSIS CRC; both mod archives passed ZIP CRC |
| Official engine source archive | `https://releases.wildfiregames.com/0ad-0.28.0-unix-build.tar.xz`; 164,975,536 bytes; SHA-256 `27e217755ef76a922fe58dbf593d96e54b6ed2375d23f548c35619aa6bd5a42a` | Download verified locally; include unchanged in corresponding source delivery |
| Official source revision | Gitea API tag `v0.28.0` → `a2cae4d69f816e9e9d7eecb6bf88f762afc0c90d` | Official tags API inspected |
| Windows dependency revision | That commit's `libraries/get-windows-libs.bat` pins SVN `28275`, repository `windows-libs-amd64` | File and immutable revision listing inspected |
| Engine executable | `binaries/system/pyrogenesis.exe`; 5,857,280 bytes; SHA-256 `11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f` | PE32+ AMD64; resource version 0.28.0; Wildfire Games copyright preserved |
| Original game/module/launcher source | Project source kit and Git bundle; exact release revision belongs in the generated release manifest | GPL-2.0-or-later; keep editable source and build scripts |
| Millennium art | Commit `91636b405ee8d0088ec3a34fba6074dbd5c9d0f3`; `asset-manifest-millennium.json` and original module notices | Selected subset only; CC BY-SA 3.0 attribution and modifications already recorded |
| Medieval A.D. | No files admitted to the game | No Medieval runtime or art redistribution claimed |

Release provenance does not mean this project rebuilt the engine or reproduced its Windows binaries. The engine is an unchanged upstream binary, started by a separate original launcher. Preserve its original executable metadata, copyright notices, credits, author lists and upstream service terms. The original mod title and publisher do not imply endorsement by Wildfire Games, Microsoft or Total War's owners.

## Actual runtime components

The following inventory comes from extracted `binaries/system` files, inspected PE resources/imports, the actual R28 `LICENSE.md` and `libraries/LICENSE.txt`, and pinned dependency listings. An upstream umbrella label is not a substitute for a missing component license. Exact final file hashes belong in the runtime packaging manifest.

| Actual files | Component / license evidence | Corresponding source and notice status |
|---|---|---|
| `pyrogenesis.exe`, `Collada.dll`, `ActorEditor.exe`, `AtlasUI.dll` | Pyrogenesis/Atlas; source primarily GPL-2.0-or-later, directory-specific MIT and other exceptions | R28 engine source archive acquired. AtlasUI may contain additional statically linked wxWidgets code; verify its exact build and notices if distributing editor files |
| `FCollada.dll` | FCollada, MIT per R28 library map | Engine source archive contains source-library material; retain its Copyright.txt and match Windows build revisions |
| `gloox-1.0.dll` | gloox, GPL v3 per R28 library map; PE version `1.1-svn`, Jakob Schroeter | **Exact upstream SVN source revision/build unresolved.** WFG SVN r28266 explicitly changed stable1.0.28 back to future1.1 trunk. Official upstream SVN HTTPS returned503; no exact trunk revision in WFG log. Stable1.0.28 is NOT matching source. GPLv3 text acquired; do not relabel stable source as corresponding |
| `OpenAL32.dll` | OpenAL Soft, PE version `1.24.3`; R28 library map says LGPL v2.0-or-later | Exact upstream 1.24.3 source acquired; COPYING is GNU Library GPL version 2 (1991), plus BSD/pffft notices. Version matches WFG SVN r28264. Windows build configuration/patch match not reproduced |
| `libiconv.dll` | GNU libiconv; R28 map says LGPL v2.0-or-later | Pinned WFG header identifies version1.17; exact GNU1.17 source acquired, library license LGPL2.1-or-later. Its Windows CMake integration/build revision remains to match |
| `mozjs128-release.dll` | SpiderMonkey ESR128 family; R28 map broadly says MPL/GPL/LGPL | WFG SVN r28273 identifies ESR128.13. The engine source tar contains mozjs-128.13.0.tar.xz, mozconfig and patches. Exact Windows build options/patch correspondence and complete Mozilla third-party notice aggregation remain to verify |
| `freetype.dll` | FreeType `2.13.3` from PE; upstream offers FTL or GPL2-or-later | Add selected applicable license and attribution; acquire exact source/build record. FTL has an attribution requirement and is not GPL2-only compatible |
| `enet.dll` | ENet, MIT per R28 map | Preserve exact copyright/license; immutable dependency binary exists; source/build association still to archive |
| `icudt77.dll`, `icuin77.dll`, `icuio77.dll`, `icutu77.dll`, `icuuc77.dll` | ICU77, MIT-X11 according to R28 map; pinned SVN `icu/LICENSE` exists | Retain complete ICU license/data notices; confirm exact source patchlevel |
| `libcurl.dll` | curl, MIT-style curl license per R28 map | Preserve curl copyright/license and build TLS dependency notices; source/build record still to archive |
| `libpng16.dll` | libpng license per R28 map | Preserve complete libpng license and copyright |
| `libsodium.dll` | ISC per R28 map | Preserve license/copyright |
| `libxml2.dll` | MIT per R28 map | Preserve license/copyright and exact source version |
| `miniupnpc.dll` | BSD per R28 map | Preserve license/copyright |
| `nvcore.dll`, `nvimage.dll`, `nvmath.dll`, `nvtt.dll` | NVIDIA Texture Tools, MIT per R28 source-library map | Retain `NVIDIA_Texture_Tools_LICENSE.txt` and bundled third-party notices; match Windows source build |
| `SDL2.dll` | SDL2, zlib license per R28 map | Preserve license/copyright |
| `ogg.dll`, `vorbis.dll`, `vorbisenc.dll`, `vorbisfile.dll` | Xiph codecs; Vorbis BSD per R28 map | Preserve each Ogg/Vorbis component's own BSD notice |
| `zlib1.dll` | zlib license per R28 map | Preserve license/copyright |
| Static Boost and fmt code | Explicitly identified as static by pinned Windows dependency script; Boost Software License and MIT per R28 map | Include notices even though no Boost/fmt DLL appears in the bundle |
| `msvcp140.dll`, `vcruntime140.dll`, `concrt140.dll` | Microsoft VC runtime; inspected `concrt140.dll` version `14.44.35211.0`; proprietary redistributable terms | Existing GPL/MIT texts do not cover these. Verify publisher's redistribution entitlement and preserve applicable Microsoft terms; prefer documented official prerequisite installation |
| `dbghelp.dll`, `dbgcore.dll` | Microsoft debug libraries, inspected version `10.0.26100.3916`; root `license_dbghelp.txt` has specific proprietary terms | Keep license; establish the matching redistributable-file designation/terms for both DLLs. The extracted root has no matching REDIST.TXT; this audit does not certify entitlement |
| `.pdb` files | Debug symbols shipped by upstream, component ownership differs | Optional for player package. Do not apply engine GPL indiscriminately to Microsoft debugging symbols. Preserve only symbols whose distribution rights are established |

The original extracted root contains `license_gpl-2.0.txt`, `license_lgpl-2.1.txt`, `license_mit.txt`, and `license_dbghelp.txt`. Its NSIS recipe includes root `*.txt`, DLLs, PDBs and `binaries/system/*.txt`; inclusion of the full source tree is disabled by default. Thus successful extraction of the official installer does not establish a complete source/notice delivery for this project's redistribution.

## Source delivery that can be reproduced

Primary release sources:

- [Official R28 release downloads](https://releases.wildfiregames.com/).
- [Official source download instructions](https://play0ad.com/download/source/).
- [Pinned Windows dependency script](https://gitea.wildfiregames.com/0ad/0ad/raw/commit/a2cae4d69f816e9e9d7eecb6bf88f762afc0c90d/libraries/get-windows-libs.bat).
- [Immutable Win64 dependency tree, SVN r28275](https://svn.wildfiregames.com/public/!svn/bc/28275/windows-libs-amd64/trunk/).

Reproduce the dependency binary checkout with:

```bat
svn checkout -r 28275 https://svn.wildfiregames.com/public/windows-libs-amd64/trunk@28275 windows-libs-amd64-r28275
```

This tree has **headers and precompiled binaries, not complete source for all DLLs**. The inspected `unix-build` tarball does not contain `libraries/win32`, `libraries/win64`, or `get-windows-libs.bat`. Therefore the source tarball plus this checkout alone must not be advertised as a fully reproducible Windows engine build or a completed corresponding-source package for every bundled dependency.

The source delivery for a runtime-rebundling release must include the original KTW code, launcher code, build/package scripts, exact upstream engine source, dependency sources and applicable patches/build recipes, full licenses and the asset manifest. A generic home-page link or an unidentified newer source version is insufficient evidence of a matching source delivery. If sources are offered as downloads, keep equivalent reliable access alongside the binaries; do not make an unfulfillable written source offer. See the actual GPL text supplied with the project, [FSF GPLv2 FAQ](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.en.html), and component-specific terms, including [MPL2](https://www.mozilla.org/en-US/MPL/2.0/).

The accompanying game-data archive is separately listed by upstream at `https://releases.wildfiregames.com/0ad-0.28.0-unix-data.tar.xz`. Original artwork/audio credits and per-directory LICENSE.txt files must remain accessible. Do not describe all game data as GPL: the R28 art/audio rules primarily specify CC BY-SA 3.0 with directory/file exceptions. Include the [CC BY-SA 3.0 license](https://creativecommons.org/licenses/by-sa/3.0/legalcode), the authors and source links already recorded for imported Millennium assets, and modification notices. Do not imply original authors endorse the game.

## Additional sources and prerequisite recovered

The release audit acquired these authentic files under `upstream/distribution-sources` (see `DISTRIBUTION_AUDIT.json`):

| File | SHA-256 | Verified scope |
|---|---|---|
| `openal-soft-1.24.3.tar.bz2` | `cb5e6197a1c0da0edcf2a81024953cc8fa8545c3b9474e48c852af709d587892` | Official OpenAL source; version matches DLL and WFG SVN log; LGPL2.0/BSD/pffft license texts extracted |
| `libiconv-1.17.tar.gz` | `8f74213b56238c85a50a5329f77e06198771e70dd9a739779f4c02f65d971313` | Official GNU source; version matches pinned WFG header; GPL3 and LGPL2.1 license texts extracted |
| `vc_redist.x64.exe`, 18,731,856 bytes | `843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c` | Official Microsoft prerequisite14.51.36247; cryptographic digest, current-time signing chain and CRL verified; not executed |

The VC installer came from the documented `https://aka.ms/vc14/vc_redist.x64.exe` link, resolving to an official Microsoft immutable download path recorded in `vc_redist.x64.provenance.json`. `osslsigncode2.8` verified it against Microsoft's Root Certificate Authority2011 certificate fetched from the embedded certificate's official AIA. Verification used `-ignore-timestamp`: current signer validity and CRL passed; timestamp validity was not asserted. No Wine trust store or execution was involved.

The actual signed installer UI points to `https://aka.ms/VCRedistLicense`, which resolves to Microsoft's Visual C++ v14 runtime license page and its 39,553-byte DOCX. The authentic DOCX and extracted text are saved as `VC-Redistributable-License.docx` / `.txt`; the applicable public end-user terms prohibit redistribution. Microsoft's developer documentation separately permits licensed Visual Studio users to redistribute under their applicable license. No such publisher entitlement has been established here, so **do not bundle the prerequisite under the public download terms alone**. A direct Microsoft download on the user's PC, retaining the original installer and license UI, is the available route. Signature verification establishes provenance, not redistribution entitlement.

## Concrete Windows acceptance gaps

1. **Missing VC runtime dependency:** `pyrogenesis.exe` directly imports `VCRUNTIME140_1.dll`; the extracted official installer does not include it. The same missing dependency is imported by SpiderMonkey, gloox, OpenAL and other components. Resolve with an appropriate official x64 VC redistributable prerequisite or a properly licensed, tested app-local set. Wine built-ins or an already configured developer PC can hide this gap. See [Microsoft's current runtime download and version guidance](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/) and [redistribution rules](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files/).
2. **Debug DLLs cannot be removed on assumption:** `mozjs128-release.dll` directly imports `dbghelp.dll`. A Windows system copy may suffice, but that must be tested on the supported Windows versions before omitting the shipped copy. Keep all original notices while evaluating this. The debug license limits redistribution to Windows and has conditions beyond retaining a text file.
3. **Source/notice closure:** exact source for `gloox 1.1-svn`, libiconv, Windows build patches and all third-party notices remains to be established. The existence of an official upstream installer does not make the new standalone distribution automatically cleared.
4. **Native acceptance:** a PE header check, ZIP/NSIS CRC check, Linux gameplay test or Wine smoke test does not prove clean Windows 10/11 operation. Required evidence: clean non-admin install, offline launch after prerequisites, Russian/Kazakh Unicode paths, menu, campaign, player-controlled battle, saved losses, full process restart and reload, and log review. Test missing-prerequisite and unwritable-install cases explicitly. Record GPU/driver and avoid unmeasured 60-FPS claims.
5. **Steam:** no Steam build review, store review, trademark clearance, commercial asset clearance or publisher-account approval is implied. The title remains a working title; proprietary Total War content is not included. These are release tasks, separate from demonstrating the prototype loop.

## Packaging decisions

**Available fallback:** distribute the original launcher, mod and editable source/build scripts, and download the checksum-pinned official 0 A.D. installer and official Microsoft prerequisite directly on the user's PC during setup. This does not redistribute the unresolved third-party runtime binaries in the delivered kit. Keep the upstream license/installer interactions intact. Installation initially needs network access; gameplay after installation must work offline. This is a Windows launcher/setup kit, not an already installed standalone game and not evidence of native Windows acceptance.

**Full bundled runtime remains open:** identifying gloox1.1's exact source snapshot and matching build, finishing component notices/source closure and resolving Microsoft redistributable conditions are concrete unfinished tasks. The stable gloox1.0.28 archive was fetched only to examine upstream license material and must not be included or described as the shipped DLL's corresponding source.


Keep the original runtime in its own directory, original license/credit files intact; place the original module and separate launcher around it. Include this standalone-specific audit alongside the unchanged module notice. Record every addition/removal and its hash in a package manifest. Keep install-time prerequisite access separate from game runtime: the game must not require a network connection after installation.

A local QA candidate may be produced and tested while these items are completed. Its status must be described accurately: engine/runtime provenance verified; standalone Windows acceptance and full redistribution closure still open until the listed evidence exists. Do not label it a finished Steam release or a completely audited redistributable merely because a launcher EXE was built.

## Evidence preserved in this source kit

`docs/distribution-evidence/` contains the artifact audit, PE inventory, original pinned Windows dependency script, Microsoft prerequisite provenance and signature-check output. Source archive acquisition hashes identify reproducible audit downloads; those upstream runtime binaries and downloaded archives are not included in this bootstrap delivery. The final package manifests identify exactly what is distributed.
