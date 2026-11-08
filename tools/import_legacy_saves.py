#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Copy only verified KTW/R28 saves; never overwrite, alter or delete an old save."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def validate_save(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if sorted(names) != ['metadata.json', 'simulation.dat']:
            raise ValueError('Expected exactly metadata.json and simulation.dat')
        if z.getinfo('metadata.json').file_size > 4 * 1024 * 1024:
            raise ValueError('Save metadata too large')
        if not 0 < z.getinfo('simulation.dat').file_size <= 256 * 1024 * 1024:
            raise ValueError('Save simulation size outside import limits')
        metadata = json.loads(z.read('metadata.json'))
        if metadata.get('engine_version') != '0.28.0' or metadata.get('engine_serialization_version') != '0.28.0':
            raise ValueError('Save requires a different engine version')
        mods = metadata.get('mods', [])
        ktw = [m for m in mods if m.get('mod') == 'kazakh_total_war']
        if len(ktw) != 1 or ktw[0].get('version') not in ('0.1.0', '0.2.0'):
            raise ValueError('Unsupported or missing KTW module')
        if any(m.get('mod') not in ('public', 'kazakh_total_war') and not m.get('ignoreInCompatibilityChecks', False) for m in mods):
            raise ValueError('Save requires additional gameplay mods')
        init = metadata.get('initAttributes', {})
        settings = init.get('settings', {})
        mode = settings.get('KtwMode')
        if mode not in ('campaign', 'battle') or init.get('map') != 'maps/random/ktw_' + mode:
            raise ValueError('Not a KTW campaign/battle save')
        if settings.get('KtwCampaign', {}).get('campaignId') != 'great_steppe_1465_slice':
            raise ValueError('Unknown campaign identity')
        if z.testzip():
            raise ValueError('Save ZIP CRC failed')
    return metadata

def publish_new(staging, target):
    # Windows rename fails if the destination exists. POSIX rename replaces it,
    # so use a same-directory hard link there for atomic no-replace publication.
    if os.name == 'nt':
        os.rename(staging, target)
    else:
        os.link(staging, target)
        staging.unlink()

def import_save(source, destination):
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or not source.is_file():
        raise ValueError('Save must be a regular file, not a symbolic link')
    validate_save(source)
    original_hash = sha256(source)
    destination.mkdir(parents=True, exist_ok=True)
    # Compare all existing saves to make repeated imports idempotent, even if
    # the first import needed a collision suffix.
    for existing in destination.glob('*.0adsave'):
        if existing.is_file() and not existing.is_symlink() and sha256(existing) == original_hash:
            return {'status': 'already_present', 'source': str(source), 'destination': str(existing), 'sha256': original_hash}
    fd, temporary = tempfile.mkstemp(prefix='.ktw-import-', suffix='.partial', dir=destination)
    staging = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as out, source.open('rb') as inp:
            shutil.copyfileobj(inp, out, 1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        if sha256(staging) != original_hash:
            raise ValueError('Source changed during import; original and destination retained')
        validate_save(staging)
        stem = ''.join(c if c.isascii() and (c.isalnum() or c in '_-') else '_' for c in source.stem)[:100] or 'save'
        # Prefix avoids Windows device names; arbitrary source filenames never
        # become executable content or destination path components.
        stem = 'ktw_import_' + stem
        for number in range(10000):
            target = destination / (stem + (('_' + str(number)) if number else '') + '.0adsave')
            try:
                publish_new(staging, target)
                return {'status': 'imported', 'source': str(source), 'destination': str(target), 'sha256': original_hash}
            except FileExistsError:
                continue
        raise ValueError('Too many filename collisions')
    finally:
        if staging.exists():
            staging.unlink()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--destination', type=Path, required=True)
    args = ap.parse_args()
    if not args.source.is_dir():
        ap.error('Source save directory does not exist')
    results = []
    for source in sorted(args.source.glob('*.0adsave')):
        try:
            results.append(import_save(source, args.destination))
        except (ValueError, OSError, zipfile.BadZipFile, KeyError, TypeError, AttributeError) as error:
            results.append({'status': 'skipped', 'source': str(source), 'reason': str(error)})
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
