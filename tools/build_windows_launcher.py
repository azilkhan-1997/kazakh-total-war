#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the real Windows x64 launcher; never downloads or substitutes an engine.

Ubuntu 24.04 x86_64 host. A pinned MinGW toolchain can be extracted locally with
--fetch-toolchain, without installing system packages or requiring administrator
access. See launcher/windows/README.md for the separate runtime contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "launcher" / "windows"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(args: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> str:
    result = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, cwd=cwd)
    return result.stdout


def fetch_toolchain(directory: Path) -> None:
    """Only verified, pinned .deb payloads are extracted into directory/root."""
    lock = json.loads((SOURCE / "toolchain-lock.json").read_text())
    cache = directory / "packages"
    extracted = directory / "root"
    cache.mkdir(parents=True, exist_ok=True)
    extracted.mkdir(parents=True, exist_ok=True)
    for package in lock["packages"]:
        target = cache / Path(package["Filename"]).name
        if not target.exists():
            # .part never counts as a successful download; no shell interpolation.
            with urllib.request.urlopen(lock["base_url"] + package["Filename"], timeout=120) as response:
                with target.with_suffix(".part").open("wb") as output:
                    shutil.copyfileobj(response, output)
            target.with_suffix(".part").replace(target)
        if target.stat().st_size != int(package["Size"]) or sha256(target) != package["SHA256"]:
            raise RuntimeError(f"Toolchain package integrity check failed: {target}")
        run(["dpkg-deb", "-x", str(target), str(extracted)])
    print(f"Verified toolchain extracted into {extracted}")


def pe_report(path: Path) -> dict:
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise RuntimeError("Output lacks a DOS/PE header")
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[offset:offset + 4] != b"PE\x00\x00":
        raise RuntimeError("Output lacks a PE signature")
    machine, sections, timestamp = struct.unpack_from("<HHI", data, offset + 4)
    magic = struct.unpack_from("<H", data, offset + 24)[0]
    subsystem = struct.unpack_from("<H", data, offset + 24 + 68)[0]
    if machine != 0x8664 or magic != 0x20B or subsystem != 2:
        raise RuntimeError("Output is not an AMD64 PE32+ Windows GUI executable")
    if timestamp != 0:
        raise RuntimeError("PE linker timestamp is not deterministic")
    return {"machine": "AMD64", "format": "PE32+", "subsystem": "Windows GUI",
            "sections": sections, "timestamp": timestamp}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, help="Local toolchain folder containing root/usr/bin")
    parser.add_argument("--fetch-toolchain", action="store_true", help="Download exact checksum-pinned toolchain packages")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/windows/KazakhTotalWar.exe")
    parser.add_argument("--tests-only", action="store_true", help="Run portable C++ launcher logic tests on the host")
    args = parser.parse_args()
    if args.fetch_toolchain and not args.toolchain:
        parser.error("--fetch-toolchain requires --toolchain (a writable local directory)")
    if args.fetch_toolchain:
        fetch_toolchain(args.toolchain.resolve())

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ktw-launcher-") as temporary:
        staging = Path(temporary)
        host_compiler = os.environ.get("CXX", "g++")
        print(run([host_compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                   str(SOURCE / "launcher_core_tests.cpp"), "-o", str(staging / "core-tests")]), end="")
        host_result = run([str(staging / "core-tests")]).strip()
        print(host_result)
        if args.tests_only:
            return
        env = os.environ.copy()
        if args.toolchain:
            bin_directory = args.toolchain.resolve() / "root/usr/bin"
            env["PATH"] = str(bin_directory) + os.pathsep + env.get("PATH", "")
            compiler = str(bin_directory / "x86_64-w64-mingw32-g++-win32")
            preprocessor = str(bin_directory / "x86_64-w64-mingw32-gcc-win32")
            windres = str(bin_directory / "x86_64-w64-mingw32-windres")
            objdump = str(bin_directory / "x86_64-w64-mingw32-objdump")
        else:
            compiler = "x86_64-w64-mingw32-g++-win32"
            preprocessor = "x86_64-w64-mingw32-gcc-win32"
            windres = "x86_64-w64-mingw32-windres"
            objdump = "x86_64-w64-mingw32-objdump"
        compiler_version = run([compiler, "--version"], env=env).splitlines()[0]
        resource_version = run([windres, "--version"], env=env).splitlines()[0]
        resource_command = [windres, "--codepage=65001", "--preprocessor=" + preprocessor,
                            "--preprocessor-arg=-E", "--preprocessor-arg=-xc", "--preprocessor-arg=-DRC_INVOKED", "-I", str(SOURCE),
                            str(SOURCE / "launcher.rc"), str(staging / "launcher-res.o")]
        print(run(resource_command, env=env, cwd=SOURCE), end="")
        command = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                   "-municode", "-mwindows", "-static", "-static-libgcc", "-static-libstdc++",
                   "-ffile-prefix-map=" + str(ROOT) + "=.", "-Wl,--no-insert-timestamp,--dynamicbase,--nxcompat",
                   str(SOURCE / "main.cpp"), str(staging / "launcher-res.o"), "-lshell32", "-luser32",
                   "-o", str(staging / "KazakhTotalWar.exe")]
        print(run(command, env=env), end="")
        staged_output = staging / "KazakhTotalWar.exe"
        pe = pe_report(staged_output)
        imports = re.findall(r"DLL Name:\s*(\S+)", run([objdump, "-p", str(staged_output)], env=env))
        allowed = {"kernel32.dll", "msvcrt.dll", "shell32.dll", "user32.dll"}
        if not imports or any(name.lower() not in allowed for name in imports):
            raise RuntimeError(f"Unexpected non-OS launcher dependency: {imports}")
        # Copy to same-volume temporary file before replacing the requested output.
        temporary_output = output.with_suffix(output.suffix + ".new")
        shutil.copyfile(staged_output, temporary_output)
        temporary_output.replace(output)
        inputs = [*sorted(SOURCE.glob("*.cpp")), *sorted(SOURCE.glob("*.hpp")),
                  SOURCE / "launcher.rc", SOURCE / "launcher.manifest", SOURCE / "toolchain-lock.json",
                  Path(__file__).resolve()]
        report = {
            "component": "Kazakh Total War native Windows launcher",
            "component_version": "0.3.0", "required_engine": "0.28.0",
            "compiler": compiler_version, "resource_compiler": resource_version,
            "executable": output.name, "bytes": output.stat().st_size, "sha256": sha256(output),
            "pe": pe, "imports": imports,
            "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
            "host_logic_tests": host_result,
            "native_windows_execution": "NOT RUN by this build script",
            "bundled_engine_execution": "NOT RUN by this build script",
            "scope": "Launcher only. Official Pyrogenesis and game data must be packaged separately.",
        }
        output.with_suffix(".build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Built {output} ({report['bytes']} bytes, SHA-256 {report['sha256']})")
        print("PE32+ AMD64 GUI and OS-only imports validated. Native Windows execution: NOT RUN.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(error.stdout or "", end="")
        raise SystemExit(f"Build command failed (exit {error.returncode}): {error.cmd}") from error
    except (OSError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
