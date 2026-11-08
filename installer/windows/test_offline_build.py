#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Portable regression checks for rejection of incomplete offline build inputs."""
from pathlib import Path
import hashlib
import tempfile
import unittest
from types import SimpleNamespace
import build_offline_qa as build


class OfflineInputContracts(unittest.TestCase):
    def test_private_qa_mode_required_before_any_build(self):
        with self.assertRaisesRegex(ValueError, '--private-qa-only'):
            build.build(SimpleNamespace(private_qa_only=False))

    def test_output_outside_temporary_root_is_rejected(self):
        args = SimpleNamespace(private_qa_only=True, project=Path(__file__).parent,
                               launcher=Path('/not-executed.exe'), output=Path('/not-created.exe'))
        with self.assertRaisesRegex(ValueError, 'must remain under'):
            build.build(args)

    def test_valid_component(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.bin'; p.write_bytes(b'offline')
            self.assertEqual(build.verify_component(p, 'test.bin', 7, hashlib.sha256(b'offline').hexdigest())['bytes'], 7)

    def test_missing_component_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'Missing'):
                build.verify_component(Path(d) / 'missing.bin', 'missing.bin', 7, '0' * 64)

    def test_same_size_tampering_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.bin'; p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                build.verify_component(p, 'test.bin', 7, hashlib.sha256(b'offline').hexdigest())

    def test_wrong_size_fails_before_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.bin'; p.write_bytes(b'x')
            with self.assertRaisesRegex(ValueError, 'size'):
                build.verify_component(p, 'test.bin', 7, '0' * 64)

    def test_symlink_component_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'real.bin'; p.write_bytes(b'offline')
            link = Path(d) / 'linked.bin'; link.symlink_to(p)
            with self.assertRaisesRegex(ValueError, 'linked'):
                build.verify_component(link, 'linked.bin', 7, hashlib.sha256(b'offline').hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)
