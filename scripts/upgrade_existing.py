#!/usr/bin/env python3
"""Upgrade owned app files after preflight; preserve the private workspace."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def entries(root):return json.loads((root/'BUNDLE-MANIFEST.json').read_text())['files']
def safe(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts or 'workspace' in relative.parts:raise ValueError('Unsafe manifest path: '+name)
    target=root/relative
    if target.is_symlink() or any(p.is_symlink() for p in target.parents if p!=root.parent):raise ValueError('Symlink upgrade target: '+name)
    return target

def upgrade(source,target):
    source,target=Path(source).resolve(),Path(target).resolve()
    if source==target or not (target/'workbench.py').exists():raise ValueError('Choose a different, existing starter folder.')
    new,old=entries(source),entries(target);conflicts=[]
    for name,info in new.items():
        src,dst=safe(source,name),safe(target,name)
        if digest(src)!=info['sha256']:raise ValueError('New release failed manifest: '+name)
        if dst.exists() and digest(dst)!=info['sha256'] and (name not in old or digest(dst)!=old[name]['sha256']):conflicts.append(name)
    if conflicts:raise ValueError('Locally edited files need review before any writes: '+', '.join(conflicts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup=target/'workspace/upgrade-backups'/stamp
    backup.mkdir(parents=True,exist_ok=False);replaced=[]
    try:
        for name in list(new)+['BUNDLE-MANIFEST.json']:
            src,dst=safe(source,name),safe(target,name)
            if dst.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
            dst.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as f:temp=Path(f.name)
            shutil.copy2(src,temp);os.replace(temp,dst);replaced.append(name)
    except BaseException:
        for name in reversed(replaced):
            dst=target/name;saved=backup/name
            if saved.exists():shutil.copy2(saved,dst)
            else:dst.unlink(missing_ok=True)
        raise
    return {'upgraded':True,'version':(target/'VERSION').read_text().strip(),'backup':str(backup),'workspace_preserved':True}

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Stop Workbench first. Preserves workspace and stops on app-file edits.');p.add_argument('existing_folder');args=p.parse_args()
    print(json.dumps(upgrade(Path(__file__).resolve().parents[1],Path(args.existing_folder))))
