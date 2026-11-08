#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Restore exactly 19 admitted CC-BY-SA PNGs; no engine, EXE or log imports.

URLs and byte digests are fixed below and cross-checked against both provenance
records. All downloads are validated before any working-tree mutation. A public
push is possible only with explicit --publish and an exact expected main HEAD.
"""
from pathlib import Path, PurePosixPath
import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request

PROJECT = Path(__file__).resolve().parents[2]
REPOSITORY = "azilkhan-1997/kazakh-total-war"
ORIGIN = "https://github.com/" + REPOSITORY + ".git"
REVISION = "91636b405ee8d0088ec3a34fba6074dbd5c9d0f3"
RAW = "https://raw.githubusercontent.com/0ADMods/millenniumad/" + REVISION + "/"
LICENSE_SHA = "247ea9380781c56e71018bb3714faf557192f0c3ad6a3d7d231c6f20f325d0e4"
ATTRIBUTION = "The Council of Modders, Fallen Empire Studio, Scion Development"
AUDIT = "docs/distribution-evidence/github-source-binary-audit.json"
MANIFEST = "docs/asset-manifest-millennium.json"
# Exact reviewed subset, not an extensible directory/suffix import rule.
ASSETS = {'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/head/chin_b.png': {'bytes': 25442,
                                                                                   'sha256': '146bc14cbc1b671209c7f18bd6d7dcb4c6ba3e6810ca8d37b5b7c1276a280014',
                                                                                   'source_path': 'art/textures/skins/props/head/chin_b.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/head/xion_b.png': {'bytes': 19094,
                                                                                   'sha256': 'bbb674371b41c7593ca9948e0400ef53bdf4f5bfcf85844338ae72e54d40aa63',
                                                                                   'source_path': 'art/textures/skins/props/head/xion_b.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/helmet/byzantine_archer_helmet_iron.png': {'bytes': 254526,
                                                                                                           'sha256': '5414af27f58014d702fa0815e3ba495c160db35ecd8885d1226787dc14cdbf76',
                                                                                                           'source_path': 'art/textures/skins/props/helmet/byzantine_archer_helmet_iron.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/helmet/byzantine_archer_helmet_norm.png': {'bytes': 394788,
                                                                                                           'sha256': 'edb7a5572e377894b35b7382a3851bfebd313268eb15f90fee2a39e8eaeaac7f',
                                                                                                           'source_path': 'art/textures/skins/props/helmet/byzantine_archer_helmet_norm.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/helmet/byzantine_archer_helmet_spec.png': {'bytes': 159149,
                                                                                                           'sha256': 'c6559bb09b62b81e81f0cc1a510967ab8f6bcc4e26e9738ce8dfced3949cec5d',
                                                                                                           'source_path': 'art/textures/skins/props/helmet/byzantine_archer_helmet_spec.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/horse/cataphract_armor_lamellar.png': {'bytes': 387423,
                                                                                                       'sha256': '9d493266f8da9293c9205eae670bc23d6c330666a9191461c4e96755d30b297a',
                                                                                                       'source_path': 'art/textures/skins/props/horse/cataphract_armor_lamellar.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/horse/cataphract_armor_lamellar2.png': {'bytes': 368962,
                                                                                                        'sha256': 'd36ba00dddd8c4ac6b2e5ffee2d5d86691bd0c77ead9415409cc5926c1e256cb',
                                                                                                        'source_path': 'art/textures/skins/props/horse/cataphract_armor_lamellar2.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/horse/cataphract_armor_norm.png': {'bytes': 468337,
                                                                                                   'sha256': '1a929c714b2d6c4258900ef1e762cb0b41e90e23eb5f3b358ffaae2b42e0caf7',
                                                                                                   'source_path': 'art/textures/skins/props/horse/cataphract_armor_norm.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/horse/cataphract_armor_spec.png': {'bytes': 285278,
                                                                                                   'sha256': '23c2ddbc818b591c210ea6b67a921576e671eddb5978bc9892dca20a19018dbc',
                                                                                                   'source_path': 'art/textures/skins/props/horse/cataphract_armor_spec.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/xion_quiver_basic.png': {'bytes': 376939,
                                                                                         'sha256': 'a6a5bfd7af728291515074b89670a0de4a40fba22ca1927bda5b4ec676260b1d',
                                                                                         'source_path': 'art/textures/skins/props/xion_quiver_basic.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/xion_quiver_basic_b.png': {'bytes': 372206,
                                                                                           'sha256': 'a67cd50c150d8f8684f8f59093811b47d34739f83261393110583eced4ce5d60',
                                                                                           'source_path': 'art/textures/skins/props/xion_quiver_basic_b.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/xion_quiver_basic_norm.png': {'bytes': 422821,
                                                                                              'sha256': '4ed6d682e4192541be68a2705258017e645dcf2fb7ba87662eeb35bbfb956c33',
                                                                                              'source_path': 'art/textures/skins/props/xion_quiver_basic_norm.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/props/xion_quiver_spec.png': {'bytes': 17170,
                                                                                        'sha256': '4a1734bcf56479794994eaae236168a98248bddac61cc3bd4cbc6352e759875e',
                                                                                        'source_path': 'art/textures/skins/props/xion_quiver_spec.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/skeletal/xion_cloth_a.png': {'bytes': 530777,
                                                                                       'sha256': 'e0e04c55d8c3b6fe45dd7c6345734636c88e978cf9454b20a0d70fbf134a3ff1',
                                                                                       'source_path': 'art/textures/skins/skeletal/xion_cloth_a.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/skeletal/xion_cloth_b.png': {'bytes': 611203,
                                                                                       'sha256': 'bd99a41a278ddebbc84922aeb4f7be86134aece9f9f136cd83e053f897fbd308',
                                                                                       'source_path': 'art/textures/skins/skeletal/xion_cloth_b.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/skeletal/xion_cloth_c.png': {'bytes': 532898,
                                                                                       'sha256': 'c4701e3feee264224e281ea97ceba6ea68e7f0affe04fd37fff5dc236515017d',
                                                                                       'source_path': 'art/textures/skins/skeletal/xion_cloth_c.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/skeletal/xion_cloth_norm.png': {'bytes': 506876,
                                                                                          'sha256': 'fb28e313f0b5957699e00c5391f81c5e4cf9149b0a1176702ecdf5f4b57e30e3',
                                                                                          'source_path': 'art/textures/skins/skeletal/xion_cloth_norm.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/skeletal/xion_cloth_spec.png': {'bytes': 1232,
                                                                                          'sha256': 'f6d18dc2a4241da770a44e0758e3cfecefb845e34e65fc526ee21f8d5781d0cd',
                                                                                          'source_path': 'art/textures/skins/skeletal/xion_cloth_spec.png'},
 'mods/kazakh_total_war/art/textures/skins/ktw/millennium/structural/xion_structure.png': {'bytes': 1741352,
                                                                                           'sha256': '66993d3783940de65c857543794e596c8e560b020527d2d899f0876e00af8315',
                                                                                           'source_path': 'art/textures/skins/structural/xion_structure.png'}}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical_name(name):
    require(isinstance(name, str) and bool(name), "Empty or non-string path")
    p = PurePosixPath(name)
    require(not p.is_absolute() and str(p) == name and
            all(part not in (".", "..") for part in p.parts) and
            not any(c in name for c in ("\\", ":", "\0")), "Noncanonical path: " + name)
    return p


def safe_path(root, name):
    p = canonical_name(name)
    current = root
    for part in p.parts:
        current = current / part
        require(not current.is_symlink(), "Symlink path refused: " + name)
    require(current.resolve().is_relative_to(root.resolve()), "Path escapes project: " + name)
    return current


def check_bytes(data, row, name):
    require(len(data) == row["bytes"], "Wrong byte count: " + name)
    require(digest(data) == row["sha256"], "SHA-256 mismatch: " + name)
    return data


def load_plan(root):
    audit = json.loads(safe_path(root, AUDIT).read_text())
    manifest = json.loads(safe_path(root, MANIFEST).read_text())
    rows = audit["textures"]
    require(len(rows) == 19 and len({r["path"] for r in rows}) == 19 and
            {r["path"] for r in rows} == set(ASSETS), "Audit does not contain exact 19-path allowlist")
    require(audit["license_url"] == RAW + "art/license.txt" and
            audit["license_sha256"] == LICENSE_SHA, "Unexpected license provenance")
    require(manifest["commit"] == REVISION and manifest["license_sha256"] == LICENSE_SHA and
            manifest["asset_license"] == "CC-BY-SA-3.0", "Manifest license/revision differs")
    for row in rows:
        name = row["path"]; canonical_name(name)
        expected = ASSETS[name]; canonical_name(expected["source_path"])
        require(row["bytes"] == expected["bytes"] and row["sha256"] == expected["sha256"] and
                row["source_url"] == RAW + expected["source_path"] and
                row["license"] == "CC-BY-SA-3.0" and row["attribution"] == ATTRIBUTION,
                "Audit provenance differs: " + name)
        entry = manifest["files"][name.removeprefix("mods/kazakh_total_war/")]
        require(entry["source_path"] == expected["source_path"] and entry["source_commit"] == REVISION and
                entry["source_sha256"] == expected["sha256"] and entry["output_sha256"] == expected["sha256"] and
                entry["license"] == "CC-BY-SA-3.0" and entry["attribution"] == ATTRIBUTION and
                entry["modifications"] == [], "Manifest provenance differs: " + name)
    original = safe_path(root, "LICENSES/Millennium-Art.txt").read_bytes()
    require(digest(original) == LICENSE_SHA, "Original artwork license changed or missing")
    module_notice = safe_path(root, "mods/kazakh_total_war/art/ktw-MILLENNIUM-LICENSE.txt").read_bytes()
    require(module_notice.startswith(original) and REVISION.encode() in module_notice,
            "Module attribution/source notice incomplete")
    notices = safe_path(root, "THIRD_PARTY_NOTICES.md").read_text()
    require(ATTRIBUTION in notices and REVISION in notices, "Third-party attribution missing")
    return original


def download(url, maximum):
    allowed = {RAW + "art/license.txt"} | {RAW + r["source_path"] for r in ASSETS.values()}
    require(url in allowed, "URL outside pinned source allowlist")
    request = urllib.request.Request(url, headers={"User-Agent": "KAZAKH-TOTAL-WAR-source-import/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(maximum + 1)
    require(len(data) <= maximum, "Download exceeds fixed size: " + url)
    return data


def prepare(root, fetch=download, download_all=False):
    original = load_plan(root)
    existing, missing = {}, []
    # Check every destination before any network operation or directory creation.
    for name, row in ASSETS.items():
        path = safe_path(root, name)
        if path.exists():
            require(path.is_file(), "Destination is not a regular file: " + name)
            existing[name] = check_bytes(path.read_bytes(), row, name)
        else:
            missing.append(name)
    if not missing and not download_all:
        return existing, []
    licensed = fetch(RAW + "art/license.txt", len(original))
    require(licensed == original and digest(licensed) == LICENSE_SHA, "Upstream license hash/content mismatch")
    verified = {}
    for name, row in ASSETS.items():
        data = check_bytes(fetch(RAW + row["source_path"], row["bytes"]), row, name)
        require(data.startswith(b"\x89PNG\r\n\x1a\n"), "Expected PNG file: " + name)
        verified[name] = data
    return verified, missing


def apply_verified(root, verified, missing):
    require(set(verified) == set(ASSETS), "Incomplete prefetched asset set")
    require(set(missing) <= set(ASSETS) and len(set(missing)) == len(missing), "Unexpected write allowlist")
    # Revalidate all buffers and paths before first write, including already-present files.
    for name, row in ASSETS.items():
        check_bytes(verified[name], row, name)
        p = safe_path(root, name)
        if p.exists():
            require(p.is_file() and p.read_bytes() == verified[name], "Destination changed: " + name)
        else:
            require(name in missing, "Destination disappeared: " + name)
    for name in missing:
        target = safe_path(root, name)
        require(not target.exists(), "Destination appeared concurrently: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        safe_path(root, name)
        fd, temporary = tempfile.mkstemp(prefix=".source-import-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(verified[name]); stream.flush(); os.fsync(stream.fileno())
            # Link does not overwrite a concurrently created destination.
            os.link(temporary, target, follow_symlinks=False)
        finally:
            Path(temporary).unlink(missing_ok=True)
    for name, row in ASSETS.items():
        check_bytes(safe_path(root, name).read_bytes(), row, name)
    return missing


def git(root, *args, env=None):
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=root, env=env).decode().strip()


def remote_tip(root, env=None):
    parts = git(root, "ls-remote", "--exit-code", "origin", "refs/heads/main", env=env).split()
    require(len(parts) == 2 and parts[1] == "refs/heads/main" and re.fullmatch(r"[0-9a-f]{40}", parts[0]),
            "Unexpected main branch response")
    return parts[0]


def require_expected_head(root, expected, env=None):
    require(bool(re.fullmatch(r"[0-9a-f]{40}", expected or "")), "An exact expected HEAD is required")
    require(git(root, "rev-parse", "HEAD") == expected, "Checkout HEAD differs from expected event SHA")
    require(git(root, "remote", "get-url", "origin") in (ORIGIN, ORIGIN.removesuffix(".git")),
            "Unexpected repository origin")
    require(remote_tip(root, env) == expected, "main moved: stop without retry, force or rebase")


def assert_staged_assets(root, changed, verified):
    raw = subprocess.check_output(["git", "diff", "--cached", "--name-status", "-z"], cwd=root)
    tokens = raw.split(b"\0"); require(tokens[-1] == b"", "Invalid staged path listing")
    tokens = tokens[:-1]
    require(len(tokens) == 2 * len(changed), "Staged set differs from expected additions")
    rows = [(tokens[i].decode(), tokens[i + 1].decode()) for i in range(0, len(tokens), 2)]
    require({name for status, name in rows} == set(changed) and all(status == "A" for status, name in rows),
            "Only the exact missing asset additions may be committed")
    for name in changed:
        require(name in ASSETS and git(root, "rev-parse", ":" + name) == git_blob(verified[name]),
                "Staged bytes differ from verified PNG: " + name)


def publish(root, expected, fetch=download):
    require_expected_head(root, expected)
    require(not git(root, "status", "--porcelain"), "Publish requires an initially clean checkout/index")
    verified, missing = prepare(root, fetch)
    if not missing:
        return {"status": "already_verified", "verified_pngs": 19, "changed": [], "pushed": False}
    require_expected_head(root, expected)
    apply_verified(root, verified, missing)
    git(root, "add", "--", *missing)
    assert_staged_assets(root, missing, verified)
    require(remote_tip(root) == expected, "main moved before commit: stop without pushing")
    git(root, "-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "-c", "commit.gpgsign=false", "commit", "-m", "Restore 19 SHA-verified licensed Millennium source textures")
    require(git(root, "rev-parse", "HEAD^") == expected, "Import commit parent differs from expected main")
    require(not git(root, "status", "--porcelain"), "Unexpected changes remain after import commit")
    # A fresh tip check plus a normal non-force push: concurrent commits reject
    # the update. Git's ref-update protocol also checks the advertised old ref.
    require(remote_tip(root) == expected, "main moved before push: stop without retry, force or rebase")
    token = os.environ.get("GITHUB_TOKEN", "")
    require(bool(token), "GITHUB_TOKEN is required for the explicit publish step")
    auth = base64.b64encode(("x-access-token:" + token).encode()).decode()
    env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
               GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + auth, GIT_TERMINAL_PROMPT="0")
    git(root, "push", "--porcelain", "origin", "HEAD:refs/heads/main", env=env)
    return {"status": "published_source_textures", "verified_pngs": 19, "changed": missing,
            "commit": git(root, "rev-parse", "HEAD"), "pushed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-downloads", action="store_true", help="Fetch and verify pinned sources without writing")
    mode.add_argument("--apply", action="store_true", help="Restore missing verified PNG files locally; no Git writes")
    mode.add_argument("--publish", action="store_true", help="Explicit CI-only normal push of exact PNG additions")
    parser.add_argument("--expected-head")
    args = parser.parse_args(); root = args.project.resolve()
    if args.publish:
        report = publish(root, args.expected_head)
    else:
        verified, missing = prepare(root, download_all=args.verify_downloads)
        changed = apply_verified(root, verified, missing) if args.apply else []
        report = {"status": "applied_locally" if args.apply else "downloads_verified_no_writes",
                  "verified_pngs": 19, "missing": missing, "changed": changed, "pushed": False}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
