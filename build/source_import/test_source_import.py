#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Network-free importer contracts using synthetic PNG data and temporary Git."""
from pathlib import Path
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import import_source as importer


class ImportContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ktw-import-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = copy.deepcopy(importer.ASSETS)
        self.data = {name: b"\x89PNG\r\n\x1a\nTEST-FIXTURE:" + name.encode() for name in self.rows}
        for name, row in self.rows.items():
            row["bytes"] = len(self.data[name]); row["sha256"] = importer.digest(self.data[name])
        self.asset_patch = patch.object(importer, "ASSETS", self.rows)
        self.asset_patch.start(); self.addCleanup(self.asset_patch.stop)
        for name in (importer.AUDIT, importer.MANIFEST, "LICENSES/Millennium-Art.txt",
                     "mods/kazakh_total_war/art/ktw-MILLENNIUM-LICENSE.txt", "THIRD_PARTY_NOTICES.md"):
            destination = self.root / name; destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(importer.PROJECT / name, destination)
        audit = json.loads((self.root / importer.AUDIT).read_text())
        manifest = json.loads((self.root / importer.MANIFEST).read_text())
        for row in audit["textures"]:
            expected = self.rows[row["path"]]
            row["bytes"] = expected["bytes"]; row["sha256"] = expected["sha256"]
            entry = manifest["files"][row["path"].removeprefix("mods/kazakh_total_war/")]
            entry["source_sha256"] = expected["sha256"]; entry["output_sha256"] = expected["sha256"]
        (self.root / importer.AUDIT).write_text(json.dumps(audit))
        (self.root / importer.MANIFEST).write_text(json.dumps(manifest))
        self.license = (self.root / "LICENSES/Millennium-Art.txt").read_bytes()
        self.downloads = {importer.RAW + "art/license.txt": self.license}
        self.downloads.update({importer.RAW + row["source_path"]: self.data[name] for name, row in self.rows.items()})
        self.calls = []

    def fetch(self, url, limit):
        self.calls.append(url)
        data = self.downloads[url]
        self.assertLessEqual(len(data), limit)
        return data

    def assert_no_assets(self):
        self.assertFalse(any((self.root / name).exists() for name in self.rows))

    def write_json(self, path, change):
        destination = self.root / path
        data = json.loads(destination.read_text()); change(data)
        destination.write_text(json.dumps(data))

    def init_git(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        importer.git(self.root, "add", "--", importer.AUDIT, importer.MANIFEST,
                     "LICENSES/Millennium-Art.txt", "mods/kazakh_total_war/art/ktw-MILLENNIUM-LICENSE.txt",
                     "THIRD_PARTY_NOTICES.md")
        importer.git(self.root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Fixture metadata")

    def test_complete_prefetch_does_not_write(self):
        verified, missing = importer.prepare(self.root, self.fetch)
        self.assertEqual(verified, self.data)
        self.assertEqual(set(missing), set(self.rows))
        self.assertEqual(len(self.calls), 20)
        self.assert_no_assets()

    def test_last_download_corruption_leaves_all_destinations_untouched(self):
        last = list(self.rows)[-1]
        url = importer.RAW + self.rows[last]["source_path"]
        self.downloads[url] = b"X" + self.downloads[url][1:]
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            importer.prepare(self.root, self.fetch)
        self.assert_no_assets()

    def test_upstream_license_mismatch_precedes_art_fetch(self):
        self.downloads[importer.RAW + "art/license.txt"] = b"X" + self.license[1:]
        with self.assertRaisesRegex(ValueError, "license hash"):
            importer.prepare(self.root, self.fetch)
        self.assertEqual(len(self.calls), 1); self.assert_no_assets()

    def test_audit_cannot_expand_write_allowlist(self):
        self.write_json(importer.AUDIT, lambda d: d["textures"][0].update(path="../../outside.exe"))
        with self.assertRaisesRegex(ValueError, "19-path"):
            importer.prepare(self.root, self.fetch)
        self.assertEqual(self.calls, []); self.assert_no_assets()

    def test_audit_hash_cannot_override_pinned_bytes(self):
        self.write_json(importer.AUDIT, lambda d: d["textures"][0].update(sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "Audit provenance"):
            importer.prepare(self.root, self.fetch)
        self.assertEqual(self.calls, [])

    def test_manifest_hash_mismatch_rejected(self):
        name = next(iter(self.rows)).removeprefix("mods/kazakh_total_war/")
        self.write_json(importer.MANIFEST, lambda d: d["files"][name].update(output_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "Manifest provenance"):
            importer.prepare(self.root, self.fetch)

    def test_canonical_paths(self):
        for name in ("../bad.png", "/bad.png", "x/../bad.png", "x//bad.png", "x\\bad.png", "x:bad.png", "", "./x.png"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                importer.canonical_name(name)

    def test_exact_apply_is_idempotent_and_does_not_touch_logs(self):
        log = self.root / "evidence/headless-battle-full.log.gz"
        log.parent.mkdir(); log.write_bytes(b"UNRELATED EXISTING LOG")
        verified, missing = importer.prepare(self.root, self.fetch)
        self.assertEqual(set(importer.apply_verified(self.root, verified, missing)), set(self.rows))
        before = {name: (self.root / name).stat().st_mtime_ns for name in self.rows}
        verified_again, missing_again = importer.prepare(self.root, lambda *args: self.fail("Repeated import fetched network"))
        self.assertEqual(importer.apply_verified(self.root, verified_again, missing_again), [])
        self.assertEqual(before, {name: (self.root / name).stat().st_mtime_ns for name in self.rows})
        self.assertEqual(log.read_bytes(), b"UNRELATED EXISTING LOG")

    def test_existing_modified_asset_is_preserved(self):
        name = next(iter(self.rows)); destination = self.root / name
        destination.parent.mkdir(parents=True); destination.write_bytes(b"USER MODIFIED")
        with self.assertRaisesRegex(ValueError, "byte count"):
            importer.prepare(self.root, self.fetch)
        self.assertEqual(destination.read_bytes(), b"USER MODIFIED"); self.assertEqual(self.calls, [])

    def test_symlink_ancestor_rejected(self):
        destination = self.root / "mods/kazakh_total_war/art/textures"
        outside = self.root / "other"; outside.mkdir()
        destination.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            importer.prepare(self.root, self.fetch)
        self.assertEqual(self.calls, [])

    def test_new_conflict_rejected_before_first_write(self):
        verified, missing = importer.prepare(self.root, self.fetch)
        name = list(self.rows)[-1]; destination = self.root / name
        destination.parent.mkdir(parents=True); destination.write_bytes(b"OTHER PROCESS")
        with self.assertRaisesRegex(ValueError, "Destination changed"):
            importer.apply_verified(self.root, verified, missing)
        self.assertFalse((self.root / next(iter(self.rows))).exists())
        self.assertEqual(destination.read_bytes(), b"OTHER PROCESS")

    def test_partial_prefetch_cannot_write(self):
        verified, missing = importer.prepare(self.root, self.fetch)
        verified.pop(next(iter(verified)))
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            importer.apply_verified(self.root, verified, missing)
        self.assert_no_assets()

    def test_git_stage_exact_png_set_and_bytes(self):
        self.init_git()
        verified, missing = importer.prepare(self.root, self.fetch)
        importer.apply_verified(self.root, verified, missing)
        importer.git(self.root, "add", "--", *missing)
        importer.assert_staged_assets(self.root, missing, verified)

    def test_extra_staged_file_blocks_commit(self):
        self.init_git()
        verified, missing = importer.prepare(self.root, self.fetch)
        importer.apply_verified(self.root, verified, missing)
        unexpected = self.root / "unexpected.exe"; unexpected.write_bytes(b"NOT A REAL EXE")
        importer.git(self.root, "add", "--", *missing, "unexpected.exe")
        with self.assertRaisesRegex(ValueError, "Staged set"):
            importer.assert_staged_assets(self.root, missing, verified)

    def test_branch_race_rejected_before_fetch_or_write(self):
        expected = "1" * 40
        def fake_git(root, *args, **kwargs):
            if args == ("rev-parse", "HEAD"):
                return expected
            if args == ("remote", "get-url", "origin"):
                return importer.ORIGIN
            self.fail("Unexpected Git command: " + repr(args))
        with patch.object(importer, "git", side_effect=fake_git), patch.object(importer, "remote_tip", return_value="2" * 40):
            with self.assertRaisesRegex(ValueError, "main moved"):
                importer.publish(self.root, expected, self.fetch)
        self.assertEqual(self.calls, []); self.assert_no_assets()

    def test_exact_origin_with_or_without_dot_git_is_accepted(self):
        expected = "1" * 40
        for origin in (importer.ORIGIN, importer.ORIGIN.removesuffix(".git")):
            with self.subTest(origin=origin):
                with patch.object(importer, "git", side_effect=[expected, origin]), patch.object(importer, "remote_tip", return_value=expected):
                    importer.require_expected_head(self.root, expected)

    def test_foreign_or_credential_bearing_origin_is_rejected(self):
        expected = "1" * 40
        for origin in ("https://github.com/other/repository.git", "https://token@github.com/azilkhan-1997/kazakh-total-war.git",
                       "https://example.com/azilkhan-1997/kazakh-total-war.git"):
            with self.subTest(origin=origin), patch.object(importer, "git", side_effect=[expected, origin]):
                with self.assertRaisesRegex(ValueError, "Unexpected repository"):
                    importer.require_expected_head(self.root, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
