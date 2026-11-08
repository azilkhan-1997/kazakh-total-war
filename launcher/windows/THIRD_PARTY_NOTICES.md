# Windows launcher — third-party notices

This notice covers `KazakhTotalWar.exe`, the original launcher, not the separately downloaded Pyrogenesis engine. Original launcher source is GPL-2.0-or-later under the project root `LICENSE`; its source and reproducible build script are supplied in this kit.

| Linked component | Applicable notices |
|---|---|
| GCC 13 libgcc and GNU libstdc++ runtime/header code | GPL-3.0-or-later with GCC Runtime Library Exception 3.1; `LICENSES/GPL-3.0.txt`, `LICENSES/GCC-Runtime-Library-Exception-3.1.txt`, `LICENSES/GCC-RUNTIME-NOTICES.txt` |
| Historical STL code included by libstdc++ headers | Hewlett-Packard 1994 and Silicon Graphics 1996–1998 permission notices in `LICENSES/libstdc++-STL-NOTICES.txt` |
| MinGW-w64 11.0.1 startup/runtime and headers | Original copyright/license mapping retained verbatim in `LICENSES/MinGW-w64-COPYRIGHT.txt`; includes public-domain, ZPL 2.1 and other per-file permissive notices |

The launcher is compiled from independent C++ source by the ordinary GCC/MinGW toolchain using `-static -static-libgcc -static-libstdc++`. The build does not use a non-GPL-compatible GCC plugin or intermediate-code optimizer. This is the eligible compilation route described by Runtime Library Exception 3.1; its additional permission permits distribution of this combined target code consistently with the launcher's original license. This permission concerns the covered runtime portions in the compiled launcher; it is not a blanket exemption for redistributing GCC, modifying runtime libraries, or bundling unrelated engines.

The actual launcher imports only Windows-provided `KERNEL32.dll`, `msvcrt.dll`, `SHELL32.dll` and `USER32.dll`. These operating-system DLLs, GCC runtime DLLs, compiler executables and binutils are not included in the launcher distribution. Static runtime code is nevertheless present and its notices above are retained.

## Provenance

The exact downloaded package versions, upstream download locations and verified package SHA-256 values are in `toolchain-lock.json`. The build script is `tools/build_windows_launcher.py`. Toolchain package versions: GCC/MinGW `13.2.0-6ubuntu1+26.1`, MinGW-w64 `11.0.1-3build1`, GNU binutils `2.41.90.20240122-1ubuntu1+11.4`.

The exception and runtime mapping were copied from the verified toolchain's `usr/share/doc/gcc-mingw-w64-base/copyright`; the GNU libstdc++ and STL notices were copied from its actual GCC 13 headers. The package copyright document contains historical GCC 9 packaging prose, so this notice uses the actual compiler version and GCC 13 header notices rather than treating that historical prose as the installed version. The complete MinGW notice is the unchanged `usr/share/doc/mingw-w64-common/copyright`, identical to the corresponding development package's copyright file. GPL 3 is the complete `/usr/share/common-licenses/GPL-3` text explicitly referenced by the toolchain copyright file.

Primary upstream explanation: [GCC libstdc++ code license and Runtime Library Exception 3.1](https://gcc.gnu.org/onlinedocs/libstdc++/manual/license.html). The included complete license texts govern; this notice does not replace them.
