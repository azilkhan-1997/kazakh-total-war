import importlib.util,sys,unittest,json,os
from pathlib import Path
from unittest.mock import patch
SOURCE=Path('/workspace/scratch/a712cf7eed58/offline_game/build/source_import')
sys.path.insert(0,str(SOURCE))
import import_source as imp
import test_source_import as fixture
class Review(fixture.ImportContracts):
    def repo(self):
        self.init_git()
        imp.git(self.root,'remote','add','origin',imp.ORIGIN)
        return imp.git(self.root,'rev-parse','HEAD')
    def test_review_staged_content_substitution_rejected(self):
        self.repo();verified,missing=imp.prepare(self.root,self.fetch)
        imp.apply_verified(self.root,verified,missing)
        name=missing[0];(self.root/name).write_bytes(b'ATTACKER BYTES')
        imp.git(self.root,'add','--',*missing)
        with self.assertRaisesRegex(ValueError,'Staged bytes'):
            imp.assert_staged_assets(self.root,missing,verified)
    def test_review_existing_tracked_modification_not_addition_rejected(self):
        self.repo();verified,missing=imp.prepare(self.root,self.fetch)
        imp.apply_verified(self.root,verified,missing)
        imp.git(self.root,'add','--',*missing)
        imp.git(self.root,'-c','user.name=QA','-c','user.email=qa@example.invalid','-c','commit.gpgsign=false','commit','-m','Fixture art')
        name=missing[0];(self.root/name).write_bytes(b'MODIFIED')
        imp.git(self.root,'add','--',name)
        with self.assertRaisesRegex(ValueError,'exact missing asset additions'):
            imp.assert_staged_assets(self.root,[name],verified)
    def test_review_corrupt_last_verified_buffer_no_first_write(self):
        verified,missing=imp.prepare(self.root,self.fetch)
        last=missing[-1];verified[last]=b'X'+verified[last][1:]
        with self.assertRaisesRegex(ValueError,'SHA-256'):
            imp.apply_verified(self.root,verified,missing)
        self.assert_no_assets()
    def test_review_missing_attribution_stops_before_network(self):
        (self.root/'THIRD_PARTY_NOTICES.md').write_text('No attribution')
        with self.assertRaisesRegex(ValueError,'attribution missing'):
            imp.prepare(self.root,self.fetch)
        self.assertEqual(self.calls,[]);self.assert_no_assets()
    def test_review_nonallowlisted_url_rejected_before_transport(self):
        with patch.object(imp.urllib.request,'urlopen',side_effect=AssertionError('Network must not run')):
            with self.assertRaisesRegex(ValueError,'URL outside'):
                imp.download('https://raw.githubusercontent.com/0ADMods/millenniumad/main/art/unknown.png',100)
    def test_review_branch_moves_after_prefetch_before_write(self):
        expected=self.repo()
        with patch.object(imp,'remote_tip',side_effect=[expected,'2'*40]):
            with self.assertRaisesRegex(ValueError,'main moved'):
                imp.publish(self.root,expected,self.fetch)
        self.assertEqual(len(self.calls),20);self.assert_no_assets()
        self.assertEqual(imp.git(self.root,'status','--porcelain'),'')
    def test_review_branch_moves_after_stage_before_commit(self):
        expected=self.repo()
        with patch.object(imp,'remote_tip',side_effect=[expected,expected,'2'*40]):
            with self.assertRaisesRegex(ValueError,'main moved before commit'):
                imp.publish(self.root,expected,self.fetch)
        self.assertEqual(imp.git(self.root,'rev-parse','HEAD'),expected)
        imp.assert_staged_assets(self.root,list(self.rows),self.data)
    def test_review_branch_moves_after_commit_before_push(self):
        expected=self.repo()
        with patch.object(imp,'remote_tip',side_effect=[expected,expected,expected,'2'*40]):
            with self.assertRaisesRegex(ValueError,'main moved before push'):
                imp.publish(self.root,expected,self.fetch)
        self.assertEqual(imp.git(self.root,'rev-parse','HEAD^'),expected)
        self.assertEqual(imp.git(self.root,'status','--porcelain'),'')
    def test_review_publish_command_exact_nonforce_no_real_network(self):
        expected=self.repo();realgit=imp.git;pushes=[]
        def controlled_git(root,*args,**kwargs):
            if args and args[0]=='push':
                pushes.append((args,kwargs['env']))
                return 'SIMULATED PUSH ONLY'
            return realgit(root,*args,**kwargs)
        with patch.object(imp,'remote_tip',return_value=expected),patch.object(imp,'git',side_effect=controlled_git),patch.dict(os.environ,{'GITHUB_TOKEN':'QA_DUMMY_NOT_A_REAL_CREDENTIAL'}):
            result=imp.publish(self.root,expected,self.fetch)
        self.assertEqual(result['status'],'published_source_textures')
        self.assertEqual(len(pushes),1)
        self.assertEqual(pushes[0][0],('push','--porcelain','origin','HEAD:refs/heads/main'))
        self.assertNotIn('QA_DUMMY_NOT_A_REAL_CREDENTIAL',str(pushes[0][0]))
        self.assertEqual(pushes[0][1]['GIT_TERMINAL_PROMPT'],'0')
        self.assertEqual(realgit(self.root,'rev-parse','HEAD^'),expected)
        changed=realgit(self.root,'diff-tree','--no-commit-id','--name-only','-r','HEAD').splitlines()
        self.assertEqual(set(changed),set(self.rows))
        self.assertFalse((self.root/'evidence').exists())
    def test_review_repeat_publish_skips_network_commit_push(self):
        self.repo();verified,missing=imp.prepare(self.root,self.fetch)
        imp.apply_verified(self.root,verified,missing)
        imp.git(self.root,'add','--',*missing)
        imp.git(self.root,'-c','user.name=QA','-c','user.email=qa@example.invalid','-c','commit.gpgsign=false','commit','-m','Fixture art')
        expected=imp.git(self.root,'rev-parse','HEAD')
        with patch.object(imp,'remote_tip',return_value=expected):
            result=imp.publish(self.root,expected,lambda *a:self.fail('No fetch on repeat'))
        self.assertEqual(result,{'status':'already_verified','verified_pngs':19,'changed':[],'pushed':False})
        self.assertEqual(imp.git(self.root,'rev-parse','HEAD'),expected)
        self.assertEqual(imp.git(self.root,'status','--porcelain'),'')
names=[n for n in dir(Review) if n.startswith('test_review_')]
suite=unittest.TestSuite(Review(n) for n in names)
result=unittest.TextTestRunner(verbosity=2).run(suite)
report={'independent_tests':len(names),'passed':result.wasSuccessful(),'failures':[str(x[0]) for x in result.failures],'errors':[str(x[0]) for x in result.errors],'real_network_operations':False,'real_github_push':False,'source_files_edited':False,'scope':'Real local Git and synthetic fixture content; remote tips and final push mocked. Parent workflow not executed.'}
Path('/tmp/source-import-independent-targeted-tests.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
