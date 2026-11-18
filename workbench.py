#!/usr/bin/env python3
"""Portable, local-only Workbench. Python 3.10+; standard library only."""
import argparse
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
from urllib.parse import urlsplit, parse_qs
import webbrowser
import zipfile

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'app'))
import onboarding
import product_feedback
if (ROOT/'VERSION').exists():
    product_feedback.VERSION=(ROOT/'VERSION').read_text().strip()
from card_order import update_order
ALLOWED_DIRS={'.agents','.claude','app','automations','docs','examples','scripts'}
ALLOWED_FILES={'workbench.py','README.md','START-HERE.html','AGENTS.md','CLAUDE.md','profile.example.json','.gitignore','Start Workbench.command','Start Workbench.cmd','VERSION','RELEASE-NOTES.md','BUNDLE-MANIFEST.json','PACKAGE-REPORT.json','SETUP-PROMPT.txt'}
STATE_KEYS={'task_briefs','date','updated_at','queue','tasks','internal_work','calls','changes','notes','roster','sms_brief','communications','coaching','morning_plan','snapshot','weekly_suggestions','source_limits','prep_links','product_roadblocks','email_review','intake','task_history'}
LIST_KEYS={'items':'id','tasks':'id','internal_work':'id','calls':'call_id','changes':'id','notes':'id','roster':'id','priorities':'task_id','deal_work':'task_id','first_touchpoints':'task_id','internal':'id','feedback':'id','evidence':'id','focus':'id','qci_goals':'id','weekly_reviews':'id','schedule':'id','feed':'id','bundles':'id','roadblocks':'id'}

def utcnow():return datetime.now(timezone.utc).isoformat()
def read_json(path,default=None):return json.loads(path.read_text()) if path.exists() else deepcopy(default)
def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False,encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');tmp=f.name
    os.replace(tmp,path)
def shift_demo(value,days):
    if isinstance(value,dict):return {k:shift_demo(v,days) for k,v in value.items()}
    if isinstance(value,list):return [shift_demo(v,days) for v in value]
    if isinstance(value,str):
        def change(m):
            try:return (date.fromisoformat(m[0])+timedelta(days=days)).isoformat()
            except ValueError:return m[0]
        return re.sub(r'\b\d{4}-\d{2}-\d{2}\b',change,value)
    return value
def merge(old,new,key=''):
    if isinstance(old,dict) and isinstance(new,dict):
        result=deepcopy(old)
        for k,v in new.items():result[k]=merge(result.get(k),v,k)
        return result
    identity=LIST_KEYS.get(key)
    if identity and isinstance(old,list) and isinstance(new,list) and all(isinstance(x,dict) and identity in x for x in old+new):
        result={str(x[identity]):deepcopy(x) for x in old}
        for x in new:
            id=str(x[identity]);result[id]=merge(result.get(id,{}),x)
        return list(result.values())
    return deepcopy(new)
def catalog(state):
    rows=list(state.get('tasks',[]))+list(state.get('internal_work',[]))
    plan=state.get('morning_plan',{})
    rows+=list(plan.get('priorities',[]))+list(plan.get('internal',[]))
    return {str(x.get('task_id') or x.get('id')):dict(x,id=x.get('task_id') or x.get('id')) for x in rows if isinstance(x,dict) and (x.get('task_id') or x.get('id'))}
def validate_state(state):
    for k in ['tasks','calls','changes','notes','roster','internal_work']:
        if not isinstance(state.get(k),list):raise ValueError(k+' must be a list')
    plan=state.get('morning_plan',{})
    for k in ['priorities','internal','pending_updates','accomplishments','new_commitments','not_on_today']:
        if not isinstance(plan.get(k),list):raise ValueError('morning_plan.'+k+' must be a list')
    for x in state['tasks']:
        if not isinstance(x,dict) or not isinstance(x.get('id'),str) or not x['id']:raise ValueError('Each task needs a stable string id')
    for x in plan['priorities']:
        if not isinstance(x,dict) or not isinstance(x.get('task_id'),str):raise ValueError('Each priority needs task_id')
    # Dates used by the live viewer must parse; an unknown date should be absent.
    for x in state.get('snapshot',{}).get('schedule',[]):
        datetime.fromisoformat(x['at'].replace('Z','+00:00'))
    return state

