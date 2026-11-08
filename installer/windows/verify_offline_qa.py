#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect a private offline QA EXE as data; never execute a Windows binary."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(args):
    expected = json.loads(args.build_report.read_text())
    report = {'scope': 'Full private NSIS data extraction, actual embedded bytes and offline source inspection; Linux host only.',
              'native_windows_install_tested': False, 'native_windows_gameplay_tested': False,
              'redistribution_cleared': False, 'public_upload_permitted': False, 'checks': []}
    def check(value, name):
        report['checks'].append({'check': name, 'pass': bool(value)})
        if not value:
            raise AssertionError(name)
    try:
        check(args.installer.stat().st_size == expected['bytes'] and sha(args.installer) == expected['sha256'], 'Actual complete EXE matches build report')
        report['installer_bytes'] = expected['bytes']; report['installer_sha256'] = expected['sha256']
        with tempfile.TemporaryDirectory(prefix='ktw-offline-extracted-') as folder:
            output = Path(folder)
            extracted = subprocess.run([str(args.sevenzip), 'x', '-y', '-o' + folder, str(args.installer)], capture_output=True, text=True)
            check(extracted.returncode == 0, 'Complete NSIS wrapper extracts successfully')
            payload = output / '$PLUGINSDIR/payload'
            components = output / '$PLUGINSDIR/components'
            check(sha(payload / 'PAYLOAD_MANIFEST.json') == expected['payload_manifest_sha256'], 'Actual embedded own-payload manifest matches build record')
            manifest = json.loads((payload / 'PAYLOAD_MANIFEST.json').read_text())
            check({p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()} == {r['path'] for r in manifest['files']} | {'PAYLOAD_MANIFEST.json'}, 'Exact own-payload inventory')
            for row in manifest['files']:
                actual = payload / row['path']
                check(actual.stat().st_size == row['bytes'] and sha(actual) == row['sha256'], 'Own file hash: ' + row['path'])
                source = args.source / row['path']
                if row['path'] != 'KazakhTotalWar.exe':
                    original = source.read_bytes()
                    if row['path'].startswith('installer/windows/') and row['path'].endswith('.ps1'):
                        original = original.decode('utf-8-sig').encode('utf-8-sig')
                    check(actual.read_bytes() == original, 'Own source bytes: ' + row['path'])
            report['payload_files_verified'] = len(manifest['files'])
            check({p.name for p in components.iterdir()} == {x['name'] for x in expected['components']}, 'Exactly three offline components are embedded outside own payload')
            for row in expected['components']:
                p = components / row['name']
                check(p.is_file() and p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Entire component bytes: ' + row['name'])
            report['component_files_verified'] = len(expected['components'])
            bootstrap = (payload / 'installer/windows/OfflineBootstrap.ps1').read_text(encoding='utf-8-sig')
            for token in ('WebClient', 'Invoke-WebRequest', 'DownloadFile', 'Invoke-RestMethod', 'Start-BitsTransfer', 'Get-VerifiedFile', '$installerUrl', '$pythonUrl', '$vcUrl'):
                check(token not in bootstrap, 'Offline entry point contains no acquisition primitive: ' + token)
            check('Get-EmbeddedComponent' in bootstrap and 'No network fallback is permitted.' in bootstrap, 'Offline component failure stops installation')
            spec = importlib.util.spec_from_file_location('offline_embedded_worker', payload / 'installer/windows/setup_worker.py')
            module = importlib.util.module_from_spec(spec)
            old = sys.dont_write_bytecode
            try:
                sys.dont_write_bytecode = True; spec.loader.exec_module(module)
            finally:
                sys.dont_write_bytecode = old
            module.verify_tree(payload, manifest['files'], ['PAYLOAD_MANIFEST.json'])
            check(True, 'Actual embedded worker independently verifies its own payload without copying component packages')
        report['pass'] = True
    except Exception as exc:
        report['pass'] = False; report['failure'] = str(exc)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({k: v for k, v in report.items() if k != 'checks'}, indent=2))
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--installer', type=Path, required=True)
    ap.add_argument('--sevenzip', type=Path, required=True)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--build-report', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    verify(ap.parse_args())
