"""Daily GitHub checks, automatic-update preference and a version-pinned queue."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import threading
import product_feedback as feedback

_LOCK=threading.RLock()
FILE='workbench-updates.json'

def _now(now=None):return now or datetime.now(timezone.utc)
def _due(stamp,now):
    try:return now-datetime.fromisoformat(stamp.replace('Z','+00:00'))>=timedelta(days=1)
    except (ValueError,TypeError,AttributeError):return True

def state(folder, *, force=False, now=None, fetch=None, installed=None, root=None):
    folder=Path(folder);now=_now(now)
    with _LOCK:
        saved=feedback.read(folder/FILE,{'daily_enabled':True})
        if force or (checks_enabled(saved,root) and _due(saved.get('checked_at'),now)):
            result=feedback.release_status(installed=installed,fetch=fetch)
            saved.update(result=result,checked_at=now.isoformat())
            feedback.write(folder/FILE,saved)
        return public(saved,root)

def checks_enabled(saved,root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    profile=feedback.read(root/'workspace/profile.json',{})
    features=profile.get('preferences',{}).get('automatic_features',{}).get('features',{})
    return saved.get('daily_enabled',True) and features.get('workbench_update_checks',True)

def public(saved,root=None):
    result=dict(saved.get('result') or {'status':'not_checked','available':False,'url':feedback.LATEST})
    return {**result,'checked_at':saved.get('checked_at'),'daily_enabled':checks_enabled(saved,root),'auto_install_enabled':saved.get('auto_install_enabled',True),'approval':saved.get('approval')}

def update(folder,body,*,now=None,fetch=None,installed=None):
    if not isinstance(body,dict):raise ValueError('Expected update action')
    folder=Path(folder);now=_now(now);action=body.get('action')
    with _LOCK:
        if action=='check':return state(folder,force=True,now=now,fetch=fetch,installed=installed)
        saved=feedback.read(folder/FILE,{'daily_enabled':True});result=saved.get('result',{})
        if action in {'daily_enabled','auto_install_enabled'}:
            if not isinstance(body.get('enabled'),bool):raise ValueError('Expected enabled true or false')
            saved[action]=body['enabled']
            if not body['enabled'] and (saved.get('approval') or {}).get('automatic') and saved['approval']['status']!='running':saved['approval']=None
        elif action=='approve':
            if result.get('status')!='checked' or not result.get('available') or result.get('latest')!=body.get('version'):raise ValueError('That release is no longer available. Check for updates first.')
            feedback.version_tuple(result['latest'])
            if _due(saved.get('checked_at'),now):raise ValueError('Check for updates again before approving this release.')
            prior=saved.get('approval') or {}
            if prior.get('status') in {'queued','running'} and prior.get('version')==result['latest']:return public(saved)
            saved['approval']={'version':result['latest'],'release_url':result.get('release_url') or 'https://github.com/'+feedback.REPOSITORY+'/releases/tag/v'+result['latest'],'release_id':result.get('release_id'),'status':'queued','approved_at':now.isoformat(),'prompt':result['upgrade_prompt']}
        elif action=='cancel':
            if (saved.get('approval') or {}).get('status')=='running':raise ValueError('The update is already running.')
            if saved.get('approval'):
                saved.setdefault('history',[]).append({**saved['approval'],'status':'cancelled','cancelled_at':now.isoformat()});saved['approval']=None
        else:raise ValueError('Unknown update action')
        feedback.write(folder/FILE,saved);return public(saved)

def finish(folder,version,status,detail,*,now=None):
    """Called by the workflow after verified installation, or an exact preflight blocker."""
    if status not in {'installed','blocked','running'}:raise ValueError('Invalid update outcome')
    with _LOCK:
        folder=Path(folder);saved=feedback.read(folder/FILE,{});approval=saved.get('approval') or {}
        if approval.get('version')!=version or approval.get('status') not in {'queued','running','blocked'}:raise ValueError('No matching approved release')
        approval.update(status=status,detail=str(detail)[:1200],updated_at=_now(now).isoformat());saved['approval']=approval
        if status=='installed':saved['result']={**saved.get('result',{}),'installed':version,'available':False}
        feedback.write(folder/FILE,saved);return public(saved)
