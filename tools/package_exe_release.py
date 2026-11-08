#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Package the original 0.4 installer, launcher and their complete editable source.

Run after committing source and verifying the final installer, for example:
  python3 tools/package_exe_release.py --launcher dist/windows/KazakhTotalWar.exe \
    --installer dist/KazakhTotalWar_Setup_0.4.0.exe \
    --report dist/installer-build.json --report dist/installer-build.log \
    --baseline-evidence /path/to/verified/v0.3/evidence \
    --baseline-archive /path/to/KAZAKH_TOTAL_WAR_Pyrogenesis_Prototype_v0.3.zip

Only explicitly selected own executables and JSON/log/MD/txt reports are added.
No downloaded engine, Python, Microsoft runtime, compiler or vendor directory
is packaged. The full ZIP includes preserved evidence and a verified Git
bundle. The web ZIP omits only evidence images/video, the installer executable
and Git bundle; it retains editable art, code, genuine saves and QA fixtures.
Packaging and integrity checks do not constitute native Windows acceptance.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'KAZAKH_TOTAL_WAR_Source/'
STAMP = (2026, 11, 8, 0, 0, 0)
BASELINE_ARCHIVE_SHA256 = '820c924ef89c748ca8cbc5e34fba5fabc7e9fe65240a2384354470e4bfa03fd8'
EVIDENCE_MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tga', '.tif', '.tiff',
                  '.mp4', '.mov', '.mkv', '.webm', '.avi', '.mpeg', '.mpg', '.m4v'}
REPORT_SUFFIXES = {'.json', '.log', '.md', '.txt'}
FORBIDDEN_SOURCE_SUFFIXES = {'.exe', '.dll', '.so', '.a', '.lib', '.o', '.obj', '.pdb',
    '.deb', '.msi', '.whl', '.7z', '.zip', '.pyromod', '.pyc', '.bundle'}
FORBIDDEN_SOURCE_ROOTS = {'dist', 'runtime', 'upstream', 'vendor', 'vendors', 'toolchain',
                        'node_modules', '.build', '.venv', 'venv'}

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def safe_name(name):
    path = PurePosixPath(name)
    devices = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{p}{i}' for p in ('COM', 'LPT') for i in range(1, 10)}
    if (not name or not path.parts or path.is_absolute() or name != path.as_posix()
            or '..' in path.parts or '\\' in name or ':' in name
            or any(ord(c) < 32 or c in '<>"|?*' for c in name)
            or any(p.endswith((' ', '.')) or p.split('.')[0].upper() in devices for p in path.parts)):
        raise ValueError('Unsafe or ambiguous archive path: ' + name)
    return name

@dataclass(frozen=True)
class Item:
    data: bytes
    mode: int = 0o100644
    origin: str = 'tracked source'

def read_regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular non-symlink file: ' + str(path))
    return path.read_bytes()

def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)

def require_clean(root):
    if git(root, 'status', '--porcelain', '--untracked-files=normal').strip():
        raise ValueError('Commit all project source changes before packaging; working tree must be clean')
    return git(root, 'rev-parse', 'HEAD').decode().strip()

def is_evidence_media(name):
    return name.startswith('evidence/') and PurePosixPath(name).suffix.lower() in EVIDENCE_MEDIA

def allowed_source(name):
    safe_name(name)
    path = PurePosixPath(name)
    if path.parts[0].lower() in FORBIDDEN_SOURCE_ROOTS or path.suffix.lower() in FORBIDDEN_SOURCE_SUFFIXES:
        raise ValueError('Unexpected binary, bundle or vendor payload tracked as source: ' + name)
    if name.lower().endswith(('.tar.gz', '.tar.xz', '.tar.bz2')):
        raise ValueError('Downloaded source/vendor archive must not be nested in this release: ' + name)

