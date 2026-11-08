from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, tempfile, ast
parser=argparse.ArgumentParser(description='Independent offline installer source/helper QA; never executes setup')
parser.add_argument('--project',type=Path,required=True)
parser.add_argument('--report-dir',type=Path,required=True)
args=parser.parse_args()
project=args.project.resolve()
root=args.report_dir.resolve();root.mkdir(parents=True,exist_ok=True)
script=project/'installer/windows/build_offline_qa.py'
spec=importlib.util.spec_from_file_location('reviewed_builder',script); builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
rows=[]
def case(name, action, pattern=None):
 try: result=action()
 except Exception as exc:
  rows.append({'name':name,'pass':pattern is not None and pattern in str(exc),'error':str(exc)})
 else:
  rows.append({'name':name,'pass':pattern is None and result is not False})
with tempfile.TemporaryDirectory(prefix='builder-fixtures-',dir=root) as d:
 d=Path(d); good=d/'good.bin';good.write_bytes(b'verified original fixture')
 data=good.read_bytes();sha=hashlib.sha256(data).hexdigest()
 case('verified component accepted',lambda:builder.verify_component(good,'good',len(data),sha)['sha256']==sha)
 case('missing component rejected',lambda:builder.verify_component(d/'missing','missing',len(data),sha),'Missing or linked')
 case('wrong size rejected',lambda:builder.verify_component(good,'good',len(data)+1,sha),'Wrong component size')
 case('wrong hash rejected',lambda:builder.verify_component(good,'good',len(data),'0'*64),'Wrong component SHA-256')
 link=d/'linked.bin';link.symlink_to(good)
 case('symlink rejected',lambda:builder.verify_component(link,'linked',len(data),sha),'Missing or linked')
 foreign=d/'foreign';(foreign/'installer/windows').mkdir(parents=True);(foreign/'installer/windows/vendor.exe').write_bytes(b'vendor')
 payload=d/'payload';payload.mkdir()
 case('binary package rejected from own source snapshot',lambda:builder.snapshot(foreign,good,payload,'test',True),'Do not vendor binary packages')
# Independent static checks make no claims about Windows runtime behavior.
bootstrap=(project/'installer/windows/OfflineBootstrap.ps1').read_text()
nsi=(project/'installer/windows/OfflineGameSetup.nsi').read_text()
network_markers=['WebClient','DownloadFile','Invoke-WebRequest','Invoke-RestMethod','Start-BitsTransfer','Get-VerifiedFile','Resolve-DnsName']
case('offline bootstrap has no acquisition commands',lambda:not any(word in bootstrap for word in network_markers))
case('every pinned input checked before execution',lambda:max(bootstrap.index("Get-EmbeddedComponent '"+name+"'") for _,name,_,_ in builder.COMPONENTS)<bootstrap.index('Expand-Archive -LiteralPath $pythonZip'))
case('component inventory exact match enforced',lambda:'Compare-Object $expectedNames $actualNames -CaseSensitive' in bootstrap)
case('NSIS component directory separate from payload',lambda:'SetOutPath "$PLUGINSDIR\\components"' in nsi and '-ComponentRoot "$PLUGINSDIR\\components"' in nsi and '-PayloadRoot "$PLUGINSDIR\\payload"' in nsi)
case('NSIS retains component compression disabled',lambda:nsi.index('SetCompress off')<nsi.index('File /oname=0ad-0.28.0-win64.exe')<nsi.index('SetCompress auto'))
case('official component checks align with PowerShell pins',lambda:all(str(size) in bootstrap and sha in bootstrap for _,name,size,sha in builder.COMPONENTS))
case('builder has no networking imports',lambda:not any(n.name.split('.')[0] in {'urllib','requests','socket','http','httpx'} for node in ast.walk(ast.parse(script.read_text())) for n in (node.names if isinstance(node,ast.Import) else [])))
paths=['Bootstrap.ps1','GameSetup.nsi','build_installer.py','setup_worker.py','Uninstall-KTW.ps1']
unchanged=subprocess.run(['git','diff','--exit-code','d87603fe71a7f390862bcfb0c0be1aafaf520774','--',*[f'installer/windows/{p}' for p in paths]],cwd=project,capture_output=True,text=True)
case('five existing online files unchanged against base',lambda:unchanged.returncode==0)
report={'pass':all(r['pass'] for r in rows),'cases':rows,'source_hashes':{name:hashlib.sha256((project/'installer/windows'/name).read_bytes()).hexdigest() for name in ['OfflineBootstrap.ps1','OfflineGameSetup.nsi','build_offline_qa.py']},'native_windows_execution':False,'licensing_clearance':False,'scope':'Independent Python helper execution and source assertions; not Windows installation, OS guard bypass or gameplay execution.'}
(root/'independent-python-and-source-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(not report['pass'])
