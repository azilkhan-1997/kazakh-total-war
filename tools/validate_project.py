#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Read-only KTW/R28 static contract validation. This is NOT runtime/GPU validation.

Usage: python3 tools/validate_project.py --public /path/to/public.zip
       python3 tools/validate_project.py --self-test
No outputs are written by this tool. JSON is printed to stdout; exit 1 means failure.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

UNITS = ['mounted_archer', 'light_cavalry', 'heavy_cavalry', 'spearman', 'infantry_archer']
CACHE_SUFFIXES = ['', '.cached.pmd', '.cached.psa', '.cached.dds', '.cached.xmb']

class VFS:
    """Read-only mod-over-public resolver, including official precompiled art."""
    def __init__(self, mod: Path, public: Path):
        self.mod = mod
        self.zip = ZipFile(public)
        self.names = set(self.zip.namelist())
    def resolve(self, name):
        if not isinstance(name,str) or name.startswith('/') or '\\' in name or '..' in PurePosixPath(name).parts:
            return None
        path = self.mod/name
        if path.is_file():
            return {'provider':'mod', 'path':name, 'bytes':path.read_bytes()}
        for suffix in CACHE_SUFFIXES:
            if name+suffix in self.names:
                return {'provider':'release28' if not suffix else 'release28-cache', 'path':name+suffix,'bytes':self.zip.read(name+suffix)}
        return None
    def close(self):
        self.zip.close()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def art_references(root):
    for n in root.iter():
        text = (n.text or '').strip()
        if n.tag == 'mesh' and text: yield 'art/meshes/'+text
        elif n.tag == 'material' and text: yield 'art/materials/'+text
        elif n.tag == 'prop' and n.get('actor'): yield 'art/actors/'+n.get('actor')
        elif n.tag == 'variant' and n.get('file'): yield 'art/variants/'+n.get('file')
        elif n.tag == 'texture' and n.get('file'): yield 'art/textures/skins/'+n.get('file')
        elif n.tag == 'animation' and n.get('file'): yield 'art/animation/'+n.get('file')

