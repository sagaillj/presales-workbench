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
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import local_changes

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def entries(root):
    path=root/'BUNDLE-MANIFEST.json'
    if not path.is_file():raise ValueError('This install has no bundle manifest. Ask your assistant to migrate it into a fresh verified release while preserving the private workspace.')
    return json.loads(path.read_text())['files']
def safe(root,name):
    relative=Path(name)
    if relative.is_absolute() or '..' in relative.parts or any(part.casefold()=='workspace' for part in relative.parts):raise ValueError('Unsafe manifest path: '+name)
    root=Path(root).resolve();target=root/relative
    try:target.resolve(strict=False).relative_to(root)
    except ValueError:raise ValueError('Upgrade path escapes installation: '+name)
    if target.is_symlink() or any(p.is_symlink() for p in target.parents if p!=root.parent):raise ValueError('Symlink upgrade target: '+name)
    return target

def upgrade(source,target,baseline_source=None):
    source,target=Path(source).resolve(),Path(target).resolve()
    if source==target or not (target/'workbench.py').exists():raise ValueError('Choose a different, existing starter folder.')
    new,old=entries(source),entries(target);conflicts=[];unchanged=set();planned={};reapplied=[]
    # Validate the complete incoming bundle before changing even local receipts.
    for name,info in new.items():
        if digest(safe(source,name))!=info['sha256']:raise ValueError('New release failed manifest: '+name)
        safe(target,name)
    if baseline_source is not None:local_changes.baseline(target,baseline_source)
    local_changes.capture(target)
    custom={row['path']:row for row in local_changes.load(target).get('files',[])}
    for name,info in new.items():
        src,dst=safe(source,name),safe(target,name)
        if name in old and info['sha256']==old[name]['sha256']:
            unchanged.add(name);continue
        if name in custom:
            try:planned[name]=local_changes.rebase(custom[name],src.read_bytes());reapplied.append(name)
            except ValueError as error:conflicts.append(name+' ('+str(error)+')')
        elif dst.exists() and digest(dst)!=info['sha256'] and (name not in old or digest(dst)!=old[name]['sha256']):conflicts.append(name)
        else:planned[name]=src.read_bytes()
    if conflicts:raise ValueError('Local edits preserved in workspace/LOCAL-CHANGES.md; reconcile before replacing conflicting files: '+', '.join(conflicts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');backup=target/'workspace/upgrade-backups'/stamp
    backup.mkdir(parents=True,exist_ok=False);replaced=[]
    try:
        for name in [key for key in new if key not in unchanged]+['BUNDLE-MANIFEST.json']:
            src,dst=safe(source,name),safe(target,name)
            if dst.exists():
                saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
            content=planned.get(name,src.read_bytes())
            if content is None:
                dst.unlink(missing_ok=True);replaced.append(name);continue
            dst.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dst.parent,delete=False) as f:temp=Path(f.name)
            try:
                temp.write_bytes(content)
                if src.stat().st_mode & 0o111:temp.chmod(src.stat().st_mode)
                os.replace(temp,dst);replaced.append(name)
            finally:temp.unlink(missing_ok=True)
    except BaseException:
        for name in reversed(replaced):
            dst=target/name;saved=backup/name
            if saved.exists():shutil.copy2(saved,dst)
            else:dst.unlink(missing_ok=True)
        raise
    local_changes.baseline(target,source)
    journal=local_changes.capture(target)
    return {'upgraded':True,'version':(target/'VERSION').read_text().strip(),'backup':str(backup),'workspace_preserved':True,'retained_removed_files':sorted(set(old)-set(new)),'customizations_reapplied':reapplied,'local_changes_journal':journal['journal']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Stop Workbench first. Preserves workspace and compatible app edits.');p.add_argument('existing_folder');p.add_argument('--baseline-folder',help='Verified original release folder for an older install without saved baseline bytes');args=p.parse_args()
    print(json.dumps(upgrade(Path(__file__).resolve().parents[1],Path(args.existing_folder),args.baseline_folder)))
