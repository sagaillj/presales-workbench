"""Verified release downloads and workspace-preserving local update execution."""
from pathlib import Path
import hashlib,json,re,stat,subprocess,sys,tempfile,zipfile
import urllib.request,urllib.parse
import product_feedback as feedback
import workbench_updates as updates
from runtime_lock import exclusive

ARCHIVE='presales-workbench-starter-latest.zip'
CHECKSUM='presales-workbench-starter-latest.sha256'
MAX_ZIP=100*1024*1024

def download(url,limit):
    class OfficialRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            parsed=urllib.parse.urlsplit(newurl)
            if parsed.scheme!='https' or parsed.hostname not in {'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}:
                raise ValueError('Unexpected release download redirect')
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    request=urllib.request.Request(url,headers={'User-Agent':'Workbench-updater'})
    with urllib.request.build_opener(OfficialRedirect()).open(request,timeout=45) as response:data=response.read(limit+1)
    if len(data)>limit:raise ValueError('Release asset exceeds size limit')
    return data

def verify(archive,version,expected,extract=None):
    if hashlib.sha256(archive).hexdigest()!=expected:raise ValueError('Release ZIP checksum mismatch')
    import io
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        rows=bundle.infolist();names=[r.filename for r in rows]
        if len(rows)>3000 or len(set(names))!=len(names) or sum(r.file_size for r in rows)>200*1024*1024:raise ValueError('Invalid release ZIP size or duplicate paths')
        prefix='presales-workbench-starter/'
        for row in rows:
            path=Path(row.filename)
            if not row.filename.startswith(prefix) or path.is_absolute() or '..' in path.parts or '\\' in row.filename or any(p.casefold() in {'workspace','.git'} for p in path.parts) or stat.S_ISLNK(row.external_attr>>16):raise ValueError('Unsafe release ZIP path')
        manifest=json.loads(bundle.read(prefix+'BUNDLE-MANIFEST.json'))
        if manifest.get('release')!=version or bundle.read(prefix+'VERSION').decode().strip()!=version:raise ValueError('Release version mismatch')
        files=manifest['files']
        actual={r.filename[len(prefix):] for r in rows if not r.is_dir()}
        if actual!=set(files)|{'BUNDLE-MANIFEST.json'} or not {'VERSION','workbench.py','scripts/upgrade_existing.py'}<=set(files):raise ValueError('Incomplete release manifest')
        for name,info in files.items():
            if hashlib.sha256(bundle.read(prefix+name)).hexdigest()!=info['sha256']:raise ValueError('Release manifest mismatch: '+name)
        if extract:
            bundle.extractall(extract)
            for row in rows:
                if not row.is_dir() and row.external_attr>>16&0o111:(Path(extract)/row.filename).chmod(0o755)
    return manifest

def stage(root,result,fetch_bytes=download):
    version=result['latest'];feedback.version_tuple(version)
    if type(result.get('release_id')) is not int or result['release_id']<=0:raise ValueError('Missing release identity')
    folder=Path(root)/'workspace/update-downloads'/('v'+version);folder.mkdir(parents=True,exist_ok=True)
    base='https://github.com/'+feedback.REPOSITORY+'/releases/download/v'+version+'/'
    receipt=folder/'verified.json';zip_path=folder/ARCHIVE
    if receipt.is_file() and zip_path.is_file():
        saved=feedback.read(receipt,{})
        if saved.get('release_id')!=result['release_id']:raise ValueError('Release identity changed; review required')
        verify(zip_path.read_bytes(),version,saved['sha256'])
        return saved
    checksum=fetch_bytes(base+CHECKSUM,4096).decode().strip()
    match=re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?'+re.escape(ARCHIVE),checksum)
    if not match:raise ValueError('Invalid release checksum asset')
    archive=fetch_bytes(base+ARCHIVE,MAX_ZIP);expected=match[1].lower()
    verify(archive,version,expected)
    zip_path.write_bytes(archive)
    saved={'version':version,'release_id':result['release_id'],'sha256':expected,'release_url':result['release_url']}
    feedback.write(receipt,saved);return saved

def install(root,folder,approval):
    root=Path(root).resolve();version=approval['version'];feedback.version_tuple(version)
    if not (root/'BUNDLE-MANIFEST.json').is_file() or (root/'.git').exists():raise ValueError('Automatic installation requires a managed standalone release, never a development checkout')
    download_dir=root/'workspace/update-downloads'/('v'+version)
    receipt=feedback.read(download_dir/'verified.json',{})
    if receipt.get('release_id')!=approval.get('release_id') or receipt.get('version')!=version:raise ValueError('Staged release identity does not match the queued update')
    with exclusive(root/'workspace/.app-runtime.lock'), tempfile.TemporaryDirectory(prefix='install-',dir=download_dir) as extracted:
        verify((download_dir/ARCHIVE).read_bytes(),version,receipt['sha256'],Path(extracted))
        source=Path(extracted)/'presales-workbench-starter'
        # The existing verified helper provides preflight, journal replay, backups and rollback.
        done=subprocess.run([sys.executable,str(source/'scripts/upgrade_existing.py'),str(root)],capture_output=True,text=True,timeout=180)
        if done.returncode:raise ValueError((done.stderr or done.stdout)[-1600:])
        outcome=json.loads(done.stdout)
        if (root/'VERSION').read_text().strip()!=version or not outcome.get('workspace_preserved'):raise ValueError('Installed version readback failed')
        updates.finish(folder,version,'installed','Verified installed VERSION, manifest preflight and preserved workspace. Restart this Workbench and verify its saved progress.')
        return {**outcome,'restart_required':True}

def daily(root,folder,*,force=False,fetch=None,fetch_bytes=download,install_now=False):
    root,folder=Path(root),Path(folder)
    with exclusive(root/'workspace/.daily-update.lock'):
        installed=(root/'VERSION').read_text().strip() if (root/'VERSION').exists() else feedback.VERSION
        result=updates.state(folder,force=force,installed=installed,fetch=fetch,root=root)
        approval=result.get('approval') or {}
        if result.get('status')!='checked':return result
        if not result.get('available'):
            if approval.get('version')==installed and approval.get('status') in {'queued','running','blocked'}:return updates.finish(folder,installed,'installed','Installed VERSION verified on the next daily review.')
            return result
        automatic=result['daily_enabled'] and result['auto_install_enabled']
        if automatic and approval.get('status')!='running':
            updates.update(folder,{'action':'approve','version':result['latest']},installed=installed)
            saved=feedback.read(folder/updates.FILE,{})
            saved['approval']['automatic']=True;feedback.write(folder/updates.FILE,saved)
            approval=saved['approval']
        if approval.get('automatic') and not automatic:return result
        if approval.get('status') not in {'queued','blocked'}:return result
        try:
            if approval['version']!=result['latest'] or approval['release_id']!=result['release_id']:raise ValueError('Queued release changed. Review the current release before installing.')
            stage(root,result,fetch_bytes)
            if install_now:
                outcome=install(root,folder,approval)
                return {**updates.state(folder,installed=approval['version']), 'installation':outcome}
            saved=feedback.read(folder/updates.FILE,{});saved['approval'].update(status='queued',download_verified=True);feedback.write(folder/updates.FILE,saved)
            return {**updates.public(saved,root),'workflow_action':'Update downloaded and verified. Without another approval, stop ONLY this Workbench server, run python3 scripts/check_updates.py --install-staged, restart this same installation on its existing URL, and verify VERSION plus saved progress. Record blockers in the single Internal work update card. Do not stop unrelated apps or add source access, schedules or external action grants.'}
        except Exception as error:
            return updates.finish(folder,approval['version'],'blocked',str(error))
