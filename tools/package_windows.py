#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a Windows bootstrap kit, or a local complete-runtime QA candidate.

No execution or Windows acceptance is implied by packaging. Large files are
streamed; a completed ZIP replaces its output only after CRC validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STAMP = (2026, 11, 8, 0, 0, 0)
ENGINE_SOURCE_SHA = '27e217755ef76a922fe58dbf593d96e54b6ed2375d23f548c35619aa6bd5a42a'
ENGINE_EXE_SHA = '11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f'

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def pe_machine(path):
    with Path(path).open('rb') as stream:
        header = stream.read(64)
        if len(header) != 64 or header[:2] != b'MZ':
            raise ValueError('Not a Windows PE executable: ' + str(path))
        stream.seek(struct.unpack_from('<I', header, 60)[0])
        pe = stream.read(26)
    if len(pe) != 26 or pe[:4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    machine, magic = struct.unpack_from('<H', pe, 4)[0], struct.unpack_from('<H', pe, 24)[0]
    if machine != 0x8664 or magic != 0x20b:
        raise ValueError('Expected AMD64 PE32+ executable')
    return machine

def safe_name(name):
    p = PurePosixPath(name)
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {'COM' + str(n) for n in range(1, 10)} | {'LPT' + str(n) for n in range(1, 10)}
    if (not name or p.is_absolute() or name != p.as_posix() or '..' in p.parts or
            '\\' in name or ':' in name or not p.parts or
            any(ord(c) < 32 or c in '<>"|?*' for c in name) or
            any(part.endswith((' ', '.')) or part.split('.')[0].upper() in reserved for part in p.parts)):
        raise ValueError('Unsafe archive path: ' + name)
    return p.as_posix()

def add_tree(items, prefix, directory, omit_symbols=False):
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError('Required directory does not exist: ' + str(directory))
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks are not supported in portable packages: ' + str(path))
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if omit_symbols and path.suffix.lower() == '.pdb':
            continue
        if rel.lower().startswith(('binaries/data/saves/', 'binaries/data/cache/')):
            raise ValueError('Runtime contains user saves/cache; use a clean extraction')
        items.append((safe_name(prefix + '/' + rel), path))

def write_archive(output, items):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    names = [safe_name(name) for name, _ in items]
    if len(set(name.casefold() for name in names)) != len(names):
        raise ValueError('Duplicate Windows archive path')
    folded = {name.casefold() for name in names}
    for name in names:
        if any(parent.as_posix().casefold() in folded for parent in PurePosixPath(name).parents if parent.as_posix() != '.'):
            raise ValueError('Archive file/directory collision: ' + name)
    staging = output.with_name(output.name + '.partial')
    with zipfile.ZipFile(staging, 'w', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for name, source in sorted(items, key=lambda row: row[0]):
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            with z.open(info, 'w', force_zip64=True) as dest:
                if isinstance(source, bytes):
                    dest.write(source)
                else:
                    with source.open('rb') as stream:
                        while chunk := stream.read(8 * 1024 * 1024):
                            dest.write(chunk)
            print('Packed ' + name, flush=True)
    with staging.open('rb') as stream:
        os.fsync(stream.fileno())
    with zipfile.ZipFile(staging) as check:
        failed = check.testzip()
        if failed:
            raise ValueError('ZIP CRC failed: ' + failed)
    os.replace(staging, output)
    return {'file': output.name, 'bytes': output.stat().st_size, 'sha256': sha256(output)}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime', type=Path, help='Local QA candidate only; redistribution audit remains open')
    ap.add_argument('--launcher', type=Path, required=True)
    ap.add_argument('--engine-source', type=Path)
    ap.add_argument('--source-kit', type=Path, required=True)
    ap.add_argument('--prerequisite', type=Path)
    ap.add_argument('--dependency-sources', type=Path)
    ap.add_argument('--output', type=Path, default=ROOT / 'dist/KAZAKH_TOTAL_WAR_Windows_Setup_v0.3.zip')
    args = ap.parse_args()
    pe_machine(args.launcher)
    mod = json.loads((ROOT / 'mods/kazakh_total_war/mod.json').read_text())
    if mod.get('dependencies') != ['0ad=0.28.0']:
        raise ValueError('Release 28 dependency validation failed')
    if args.runtime:
        runtime = args.runtime.resolve()
        engine = runtime / 'binaries/system/pyrogenesis.exe'
        pe_machine(engine)
        if sha256(engine) != ENGINE_EXE_SHA:
            raise ValueError('Engine differs from verified official R28 extraction')
        if not args.engine_source or sha256(args.engine_source) != ENGINE_SOURCE_SHA:
            raise ValueError('Full local QA candidate requires matching engine source archive')
        base = json.loads((runtime / 'binaries/data/mods/public/mod.json').read_text())
        if base.get('name') != '0ad' or base.get('version') != '0.28.0':
            raise ValueError('Release 28 metadata mismatch')
        for name in ['public/public.zip', 'mod/mod.zip']:
            with zipfile.ZipFile(runtime / 'binaries/data/mods' / name) as z:
                if z.testzip():
                    raise ValueError('Original runtime data archive failed CRC')
    with zipfile.ZipFile(args.source_kit) as z:
        source_release = json.loads(z.read('KAZAKH_TOTAL_WAR_Prototype/RELEASE.json'))
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('Commit project changes before producing a source-matched distribution')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if source_release['source_revision'] != revision:
        raise ValueError('Source kit is not from the current source revision')
    prefix = 'KAZAKH_TOTAL_WAR_Windows'
    items = []
    if args.runtime:
        add_tree(items, prefix + '/runtime', runtime, omit_symbols=False)
        add_tree(items, prefix + '/runtime/binaries/data/mods/kazakh_total_war', ROOT / 'mods/kazakh_total_war')
        items.append((prefix + '/source/0ad-0.28.0-unix-build.tar.xz', args.engine_source))
        if args.prerequisite:
            items.append((prefix + '/prerequisites/VC_redist.x64.exe', args.prerequisite))
        if args.dependency_sources:
            add_tree(items, prefix + '/source/windows-dependencies', args.dependency_sources)
    else:
        add_tree(items, prefix + '/mods/kazakh_total_war', ROOT / 'mods/kazakh_total_war')
    items.extend([
        (prefix + '/KazakhTotalWar.exe', args.launcher),
        (prefix + '/Setup-Windows.cmd', ROOT / 'Setup-Windows.cmd'),
        (prefix + '/README_WINDOWS_RU.md', ROOT / 'docs/README_WINDOWS_RU.md'),
        (prefix + '/WINDOWS_DISTRIBUTION_NOTICES.md', ROOT / 'docs/WINDOWS_DISTRIBUTION_NOTICES.md'),
        (prefix + '/THIRD_PARTY_NOTICES.md', ROOT / 'THIRD_PARTY_NOTICES.md'),
        (prefix + '/launcher/windows/THIRD_PARTY_NOTICES.md', ROOT / 'launcher/windows/THIRD_PARTY_NOTICES.md'),
        (prefix + '/LICENSE_KTW.txt', ROOT / 'LICENSE'),
        (prefix + '/source/' + args.source_kit.name, args.source_kit),
    ])
    for name in ['Test-Windows.ps1', 'Import-LegacySaves.ps1', 'import_legacy_saves.py',
                 'Install-WindowsRuntime.ps1', 'extract_r28_nsisbi.py']:
        items.append((prefix + '/tools/' + name, ROOT / 'tools' / name))
    for name in ['windows-runtime-manifest.json', 'asset-manifest-millennium.json', 'windows-acceptance-checklist.md']:
        items.append((prefix + '/docs/' + name, ROOT / 'docs' / name))
    add_tree(items, prefix + '/LICENSES_KTW', ROOT / 'LICENSES')
    add_tree(items, prefix + '/launcher/windows/LICENSES', ROOT / 'launcher/windows/LICENSES')
    manifest = {
        'releaseVersion': '0.3.0', 'moduleVersion': mod['version'], 'engineVersion': '0.28.0',
        'sourceRevision': revision, 'nativeWindowsExecutionTested': False,
        'wineExecutionTested': False, 'steamAccepted': False,
        'deliveryType': 'local-runtime-qa-candidate' if args.runtime else 'bootstrap',
        'status': 'Windows execution untested; first setup requires CPython 3.11+ and official downloads',
        'portableProfile': 'runtime/binaries/data',
        'omitted': [] if args.runtime else ['Upstream runtime and Microsoft binaries are downloaded from their official publishers during setup'],
        'files': []
    }
    for name, path in items:
        manifest['files'].append({'path': name[len(prefix) + 1:], 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    items.append((prefix + '/BUILD_MANIFEST.json', (json.dumps(manifest, indent=2) + '\n').encode()))
    result = write_archive(args.output, items)
    result['source_revision'] = revision
    args.output.with_suffix('.sha256.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
