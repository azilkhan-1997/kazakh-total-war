#!/usr/bin/env python3
"""Static resource closure check. Does not assert rendered or playable output."""
from pathlib import Path
from zipfile import ZipFile
import argparse,json,hashlib,xml.etree.ElementTree as E
P=argparse.ArgumentParser();P.add_argument('--public-zip',default='../upstream/0ad-0.28.0/binaries/data/mods/public/public.zip');a=P.parse_args()
mod=Path('mods/kazakh_total_war');z=ZipFile(a.public_zip);ns=set(z.namelist());seen={};missing=[]
starts=['art/actors/ktw/units/'+n+'.xml' for n in ['mounted_archer','light_cavalry','heavy_cavalry','spearman','infantry_archer']]+['art/skeletons/ktw_millennium_bow.xml']
def resource(path):
 if (mod/path).is_file():return ('module',path,(mod/path).read_bytes())
 if path in ns:return ('release28',path,z.read(path))
 for suffix in ['.cached.pmd','.cached.psa','.cached.dds','.cached.xmb']:
  if path+suffix in ns:return ('release28-cache',path+suffix,z.read(path+suffix))
 return None

def refs(root):
 for node in root.iter():
  if node.tag=='mesh' and node.text:yield 'art/meshes/'+node.text.strip()
  if node.tag=='material' and node.text and node.text.strip():yield 'art/materials/'+node.text.strip()
  if node.tag=='prop' and node.get('actor'):yield 'art/actors/'+node.get('actor')
  if node.tag=='variant' and node.get('file'):yield 'art/variants/'+node.get('file')
  if node.tag=='texture' and node.get('file'):yield 'art/textures/skins/'+node.get('file')
  if node.tag=='animation' and node.get('file'):yield 'art/animation/'+node.get('file')

def visit(path,via=None):
 if path in seen:return
 r=resource(path)
 if not r:missing.append({'resource':path,'referenced_by':via});seen[path]={'missing':True};return
 kind,actual,raw=r;seen[path]={'provider':kind,'physical_path':actual,'sha256':hashlib.sha256(raw).hexdigest()}
 if path.endswith('.xml') and actual.endswith('.xml'):
  try:root=E.fromstring(raw)
  except Exception as e:missing.append({'parse_error':str(e),'path':path});return
  for ref in refs(root):visit(ref,path)
for s in starts:visit(s)
report={'scope':'Recursive actor/prop/variant/material/mesh/texture/animation resource paths; accepts official cached PMD/PSA/DDS/XMB. Does not validate GPU, COLLADA rig equivalence or material shader execution.','roots':starts,'resources':seen,'missing':missing,'pass':not missing,'resource_count':len(seen),'providers':{p:sum(v.get('provider')==p for v in seen.values()) for p in ['module','release28','release28-cache']}}
Path('docs/art-closure-release28.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['resources','roots']}));raise SystemExit(bool(missing))
