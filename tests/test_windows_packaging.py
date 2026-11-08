# SPDX-License-Identifier: GPL-2.0-or-later
"""Portable Windows ZIP integrity and rejection behavior using tiny fixtures."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

SPEC = importlib.util.spec_from_file_location(
    'ktw_windows_package', Path(__file__).resolve().parents[1] / 'tools' / 'package_windows.py')
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)


def pe_fixture(machine=0x8664, magic=0x20b, offset=64):
    data = bytearray(max(64, offset + 26))
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, offset)
    data[offset:offset+4] = b'PE\0\0'
    struct.pack_into('<H', data, offset+4, machine)
    struct.pack_into('<H', data, offset+24, magic)
    return bytes(data)


class WindowsPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'delivery.zip'
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def existing_output(self):
        with zipfile.ZipFile(self.output, 'w') as z:
            z.writestr('previous-release.txt', b'unchanged known good release')
        return self.output.read_bytes()

    def test_rejects_path_traversal_and_windows_absolute_forms(self):
        for name in ('', '../outside', 'a/../../outside', '/rooted', 'C:/outside',
                     'folder\\outside', '\\\\server\\share', 'dir/file:stream'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                PACKAGE.write_archive(self.output, [(name, b'bad')])
        self.assertFalse(self.output.exists())
        self.assertFalse(self.output.with_name('delivery.zip.partial').exists())

    def test_rejects_windows_non_file_and_ambiguous_names(self):
        for name in ('.', 'folder/.', 'NUL', 'con.txt', 'folder/AUX', 'LPT1.log',
                     'folder/trailing.', 'folder/trailing ', 'bad\x00name', 'bad\nname'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                PACKAGE.safe_name(name)

    def test_rejects_case_insensitive_duplicates_before_staging(self):
        old = self.existing_output()
        with self.assertRaises(ValueError):
            PACKAGE.write_archive(self.output, [('runtime/A.dll', b'a'), ('Runtime/a.DLL', b'b')])
        self.assertEqual(self.output.read_bytes(), old)
        self.assertFalse(self.output.with_name('delivery.zip.partial').exists())

    def test_rejects_normalized_path_duplicates(self):
        with self.assertRaises(ValueError):
            PACKAGE.write_archive(self.output, [('runtime/a', b'a'), ('runtime/./a', b'b')])

    def test_rejects_file_directory_collisions(self):
        with self.assertRaises(ValueError):
            PACKAGE.write_archive(self.output, [('Runtime', b'a'), ('runtime/engine.exe', b'b')])

    def test_noncanonical_paths_rejected(self):
        for name in ('runtime/./engine.exe', 'runtime//engine.exe', 'runtime/'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                PACKAGE.write_archive(self.output, [(name, b'fixture')])

    def test_accepts_amd64_pe32_plus_header(self):
        path = self.root / 'fixture.exe'
        path.write_bytes(pe_fixture())
        self.assertEqual(PACKAGE.pe_machine(path), 0x8664)

    def test_rejects_wrong_machine_optional_header_and_truncation(self):
        path = self.root / 'fixture.exe'
        bad = [b'not an executable', pe_fixture(0x14c, 0x10b), pe_fixture(0xaa64),
               pe_fixture(magic=0x10b), pe_fixture()[:-1], b'MZ'+b'\0'*62]
        for data in bad:
            with self.subTest(data=data[:8]):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    PACKAGE.pe_machine(path)

    def test_zip_crc_hash_and_atomic_replace(self):
        old = self.existing_output()
        payload = self.root / 'file.bin'
        payload.write_bytes(bytes(range(256)) * 3)
        events = []
        real_replace = os.replace
        def observed_replace(source, target):
            self.assertEqual(Path(target).read_bytes(), old)
            with zipfile.ZipFile(source) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read('runtime/file.bin'), payload.read_bytes())
                self.assertEqual(z.read('README.txt'), b'new release')
            events.append('verified before replacement')
            return real_replace(source, target)
        with patch.object(PACKAGE.os, 'replace', side_effect=observed_replace):
            result = PACKAGE.write_archive(self.output, [('runtime/file.bin', payload), ('README.txt', b'new release')])
        self.assertEqual(events, ['verified before replacement'])
        self.assertEqual(result['sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(result['bytes'], self.output.stat().st_size)
        self.assertFalse(self.output.with_name('delivery.zip.partial').exists())

    def test_source_read_error_preserves_previous_release(self):
        old = self.existing_output()
        with self.assertRaises(OSError):
            PACKAGE.write_archive(self.output, [('a.txt', b'already written'), ('missing', self.root / 'absent')])
        self.assertEqual(self.output.read_bytes(), old)
        with zipfile.ZipFile(self.output) as z:
            self.assertIsNone(z.testzip())

    def test_actual_staging_corruption_never_replaces_previous_release(self):
        old = self.existing_output()
        staging = self.output.with_name('delivery.zip.partial')
        def corrupt_after_write(_fd):
            with zipfile.ZipFile(staging) as archive:
                info = archive.getinfo('payload.bin')
            with staging.open('r+b') as stream:
                stream.seek(info.header_offset+26)
                name_len, extra_len = struct.unpack('<HH', stream.read(4))
                data_offset = info.header_offset+30+name_len+extra_len
                stream.seek(data_offset+info.compress_size//2)
                value = stream.read(1)
                stream.seek(-1, 1)
                stream.write(bytes([value[0] ^ 0xff]))
        with patch.object(PACKAGE.os, 'fsync', side_effect=corrupt_after_write):
            with self.assertRaises((ValueError, zipfile.BadZipFile, zlib.error)):
                PACKAGE.write_archive(self.output, [('payload.bin', bytes(range(256))*20)])
        self.assertEqual(self.output.read_bytes(), old)

    def test_replace_failure_preserves_previous_release(self):
        old = self.existing_output()
        with patch.object(PACKAGE.os, 'replace', side_effect=PermissionError('read-only destination')):
            with self.assertRaises(PermissionError):
                PACKAGE.write_archive(self.output, [('new.txt', b'valid replacement')])
        self.assertEqual(self.output.read_bytes(), old)

    def test_runtime_tree_omits_symbols_and_rejects_saves(self):
        directory = self.root/'runtime'
        directory.mkdir()
        (directory/'engine.dll').write_bytes(b'dll')
        (directory/'debug.PDB').write_bytes(b'symbols')
        items = []
        PACKAGE.add_tree(items, 'runtime', directory, omit_symbols=True)
        self.assertEqual([name for name, _ in items], ['runtime/engine.dll'])
        savedir = directory/'binaries/data/saves'
        savedir.mkdir(parents=True)
        (savedir/'private-save.0adsave').write_bytes(b'user data')
        with self.assertRaises(ValueError):
            PACKAGE.add_tree([], 'runtime', directory)

    def test_explicit_missing_tree_cannot_silently_omit_files(self):
        with self.assertRaises((OSError, ValueError)):
            PACKAGE.add_tree([], 'source/dependencies', self.root/'misspelled-dependencies')

    def test_runtime_tree_rejects_symlink(self):
        directory = self.root/'runtime'
        directory.mkdir()
        source = self.root/'external-secret'
        source.write_bytes(b'outside')
        (directory/'link').symlink_to(source)
        with self.assertRaises(ValueError):
            PACKAGE.add_tree([], 'runtime', directory)


if __name__ == '__main__':
    unittest.main()
