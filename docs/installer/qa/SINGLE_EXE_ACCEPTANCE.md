# Single EXE acceptance — KAZAKH TOTAL WAR

This is a test plan and scope boundary, not a record that native Windows was tested.
The target user flow is download one setup EXE, install, start from a shortcut.
No installed Python, command-line extraction, manual ZIP handling, or separate
0 A.D. installation may be required of the player. An installer that automatically
downloads the official runtime must disclose first-install Internet access and
approximately 1.65 GB download. It is not an offline self-contained installer.

## Linux-verifiable build gates

The first candidate compiled successfully with NSIS v3.09-4, using an x86
installer stub with an explicit x64 Windows gate. Final exact-artifact reports
are recorded separately because installer sources may change during review.

| Gate | Required evidence | Initial status |
|---|---|---|
| Real setup executable | Successful NSIS/native build; valid PE GUI header, architecture that runs on Windows10/11x64; size/hash recorded | Pending candidate |
| Embedded own content | Module/art/launcher hashes match the verified game revision; original licenses retained | Pending candidate |
| Private Python if used | Official pinned embeddable runtime and its complete license notices; private application/temp location; not added to PATH or installed globally | Pending candidate |
| Source/delivery closure | Exact editable own setup/source and build scripts; actual runtime licenses/source obligations recorded; no invented clearance | Pending legal/source review |
| Corrupt download/cache | Wrong size/hash rejected before extraction or execution; current installation and saves unchanged | Pending worker tests |
| Extraction | Full140-file inventory and both official asset ZIP CRCs match; path traversal/symlinks/duplicate paths rejected | Existing extractor tests available; new integration pending |
| Interrupted install | Staging retained or safely removed; final marker not written until verified complete; retry does not duplicate or damage saves | Pending worker tests |
| Existing installation | No writes to ordinary0AD, arbitrary directories or unrelated product; stable profile identity; ownership marker required before removal/update | Pending worker tests |
| Cancel/error | No success page/launch until worker exit and post-install checks pass; child process ownership handled; partial result never presented as installed | Pending candidate |
| Disk/path guard | Nonempty per-user target, no drive root or protected/system directory, enough simultaneous download+extract+rollback disk | Pending candidate |
| Uninstall | Removes only owned product/shortcuts/registry entries; preserves saves/config by default; no recursive erase of arbitrary destination | Pending candidate |

## Known delivery limitations

This delivery supports fresh installation into an empty per-user folder. It
refuses arbitrary nonempty destinations. A same-version owned installation can
restore its shortcuts after launcher/engine hash and launcher preflight checks;
this does not replace gameplay files or upgrade the profile. The
uninstaller preserves saves/config and unknown or modified files, so reinstall
into that same folder is also refused when those files remain. Continuing a
preserved campaign requires a separate fresh install and copying the preserved
saves into its profile. In-place upgrade, repair and automatic profile migration
are not implemented.

If shortcut or registry registration fails after atomic publication, the game
files can already exist even though the wizard reports an error. Same-version
registration retry has been implemented; native Windows acceptance must verify
that rerunning the EXE restores shortcuts and registry without changing saves.

## Native Windows acceptance still required

Use clean Windows10 and11x64 accounts without Python and without preinstalled0AD.
Record actual OS/build/GPU/driver, installer SHA256, source revision, date, tester,
logs and each observed outcome. Use PASS/FAIL/NOT TESTED.

1. Download the single EXE, execute from a path with spaces and Kazakh letters.
2. Confirm ordinary per-user install does not require administrator rights; if
   Visual C++ installation requires elevation, only the official prerequisite
   process may ask for it. Test declined UAC, existing current prerequisite,
   missing prerequisite, failed installer and reboot-required exit codes.
3. Confirm no global Python or0AD installation, PATH change or overwritten0AD
   registry/uninstaller entries. Inspect original existing0AD profile unchanged.
4. Confirm download progress/error/cancel and retry; test a connection interruption
   and an equal-size corrupted cached payload. Never execute an unverified payload.
5. Confirm menu, RU/KK glyphs, campaign army movement/recruitment/endturn, real
   battle transition and unit commands; let a real battle resolve normally.
6. Confirm battle losses/commander consequences applied once, save after battle,
   restart process and reload. Repeat a mid-battle save/restart.
7. Disconnect networking after completed install and repeat campaign/battle/save
   loop. Verify this is actual offline play, not a hidden download dependency.
8. Run installer again over its own valid same-version install; confirm shortcut
   restoration and keep profiles/saves unchanged. Test an unrelated existing
   shortcut and the per-install alternate name on repeated runs. Automatic
   upgrade remains out of scope.
   Run against a directory without its ownership marker; reject destructive reuse.
9. Uninstall, verify owned executable/assets/shortcuts removed and saves/config
   retained by default; confirm same-folder refusal, then install into a different
    empty folder and verify explicit saved-campaign transfer. Automatic reuse of
    the retained profile is a missing feature.
10. Record true GPU/frame-time measurements separately. Static build success does
    not establish Windows gameplay, unsigned SmartScreen behavior, or Steam acceptance.

## Important architecture constraints

The current launcher uses `-writableRoot`; default installation under Program Files
will fail ordinary-user profile writes. Prefer an owned per-user folder, with
elevation confined to Microsoft's original prerequisite process. Do not invoke
the official0AD installer silently into a staging directory: its global registry
and shortcuts can affect the user's independent0AD installation. Verified static
extraction into a private runtime is safer.

All pending native checks remain pending until a real run supplies evidence.