class Validator:
    def __init__(self, project, public, engine_source=None):
        self.project=project; self.mod=project/'mods/kazakh_total_war'; self.vfs=VFS(self.mod,public)
        self.engine_source=engine_source; self.errors=[]; self.warnings=[]; self.checks={}; self.art_seen={}; self.templates={}
    def error(self, code, **data): self.errors.append({'code':code, **data})
    def warn(self, code, **data): self.warnings.append({'code':code, **data})
    def xml(self,path):
        r=self.vfs.resolve(path)
        if not r: self.error('missing_xml',path=path); return None
        if not r['path'].endswith('.xml'): self.error('xml_source_unavailable',path=path); return None
        try:return ET.fromstring(r['bytes'])
        except ET.ParseError as e:self.error('xml_parse',path=path,detail=str(e));return None
    def template(self,name,chain=()):
        if name in chain: self.error('template_cycle',chain=list(chain)+[name]);return {}
        if name in self.templates:return self.templates[name]
        candidates=['simulation/templates/'+prefix+name+'.xml' for prefix in ['special/filter/','mixins/','']]
        path=next((x for x in candidates if self.vfs.resolve(x)),candidates[-1]);root=self.xml(path)
        if root is None:return {}
        merged={}
        for parent in reversed(root.get('parent','').split('|')):
            if parent:merged.update(self.template(parent,chain+(name,)))
        for child in root:
            if child.tag not in self.component_names:self.error('unknown_component',template=name,component=child.tag)
            if 'disable' in child.attrib:merged.pop(child.tag,None)
            else: merged[child.tag]=child
        self.templates[name]=merged
        return merged
    def visit_art(self,path,via):
        if path in self.art_seen:return
        r=self.vfs.resolve(path)
        if not r:self.art_seen[path]='missing';self.error('art_reference',path=path,via=via);return
        self.art_seen[path]=r['provider']
        if path.endswith('.xml') and r['path'].endswith('.xml'):
            try:root=ET.fromstring(r['bytes'])
            except ET.ParseError as e:self.error('art_xml',path=path,detail=str(e));return
            for ref in art_references(root):self.visit_art(ref,path)
    def check_mod(self):
        try:
            mod=json.loads((self.mod/'mod.json').read_text());base=json.loads(self.vfs.zip.read('mod.json'))
            if base.get('version')!='0.28.0' or base.get('name')!='0ad':self.error('wrong_public_version',actual=base)
            if mod.get('name')!='kazakh_total_war' or mod.get('dependencies')!=['0ad=0.28.0']:self.error('wrong_mod_dependency',actual=mod)
            self.checks['dependency']={'base_version':base.get('version'),'mod_dependencies':mod.get('dependencies')}
        except (ValueError,OSError,KeyError) as e:self.error('mod_metadata',detail=str(e))
    def check_xml_and_license(self):
        files=list(self.mod.rglob('*.xml'));count=0
        for p in files:
            try:ET.parse(p);count+=1
            except ET.ParseError as e:self.error('module_xml_parse',path=str(p.relative_to(self.mod)),detail=str(e))
        self.checks['well_formed_module_xml']=count
        missing=[]
        for p in self.mod.rglob('*'):
            rel=p.relative_to(self.mod).as_posix()
            if p.is_file() and (p.suffix=='.js' or rel.startswith('simulation/templates/') and p.suffix=='.xml'):
                if 'SPDX-License-Identifier: GPL-2.0-or-later' not in p.read_text(errors='replace')[:800]:missing.append(rel)
        if missing:self.error('missing_code_license_headers',paths=missing)
        self.checks['code_license_headers']={'missing':missing}
    def check_templates(self):
        self.component_names={Path(n).stem for n in self.vfs.names if n.startswith('simulation/components/') and n.endswith('.js') and '/tests/' not in n}
        self.component_names.update(p.stem for p in (self.mod/'simulation/components').rglob('*.js'))
        if self.engine_source and self.engine_source.exists():self.component_names.update(p.stem[4:] for p in (self.engine_source/'source/simulation2/components').glob('ICmp*.h'))
        # Native interfaces are also represented by components used in the exact R28 templates.
        for name in self.vfs.names:
            if name.startswith('simulation/templates/template_') and name.endswith('.xml'):
                try:self.component_names.update(n.tag for n in ET.fromstring(self.vfs.zip.read(name)))
                except ET.ParseError:pass
        checked={}
        for path in (self.mod/'simulation/templates').rglob('*.xml'):
            name=path.relative_to(self.mod/'simulation/templates').as_posix()[:-4];components=self.template(name)
            if name.startswith('units/ktw/') and name.split('/')[-1] in UNITS:
                required={'Attack','Health','UnitAI','UnitMotion','Identity','VisualActor','Ownership','Position'}
                if required-set(components):self.error('unit_component_missing',template=name,components=sorted(required-set(components)))
                actor=components.get('VisualActor'); actor=actor.findtext('Actor') if actor is not None else None
                if not actor:self.error('unit_actor_missing',template=name)
                else:self.visit_art('art/actors/'+actor,name)
                checked[name]={'resolved_components':sorted(components),'actor':actor}
            root=ET.parse(path).getroot()
            icon=root.findtext('Identity/Icon')
            if icon and not self.vfs.resolve('art/textures/ui/session/portraits/'+icon):self.error('unit_portrait_missing',template=name,icon=icon)
        for unit in UNITS:
            if 'units/ktw/'+unit not in checked:self.error('required_unit_missing',unit=unit)
        self.checks['unit_templates']=checked;self.checks['template_chain_count']=len(self.templates)
        self.checks['schema_scope']='Top-level component names and inherited component presence only; NOT full RelaxNG engine schema validation.'
    def check_terrain(self):
        terrain_index={Path(n).stem:n for n in self.vfs.names if n.startswith('art/terrains/') and n.endswith('.xml')}
        textures=set();actors=set()
        for p in (self.mod/'maps/random').rglob('*.js'):
            text=p.read_text()
            textures.update(re.findall(r'"((?:alpine_|steppe_|desert_)[A-Za-z0-9_]+)"',text))
            actors.update(re.findall(r'"(props/flora/[^"\n]+\.xml)"',text))
        for name in sorted(textures):
            if name not in terrain_index:self.error('terrain_texture_missing',texture=name)
        for name in sorted(actors):self.visit_art('art/actors/'+name,'random_map')
        for name in ['ktw_campaign','ktw_battle']:
            path=self.mod/'maps/random'/f'{name}.json'
            try:metadata=json.loads(path.read_text());settings=metadata['settings']
            except (ValueError,KeyError,OSError) as e:self.error('random_map_metadata',map=name,detail=str(e));continue
            if settings.get('Script')!=name+'.js':self.error('random_map_script',map=name,script=settings.get('Script'))
            if not (self.mod/'maps/random'/f'{name}.js').is_file():self.error('random_map_code_missing',map=name)
        self.checks['terrain_textures']={x:terrain_index.get(x) for x in sorted(textures)}
    def check_assets(self):
        manifest_path=self.project/'docs/asset-manifest-millennium.json'
        try:manifest=json.loads(manifest_path.read_text())
        except (OSError,ValueError) as e:self.error('asset_manifest',detail=str(e));return
        verified=0
        for name,item in manifest.get('files',{}).items():
            r=self.vfs.resolve(name)
            if not r or r['provider']!='mod':self.error('manifest_missing_asset',path=name);continue
            actual=sha(r['bytes'])
            if actual!=item.get('output_sha256'):self.error('manifest_hash_mismatch',path=name,expected=item.get('output_sha256'),actual=actual)
            else:verified+=1
            if not item.get('license') or not item.get('attribution'):self.error('manifest_license_missing',path=name)
        for p in (self.mod/'art').rglob('*.xml'):
            self.visit_art(p.relative_to(self.mod).as_posix(),'module_art')
        tracked=set(manifest.get('files',{}))
        untracked=[p.relative_to(self.mod).as_posix() for p in (self.mod/'art').rglob('*') if p.is_file() and p.suffix.lower() not in ['.txt','.md'] and p.relative_to(self.mod).as_posix() not in tracked]
        if untracked:self.warn('art_not_in_millennium_manifest',paths=untracked,detail='May be original project art; requires its own attribution record.')
        self.checks['asset_manifest']={'verified_hashes':verified,'entries':len(tracked),'commit':manifest.get('commit')}
        self.checks['art_closure']={'visited':len(self.art_seen),'providers':{p:list(self.art_seen.values()).count(p) for p in ['mod','release28','release28-cache','missing']}}
    def check_bridge(self):
        ctrl=(self.mod/'simulation/components/KtwController.js').read_text();cmd=(self.mod/'simulation/helpers/KtwCommands.js').read_text();core=(self.mod/'simulation/helpers/KtwCampaign.js').read_text()
        contracts={
          'controller_system_registered':'Engine.RegisterSystemComponentType(IID_KtwController' in ctrl,
          'gui_state_gateway':'name === "KtwGetState"' in ctrl or "name === 'KtwGetState'" in ctrl,
          'upstream_gui_delegation':bool(re.search(r'KtwBaseScriptCall\.call\(this,\s*player,\s*name,\s*args\)',ctrl)),
          'deterministic_command_gateway':bool(re.search(r'g_Commands\.ktw\s*=',cmd)),
          'player_authorization':bool(re.search(r'player\s*!==\s*1',ctrl)),
          'campaign_global':bool(re.search(r'Engine\.RegisterGlobal\([\'\"]KtwCampaign',core)),
          'battle_survivor_return':'KtwCampaign.resolveBattle(this.state, result)' in ctrl,
          'campaign_state_validation':'KtwCampaign.validate(this.state)' in ctrl,
          'core_forbids_unimplemented_recruitment':'!IMPLEMENTED_UNITS.includes(type)' in core,
        }
        for name,ok in contracts.items():
            if not ok:self.error('bridge_static_contract',contract=name)
        self.checks['bridge_contract']=contracts
        # Confirm only the concrete engine methods the bridge uses in our adaptation.
        api_checks={}
        js_components={'Diplomacy':['SetEnemy'],'UnitAI':['SwitchToStance','Walk','Attack'],'Timer':['SetInterval'],'GuiInterface':['ScriptCall']}
        for component,methods in js_components.items():
            r=self.vfs.resolve('simulation/components/'+component+'.js');text=r['bytes'].decode() if r else ''
            for method in methods:
                key=component+'.'+method;api_checks[key]=component+'.prototype.'+method in text
                if not api_checks[key]:self.error('r28_api_missing',method=key)
        if self.engine_source:
            for component,methods in {'UnitMotion':['GetCurrentSpeed','SetSpeedMultiplier'],'RangeManager':['SetLosRevealAll']}.items():
                p=self.engine_source/'source/simulation2/components'/('ICmp'+component+'.cpp');text=p.read_text() if p.exists() else ''
                for method in methods:
                    key=component+'.'+method;api_checks[key]=bool(re.search(r'DEFINE_INTERFACE_METHOD\("'+method+'"',text))
                    if not api_checks[key]:self.error('r28_native_api_missing',method=key)
        self.checks['selected_r28_apis']=api_checks
    def run_js_tests(self):
        test_files=sorted(str(p.relative_to(self.project)) for p in (self.project/'tests').glob('*.test.cjs'))
        try:result=subprocess.run(['node','--test','--test-reporter=tap',*test_files],cwd=self.project,text=True,capture_output=True,timeout=60)
        except (OSError,subprocess.TimeoutExpired) as e:self.error('campaign_tests_unavailable',detail=str(e));return
        report={'exit_code':result.returncode,'files':test_files,'scope':'Pure campaign/politics/save tests plus explicitly mocked controller/GUI tests; not native acceptance'}
        for key in ['tests','pass','fail','skipped']:
            m=re.search(r'^# '+key+r' (\d+)',result.stdout,re.M);report[key]=int(m.group(1)) if m else None
        if result.returncode:self.error('campaign_tests_failed',output=(result.stdout+result.stderr)[-12000:])
        self.checks['campaign_tests']=report
    def run(self,js_tests=True):
        self.check_mod();self.check_xml_and_license();self.check_templates();self.check_terrain();self.check_assets();self.check_bridge()
        if js_tests:self.run_js_tests()
        self.vfs.close()
        return {'pass':not self.errors,'scope':'Static merged-VFS, dependency, template inheritance, asset reference/hash/license metadata, selected R28 APIs and pure campaign tests. No game launch, GPU, Windows, FPS or complete XML schema certification.','checks':self.checks,'errors':self.errors,'warnings':self.warnings}

