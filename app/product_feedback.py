"""Local weekly feedback, explicit submissions and metadata-only update checks."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import hashlib
import json
import math
import os
import re
import tempfile
import threading
import subprocess
import ssl
import sys
import urllib.error
import urllib.request
import uuid
from time_savings import savings_summary
REPOSITORY='sagaillj/presales-workbench'
LATEST='https://github.com/'+REPOSITORY+'/releases/latest'
VERSION=(Path(__file__).resolve().parents[1]/'VERSION').read_text().strip() if (Path(__file__).resolve().parents[1]/'VERSION').is_file() else '0.5.1'
_LOCK=threading.RLock()
DONE={'submitted_verified','submitted_user_reported','sent_user_reported','skipped'}
def now_at(now=None,zone='UTC'):
    try:tz=ZoneInfo(zone or 'UTC')
    except (ZoneInfoNotFoundError,ValueError,TypeError):tz=timezone.utc
    return (now or datetime.now(timezone.utc)).astimezone(tz)
def read(path,default):return json.loads(path.read_text()) if path.exists() else default
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False,encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');temp=f.name
    os.replace(temp,path)
def week_key(now):return (now.date()-timedelta(days=now.weekday())).isoformat()
def valid_email(value):return isinstance(value,str) and len(value)<=254 and bool(re.fullmatch(r'[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+',value))
def form_config(contact):
    c=contact.get('feedback_form',{}) if isinstance(contact,dict) else {}
    url=c.get('url') or '';entries=c.get('entries',{})
    valid=bool(re.fullmatch(r'https://docs\.google\.com/forms/d/e/[A-Za-z0-9_-]+/viewform',url)) and set(entries)=={'rating','hours','comments','usage','email'} and all(isinstance(v,str) and re.fullmatch(r'entry\.\d+',v) for v in entries.values())
    endpoint=c.get('endpoint') or '';direct=bool(re.fullmatch(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',endpoint))
    return {**c,'form_valid':valid,'direct':direct,'configured':valid or direct}
def counts(folder,progress,now,zone):
    saved=read(Path(folder)/'product-feedback.json',{});week=week_key(now);done=0
    for row in progress.get('tasks',{}).values():
        if not isinstance(row,dict) or not row.get('done') or not isinstance(row.get('updated_at'),str):continue
        try:
            at=datetime.fromisoformat(row['updated_at'].replace('Z','+00:00'))
            if at.tzinfo and week<=now_at(at,zone).date().isoformat()<=now.date().isoformat():done+=1
        except (ValueError,TypeError):pass
    return {'active_days':sum(1 for day in saved.get('active_dates',[]) if week<=day<=now.date().isoformat()),'tasks_marked_done':done}
def feedback_eligibility(saved,now):
    # Count actual distinct local use dates, never install/download age or future dates.
    days=set()
    for value in saved.get('active_dates',[]):
        try:
            day=datetime.strptime(value,'%Y-%m-%d').date()
            if day<=now.date():days.add(day)
        except (TypeError,ValueError):pass
    return {'eligible':len(days)>=10,'usage_days':len(days),'minimum_usage_days':10}
def summary(folder,progress,now=None,zone='UTC',contact=None,operator=None,force=False):
    now=now_at(now,zone);week=week_key(now);saved=read(Path(folder)/'product-feedback.json',{});record=saved.get('weeks',{}).get(week,{})
    cadence=saved.get('cadence_weeks',1);anchor=saved.get('cadence_anchor',week)
    try:scheduled=((now.date()-datetime.fromisoformat(anchor).date()).days//7)%cadence==0
    except (ValueError,TypeError,ZeroDivisionError):scheduled=True;cadence=1
    eligibility=feedback_eligibility(saved,now)
    first=not any(row.get('status') in DONE for row in saved.get('weeks',{}).values())
    due=eligibility['eligible'] and saved.get('enabled',True) and (force or first and scheduled or record.get('status') in {'submission_pending','form_opened'} or now.weekday()>=4 and scheduled) and record.get('status') not in DONE
    cfg=form_config(contact)
    return {**eligibility,'week':week,'due':bool(due),'enabled':saved.get('enabled',True),'cadence_weeks':cadence,'record':record,'counts':counts(folder,progress,now,zone),'time_savings':savings_summary(progress,now,zone,retrospective=read(Path(folder)/'time-savings-ledger.json',{})),'version':VERSION,'submission_reference':hashlib.sha256((saved['installation_id']+':'+week).encode()).hexdigest() if saved.get('installation_id') else None,'email':record.get('email',operator if valid_email(operator) else ''),'destination':{'configured':cfg['configured'],'direct':cfg['direct'],'form_available':cfg['form_valid'],'label':'Workbench feedback · Google Form'},'privacy':'Share your rating, optional comments and time estimate. Include local usage counts only if you choose. No deal names, messages or transcripts.'}
def payload(body,saved,week,folder,progress,now,zone,operator):
    rating=body.get('rating')
    if type(rating) is not int or not 0<=rating<=10:raise ValueError('Choose a rating from 0 to 10')
    hours=body.get('hours')
    if hours in ['',None]:hours=None
    elif isinstance(hours,bool) or not isinstance(hours,(int,float)) or not 0<=hours<=168 or not math.isfinite(hours):raise ValueError('Hours saved must be between 0 and 168, or blank')
    comments=body.get('comments','');email=body.get('email',operator or '')
    if not isinstance(comments,str) or len(comments)>2000:raise ValueError('Keep feedback to 2,000 characters')
    if not isinstance(email,str) or email and not valid_email(email):raise ValueError('Use a valid work email or leave it blank')
    include=body.get('include_counts',True)
    if type(include) is not bool:raise ValueError('Choose whether to include local counts')
    install=saved.setdefault('installation_id',str(uuid.uuid4()));key=hashlib.sha256((install+':'+week).encode()).hexdigest()
    return {'schema':1,'submission_id':key,'week':week,'rating':rating,'hours':hours,'comments':comments.strip(),'email':email.strip(),'counts':counts(folder,progress,now,zone) if include else None,'version':VERSION}
def usage_text(p):
    lines=['Week of '+p['week'],'Workbench '+p['version']]
    if p['counts'] is not None:lines+=['Days opened: '+str(p['counts']['active_days']),'Tasks marked done: '+str(p['counts']['tasks_marked_done']),'Checkbox completions are user-reported, not verified deliveries.']
    else:lines+=['Usage counts not included.']
    return '\n'.join(lines+['Submission reference: '+p['submission_id']])
def prefill(cfg,p):
    if not cfg['form_valid']:raise ValueError('Google Form is not configured')
    values={'rating':str(p['rating']),'hours':'' if p['hours'] is None else str(p['hours']),'comments':p['comments'],'usage':usage_text(p),'email':p['email']}
    url=cfg['url']+'?'+urlencode({'usp':'pp_url',**{cfg['entries'][k]:v for k,v in values.items()}})
    if len(url)>7000:raise ValueError('Please shorten the feedback a little so Google can prefill it reliably.')
    return url
class GoogleRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        u=urlsplit(newurl)
        if u.scheme!='https' or u.hostname not in {'script.google.com','script.googleusercontent.com'}:raise ValueError('Unexpected submission redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def platform_google_request(endpoint,data):
    """Use the OS TLS trust implementation, never an insecure certificate bypass."""
    curl=Path('/usr/bin/curl') if sys.platform!='win32' else Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/curl.exe'
    if not curl.is_file():raise ValueError('System HTTPS transport is unavailable')
    url=endpoint;method='POST'
    with tempfile.TemporaryDirectory(prefix='workbench-feedback-') as temp:
        headers=Path(temp)/'headers';content=Path(temp)/'response'
        for _ in range(6):
            u=urlsplit(url)
            if u.scheme!='https' or u.hostname not in {'script.google.com','script.googleusercontent.com'} or u.username:raise ValueError('Unexpected submission destination')
            command=[str(curl),'--silent','--show-error','--proto','=https','--max-time','15','--max-redirs','0','--max-filesize','64000','--dump-header',str(headers),'--output',str(content),'--write-out','%{http_code}','--request',method]
            if method=='POST':command+=['--header','Content-Type: application/json','--data-binary','@-']
            result=subprocess.run(command+[url],input=data if method=='POST' else None,capture_output=True,timeout=18)
            if result.returncode:raise ValueError('Secure system HTTPS request failed')
            code=int(result.stdout)
            if code in [301,302,303,307,308]:
                locations=re.findall(r'^location:\s*(.*?)\r?$',headers.read_text(),re.M|re.I)
                if not locations:raise ValueError('Missing redirect destination')
                url=locations[-1].strip()
                if code in [301,302,303]:method='GET'
                continue
            if not 200<=code<300 or content.stat().st_size>64000:raise ValueError('Feedback service did not return a valid receipt')
            return content.read_bytes()
    raise ValueError('Too many submission redirects')
def post_feedback(endpoint,p):
    data=json.dumps(p,ensure_ascii=False).encode();request=urllib.request.Request(endpoint,data=data,headers={'Content-Type':'application/json','User-Agent':'Workbench-feedback'},method='POST')
    try:
        with urllib.request.build_opener(GoogleRedirects()).open(request,timeout=12) as response:raw=response.read(64001)
    except urllib.error.URLError as error:
        if not isinstance(error.reason,ssl.SSLCertVerificationError):raise
        raw=platform_google_request(endpoint,data)
    if len(raw)>64000:raise ValueError('Invalid submission receipt')
    return json.loads(raw)
def update(folder,body,progress,contact,operator=None,now=None,zone='UTC',post=None):
    with _LOCK:return _update(Path(folder),body,progress,contact,operator,now,zone,post)
def _update(folder,body,progress,contact,operator,now,zone,post):
    path=folder/'product-feedback.json';now=now_at(now,zone);week=week_key(now);saved=read(path,{});action=body.get('action');cfg=form_config(contact)
    if action=='visit':
        saved.setdefault('installation_id',str(uuid.uuid4()));saved['active_dates']=sorted(set(saved.get('active_dates',[]))|{now.date().isoformat()})[-100:]
    elif action=='enabled':
        if type(body.get('enabled')) is not bool:raise ValueError('Choose whether feedback is enabled')
        saved['enabled']=body['enabled']
    elif action=='cadence':
        if type(body.get('weeks')) is not int or body['weeks'] not in [1,2]:raise ValueError('Choose weekly or every other week')
        saved.update(cadence_weeks=body['weeks'],cadence_anchor=week)
    elif action in ['submit','form','submitted','skip']:
        if body.get('week')!=week:raise ValueError('The week changed. Refresh before continuing.')
        records=saved.setdefault('weeks',{});old=records.get(week,{})
        if old.get('status') in DONE-{'skipped'}:raise ValueError('This week is already submitted')
        if action in ['submit','form']:
            if not cfg['configured']:raise ValueError('Feedback collection is not configured yet')
            p=payload(body,saved,week,folder,progress,now,zone,operator)
            if old.get('status')=='submission_pending':
                original=old.get('payload',{})
                for key in ['rating','hours','comments','email']:
                    if p[key]!=original.get(key):raise ValueError('Retry your previous submission before editing it. Its saved status is still unknown.')
                p=original
            row={'rating':p['rating'],'hours':p['hours'],'comments':p['comments'],'email':p['email'],'include_counts':p['counts'] is not None,'updated_at':now.isoformat(),'payload':p}
            if action=='form' and old.get('status')=='submission_pending':raise ValueError('Retry the pending submission before opening another form')
            if action=='form' or not cfg['direct']:
                url=prefill(cfg,p);records[week]={**row,'status':'form_opened','form_url':url};write(path,saved)
                return {'url':url,'state':summary(folder,progress,now,zone,contact,operator),'submitted':False}
            if old.get('status')=='submission_pending' and old.get('endpoint')!=cfg['endpoint']:raise ValueError('Feedback destination changed. Ask your assistant to reconcile the previous submission first.')
            records[week]={**row,'status':'submission_pending','endpoint':cfg['endpoint']};write(path,saved)
            try:
                receipt=(post or post_feedback)(cfg['endpoint'],p)
                if receipt.get('ok') is False and receipt.get('accepted') is False:
                    if old.get('status')=='submission_pending':return {'pending':True,'error':'The previous submission is still unconfirmed. Retry later with the same answers.','state':summary(folder,progress,now,zone,contact,operator)}
                    records[week]={**row,'status':'submission_failed'};write(path,saved)
                    return {'error':'The feedback service is unavailable. Retry or use the prefilled Google Form.','failed':True,'state':summary(folder,progress,now,zone,contact,operator)}
                if receipt.get('ok') is not True or receipt.get('submission_id')!=p['submission_id'] or not isinstance(receipt.get('response_id'),str) or not receipt['response_id'] or not isinstance(receipt.get('submitted_at'),str):raise ValueError('Submission was not confirmed')
                datetime.fromisoformat(receipt['submitted_at'].replace('Z','+00:00'))
            except Exception:
                return {'pending':True,'error':'Submission not confirmed. Retry safely with the same answers. Your feedback is saved here.','state':summary(folder,progress,now,zone,contact,operator)}
            records[week]={**row,'status':'submitted_verified','receipt':receipt,'provenance':'google_form_receipt_readback'}
        elif action=='submitted':
            if old.get('status')!='form_opened':raise ValueError('Open and submit the Google Form first')
            records[week]={**old,'status':'submitted_user_reported','reported_at':now.isoformat(),'provenance':'user_reported_form_submitted'}
        else:
            if old.get('status')=='submission_pending':raise ValueError('Reconcile the pending submission before skipping this week')
            records[week]={**old,'status':'skipped','updated_at':now.isoformat()}
    else:raise ValueError('Unknown feedback action')
    write(path,saved);return summary(folder,progress,now,zone,contact,operator)
def version_tuple(value):
    if not isinstance(value,str) or not re.fullmatch(r'v?\d+\.\d+\.\d+',value):raise ValueError('Invalid release version')
    return tuple(map(int,value.lstrip('v').split('.')))
def release_status(installed=None,fetch=None):
    """Read fixed public release metadata. Never fetch/execute code."""
    installed=installed or VERSION
    request=urllib.request.Request('https://api.github.com/repos/'+REPOSITORY+'/releases/latest',headers={'Accept':'application/vnd.github+json','User-Agent':'Workbench-update-check'})
    try:
        if fetch is None:
            with urllib.request.urlopen(request,timeout=8) as response:raw=response.read(500001)
            if len(raw)>500000:raise ValueError('Release response too large')
            payload=json.loads(raw)
        else:payload=fetch(request)
        core=re.fullmatch(r'v?(\d+\.\d+\.\d+)(?:-[A-Za-z0-9.-]+)?',installed)
        if not core:raise ValueError('Invalid installed version')
        current=version_tuple(core.group(1));version=payload.get('tag_name');newer=version_tuple(version)>current or (version_tuple(version)==current and '-' in installed)
        if payload.get('draft') or payload.get('prerelease'):raise ValueError('Not a stable release')
        if payload.get('html_url')!='https://github.com/'+REPOSITORY+'/releases/tag/'+version:raise ValueError('Unexpected release destination')
        expected={'presales-workbench-starter-latest.zip','presales-workbench-starter-latest.sha256'}
        assets={x.get('name'):x.get('browser_download_url') for x in payload.get('assets',[]) if isinstance(x,dict)}
        for name in expected:
            if assets.get(name)!='https://github.com/'+REPOSITORY+'/releases/download/'+version+'/'+name:raise ValueError('Stable download assets missing')
        return {'release_id':payload.get('id'),'release_url':payload.get('html_url'),'installed':installed,'latest':version.lstrip('v'),'available':newer,'ahead':current>version_tuple(version),'url':LATEST,'status':'checked','upgrade_prompt':'Help me update my existing Workbench to verified version '+version+' from '+payload['html_url']+'. Verify the release checksum and bundle manifest, read docs/UPGRADING.md, stop only this app, back up my setup, and run the included upgrade script. Preserve workspace, profile, feedback, voice preferences, progress, schedules and permissions. Stop for review if app files have local edits. Restart and run the first-test checklist. Do not add source access or write grants.'}
    except Exception:
        return {'installed':installed,'status':'unavailable','url':LATEST,'message':'Could not check GitHub. Your current Workbench is unchanged.'}