def collect_tracked(root):
    result = {}
    for record in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if not record:
            continue
        header, raw_name = record.split(b'\t', 1)
        mode, blob, stage = header.decode('ascii').split()
        name = raw_name.decode('utf-8')
        allowed_source(name)
        if stage != '0' or mode not in ('100644', '100755'):
            raise ValueError('Unmerged entry, symlink or submodule is not a complete source file: ' + name)
        data = read_regular(root / name)
        # A clean status alone could miss a transient replacement during a
        # concurrent build. Snapshot bytes must match the Git index blob.
        digest = hashlib.new('sha256' if len(blob) == 64 else 'sha1')
        digest.update(b'blob ' + str(len(data)).encode() + b'\0' + data)
        if digest.hexdigest() != blob:
            raise ValueError('Working bytes do not match the committed source blob: ' + name)
        result[name] = Item(data, int(mode, 8))
    if not result:
        raise ValueError('Git index is empty')
    return result

def evidence_provenance(source, directory, archive=None):
    if archive and directory is None:
        raise ValueError('--baseline-archive requires --baseline-evidence')
    if directory is None:
        return None
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Baseline evidence must be an existing non-symlink directory')
    reference = None
    if archive:
        archive_data = read_regular(archive)
        if sha256(archive_data) != BASELINE_ARCHIVE_SHA256:
            raise ValueError('Baseline source archive differs from the authoritative v0.3 SHA-256')
        reference = zipfile.ZipFile(io.BytesIO(archive_data))
    rows = []
    added = 0
    try:
        for path in sorted(directory.rglob('*')):
            relative = path.relative_to(directory)
            if '__pycache__' in relative.parts or path.suffix == '.pyc' or any(
                    p.startswith('.') or '.partial' in p for p in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError('Symlink in baseline evidence: ' + str(relative))
            if not path.is_file():
                continue
            name = 'evidence/' + relative.as_posix()
            allowed_source(name)
            data = read_regular(path)
            if reference is not None:
                original = reference.read('KAZAKH_TOTAL_WAR_Prototype/' + name)
                if original != data:
                    raise ValueError('Baseline evidence differs from authoritative ZIP: ' + name)
            if name in source and source[name].data != data:
                raise ValueError('Tracked and baseline evidence conflict: ' + name)
            if name not in source:
                source[name] = Item(data, origin='preserved v0.3 evidence')
                added += 1
            rows.append({'path': name, 'bytes': len(data), 'sha256': sha256(data)})
        if reference is not None:
            prefix = 'KAZAKH_TOTAL_WAR_Prototype/'
            expected = {name[len(prefix):] for name in reference.namelist()
                        if name.startswith(prefix + 'evidence/') and not name.endswith('/')}
            if {row['path'] for row in rows} != expected:
                raise ValueError('Baseline evidence directory is incomplete or has extra files compared with the authoritative archive')
    finally:
        if reference is not None:
            reference.close()
    return {'authoritative_v03_archive_sha256': BASELINE_ARCHIVE_SHA256,
            'archive_and_evidence_verified_by_this_packager': archive is not None,
            'manifest_sha256': sha256(json_bytes(rows)), 'files': rows, 'newly_merged_files': added,
            'note': 'Directory manifest is verified against the authoritative ZIP only when --baseline-archive is supplied.'}

def validate_pe(data, label, require_amd64=False):
    if len(data) < 64 or data[:2] != b'MZ':
        raise ValueError(label + ' is not a PE executable')
    offset = struct.unpack_from('<I', data, 60)[0]
    if offset + 26 > len(data) or data[offset:offset+4] != b'PE\0\0':
        raise ValueError(label + ' has an invalid PE header')
    machine = struct.unpack_from('<H', data, offset + 4)[0]
    magic = struct.unpack_from('<H', data, offset + 24)[0]
    if require_amd64 and (machine != 0x8664 or magic != 0x20b):
        raise ValueError(label + ' must be AMD64 PE32+')
    if (machine, magic) not in ((0x8664, 0x20b), (0x14c, 0x10b)):
        raise ValueError(label + ' has an unsupported PE architecture')
    return {'machine': hex(machine), 'optional_header_magic': hex(magic), 'execution_tested': False}

def add(source, name, item):
    safe_name(name)
    if name in source:
        raise ValueError('Generated artifact collides with source file: ' + name)
    source[name] = item

def validate_names(items):
    folded = set()
    for name in items:
        safe_name(name)
        key = name.casefold()
        if key in folded:
            raise ValueError('Case-insensitive archive collision: ' + name)
        folded.add(key)
    for name in items:
        if any(p.as_posix().casefold() in folded for p in PurePosixPath(name).parents if p.as_posix() != '.'):
            raise ValueError('Archive file/directory collision: ' + name)

def atomic_zip(output, items):
    validate_names(items)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + output.name + '.', suffix='.partial', dir=output.parent)
    staging = Path(temporary)
    os.close(fd)
    try:
        with zipfile.ZipFile(staging, 'w', zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as z:
            for name, item in sorted(items.items()):
                info = zipfile.ZipInfo(PREFIX + name, STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = item.mode << 16
                z.writestr(info, item.data)
        with staging.open('rb') as stream:
            os.fsync(stream.fileno())
        with zipfile.ZipFile(staging) as z:
            bad = z.testzip()
            if bad:
                raise ValueError('Staged ZIP CRC failed: ' + bad)
            for name, item in items.items():
                if sha256(z.read(PREFIX + name)) != sha256(item.data):
                    raise ValueError('Archived file hash differs from source snapshot: ' + name)
        os.replace(staging, output)
    finally:
        if staging.exists():
            staging.unlink()
    payload = output.read_bytes()
    return {'file': output.name, 'bytes': len(payload), 'sha256': sha256(payload),
            'entries': len(items), 'crc_verified': True, 'every_member_sha256_verified': True}

def atomic_json(output, data):
    fd, temporary = tempfile.mkstemp(prefix='.' + output.name + '.', suffix='.partial', dir=output.parent)
    staging = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(json_bytes(data)); stream.flush(); os.fsync(stream.fileno())
        os.replace(staging, output)
    finally:
        if staging.exists(): staging.unlink()

def with_manifest(source):
    rows = [{'path': name, 'bytes': len(item.data), 'sha256': sha256(item.data),
             'mode': oct(item.mode), 'origin': item.origin} for name, item in sorted(source.items())]
    output = dict(source)
    add(output, 'PACKAGED_FILES.json', Item(json_bytes({'format': 1, 'files': rows,
        'scope': 'Every archive file except this self-referential manifest.'}), origin='generated manifest'))
    return output

def package(args, root=ROOT):
    revision = require_clean(root)
    source = collect_tracked(root)
    module = json.loads(source['mods/kazakh_total_war/mod.json'].data)
    campaign = source['mods/kazakh_total_war/simulation/helpers/KtwCampaign.js'].data.decode('utf-8')
    if module.get('version') != '0.2.0' or module.get('dependencies') != ['0ad=0.28.0'] or not re.search(r'var VERSION\s*=\s*2\s*;', campaign):
        raise ValueError('Expected unchanged module 0.2.0 / R28 / save schema 2')
    provenance = evidence_provenance(source, args.baseline_evidence, args.baseline_archive)
    launcher = read_regular(args.launcher)
    installer = read_regular(args.installer)
    launcher_pe = validate_pe(launcher, 'Own game launcher', require_amd64=True)
    installer_pe = validate_pe(installer, 'Own setup executable')
    if args.launcher.resolve() == args.installer.resolve() or sha256(launcher) == sha256(installer):
        raise ValueError('Launcher and installer must be separate original executables')
    installer_name = safe_name(args.installer.name)
    if not installer_name.lower().endswith('.exe'):
        raise ValueError('Installer filename must end in .exe')
    add(source, 'release/KazakhTotalWar.exe', Item(launcher, origin='compiled own launcher'))
    inputs = {
        'launcher': {'file': 'KazakhTotalWar.exe', 'bytes': len(launcher), 'sha256': sha256(launcher), 'pe': launcher_pe},
        'installer': {'file': installer_name, 'bytes': len(installer), 'sha256': sha256(installer), 'pe': installer_pe}}
    report_rows = []
    for report in args.report:
        if report.suffix.lower() not in REPORT_SUFFIXES:
            raise ValueError('Reports must be JSON/log/MD/txt, not binaries or vendor archives: ' + str(report))
        data = read_regular(report)
        decoded = data.decode('utf-8-sig')
        if '\0' in decoded:
            raise ValueError('Report contains NUL bytes; binary/UTF-16 payload is not an allowed UTF-8 report: ' + str(report))
        if report.suffix.lower() == '.json':
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                for artifact in inputs.values():
                    if parsed.get('file', parsed.get('executable')) == artifact['file'] and 'sha256' in parsed:
                        if parsed['sha256'].lower() != artifact['sha256']:
                            raise ValueError('Build report does not match selected executable: ' + str(report))
        name = 'release/reports/' + report.name
        add(source, name, Item(data, origin='explicit build/QA report'))
        report_rows.append({'path': name, 'bytes': len(data), 'sha256': sha256(data)})
    if provenance is not None:
        add(source, 'BASELINE_EVIDENCE_MANIFEST.json', Item(json_bytes(provenance), origin='preserved evidence provenance'))
    with tempfile.TemporaryDirectory(prefix='ktw-source-bundle-') as temporary:
        bundle = Path(temporary) / 'KAZAKH_TOTAL_WAR_Source.git.bundle'
        subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=root, check=True, capture_output=True)
        subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=root, check=True, capture_output=True)
        bundle_data = bundle.read_bytes()
    if require_clean(root) != revision:
        raise ValueError('Source revision changed during packaging; retry from a stable committed tree')
    common = {'deliveryVersion': '0.4.0', 'moduleVersion': '0.2.0', 'saveSchemaVersion': 2,
        'sourceRevision': revision, 'engineRequirement': '0ad=0.28.0',
        'native_windows_install_tested': False, 'native_windows_gameplay_tested': False,
        'nativeWindowsExecutionTested': False, 'steamAccepted': False,
        'upstreamRuntimePythonVcOrToolchainRedistributed': False,
        'artifactInputs': inputs, 'explicitReports': report_rows,
        'baselineEvidenceManifestSha256': provenance['manifest_sha256'] if provenance else None,
        'scope': 'Original source and own build artifacts; static packaging checks only, not Windows acceptance.'}
    results = []
    for variant, filename in [('full', 'KAZAKH_TOTAL_WAR_Source_v0.4.zip'),
                              ('web', 'KAZAKH_TOTAL_WAR_Source_Web_v0.4.zip')]:
        omitted = [name for name in sorted(source) if variant == 'web' and is_evidence_media(name)]
        items = {name: item for name, item in source.items() if name not in omitted}
        if variant == 'full':
            add(items, 'KAZAKH_TOTAL_WAR_Source.git.bundle', Item(bundle_data, origin='verified complete Git bundle'))
            add(items, 'release/' + installer_name, Item(installer, origin='compiled own installer'))
        metadata = dict(common, variant=variant, omittedHistoricalEvidenceMedia=omitted,
                        gitBundleIncluded=variant == 'full', installerExecutableIncluded=variant == 'full',
                        originalLauncherIncluded=True)
        add(items, 'RELEASE.json', Item(json_bytes(metadata), origin='generated exact-revision release metadata'))
        result = atomic_zip(args.output_dir / filename, with_manifest(items))
        result['variant'] = variant
        results.append(result)
    if require_clean(root) != revision:
        raise ValueError('Source changed after snapshots were packaged; do not publish until reviewed')
    result = {'deliveryVersion': '0.4.0', 'moduleVersion': '0.2.0', 'saveSchemaVersion': 2,
              'sourceRevision': revision, 'native_windows_install_tested': False,
              'archives': results, 'artifactInputs': inputs,
              'baselineEvidenceManifestSha256': provenance['manifest_sha256'] if provenance else None}
    atomic_json(args.output_dir / 'SOURCE_RELEASE_SHA256.json', result)
    return result

