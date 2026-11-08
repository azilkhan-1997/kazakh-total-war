#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Transactional KTW installer worker, run only by its isolated private interpreter.

Downloads and license interaction belong to Bootstrap.ps1. This worker never
executes the upstream 0 A.D. installer and never touches a global 0 A.D. install.
"""
from pathlib import Path, PurePosixPath
import argparse, ctypes, hashlib, json, os, shutil, struct, subprocess, sys, time, uuid, zipfile

PRODUCT = 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR'
EXPECTED_INSTALLER_SHA = '9b5e1a16d4e0df9c84e052f56fb75da69518d5634c88d2b38db69baee63c16a1'
EXPECTED_INSTALLER_BYTES = 1616727146
EXPECTED_EXTRACTOR_SHA = 'c9c109967d74128e6d61c0cb285e397518a89e79d6899e87bb211c67018b3570'
EXPECTED_RUNTIME_MANIFEST_SHA = '6acc32df690bb3a0547a0c64818f91a2951aa24c8c1bd216b84a9d40cb1aad7d'
ENGINE_SHA = '11d79e7d1aba4ba71dd92b57131b2bd300962e2c94dcf5b79205e34aa076a24f'
PARENT_PID = 0


def check_abort():
    if not PARENT_PID or os.name != 'nt':
        return
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x00100000, False, PARENT_PID)
    if not handle:
        raise RuntimeError('Setup was closed; installation cancelled.')
    try:
        if kernel.WaitForSingleObject(handle, 0) != 258:
            raise RuntimeError('Setup was closed; installation cancelled.')
    finally:
        kernel.CloseHandle(handle)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(4*1024*1024), b''):
            check_abort()
            h.update(part)
    return h.hexdigest()


def safe_relative(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name, 'Unsafe relative path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and p.as_posix() == name and all(x not in ('', '.', '..') for x in p.parts), 'Unsafe relative path')
    return p


def no_reparse(path):
    path = Path(path)
    require(not path.is_symlink(), 'Symbolic links are not allowed: ' + str(path))
    if path.exists():
        require(not (getattr(path.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse point is not allowed: ' + str(path))


def check_ancestors(path):
    for candidate in [Path(path), *Path(path).parents]:
        no_reparse(candidate)


def regular_files(root):
    root = Path(root)
    no_reparse(root)
    result = []
    for p in root.rglob('*'):
        no_reparse(p)
        if p.is_file():
            result.append(p)
        else:
            require(p.is_dir(), 'Unexpected filesystem object: ' + str(p))
    return result


def read_manifest(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = data['files']
    require(isinstance(rows, list), 'Invalid file manifest')
    seen = set()
    for row in rows:
        name = row['path']
        safe_relative(name)
        require(name.casefold() not in seen, 'Duplicate case-insensitive path: ' + name)
        seen.add(name.casefold())
        require(isinstance(row['bytes'], int) and row['bytes'] >= 0, 'Invalid byte count')
        require(len(row['sha256']) == 64 and all(c in '0123456789abcdef' for c in row['sha256']), 'Invalid SHA-256')
    return data


def verify_tree(root, rows, extra_allowed=()):
    root = Path(root)
    expected = {row['path']: row for row in rows}
    actual = {p.relative_to(root).as_posix() for p in regular_files(root)}
    require(actual == set(expected) | set(extra_allowed), 'Unexpected or missing files in ' + str(root))
    for name, row in expected.items():
        p = root / safe_relative(name)
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'File verification failed: ' + name)
    return expected


def checked_copy(source, dest):
    no_reparse(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    require(source.stat().st_size == dest.stat().st_size and digest(source) == digest(dest), 'Copy verification failed: ' + str(dest))


def make_stage(target, install_id):
    target = Path(target).absolute()
    check_ancestors(target)
    require(target.parent != target, 'Cannot install at a drive root')
    require(not target.exists() or (target.is_dir() and not any(target.iterdir())), 'The selected folder is not empty. Choose a new empty folder; existing games and saves are never overwritten.')
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / ('.' + target.name + '.setup-' + install_id)
    stage.mkdir(exist_ok=False)
    (stage / '.ktw-staging.json').write_text(json.dumps({'product': PRODUCT, 'install_id': install_id, 'target': str(target)}), encoding='utf-8')
    return target, stage


def cleanup_stage(stage, target, install_id):
    if not stage or not stage.exists():
        return
    marker = stage / '.ktw-staging.json'
    require(stage.parent == target.parent and stage.name == '.' + target.name + '.setup-' + install_id, 'Refusing unowned staging cleanup')
    no_reparse(stage)
    data = json.loads(marker.read_text(encoding='utf-8'))
    require(data == {'product': PRODUCT, 'install_id': install_id, 'target': str(target)}, 'Refusing staging cleanup without matching ownership')
    # Python3.13 does not traverse Windows directory junction targets in rmtree.
    shutil.rmtree(stage)


def commit_stage(stage, target):
    check_ancestors(target)
    was_empty = target.exists()
    if was_empty:
        require(target.is_dir() and not any(target.iterdir()), 'Destination changed during setup; existing data was preserved.')
        target.rmdir()  # Removes only the still-empty destination selected by user.
    try:
        os.rename(stage, target)  # Same-parent, same-volume atomic publication.
    except BaseException:
        if was_empty and not target.exists():
            target.mkdir()
        raise


def install(payload, target, official_installer, uninstaller, payload_manifest_sha):
    require(os.name == 'nt' and struct.calcsize('P') == 8, 'This installer requires Windows10/11 x64.')
    payload, official_installer, uninstaller = map(lambda p: Path(p).absolute(), (payload, official_installer, uninstaller))
    require(digest(payload / 'PAYLOAD_MANIFEST.json') == payload_manifest_sha, 'Installer payload manifest mismatch')
    own = read_manifest(payload / 'PAYLOAD_MANIFEST.json')
    require(own['product'] == PRODUCT, 'Wrong product payload')
    print('Checking game files...', flush=True)
    verify_tree(payload, own['files'], ['PAYLOAD_MANIFEST.json'])
    extractor = payload / 'tools/extract_r28_nsisbi.py'
    runtime_manifest = payload / 'docs/windows-runtime-manifest.json'
    require(digest(extractor) == EXPECTED_EXTRACTOR_SHA, 'Extractor source mismatch')
    require(digest(runtime_manifest) == EXPECTED_RUNTIME_MANIFEST_SHA, 'Runtime manifest mismatch')
    require(official_installer.stat().st_size == EXPECTED_INSTALLER_BYTES and digest(official_installer) == EXPECTED_INSTALLER_SHA, 'Official runtime download mismatch')
    require(uninstaller.is_file(), 'Uninstaller is missing')
    expected = read_manifest(runtime_manifest)
    require(expected['file_count'] == 140 and len(expected['files']) == 140, 'Unexpected runtime manifest count')
    install_id = uuid.uuid4().hex
    target, stage = make_stage(target, install_id)
    published = False
    try:
        require(shutil.disk_usage(stage.parent).free >= 6*1024**3, 'At least6GiB free space is required for installation after downloads.')
        print('Unpacking game runtime. This can take several minutes...', flush=True)
        runtime = stage / 'runtime'
        run = subprocess.Popen([sys.executable, '-I', str(extractor), str(official_installer), str(runtime)])
        try:
            while run.poll() is None:
                check_abort()
                time.sleep(0.3)
        except BaseException:
            run.terminate()
            try:
                run.wait(timeout=10)
            except subprocess.TimeoutExpired:
                run.kill(); run.wait()
            raise
        require(run.returncode == 0, 'Runtime extraction failed; no installed game was replaced.')
        extraction = json.loads((stage / 'runtime-manifest.json').read_text(encoding='utf-8'))
        require(extraction['source_sha256'] == EXPECTED_INSTALLER_SHA and extraction['file_count'] == 140, 'Extraction provenance mismatch')
        for flag in ('all_file_crc_verified', 'header_crc_verified', 'installer_stub_crc_verified'):
            require(extraction[flag] is True, 'Runtime extraction integrity failed: ' + flag)
        require(extraction['installer_execution'] is False, 'Unexpected upstream installer execution')
        print('Verifying all game runtime files...', flush=True)
        verify_tree(runtime, expected['files'])
        require(digest(runtime / 'binaries/system/pyrogenesis.exe') == ENGINE_SHA, 'Wrong engine executable')
        for name in ('mod', 'public'):
            with zipfile.ZipFile(runtime / 'binaries/data/mods' / name / (name + '.zip')) as z:
                require(z.testzip() is None, 'Game data archive is corrupted: ' + name)
        base = json.loads((runtime / 'binaries/data/mods/public/mod.json').read_text(encoding='utf-8'))
        game = json.loads((payload / 'mods/kazakh_total_war/mod.json').read_text(encoding='utf-8'))
        require(base['name'] == '0ad' and base['version'] == '0.28.0', 'Incompatible engine')
        require(game['name'] == 'kazakh_total_war' and game['dependencies'] == ['0ad=0.28.0'], 'Incompatible game content')
        print('Installing KAZAKH TOTAL WAR...', flush=True)
        for p in regular_files(payload):
            checked_copy(p, stage / p.relative_to(payload))
        mod = payload / 'mods/kazakh_total_war'
        mod_target = runtime / 'binaries/data/mods/kazakh_total_war'
        for p in regular_files(mod):
            checked_copy(p, mod_target / p.relative_to(mod))
        for name in ('binaries/data/config', 'binaries/data/cache', 'binaries/data/saves', 'binaries/logs'):
            (runtime / name).mkdir(parents=True, exist_ok=True)
        checked_copy(uninstaller, stage / 'Uninstall.exe')
        (stage / 'INSTALL_ID.txt').write_text(install_id, encoding='ascii')
        check = subprocess.run([str(stage / 'KazakhTotalWar.exe'), '--check'], cwd=stage, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (stage / 'launcher-preflight.json').write_text(check.stdout, encoding='utf-8')
        require(check.returncode == 0, 'Launcher readiness check failed: ' + check.stdout.strip())
        known = {'runtime/' + r['path']: r for r in expected['files']}
        owned = []
        for p in regular_files(stage):
            name = p.relative_to(stage).as_posix()
            if name == '.ktw-staging.json':
                continue
            old = known.get(name)
            owned.append({'path': name, 'bytes': p.stat().st_size, 'sha256': old['sha256'] if old else digest(p)})
        marker = {'schema': 1, 'product': PRODUCT, 'install_id': install_id, 'delivery_version': '0.4.0', 'module_version': game['version'], 'engine_version': base['version'], 'install_root': str(target), 'owned_files': sorted(owned, key=lambda x: x['path']), 'preserve_prefixes': ['runtime/binaries/data/saves/', 'runtime/binaries/data/config/'], 'native_gameplay_verified': False, 'upstream_installer_executed': False, 'registration_complete': False}
        (stage / 'KTW_INSTALL.json').write_text(json.dumps(marker, indent=2) + '\n', encoding='utf-8')
        # Keep the staging marker until publication succeeds so all error cleanup
        # remains guarded. Remove it only from the successfully published root.
        check_abort()
        commit_stage(stage, target)
        published = True
        (target / '.ktw-staging.json').unlink()
        print('Game files installed and verified. Creating shortcuts...', flush=True)
        return target
    finally:
        if not published:
            cleanup_stage(stage, target, install_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--payload', type=Path, required=True)
    ap.add_argument('--target', type=Path, required=True)
    ap.add_argument('--runtime-installer', type=Path, required=True)
    ap.add_argument('--uninstaller', type=Path, required=True)
    ap.add_argument('--payload-manifest-sha', required=True)
    ap.add_argument('--parent-pid', type=int, required=True)
    a = ap.parse_args()
    global PARENT_PID
    PARENT_PID = a.parent_pid
    require(PARENT_PID > 0, 'An installer process is required.')
    try:
        install(a.payload, a.target, a.runtime_installer, a.uninstaller, a.payload_manifest_sha)
        return 0
    except Exception as exc:
        print('SETUP FAILED: ' + str(exc), file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
