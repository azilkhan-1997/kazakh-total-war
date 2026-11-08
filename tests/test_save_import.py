import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('import_saves', ROOT / 'tools/import_legacy_saves.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def make_save(path, version='0.2.0', engine='0.28.0', mode='battle', extra=None, duplicate=False):
    data = {'engine_version': engine, 'engine_serialization_version': engine,
            'mods': [{'mod': 'public', 'version': engine}, {'mod': 'kazakh_total_war', 'version': version}],
            'initAttributes': {'map': 'maps/random/ktw_' + mode, 'settings': {'KtwMode': mode,
                'KtwCampaign': {'campaignId': 'great_steppe_1465_slice'}}}}
    if extra: data['mods'].append(extra)
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('metadata.json', json.dumps(data))
        z.writestr('simulation.dat', b'test simulation fixture')
        if duplicate: z.writestr('unexpected.txt', b'not a save member')

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.dest = self.root / 'old.0adsave', self.root / 'new'
        make_save(self.source)

    def test_import_preserves_bytes(self):
        before = self.source.read_bytes()
        result = module.import_save(self.source, self.dest)
        self.assertEqual(result['status'], 'imported')
        self.assertEqual(Path(result['destination']).read_bytes(), before)
        self.assertEqual(self.source.read_bytes(), before)

    def test_repeat_import_does_not_duplicate(self):
        module.import_save(self.source, self.dest)
        self.assertEqual(module.import_save(self.source, self.dest)['status'], 'already_present')
        self.assertEqual(len(list(self.dest.glob('*.0adsave'))), 1)

    def test_collision_never_overwrites(self):
        self.dest.mkdir()
        target = self.dest / 'ktw_import_old.0adsave'
        target.write_bytes(b'previous player save')
        result = module.import_save(self.source, self.dest)
        self.assertNotEqual(Path(result['destination']), target)
        self.assertEqual(target.read_bytes(), b'previous player save')

    def test_previous_module_version_accepted(self):
        make_save(self.source, version='0.1.0')
        self.assertEqual(module.import_save(self.source, self.dest)['status'], 'imported')

    def test_wrong_engine_rejected(self):
        make_save(self.source, engine='0.0.26')
        with self.assertRaises(ValueError): module.import_save(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_future_module_rejected(self):
        make_save(self.source, version='8.0.0')
        with self.assertRaises(ValueError): module.validate_save(self.source)

    def test_other_gameplay_mod_rejected(self):
        make_save(self.source, extra={'mod': 'another-game'})
        with self.assertRaises(ValueError): module.validate_save(self.source)

    def test_wrong_map_rejected(self):
        make_save(self.source, mode='other')
        with self.assertRaises(ValueError): module.validate_save(self.source)

    def test_unexpected_member_rejected(self):
        make_save(self.source, duplicate=True)
        with self.assertRaises(ValueError): module.validate_save(self.source)

    def test_corrupt_archive_rejected_without_destination(self):
        self.source.write_bytes(b'corrupted')
        with self.assertRaises(zipfile.BadZipFile): module.import_save(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_publish_is_atomic_no_overwrite(self):
        stage, target = self.root / 'stage', self.root / 'target'
        stage.write_bytes(b'new')
        target.write_bytes(b'old')
        with self.assertRaises(FileExistsError): module.publish_new(stage, target)
        self.assertEqual(target.read_bytes(), b'old')
        self.assertEqual(stage.read_bytes(), b'new')

if __name__ == '__main__': unittest.main()