class Store:
    def __init__(self,root=ROOT,mode=None):
        self.root=Path(root);self.lock=threading.RLock()
        self.profile_path=self.root/'workspace/profile.json'
        self.profile=read_json(self.profile_path,read_json(self.root/'profile.example.json'))
        self.mode=mode or self.profile.get('mode','demo')
        if self.mode not in ['demo','personal']:raise ValueError('Mode must be demo or personal')
        self.folder=self.root/'workspace'/self.mode
        self.state_path=self.folder/'state.json';self.progress_path=self.folder/'progress.json'
        if not self.state_path.exists():
            name='demo-state.json' if self.mode=='demo' else 'empty-state.json'
            state=read_json(self.root/'examples'/name)
            if self.mode=='demo':
                state=shift_demo(state,(date.today()-date.fromisoformat(state['date'])).days)
                if isinstance(state.get('snapshot'),dict):
                    state['snapshot']['month']=date.today().strftime('%Y-%m')
                    if isinstance(state['snapshot'].get('metrics',{}).get('revenue'),dict):state['snapshot']['metrics']['revenue']['month']=state['snapshot']['month']
                # Demo counters should remain visible regardless of local hour.
                for row in state.get('product_roadblocks',{}).get('roadblocks',[]):row['submitted_at']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
            atomic_json(self.state_path,validate_state(state))
        if not self.progress_path.exists():atomic_json(self.progress_path,{'tasks':{},'updates':[],'revision':0})
    def state(self):
        with self.lock:
            state=read_json(self.state_path);state['progress']=read_json(self.progress_path)
            state['card_order']=read_json(self.folder/'card-order.json',{'revision':0,'lanes':{}})
            profile=read_json(self.profile_path,self.profile)
            state['profile']=deepcopy(profile)
            state['workspace_mode']=self.mode
            state['automation_status']='UNKNOWN'
            # Configuration describes proposed schedules, never evidence of runs.
            state['schedule_note']='Schedules are templates until configured in your assistant'
            return state
    def setup(self,body):
        with self.lock:
            profile=read_json(self.profile_path,read_json(self.root/'profile.example.json'))
            profile=onboarding.update(profile,body)
            atomic_json(self.profile_path,profile)
            if body.get('action')=='preferences' and ('feedback_cadence' in body or 'feedback_sharing' in body):
                folder=self.root/'workspace/personal';settings=read_json(folder/'product-feedback.json',{});pref=profile.get('preferences',{}).get('product_feedback',{})
                settings.update(enabled=pref.get('mode')!='off',cadence_weeks=pref.get('cadence_weeks',1),cadence_anchor=product_feedback.week_key(product_feedback.now_at(zone=profile.get('organization',{}).get('timezone') or 'UTC')))
                atomic_json(folder/'product-feedback.json',settings)
            summary=onboarding.handoff(profile)
            (self.root/'workspace/SETUP-HANDOFF.txt').write_text(summary+'\n')
            return {'saved':True,'profile':profile,'handoff':summary}
    def import_packet(self,packet):
        if not isinstance(packet,dict):raise ValueError('Import must be a JSON object')
        bad=set(packet)-STATE_KEYS-{'remove_task_ids'}
        if bad:raise ValueError('Unsupported import keys: '+', '.join(sorted(bad)))
        if self.mode=='demo':raise ValueError('Use --mode personal to import source-backed work; demo data stays separate')
        remove=packet.get('remove_task_ids',[])
        if not isinstance(remove,list) or any(not isinstance(x,str) for x in remove):raise ValueError('remove_task_ids must be strings')
        with self.lock:
            state=read_json(self.state_path);incoming={k:v for k,v in packet.items() if k in STATE_KEYS}
            state=merge(state,incoming)
            if remove:
                for obj,key in [(state,'tasks'),(state,'internal_work'),(state['morning_plan'],'priorities'),(state['morning_plan'],'internal'),(state['morning_plan'],'deal_work'),(state['morning_plan'],'first_touchpoints')]:
                    obj[key]=[x for x in obj.get(key,[]) if (x.get('task_id') or x.get('id')) not in remove]
            state['updated_at']=utcnow();validate_state(state)
            atomic_json(self.state_path,state)
            fingerprint=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
            atomic_json(self.folder/'imports'/f'{fingerprint}.json',packet)
            return {'imported':True,'tasks':len(catalog(state)),'fingerprint':fingerprint,'progress_preserved':True}
    def progress(self,body):
        spec=importlib.util.spec_from_file_location('task_progress',self.root/'app/task_progress.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with self.lock:
            state=read_json(self.state_path);progress=read_json(self.progress_path);now=utcnow()
            if 'task_id' in body or 'task_ids' in body:
                tasks=catalog(state);module.apply_task_progress(progress,body,set(tasks),now,tasks)
            elif isinstance(body.get('note'),str) and 0<len(body['note'].strip())<=4000:
                progress['updates'].append({'id':os.urandom(8).hex(),'kind':body.get('kind','progress'),'context':body.get('context'),'text':body['note'].strip(),'at':now,'provenance':'user_reported_local_note'})
            else:raise ValueError('Invalid progress update')
            progress['revision']=progress.get('revision',0)+1;atomic_json(self.progress_path,progress)
            return progress
    def order(self,body):
        with self.lock:
            path=self.folder/'card-order.json';current=read_json(path,{'revision':0,'lanes':{}});state=read_json(self.state_path)
            result=update_order(current,body,state.get('morning_plan',{}),read_json(self.progress_path),utcnow());atomic_json(path,result);return result
    def suggestion(self,body):
        with self.lock:
            state=read_json(self.state_path);item=next((x for x in state.get('weekly_suggestions',{}).get('items',[]) if x['id']==body.get('id')),None)
            if not item or body.get('action') not in ['done','adopt']:raise ValueError('Unknown suggestion or action')
            if item.get('status')=='proposed':
                item.update(status='adopted' if body['action']=='adopt' else 'done',decided_at=utcnow())
                atomic_json(self.state_path,state)
                if body['action']=='adopt':
                    practices=read_json(self.folder/'adopted-practices.json',[])
                    if not any(x['id']==item['id'] for x in practices):practices.append(item);atomic_json(self.folder/'adopted-practices.json',practices)
            return state['weekly_suggestions']

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,status,value,mime='application/json; charset=utf-8'):
        body=value if isinstance(value,bytes) else json.dumps(value).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");self.end_headers();self.wfile.write(body)
    def selected_store(self):
        mode=parse_qs(urlsplit(self.path).query).get('mode',[self.server.store.mode])[0]
        if mode not in ['demo','personal']:raise ValueError('Invalid workspace mode')
        with self.server.store.lock:
            stores=getattr(self.server,'workspace_stores',{})
            if mode not in stores:stores[mode]=self.server.store if self.server.store.mode==mode else Store(self.server.store.root,mode)
            self.server.workspace_stores=stores
            return stores[mode]
    def do_GET(self):
        route=urlsplit(self.path).path
        if route=='/api/release':return self.send(200,product_feedback.release_status())
        if route=='/api/product-feedback':
            store=self.selected_store();profile=read_json(store.profile_path,store.profile)
            result=product_feedback.summary(store.folder,read_json(store.progress_path,{}),zone=profile.get('organization',{}).get('timezone') or 'UTC',contact=read_json(store.root/'app/product-contact.json',{}),operator=profile.get('identity',{}).get('email'));return self.send(200,result)
        if route=='/api/state':
            try:return self.send(200,self.selected_store().state())
            except ValueError as e:return self.send(400,{'error':str(e)})
        if route=='/api/onboarding':
            profile=read_json(self.server.store.profile_path,read_json(self.server.store.root/'profile.example.json'))
            return self.send(200,{'profile':profile,'handoff':onboarding.handoff(profile)})
        files={'/reply-links.js':('app/reply-links.js','text/javascript'),'/reply-cards.css':('app/reply-cards.css','text/css'),'/branding/slack-icon.svg':('app/branding/slack-icon.svg','image/svg+xml'),'/branding/gmail-icon.svg':('app/branding/gmail-icon.svg','image/svg+xml'),'/card-order.js':('app/card-order.js','text/javascript'),'/setup':('app/setup.html','text/html; charset=utf-8'),'/':('app/index.html','text/html; charset=utf-8'),'/completion.js':('app/completion.js','text/javascript'),'/favicon.svg':('app/favicon.svg','image/svg+xml'),'/favicon.ico':('app/favicon.svg','image/svg+xml'),'/branding/hubspot-sprocket.svg':('app/branding/hubspot-sprocket.svg','image/svg+xml'),'/branding/workbench-hammock.png':('app/branding/workbench-hammock.png','image/png')}
        for asset in ['insight-views.js','insight-views.css','header-variants.css','appearance.js','product-feedback.js','product-feedback.css','presentation.js']:
            files['/'+asset]=('app/'+asset,'text/javascript; charset=utf-8' if asset.endswith('.js') else 'text/css; charset=utf-8')
        files['/branding/lexend-deca.ttf']=('app/branding/lexend-deca.ttf','font/ttf')
        if route in files:
            file,mime=files[route];return self.send(200,(self.server.store.root/file).read_bytes(),mime)
        return self.send(404,{'error':'Not found'})
    def do_POST(self):
        port=self.server.server_address[1];allowed={f'http://127.0.0.1:{port}',f'http://localhost:{port}'}
        if self.headers.get('Origin') not in allowed|{None}:return self.send(403,{'error':'Local origin required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536:raise ValueError('Invalid request size')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('Expected object')
            route=urlsplit(self.path).path
            if route=='/api/product-feedback':
                store=self.selected_store();profile=read_json(store.profile_path,store.profile)
                result=product_feedback.update(store.folder,body,read_json(store.progress_path,{}),read_json(store.root/'app/product-contact.json',{}),profile.get('identity',{}).get('email'),zone=profile.get('organization',{}).get('timezone') or 'UTC')
            elif route=='/api/onboarding':result=self.server.store.setup(body)
            elif route=='/api/card-order':result=self.selected_store().order(body)
            elif route=='/api/progress':result=self.selected_store().progress(body)
            elif route=='/api/weekly-suggestions':result=self.selected_store().suggestion(body)
            else:return self.send(404,{'error':'Not found'})
            return self.send(200,result)
        except (ValueError,KeyError,TypeError) as e:return self.send(400,{'error':str(e)})

def bundle_files(root):
    for p in sorted(Path(root).rglob('*')):
        rel=p.relative_to(root)
        if p.is_symlink():raise ValueError('Bundle export does not follow symlinks')
        if not p.is_file() or any(x in {'__pycache__','.DS_Store','.git','node_modules'} for x in rel.parts):continue
        if len(rel.parts)==1 and rel.name in ALLOWED_FILES:yield p
        elif rel.parts[0] in ALLOWED_DIRS:yield p
def export_bundle(root,destination):
    root=Path(root);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as out:
        for p in bundle_files(root):out.write(p,Path('presales-workbench-starter')/p.relative_to(root))
    return destination

def main():
    parser=argparse.ArgumentParser(description='Local presales Workbench; explicit feedback submission only, no CRM or message transport')
    commands=parser.add_subparsers(dest='command')
    serve=commands.add_parser('serve');serve.add_argument('--port',type=int,default=8781);serve.add_argument('--mode',choices=['demo','personal']);serve.add_argument('--open',action='store_true')
    commands.add_parser('doctor')
    imp=commands.add_parser('import');imp.add_argument('packet');imp.add_argument('--mode',choices=['personal'],default='personal')
    setup=commands.add_parser('configure');setup.add_argument('answers',help='Local preferences JSON; never credentials or write grants')
    export=commands.add_parser('export');export.add_argument('destination')
    args=parser.parse_args()
    if args.command=='export':print(export_bundle(ROOT,args.destination));return
    if args.command=='doctor':
        profile=read_json(ROOT/'workspace/profile.json',read_json(ROOT/'profile.example.json'))
        print(json.dumps({'python_supported':sys.version_info>=(3,10),'mode':profile.get('mode'),'identity_verified':profile.get('identity',{}).get('verified',False),'sources':profile.get('sources',{}),'schedules':'Templates only; configure with your assistant after a manual run','external_transport':'No CRM/message transport. Feedback submits only on your click to the fixed collector; public GitHub metadata checks can be disabled.'},indent=2));return
    store=Store(mode=getattr(args,'mode',None))
    if args.command=='configure':print(json.dumps(store.setup(read_json(Path(args.answers)))));return
    if args.command=='import':print(json.dumps(store.import_packet(read_json(Path(args.packet)))));return
    server=ThreadingHTTPServer(('127.0.0.1',getattr(args,'port',8781)),Handler);server.store=store
    url=f'http://127.0.0.1:{server.server_address[1]}';print('Workbench '+url,flush=True)
    if getattr(args,'open',False):webbrowser.open(url+('/setup' if not (ROOT/'workspace/profile.json').exists() else '/?mode=personal'))
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
