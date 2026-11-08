#!/usr/bin/env python3
"""Reproducibly package the editable module and source kit; no engine executable claim."""
# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
STAMP = (2026, 11, 8, 0, 0, 0)

def archive(path, items):
    # A consumer must never observe a partly rewritten release archive.
    staging = path.with_name(path.name + ".partial")
    with zipfile.ZipFile(staging, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for name, body in sorted(items):
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
            out.writestr(info, body)
    with staging.open("rb") as stream:
        os.fsync(stream.fileno())
    with zipfile.ZipFile(staging) as check:
        failure = check.testzip()
        if failure:
            raise RuntimeError(f"Staged ZIP CRC failed: {failure}")
    os.replace(staging, path)

mod = ROOT / "mods" / "kazakh_total_war"
version = json.loads((mod / "mod.json").read_text())["version"]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--release-version', default=version, help='Delivery/tooling version; does not change gameplay or save compatibility')
args = parser.parse_args()
if not __import__('re').fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', args.release_version):
    parser.error('Release version must be X.Y.Z')
release = ".".join(args.release_version.split(".")[:2])
module_archive = DIST / ("kazakh_total_war_" + version + ".pyromod")
module_files = [(p.relative_to(mod).as_posix(), p.read_bytes()) for p in mod.rglob("*") if p.is_file()]
module_files.extend([
    ("LICENSE", (ROOT / "LICENSE").read_bytes()),
    ("THIRD_PARTY_NOTICES.md", (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes()),
    ("docs/asset-manifest-millennium.json", (ROOT / "docs/asset-manifest-millennium.json").read_bytes()),
    ("README_RU.md", (ROOT / "README_RU.md").read_bytes()),
])
module_files.extend(("LICENSES/" + p.name, p.read_bytes()) for p in (ROOT / "LICENSES").iterdir() if p.is_file())
archive(module_archive, module_files)
files = []
for p in ROOT.rglob("*"):
    relative = p.relative_to(ROOT)
    if not p.is_file() or any(x in {".git", "dist", "__pycache__"} for x in relative.parts) or p.suffix == ".pyc":
        continue
    files.append(("KAZAKH_TOTAL_WAR_Prototype/" + relative.as_posix(), p.read_bytes()))
files.append(("KAZAKH_TOTAL_WAR_Prototype/" + module_archive.name, module_archive.read_bytes()))
bundle = DIST / "KAZAKH_TOTAL_WAR_Source.git.bundle"
if (ROOT / ".git").exists():
    result = subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Commit the source repository before packaging: " + result.stderr)
    files.append(("KAZAKH_TOTAL_WAR_Prototype/KAZAKH_TOTAL_WAR_Source.git.bundle", bundle.read_bytes()))
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
    raise RuntimeError("Commit all tracked source changes before packaging; bundle must match editable source")
files.append(("KAZAKH_TOTAL_WAR_Prototype/RELEASE.json", json.dumps({
    "version": args.release_version, "module_version": version, "source_revision": revision,
    "engine": "0ad=0.28.0", "standalone_windows_executable": False,
    "part1_acceptance": "incomplete: Windows validation and standalone distribution pending"
}, indent=2).encode()))
kit = DIST / ("KAZAKH_TOTAL_WAR_Pyrogenesis_Prototype_v" + release + ".zip")
archive(kit, files)
result = {}
for p in [module_archive, kit]:
    with zipfile.ZipFile(p) as z:
        failure = z.testzip()
        if failure:
            raise RuntimeError(f"ZIP CRC failed: {failure}")
    result[p.name] = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
(DIST / "SHA256SUMS.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
