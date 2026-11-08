#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect a compiled NSIS payload without executing any Windows executable."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib.util, json, struct, subprocess, sys, tempfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--installer', type=Path, required=True)
    ap.add_argument('--sevenzip', type=Path, required=True)
    ap.add_argument('--build-report', type=Path, required=True)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--runtime', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = {'scope': 'Static PE and actual NSIS payload extraction/hash validation on Linux; no Windows process executed.',
              'installer': str(args.installer), 'installer_sha256': sha(args.installer),
              'installer_bytes': args.installer.stat().st_size, 'native_windows_installation': 'NOT TESTED',
              'native_windows_gameplay': 'NOT TESTED', 'checks': []}
    def check(ok, label):
        report['checks'].append({'check': label, 'pass': bool(ok)})
        if not ok:
            raise AssertionError(label)
    try:
        built = json.loads(args.build_report.read_text())
        check(report['installer_sha256'] == built['sha256'] and report['installer_bytes'] == built['bytes'], 'Actual EXE matches build-record hash and size')
        data = args.installer.read_bytes()
        offset = int.from_bytes(data[60:64], 'little')
        check(data[:2] == b'MZ' and data[offset:offset+4] == b'PE\0\0', 'Actual Windows PE header')
        check(struct.unpack_from('<H', data, offset+4)[0] == 0x14c, 'Standard x86 NSIS stub; x64 OS gate reviewed in source')
        check(struct.unpack_from('<H', data, offset+24+68)[0] == 2, 'Windows GUI PE subsystem')
        with tempfile.TemporaryDirectory(prefix='ktw-payload-qa-', dir=args.output.parent) as temp:
            command = [str(args.sevenzip), 'x', '-y', '-o'+temp, str(args.installer)]
            result = subprocess.run(command, capture_output=True, text=True)
            report['archive_tool_exit_code'] = result.returncode
            check(result.returncode == 0, 'Actual NSIS payload decompresses successfully')
            payload = Path(temp)/'$PLUGINSDIR'/'payload'
            manifest_path = payload/'PAYLOAD_MANIFEST.json'
            check(sha(manifest_path) == built['payload_manifest_sha256'], 'Embedded manifest matches pinned build manifest')
            manifest = json.loads(manifest_path.read_text())
            check(manifest['product'] == 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR', 'Expected product identity')
            expected = {}
            casefolded = set()
            for row in manifest['files']:
                name = row['path']; path = PurePosixPath(name)
                check(not path.is_absolute() and path.as_posix() == name and '..' not in path.parts and '\\' not in name and ':' not in name, 'Safe payload path: '+name)
                check(name.casefold() not in casefolded, 'Unique case-insensitive path: '+name)
                casefolded.add(name.casefold()); expected[name] = row
            actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
            check(actual == set(expected)|{'PAYLOAD_MANIFEST.json'}, 'Exact payload inventory')
            verified = []
            for name, row in expected.items():
                file = payload/name
                if file.stat().st_size != row['bytes'] or sha(file) != row['sha256']:
                    raise AssertionError('Payload bytes do not match manifest: '+name)
                original = args.source/name
                if name != 'KazakhTotalWar.exe':
                    original_bytes = original.read_bytes()
                    if name.startswith('installer/windows/') and name.endswith('.ps1'):
                        original_bytes = original_bytes.decode('utf-8-sig').encode('utf-8-sig')
                    if file.read_bytes() != original_bytes:
                        raise AssertionError('Embedded source differs from current source: '+name)
                verified.append(name)
            report['payload_files_hashed'] = len(verified)
            report['payload_source_matches'] = len(verified)-1
            check(len(verified) == built['payload_files'], 'Every embedded game/source file verifies against manifest and source')
            check(sha(payload/'KazakhTotalWar.exe') == '3c1906f7b2c384d2470c4ddcdf35b1da01697f61260fdb3033e44d9c3e12f969', 'Embedded AMD64 launcher is exact verified binary')
            for name in ('Bootstrap.ps1', 'Uninstall-KTW.ps1'):
                check((payload/'installer/windows'/name).read_bytes().startswith(b'\xef\xbb\xbf'), 'PowerShell 5.1 UTF-8 BOM: '+name)
            spec = importlib.util.spec_from_file_location('embedded_install_worker', payload/'installer/windows/setup_worker.py')
            worker = importlib.util.module_from_spec(spec)
            previous_bytecode_setting = sys.dont_write_bytecode
            try:
                # Keep this read-only inspection from adding __pycache__ to the
                # extracted payload before its exact-file inventory is checked.
                sys.dont_write_bytecode = True
                spec.loader.exec_module(worker)
            finally:
                sys.dont_write_bytecode = previous_bytecode_setting
            rows = worker.read_manifest(payload/'PAYLOAD_MANIFEST.json')
            worker.verify_tree(payload, rows['files'], ['PAYLOAD_MANIFEST.json'])
            check(True, 'Embedded worker verifies actual payload successfully')
            runtime_manifest = payload/'docs/windows-runtime-manifest.json'
            check(sha(runtime_manifest) == worker.EXPECTED_RUNTIME_MANIFEST_SHA, 'Actual embedded official-runtime manifest is pinned')
            if args.runtime:
                rows = worker.read_manifest(runtime_manifest)
                worker.verify_tree(args.runtime, rows['files'])
                report['runtime_file_count'] = len(rows['files'])
                report['runtime_bytes'] = sum(r['bytes'] for r in rows['files'])
                check(len(rows['files']) == 140, 'Embedded worker verifies all 140 actual official runtime files')
                check(sha(args.runtime/'binaries/system/pyrogenesis.exe') == worker.ENGINE_SHA, 'Actual official engine executable matches pinned AMD64 engine')
        report['pass'] = True
    except Exception as exc:
        report['pass'] = False
        report['failure'] = str(exc)
        raise
    finally:
        args.output.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k != 'checks'}, indent=2))


if __name__ == '__main__':
    main()
