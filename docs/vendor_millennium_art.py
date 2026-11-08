#!/usr/bin/env python3
"""Vendor the admitted Millennium art subset from pinned checkout; run from project root."""
from pathlib import Path
import argparse, copy, hashlib, json, subprocess
import xml.etree.ElementTree as E
P=argparse.ArgumentParser();P.add_argument('--upstream',default='../upstream/millenniumad');a=P.parse_args()
SRC=Path(a.upstream).resolve();OUT=Path('mods/kazakh_total_war').resolve();DOC=Path('docs')
commit=subprocess.check_output(['git','-C',str(SRC),'rev-parse','HEAD'],text=True).strip()
if commit!='91636b405ee8d0088ec3a34fba6074dbd5c9d0f3':raise SystemExit('Unexpected source commit')
tracked=set(subprocess.check_output(['git','-C',str(SRC),'ls-files'],text=True).splitlines());records={};external=set()
CATS={'mesh':'art/meshes/','material':'art/materials/','particle':'art/particles/'}
def digest(b):return hashlib.sha256(b).hexdigest()
def refs(node):
 if node.tag in CATS and node.text:return CATS[node.tag],node.text.strip(),None
 if node.tag=='prop' and node.get('actor'):return 'art/actors/',node.get('actor'),'actor'
 if node.tag=='variant' and node.get('file'):return 'art/variants/',node.get('file'),'file'
 if node.tag=='texture' and node.get('file'):return 'art/textures/skins/',node.get('file'),'file'
 if node.tag=='animation' and node.get('file'):return 'art/animation/',node.get('file'),'file'
 return None

def xmlbytes(root):
 E.indent(root,space='  ');return b'<?xml version="1.0" encoding="utf-8"?>\n'+E.tostring(root,encoding='utf-8')+b'\n'

def transform(root):
 for node in root.iter():
  r=refs(node)
  if not r:continue
  prefix,ref,attr=r
  if ref.startswith('ktw/'):continue
  relative=prefix+ref
  if relative in tracked:
   dstref='ktw/millennium/'+ref;vendor(relative,prefix+dstref)
   if attr:node.set(attr,dstref)
   else:node.text=dstref
  else:external.add(relative)
 return root

def vendor(relative,dst):
 if dst in records:return
 raw=(SRC/relative).read_bytes();records[dst]={'source_path':relative,'source_sha256':digest(raw),'source_commit':commit,'license':'CC-BY-SA-3.0','attribution':'The Council of Modders, Fallen Empire Studio, Scion Development','modifications':[]}
 if relative.endswith('.xml'):
  raw=xmlbytes(transform(E.fromstring(raw)));records[dst]['modifications']=['Resource references namespaced under ktw/millennium.']
 target=OUT/dst;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);records[dst]['output_sha256']=digest(raw)

def outactor(name,root,origins,changes):
 raw=xmlbytes(transform(root));p=OUT/'art/actors/ktw/units'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 records[str(p.relative_to(OUT))]={'source_paths':origins,'source_commit':commit,'source_sha256s':{f:digest((SRC/f).read_bytes()) for f in origins},'output_sha256':digest(raw),'license':'CC-BY-SA-3.0','attribution':'The Council of Modders, Fallen Empire Studio, Scion Development; adapted by SAYRAM PLANETA HOLDING','modifications':changes}

rider_source='art/actors/units/rus/cavalry_archer_b_r.xml';horse_source='art/actors/units/rus/cavalry_archer_b_m.xml';rider=E.parse(SRC/rider_source).getroot()
for tex in rider.findall('.//texture'):
 f=tex.get('file','')
 if f.endswith('xion_cloth_norm.png'):tex.set('name','normTex')
 if f.endswith('xion_cloth_spec.png'):tex.set('name','specTex')
for group in list(rider.findall('group')):
 textures=group.findall('.//texture')
 if textures and all(t.get('file') in ['default_norm.png','null_black.dds'] for t in textures):rider.remove(group)
outactor('mounted_archer_rider.xml',copy.deepcopy(rider),[rider_source],['Corrected normal/specular slots; removed final overriding flat texture group.','Nomad visual proxy, not authenticated 1465 costume.'])
horse=E.parse(SRC/horse_source).getroot()
for p in horse.findall('.//prop'):
 if p.get('actor')=='units/rus/cavalry_archer_b_r.xml':p.set('actor','ktw/units/mounted_archer_rider.xml')
