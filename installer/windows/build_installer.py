#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build the single EXE installer; runtime downloads remain official publisher files."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, struct, subprocess, tempfile

PROJECT = Path(__file__).resolve().parents[2]
PRODUCT = 'SAYRAM_PLANETA_KAZAKH_TOTAL_WAR'
LAUNCHER_SHA = '3c1906f7b2c384d2470c4ddcdf35b1da01697f61260fdb3033e44d9c3e12f969'


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
    return h.hexdigest()


def build(project,launcher,output,makensis,nsis_dir):
    project,launcher,output=map(lambda x:Path(x).resolve(),(project,launcher,output))
    assert sha(launcher)==LAUNCHER_SHA, 'Launcher must be the verified existing AMD64 binary'
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True,stderr=subprocess.DEVNULL).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=project,text=True).strip())
    except (subprocess.CalledProcessError,FileNotFoundError):
        revision=None;dirty=None
    epoch=int(os.environ.get('SOURCE_DATE_EPOCH','1794096000'))
    with tempfile.TemporaryDirectory(prefix='ktw-single-exe-build-') as temp:
        temp=Path(temp);payload=temp/'payload';payload.mkdir()
        roots=['mods','launcher','tools','docs','research','tests','LICENSES','installer/windows','evidence']
        for root in roots:
            source=project/root
            if not source.exists():continue
            for p in source.rglob('*'):
                rel=p.relative_to(project)
                if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or p.suffix in ('.pyc','.partial'):continue
                if root=='evidence' and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.mp4','.mov','.wav','.ogg'):continue
                if root=='installer/windows' and any(x in rel.parts for x in ('vendor','build','dist')):continue
                target=payload/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        for name in ['LICENSE','README_RU.md','THIRD_PARTY_NOTICES.md','RELEASE.json']:
            if (project/name).is_file():shutil.copy2(project/name,payload/name)
        shutil.copy2(launcher,payload/'KazakhTotalWar.exe')
        # Windows PowerShell5.1 recognises UTF-8 text reliably with a BOM.
        for p in (payload/'installer/windows').glob('*.ps1'):
            p.write_text(p.read_text(encoding='utf-8-sig'),encoding='utf-8-sig')
        files=[{'path':p.relative_to(payload).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(payload.rglob('*')) if p.is_file()]
        manifest={'schema':1,'product':PRODUCT,'delivery_version':'0.4.0','module_version':'0.2.0','source_revision':revision,'source_dirty':dirty,'files':files}
        (payload/'PAYLOAD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
        manifest_sha=sha(payload/'PAYLOAD_MANIFEST.json')
        for p in payload.rglob('*'):
            if p.is_file():os.utime(p,(epoch,epoch))
        built=temp/'KazakhTotalWar_Setup_0.4.0.exe'
        env=dict(os.environ);env['NSISDIR']=str(Path(nsis_dir).resolve())
        cmd=[str(Path(makensis).resolve()),'-V3','-WX','-DPAYLOAD_DIR='+str(payload),'-DOUTPUT_FILE='+str(built),'-DPAYLOAD_SHA='+manifest_sha,str(project/'installer/windows/GameSetup.nsi')]
        proc=subprocess.run(cmd,env=env,capture_output=True,text=True)
        log=proc.stdout+proc.stderr
        (output.parent/'installer-build.log').write_text(log)
        if proc.returncode:raise RuntimeError(log)
        data=built.read_bytes();assert data[:2]==b'MZ'
        pe=int.from_bytes(data[60:64],'little');assert data[pe:pe+4]==b'PE\0\0'
        machine=struct.unpack_from('<H',data,pe+4)[0]
        assert machine==0x14c, 'Expected standard NSIS x86 stub with explicit x64 OS requirement'
        partial=output.with_suffix('.exe.partial')
        with built.open('rb') as src,partial.open('wb') as dst:
            shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
        assert sha(built)==sha(partial)
        os.replace(partial,output)
        report={'delivery_version':'0.4.0','game_module_version':'0.2.0','source_revision':revision,'source_dirty':dirty,'source_date_epoch':epoch,'file':output.name,'bytes':output.stat().st_size,'sha256':sha(output),'pe_machine':'I386 NSIS installer stub; requires Windows10/11 x64 and installs AMD64 game','payload_files':len(files),'payload_manifest_sha256':manifest_sha,'launcher_sha256':sha(launcher),'engine_binaries_redistributed':False,'user_installed_python_required':False,'official_private_python_downloaded_at_setup':True,'internet_required_during_first_setup':True,'offline_game_after_install_intended':True,'native_windows_install_tested':False,'native_windows_gameplay_tested':False,'nsis_command':cmd,'nsis_version':subprocess.check_output([str(Path(makensis).resolve()),'-VERSION'],env=env,text=True).strip()}
        (output.parent/'installer-build.json').write_text(json.dumps(report,indent=2)+'\n')
        (output.parent/'installer-payload-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,default=PROJECT)
    ap.add_argument('--launcher',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--makensis',type=Path,required=True)
    ap.add_argument('--nsis-dir',type=Path,required=True)
    a=ap.parse_args();build(a.project,a.launcher,a.output,a.makensis,a.nsis_dir)
