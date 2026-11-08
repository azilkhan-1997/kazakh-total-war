#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent Linux tests for the install worker's non-Windows transaction contract."""
from pathlib import Path
import importlib.util,json,tempfile,unittest,hashlib,os
from unittest import mock
CANDIDATES = ([Path(os.environ['KTW_GAME_SOURCE'])] if 'KTW_GAME_SOURCE' in os.environ else list(Path(__file__).resolve().parents))
ROOT = next((p for p in CANDIDATES if (p/'installer/windows/setup_worker.py').is_file()), Path(__file__).resolve().parents[1]/'game')
SOURCE=ROOT/'installer/windows/setup_worker.py'
spec=importlib.util.spec_from_file_location('ktw_install_worker_qa',SOURCE)
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

class InstallTransactionContract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='ktw-independent-qa-');self.base=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_existing_game_is_never_overwritten(self):
  target=self.base/'game';target.mkdir();(target/'save.json').write_text('valuable')
  with self.assertRaises(ValueError):w.make_stage(target,'a1')
  self.assertEqual((target/'save.json').read_text(),'valuable')
 def test_symlink_destination_rejected(self):
  real=self.base/'real';real.mkdir();(real/'save').write_text('valuable');target=self.base/'link';target.symlink_to(real,target_is_directory=True)
  with self.assertRaises(ValueError):w.make_stage(target,'a2')
  self.assertEqual((real/'save').read_text(),'valuable')
 def test_unowned_staging_cleanup_rejected(self):
  target,stage=w.make_stage(self.base/'game','a3');(stage/'payload').write_text('owned')
  data=json.loads((stage/'.ktw-staging.json').read_text());data['install_id']='different';(stage/'.ktw-staging.json').write_text(json.dumps(data))
  with self.assertRaises(ValueError):w.cleanup_stage(stage,target,'a3')
  self.assertEqual((stage/'payload').read_text(),'owned')
 def test_owned_staging_cleanup_preserves_other_data(self):
  target,stage=w.make_stage(self.base/'game','a4');outside=self.base/'outside';outside.write_text('keep')
  w.cleanup_stage(stage,target,'a4');self.assertFalse(stage.exists());self.assertEqual(outside.read_text(),'keep')
 def test_destination_race_preserves_new_user_file(self):
  target,stage=w.make_stage(self.base/'game','a5');target.mkdir();(target/'user-save').write_text('keep');(stage/'gamefile').write_text('new')
  with self.assertRaises(ValueError):w.commit_stage(stage,target)
  self.assertEqual((target/'user-save').read_text(),'keep');self.assertEqual((stage/'gamefile').read_text(),'new')
 def test_rename_failure_restores_preexisting_empty_target(self):
  target=self.base/'game';target.mkdir();target,stage=w.make_stage(target,'a6');(stage/'gamefile').write_text('new')
  with mock.patch.object(w.os,'rename',side_effect=OSError('simulated disk fault')):
   with self.assertRaises(OSError):w.commit_stage(stage,target)
  self.assertTrue(target.is_dir());self.assertFalse(any(target.iterdir()));self.assertTrue((stage/'gamefile').exists())
 def test_complete_stage_published_by_rename(self):
  target=self.base/'game';target.mkdir();target,stage=w.make_stage(target,'a7');(stage/'gamefile').write_text('new')
  w.commit_stage(stage,target);self.assertFalse(stage.exists());self.assertEqual((target/'gamefile').read_text(),'new')
 def test_equal_size_payload_tampering_is_rejected(self):
  tree=self.base/'tree';tree.mkdir();(tree/'asset').write_bytes(b'good')
  rows=[{'path':'asset','bytes':4,'sha256':hashlib.sha256(b'good').hexdigest()}]
  w.verify_tree(tree,rows);(tree/'asset').write_bytes(b'evil')
  with self.assertRaises(ValueError):w.verify_tree(tree,rows)
 def test_case_collision_manifest_rejected(self):
  row={'path':'File.txt','bytes':1,'sha256':'a'*64};p=self.base/'manifest.json';p.write_text(json.dumps({'files':[row,dict(row,path='file.txt')]}))
  with self.assertRaises(ValueError):w.read_manifest(p)
 def test_path_escape_and_windows_stream_syntax_rejected(self):
  for name in ['../outside','/absolute','a/../../outside','a\\b','a:b','a//b','./a']:
   with self.subTest(name=name):
    with self.assertRaises(ValueError):w.safe_relative(name)
 def test_hashing_honors_interrupted_setup(self):
  p=self.base/'file';p.write_bytes(b'payload')
  with mock.patch.object(w,'check_abort',side_effect=RuntimeError('setup closed')):
   with self.assertRaisesRegex(RuntimeError,'setup closed'):w.digest(p)
 def test_symlink_in_payload_is_rejected(self):
  root=self.base/'payload';root.mkdir();outside=self.base/'outside';outside.write_bytes(b'x');(root/'asset').symlink_to(outside)
  with self.assertRaises(ValueError):w.verify_tree(root,[{'path':'asset','bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}])
  self.assertEqual(outside.read_bytes(),b'x')
 def test_linked_destination_ancestor_rejected(self):
  real=self.base/'real';real.mkdir();link=self.base/'alias';link.symlink_to(real,target_is_directory=True)
  with self.assertRaises(ValueError):w.make_stage(link/'game','a8')
  self.assertFalse((real/'game').exists())
 def test_cleanup_does_not_follow_child_symlink(self):
  target,stage=w.make_stage(self.base/'game','a9');outside=self.base/'outside';outside.mkdir();(outside/'save').write_text('keep')
  (stage/'redirect').symlink_to(outside,target_is_directory=True)
  w.cleanup_stage(stage,target,'a9');self.assertFalse(stage.exists());self.assertEqual((outside/'save').read_text(),'keep')
 def test_missing_tree_file_is_rejected(self):
  root=self.base/'tree';root.mkdir()
  with self.assertRaises(ValueError):w.verify_tree(root,[{'path':'missing','bytes':0,'sha256':hashlib.sha256(b'').hexdigest()}])
 def test_unexpected_tree_file_is_rejected(self):
  tree=self.base/'tree';tree.mkdir();(tree/'unexpected').write_bytes(b'x')
  with self.assertRaises(ValueError):w.verify_tree(tree,[])

if __name__=='__main__':unittest.main(verbosity=2)