class SelfTests(unittest.TestCase):
    def test_paths_and_collisions(self):
        for name in ['../x', '/x', 'a\\b', 'a/./b', 'CON.txt', 'file.', 'a:x', 'x\0y']:
            with self.subTest(name=name), self.assertRaises(ValueError): safe_name(name)
        for names in [('a', 'A'), ('a', 'a/b')]:
            with self.assertRaises(ValueError): validate_names({n: Item(b'x') for n in names})

    def test_only_evidence_media_is_omitted(self):
        self.assertTrue(is_evidence_media('evidence/v0.2/screen.png'))
        for name in ['mods/kazakh_total_war/art/texture.png', 'evidence/saves/a.0adsave',
                     'evidence/native-fixture/simulation/component.js', 'evidence/state.json', 'evidence/run.log.gz']:
            self.assertFalse(is_evidence_media(name))

    def test_vendor_and_binary_source_rejected(self):
        for name in ['runtime/a.txt', 'upstream/source.cpp', 'tools/python.exe', 'x/vendor.tar.xz', 'old.git.bundle']:
            with self.assertRaises(ValueError): allowed_source(name)
        allowed_source('mods/kazakh_total_war/art/texture.png')
        allowed_source('evidence/saves/battle.0adsave')

    def test_evidence_duplicate_protection_and_preserved_save(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'save.0adsave').write_bytes(b'save'); (root / 'state.json').write_bytes(b'{}')
            source = {'evidence/state.json': Item(b'wrong')}
            with self.assertRaises(ValueError): evidence_provenance(source, root)
            source = {'evidence/state.json': Item(b'{}')}
            report = evidence_provenance(source, root)
            self.assertEqual(source['evidence/save.0adsave'].data, b'save')
            self.assertEqual(report['newly_merged_files'], 1)

    def test_atomic_failure_keeps_previous_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'release.zip'; out.write_bytes(b'previous archive')
            with patch('os.replace', side_effect=OSError('simulated publish failure')):
                with self.assertRaises(OSError): atomic_zip(out, {'README.md': Item(b'new')})
            self.assertEqual(out.read_bytes(), b'previous archive')
            self.assertEqual(list(Path(folder).glob('*.partial')), [])

    def test_deterministic_zip_and_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            items = with_manifest({'tools/run.sh': Item(b'#!/bin/sh\n', 0o100755), 'mods/art.png': Item(b'asset')})
            first = atomic_zip(root / 'one.zip', items); second = atomic_zip(root / 'two.zip', items)
            self.assertEqual(first['sha256'], second['sha256'])
            with zipfile.ZipFile(root / 'one.zip') as z:
                manifest = json.loads(z.read(PREFIX + 'PACKAGED_FILES.json'))
                self.assertEqual(len(manifest['files']), 2)
                self.assertEqual(z.getinfo(PREFIX + 'tools/run.sh').external_attr >> 16, 0o100755)

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--launcher', type=Path, help='Already-built original AMD64 KazakhTotalWar.exe')
    parser.add_argument('--installer', type=Path, help='Already-built original 0.4 setup EXE; full source kit only')
    parser.add_argument('--report', type=Path, action='append', default=[], help='Explicit UTF-8 JSON/log/MD/txt build or QA report; repeatable')
    parser.add_argument('--baseline-evidence', type=Path, help='Verified v0.3 evidence directory to merge, including ignored native saves/media')
    parser.add_argument('--baseline-archive', type=Path, help='Optional authoritative v0.3 ZIP, pinned SHA-256, to verify baseline evidence bytes')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist', help='Output directory (default: project dist)')
    parser.add_argument('--self-test', action='store_true', help='Run isolated packager tests without building a release')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests))
        return 0 if result.wasSuccessful() else 1
    if not args.launcher or not args.installer:
        parser.error('--launcher and --installer are required for packaging')
    print(json.dumps(package(args), ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
