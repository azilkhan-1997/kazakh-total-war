#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a PRIVATE offline QA EXE, never a cleared public distribution.

The complete offline input set is verified locally and embedded as data. The
builder does not download dependencies. Runtime source/licensing and real
Windows acceptance remain separate release gates; --private-qa-only must be
explicitly selected, and output is confined to the host temporary directory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
PRODUCT = 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR'
LAUNCHER_SHA = '3c1906f7b2c384d2470c4ddcdf35b1da01697f61260fdb3033e44d9c3e12f969'
COMPONENTS = (
    ('0ad', '0ad-0.28.0-win64.exe', 1616727146, '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'),
    ('python', 'python-3.13.16-embed-amd64.zip', 11439094, '97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'),
    ('vc', 'VC_redist.x64.exe', 18731856, '843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c'),
)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_component(path, name, size, expected_sha):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'Missing or linked offline component: ' + name)
    require(path.stat().st_size == size, 'Wrong component size: ' + name)
    require(sha(path) == expected_sha, 'Wrong component SHA-256: ' + name)
    return {'name': name, 'bytes': size, 'sha256': expected_sha, 'input_path': str(path.resolve())}


def snapshot(project, launcher, payload, revision, dirty):
    roots = ['mods', 'launcher', 'tools', 'docs', 'research', 'tests', 'LICENSES', 'installer/windows', 'evidence']
    for root in roots:
        source = project / root
        if not source.exists():
            continue
        for p in source.rglob('*'):
            rel = p.relative_to(project)
            if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or p.suffix in ('.pyc', '.partial'):
                continue
            if root == 'evidence' and p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov', '.wav', '.ogg'):
                continue
            if root == 'installer/windows' and any(x in rel.parts for x in ('vendor', 'build', 'dist')):
                continue
            require(p.suffix.lower() not in ('.exe', '.dll', '.deb', '.msi', '.whl'), 'Do not vendor binary packages into the source payload: ' + str(rel))
            dest = payload / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    for name in ('LICENSE', 'README_RU.md', 'THIRD_PARTY_NOTICES.md', 'RELEASE.json'):
        if (project / name).is_file():
            shutil.copy2(project / name, payload / name)
    shutil.copy2(launcher, payload / 'KazakhTotalWar.exe')
    for p in (payload / 'installer/windows').glob('*.ps1'):
        p.write_text(p.read_text(encoding='utf-8-sig'), encoding='utf-8-sig')
    files = [{'path': p.relative_to(payload).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(payload.rglob('*')) if p.is_file()]
    manifest = {'schema': 1, 'product': PRODUCT, 'delivery_version': '0.4.0', 'module_version': '0.2.0',
                'mode': 'private_offline_qa', 'redistribution_cleared': False,
                'source_revision': revision, 'source_dirty': dirty, 'files': files}
    (payload / 'PAYLOAD_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '1794096000'))
    for p in payload.rglob('*'):
        if p.is_file():
            os.utime(p, (epoch, epoch))
    return manifest


def build(args):
    require(args.private_qa_only, 'Explicit --private-qa-only is required; redistribution is not cleared')
    project, launcher, output = (Path(p).resolve() for p in (args.project, args.launcher, args.output))
    tmp = Path(tempfile.gettempdir()).resolve()
    require(output.is_relative_to(tmp) and output != tmp, 'Uncleared full QA executable must remain under the host temporary directory, never Library/site/source')
    require(sha(launcher) == LAUNCHER_SHA, 'Use the verified original AMD64 launcher')
    inputs = {'0ad': args.runtime_installer, 'python': args.python_embed, 'vc': args.vc_redist}
    components = [verify_component(inputs[key], name, size, digest) for key, name, size, digest in COMPONENTS]
    require(sum(row['bytes'] for row in components) < 2 * 1024**3, 'NSIS input block exceeds the supported wrapper design')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=project, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=project, text=True).strip())
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ktw-offline-qa-build-') as folder:
        stage = Path(folder); payload = stage / 'payload'; payload.mkdir()
        manifest = snapshot(project, launcher, payload, revision, dirty)
        manifest_sha = sha(payload / 'PAYLOAD_MANIFEST.json')
        built = stage / output.name
        env = dict(os.environ, NSISDIR=str(Path(args.nsis_dir).resolve()))
        cmd = [str(Path(args.makensis).resolve()), '-V3', '-WX', '-DPAYLOAD_DIR=' + str(payload),
               '-DOUTPUT_FILE=' + str(built), '-DPAYLOAD_SHA=' + manifest_sha]
        cmd.extend('-DCOMPONENT_' + key.upper() + '=' + str(Path(inputs[key]).resolve()) for key, *_ in COMPONENTS)
        cmd.append(str(project / 'installer/windows/OfflineGameSetup.nsi'))
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        (output.parent / 'offline-qa-build.log').write_text(result.stdout + result.stderr)
        require(result.returncode == 0, 'NSIS compile failed: ' + result.stdout + result.stderr)
        with built.open('rb') as f:
            head = f.read(64); require(head[:2] == b'MZ', 'Missing PE header')
            f.seek(int.from_bytes(head[60:64], 'little')); pe = f.read(26)
        require(pe[:4] == b'PE\0\0' and struct.unpack_from('<H', pe, 4)[0] == 0x14c, 'Wrong NSIS executable format')
        partial = output.with_suffix(output.suffix + '.partial')
        with built.open('rb') as src, partial.open('wb') as dst:
            shutil.copyfileobj(src, dst, 4 * 1024 * 1024); dst.flush(); os.fsync(dst.fileno())
        require(sha(built) == sha(partial), 'Output copy hash mismatch')
        os.replace(partial, output)
        report = {'status': 'PRIVATE_QA_ONLY_NOT_CLEARED_FOR_DISTRIBUTION', 'file': output.name,
                  'local_path': str(output), 'bytes': output.stat().st_size, 'sha256': sha(output),
                  'source_revision': revision, 'source_dirty': dirty, 'game_module_version': '0.2.0',
                  'payload_files': len(manifest['files']), 'payload_manifest_sha256': manifest_sha,
                  'components': components, 'components_embedded_outside_source_payload': True,
                  'installer_component_network_acquisition': False, 'network_fallback': False,
                  'native_windows_install_tested': False, 'native_windows_gameplay_tested': False,
                  'redistribution_cleared': False, 'public_upload_permitted': False,
                  'nsis_version': subprocess.check_output([str(Path(args.makensis).resolve()), '-VERSION'], env=env, text=True).strip()}
        (output.parent / 'offline-qa-build.json').write_text(json.dumps(report, indent=2) + '\n')
        (output.parent / 'offline-qa-payload-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', type=Path, default=PROJECT)
    ap.add_argument('--launcher', type=Path, required=True)
    ap.add_argument('--runtime-installer', type=Path, required=True)
    ap.add_argument('--python-embed', type=Path, required=True)
    ap.add_argument('--vc-redist', type=Path, required=True)
    ap.add_argument('--makensis', type=Path, required=True)
    ap.add_argument('--nsis-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--private-qa-only', action='store_true')
    build(ap.parse_args())