outactor('mounted_archer.xml',copy.deepcopy(horse),[horse_source],['Rider replaced by corrected namespaced mounted archer.'])

def warrior(heavy=False,infantry=False,archer=False):
 r=copy.deepcopy(rider)
 for group in list(r.findall('group')):
  if group.find('variant[@file]') is not None or group.find("variant[@name='Idle']") is not None:r.remove(group)
 props=r.find('group/variant/props')
 for p in list(props):
  if p.get('attachpoint')!='head':props.remove(p)
 if archer:
  E.SubElement(props,'prop',{'actor':'props/units/weapons/xion_bow.xml','attachpoint':'weapon_bow'})
  E.SubElement(props,'prop',{'actor':'props/units/weapons/arrow_back.xml','attachpoint':'weapon_R'})
  E.SubElement(props,'prop',{'actor':'props/units/weapons/xion_quiver_cloth_cavalry_left.xml','attachpoint':'sheath_L'})
 else:E.SubElement(props,'prop',{'actor':'props/units/weapons/spear.xml' if infantry else 'props/units/weapons/spear_lance_cavalry.xml','attachpoint':'weapon_R'})
 if heavy:
  for p in r.findall('.//prop'):
   if p.get('attachpoint')=='helmet':p.set('actor','props/units/helmets/byza_archer_helmet_basic_iron.xml')
 group=E.SubElement(r,'group')
 variant='biped/base_archer_relax.xml' if archer else ('biped/base_spearman_shield_relax_celt.xml' if infantry else 'biped/rider/cavalry/base_spearman_relax_shield_01.xml')
 E.SubElement(group,'variant',{'file':variant,'frequency':'1'})
 group=E.SubElement(r,'group');E.SubElement(group,'variant',{'name':'Idle','frequency':'1'})
 if archer:E.SubElement(group,'variant',{'file':'biped/attack_ranged_archer.xml'})
 E.SubElement(group,'variant',{'file':'biped/death_infantry.xml' if infantry else 'biped/rider/death.xml'})
 return r

for kind,heavy,infantry,archer in [('light_cavalry',False,False,False),('heavy_cavalry',True,False,False),('spearman',False,True,False),('infantry_archer',False,True,True)]:
 root=warrior(heavy,infantry,archer)
 if infantry:outactor(kind+'.xml',root,[rider_source],['Composite: nomad body with base-game infantry animations and weapon props.','Prototype; authentic equipment reconstruction pending.'])
 else:
  outactor(kind+'_rider.xml',root,[rider_source],['Composite: nomad body, spear cavalry animation, '+('iron helmet.' if heavy else 'cloth headgear.'),'Prototype, not final historical armor.'])
  mount=copy.deepcopy(horse)
  for p in mount.findall('.//prop'):
   if p.get('actor')=='ktw/units/mounted_archer_rider.xml':p.set('actor','ktw/units/'+kind+'_rider.xml')
  for v in mount.findall('.//variant'):
   if v.get('file')=='quadraped/base_horse_javelin.xml':v.set('file','quadraped/base_horse_pace.xml')
  if heavy:E.SubElement(mount.find('group/variant/props'),'prop',{'actor':'props/horse/cav_armor_umayyad_lamellar.xml','attachpoint':'root'})
  outactor(kind+'.xml',mount,[horse_source],['Horse/rider composite with namespaced '+kind+' adapter.'])
vendor('art/skeletons/bow.xml','art/skeletons/ktw_millennium_bow.xml')
license_file=OUT/'art/ktw-MILLENNIUM-LICENSE.txt';license_file.write_text((SRC/'art/license.txt').read_text()+'\n\nSource: https://github.com/0ADMods/millenniumad/tree/'+commit+'\nAdaptations: SAYRAM PLANETA HOLDING. File provenance: docs/asset-manifest-millennium.json.\n',encoding='utf-8')
report={'source_repository':'https://github.com/0ADMods/millenniumad','commit':commit,'asset_license':'CC-BY-SA-3.0','license_source':'art/license.txt','license_sha256':digest((SRC/'art/license.txt').read_bytes()),'status':'static subset admission; engine-render verification required','files':records,'external_base_game_references':sorted(external)}
(DOC/'asset-manifest-millennium.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'vendored_files':len(records),'external_references':len(external),'bytes':sum((OUT/f).stat().st_size for f in records)}))
