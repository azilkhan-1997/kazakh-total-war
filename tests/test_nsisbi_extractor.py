# SPDX-License-Identifier: GPL-2.0-or-later
"""Container invariants for the bounded, offline R28 extraction tool.

Uses small self-generated LZMA streams; does not need a 1.6 GB download.
The original payload is separately verified by the committed runtime manifest.
"""
import importlib.util
import io
import lzma
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'ktw_nsisbi', Path(__file__).resolve().parents[1] / 'tools' / 'extract_r28_nsisbi.py')
EXTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXTRACT)


def frame(data):
    props = bytes([93]) + (1 << 20).to_bytes(4, 'little')
    compressed = lzma.compress(data, format=lzma.FORMAT_RAW, filters=[
        dict(id=lzma.FILTER_LZMA1, dict_size=1 << 20, lc=3, lp=0, pb=2)])
    payload = props + compressed
    return len(payload).to_bytes(3, 'little') + payload


class NSISBIExtractorTests(unittest.TestCase):
    def stream(self, data, end=None):
        return EXTRACT.SolidStream(io.BytesIO(data), len(data) if end is None else end)

    def test_read_across_independent_chunks_then_finish(self):
        data = frame(b'first') + frame(b'second') + b'\0\0\0'
        stream = self.stream(data)
        self.assertEqual(stream.read(8), b'firstsec')
        self.assertEqual(stream.read(3), b'ond')
        stream.finish()
        self.assertTrue(stream.ended)
        self.assertEqual((stream.chunks, stream.total, stream.pos), (2, 11, 11))

    def test_truncated_frame_fails_closed(self):
        data = frame(b'payload')[:-3]
        with self.assertRaises(ValueError):
            self.stream(data).read(7)

    def test_chunk_cannot_cross_declared_archive_boundary(self):
        data = frame(b'payload') + b'\0\0\0'
        with self.assertRaises(ValueError):
            self.stream(data, 9).read(7)

    def test_trailing_bytes_after_terminator_rejected(self):
        with self.assertRaises(ValueError):
            self.stream(b'\0\0\0unexpected').finish()

    def test_early_terminator_cannot_satisfy_file_length(self):
        with self.assertRaises(ValueError):
            self.stream(b'\0\0\0').read(1)

    def test_huge_lzma_dictionary_rejected_before_allocation(self):
        data = bytearray(frame(b'payload') + b'\0\0\0')
        data[4:8] = (0xffffffff).to_bytes(4, 'little')
        with self.assertRaisesRegex(ValueError, 'LZMA properties'):
            self.stream(bytes(data)).read(7)

    def test_lzma_trailing_payload_not_silently_accepted(self):
        block = frame(b'payload')
        length = int.from_bytes(block[:3], 'little') + 1
        data = length.to_bytes(3, 'little') + block[3:] + b'X' + b'\0\0\0'
        with self.assertRaises(ValueError):
            self.stream(data).read(7)

    def test_lzma_corruption_not_silently_accepted(self):
        data = bytearray(frame(b'payload' * 50) + b'\0\0\0')
        data[8] ^= 0xff
        with self.assertRaises((ValueError, lzma.LZMAError)):
            self.stream(bytes(data)).read(350)

    def test_compiled_string_requires_termination_and_bounds(self):
        with self.assertRaises(ValueError):
            EXTRACT.decode_string(b'a\0', 0)
        with self.assertRaises(ValueError):
            EXTRACT.decode_string(b'\0\0', 2)

    def test_unsupported_string_control_fails_closed(self):
        with self.assertRaises(ValueError):
            EXTRACT.decode_string(b'\x01\0\x80\x80\0\0', 0)

    def test_wrong_installer_hash_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'modified.exe'
            target = Path(directory) / 'output'
            source.write_bytes(b'changed')
            with patch.object(EXTRACT, 'EXPECTED_BYTES', 7), patch('sys.argv', [
                    'extract_r28_nsisbi.py', str(source), str(target)]):
                with self.assertRaisesRegex(ValueError, 'SHA256'):
                    EXTRACT.main()
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