class SelfTests(unittest.TestCase):
    def test_vfs_override_cache_missing_and_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);mod=root/'mod';mod.mkdir();(mod/'file.xml').write_text('override');zip_path=root/'public.zip'
            with ZipFile(zip_path,'w') as z:z.writestr('file.xml','base');z.writestr('mesh.dae.cached.pmd',b'cached')
            v=VFS(mod,zip_path)
            self.assertEqual(v.resolve('file.xml')['bytes'],b'override');self.assertEqual(v.resolve('mesh.dae')['provider'],'release28-cache');self.assertIsNone(v.resolve('missing'));self.assertIsNone(v.resolve('../secret'));self.assertIsNone(v.resolve('/secret'));v.close()
    def test_asset_reference_types(self):
        root=ET.fromstring('<actor><mesh>a.dae</mesh><material>m.xml</material><prop actor="p.xml"/><variant file="v.xml"/><texture file="t.png"/><animation file="a.dae"/></actor>')
        self.assertEqual(list(art_references(root)),['art/meshes/a.dae','art/materials/m.xml','art/actors/p.xml','art/variants/v.xml','art/textures/skins/t.png','art/animation/a.dae'])
    def test_manifest_detects_modified_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);mod=root/'mods/kazakh_total_war';(mod/'art').mkdir(parents=True);(root/'docs').mkdir();(mod/'art/test.bin').write_bytes(b'modified')
            (root/'docs/asset-manifest-millennium.json').write_text(json.dumps({'files':{'art/test.bin':{'output_sha256':sha(b'original'),'license':'CC-BY-SA-3.0','attribution':'Example'}}}))
            public=root/'public.zip'
            with ZipFile(public,'w') as z:z.writestr('mod.json','{}')
            v=Validator(root,public);v.check_assets();v.vfs.close()
            self.assertEqual([e['code'] for e in v.errors],['manifest_hash_mismatch'])
    def test_inheritance_uses_r28_mixins_and_detects_cycles(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);mod=root/'mods/kazakh_total_war';mod.mkdir(parents=True);public=root/'public.zip'
            with ZipFile(public,'w') as z:
                z.writestr('simulation/templates/base.xml','<Entity><Health/><Position/></Entity>')
                z.writestr('simulation/templates/mixins/builder.xml','<Entity><Builder/></Entity>')
                z.writestr('simulation/templates/unit.xml','<Entity parent="builder|base"><Health disable=""/></Entity>')
                z.writestr('simulation/templates/cycle.xml','<Entity parent="cycle"/>')
            v=Validator(root,public);v.component_names={'Health','Position','Builder'}
            self.assertEqual(set(v.template('unit')),{'Position','Builder'});self.assertEqual(v.errors,[])
            v.template('cycle');v.vfs.close();self.assertEqual(v.errors[0]['code'],'template_cycle')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--public',type=Path);parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parent.parent);parser.add_argument('--engine-source',type=Path);parser.add_argument('--skip-js-tests',action='store_true');parser.add_argument('--self-test',action='store_true');a=parser.parse_args()
    if a.self_test:
        result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests));print(json.dumps({'self_tests':result.testsRun,'pass':result.wasSuccessful()}));return 0 if result.wasSuccessful() else 1
    if not a.public:parser.error('--public path is required unless --self-test')
    if not a.engine_source:
        candidate=a.public.resolve().parents[4]
        if (candidate/'source').is_dir():a.engine_source=candidate
    try:report=Validator(a.project.resolve(),a.public.resolve(),a.engine_source).run(not a.skip_js_tests)
    except Exception as e:report={'pass':False,'errors':[{'code':'validator_exception','detail':str(e)}]}
    print(json.dumps(report,indent=2,ensure_ascii=False));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
