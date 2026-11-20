"""Source-backed first-run receipts and native scheduling evidence.

Web forms can propose reads and cadence. They cannot grant account access,
execute installers, create jobs, or record these assistant-only receipts.
"""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import hashlib
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_SOURCES=('email','slack','crm','calendar','meeting_notes','hex')
DEFAULT_LIGHT_TIMES=['09:00','12:00','15:00']
DEFAULT_DAILY_TIME='17:30'

def ensure_orientation_tasks(state):
    """Add two local practice cards once, without replacing imported work or progress."""
    for lane,name,collection in [('external','Customer work','priorities'),('internal','Internal work','internal')]:
        ident='orientation-'+('customer-work' if lane=='external' else 'internal-work')
        action=('Meet your deal-side co-pilot. Open a card to find the ask, prepared context and what needs you. When you have the hang of it, mark this orientation task done.' if lane=='external' else 'Meet your behind-the-scenes co-pilot. Internal follow-through and preparation live here. Try marking this orientation task done; Undo and Completed let you bring it back.')
        row={'id':ident,'task_id':ident,'key':ident,'title':'Welcome aboard · '+name+' orientation','label':action,'action':action,'short_action':'Take a quick look, then mark this orientation task done.','why':'A local orientation task to help you get comfortable. It is not assigned customer or internal work.','done_when':'You have explored this card and marked the orientation task done.','lane':lane,'external_view':'deal-work','status':'open','waiting':False,'orientation_guide':True,'kind':'local_guide','provenance':'local_guide','completion_kind':'orientation','time_savings_category':'none','checks':[],'milestones':[],'checkpoints':[],'waiting_on':[],'dependencies':[]}
        rows=state.setdefault('tasks',[])
        if not any((x.get('task_id') or x.get('id'))==ident for x in rows):rows.append(deepcopy(row))
        rows=state.setdefault('morning_plan',{}).setdefault(collection,[])
        if not any((x.get('task_id') or x.get('id'))==ident for x in rows):rows.append(deepcopy(row))
    return state

def timestamp(value,label='timestamp'):
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None:raise ValueError()
        return parsed
    except (ValueError,TypeError,AttributeError):raise ValueError('Use a zoned ISO '+label)

def observed(value,stamp,label='timestamp'):
    parsed=timestamp(value,label)
    if parsed>timestamp(stamp,'receipt time')+timedelta(minutes=5):raise ValueError('Future '+label+' cannot verify a completed action')
    return parsed

def nonempty(value,label,limit=4000):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('Use a concise '+label)
    return value.strip()

def native_url(value):
    if not isinstance(value,str) or len(value)>4000:return False
    try:
        parsed=urlsplit(value);host=(parsed.hostname or '').lower()
        return parsed.scheme=='https' and bool(host) and not parsed.username and not parsed.password and not any(host==name or host.endswith('.'+name) for name in ['example.com','example.org','example.net','invalid','localhost']) and not host.endswith('.invalid')
    except ValueError:return False

def zone(value):
    value=nonempty(value,'IANA time zone',100)
    try:ZoneInfo(value)
    except (ZoneInfoNotFoundError,ValueError):raise ValueError('Choose a valid IANA time zone')
    return value

def clock(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',value):raise ValueError('Choose a local time as HH:MM')
    return value

def schedule_defaults(profile):
    saved=deepcopy(profile.get('schedules') or {})
    saved.setdefault('enabled',False);saved.setdefault('state','proposed')
    saved.setdefault('recurring_requested',False)
    if not saved.get('timezone'):saved['timezone']=profile.get('organization',{}).get('timezone')
    saved.setdefault('timezone_verified',False)
    saved.setdefault('light',{'weekdays_only':True,'local_times':list(DEFAULT_LIGHT_TIMES),'mode':'read_only'})
    # New installs opt out; preserve legacy verified native light jobs without
    # treating old stored times alone as an opt-in or stopping any real job.
    legacy_light=any(job.get('kind')=='light' and job.get('provider')=='codex' and
                     isinstance(job.get('readback'),dict) and job['readback'].get('status')=='ACTIVE'
                     for job in saved.get('jobs',[]) if isinstance(job,dict))
    saved['light'].setdefault('enabled',legacy_light)
    saved['light'].setdefault('weekdays_only',True)
    saved['light'].setdefault('local_times',list(DEFAULT_LIGHT_TIMES))
    saved['light'].setdefault('mode','read_only')
    saved.setdefault('daily',{'weekdays_only':True,'local_time':DEFAULT_DAILY_TIME})
    saved.setdefault('jobs',[]);saved.setdefault('authorization',{'state':'awaiting_chat_authorization'})
    return saved

def propose_cadence(profile,body,stamp):
    allowed={'action','light_times','light_enabled','daily_time','weekdays_only','timezone','recurring_requested'}
    if set(body)-allowed:raise ValueError('Cadence settings cannot grant authorization or verify jobs')
    saved=schedule_defaults(profile)
    if 'light_enabled' in body:
        if type(body['light_enabled']) is not bool:raise ValueError('Choose whether optional daytime checks are enabled')
        saved['light']['enabled']=body['light_enabled']
    if 'light_times' in body:
        times=body['light_times']
        if not isinstance(times,list) or any(not isinstance(v,str) for v in times) or not 1<=len(times)<=6 or len(set(times))!=len(times):raise ValueError('Choose one to six distinct local light-check times')
        saved['light']['local_times']=sorted(clock(v) for v in times)
    if 'daily_time' in body:saved['daily']['local_time']=clock(body['daily_time'])
    if 'weekdays_only' in body:
        if type(body['weekdays_only']) is not bool:raise ValueError('Choose a weekday preference')
        saved['light']['weekdays_only']=body['weekdays_only'];saved['daily']['weekdays_only']=body['weekdays_only']
    if 'timezone' in body:
        value=zone(body['timezone'])
        if value!=saved.get('timezone'):saved['timezone']=value;saved['timezone_verified']=False
    if 'recurring_requested' in body:
        if type(body['recurring_requested']) is not bool:raise ValueError('Choose whether recurring upkeep is requested')
        saved['recurring_requested']=body['recurring_requested']
    keys=('light','daily','timezone','recurring_requested')
    changed=any(saved.get(k)!=schedule_defaults(profile).get(k) for k in keys)
    if changed:
        # Keep existing native receipts as history; changing JSON does not update jobs.
        if saved.get('jobs'):saved['previous_jobs']=deepcopy(saved['jobs'])
        saved.update(state='changes_pending' if saved.get('jobs') else 'proposed',enabled=False,updated_at=stamp)
    profile['schedules']=saved
    return profile

def schedule_status(profile):
    value=schedule_defaults(profile);state=value.get('state','proposed')
    if state=='verified' and (not value.get('jobs') or not value.get('timezone_verified')):state='proposed'
    notes={'proposed':'Proposed cadence. No native job has been verified.',
           'configured':'Native job identifiers are recorded; their matching schedule readback is still pending.',
           'verified':'Matching native scheduler readbacks are recorded. This is scheduling evidence, not proof of a successful run.',
           'changes_pending':'Settings changed. Existing native jobs have not been verified against this new cadence.'}
    return {'state':state,'enabled':state=='verified' and value.get('enabled') is True,'recurring_requested':value['recurring_requested'],'timezone':value.get('timezone'),'timezone_verified':value.get('timezone_verified') is True,'light':value['light'],'daily':value['daily'],'job_count':len(value.get('jobs',[])),'note':notes.get(state,notes['proposed'])}

def _rule_times(rule,weekdays):
    nonempty(rule,'native recurrence',2000)
    if rule.startswith('RRULE:'):rule=rule[6:]
    parts={}
    for bit in rule.split(';'):
        if '=' not in bit:raise ValueError('Use the exact native recurrence readback')
        key,value=bit.split('=',1)
        if key in parts:raise ValueError('Duplicate recurrence field')
        parts[key]=value
    if set(parts)-{'FREQ','BYDAY','BYHOUR','BYMINUTE','BYSECOND','INTERVAL'}:raise ValueError('Native recurrence has unsupported filters')
    if parts.get('INTERVAL','1')!='1' or parts.get('BYSECOND','0')!='0':raise ValueError('Native recurrence does not match the requested cadence')
    days=set(parts.get('BYDAY','').split(','))
    if weekdays:
        if parts.get('FREQ')!='WEEKLY' or days!={'MO','TU','WE','TH','FR'}:raise ValueError('Native recurrence must match the requested weekdays')
    elif not (parts.get('FREQ')=='DAILY' and not parts.get('BYDAY') or parts.get('FREQ')=='WEEKLY' and days=={'MO','TU','WE','TH','FR','SA','SU'}):raise ValueError('Native recurrence must match every requested day')
    try:
        hours=[int(x) for x in parts['BYHOUR'].split(',')];minutes=[int(x) for x in parts['BYMINUTE'].split(',')]
        if any(not 0<=h<=23 for h in hours) or any(not 0<=m<=59 for m in minutes):raise ValueError()
    except (ValueError,KeyError):raise ValueError('Native recurrence needs exact hour and minute fields')
    return {f'{h:02d}:{m:02d}' for h in hours for m in minutes}

def record_schedule(profile,receipt,stamp):
    """Assistant-only audit receipt; the caller must have used the native scheduler."""
    if not isinstance(receipt,dict) or receipt.get('schema_version')!=1:raise ValueError('Use a schema1 native scheduling receipt')
    reference=nonempty(receipt.get('authorization_reference'),'explicit chat authorization reference')
    authorized=observed(receipt.get('authorized_at'),stamp,'authorization time')
    saved=schedule_defaults(profile)
    if not saved.get('recurring_requested'):raise ValueError('Recurring upkeep has not been requested')
    tz=zone(receipt.get('timezone'));proof=receipt.get('timezone_evidence')
    if not isinstance(proof,dict) or not native_url(proof.get('source_url')):raise ValueError('Verify the user-local time zone from an approved native source')
    nonempty(proof.get('quote'),'time zone evidence');observed(proof.get('observed_at'),stamp,'time zone evidence time')
    if saved.get('timezone') and saved['timezone']!=tz:raise ValueError('Native scheduling time zone does not match the proposed settings')
    jobs=receipt.get('jobs')
    if not isinstance(jobs,list) or not jobs or len(jobs)>7:raise ValueError('Record the actual enabled native jobs')
    ids=set();by_kind={'light':set(),'daily':set()};all_verified=True
    for job in jobs:
        if not isinstance(job,dict) or job.get('kind') not in by_kind or job.get('provider')!='codex':raise ValueError('Use a supported native scheduler job receipt')
        ident=nonempty(job.get('native_id'),'native job identifier',250)
        if ident in ids:raise ValueError('Each native job may appear only once')
        ids.add(ident);kind=job['kind'];cfg=saved[kind]
        if kind=='light' and not saved['light']['enabled']:raise ValueError('Optional daytime checks are off; do not create or verify a new light job')
        times=_rule_times(job.get('rrule'),cfg['weekdays_only'])
        if times & by_kind[kind]:raise ValueError('Duplicate native job occurrences')
        by_kind[kind]|=times;readback=job.get('readback')
        if readback is None:all_verified=False;continue
        if not isinstance(readback,dict) or readback.get('native_id')!=ident or readback.get('rrule')!=job['rrule'] or readback.get('timezone')!=tz or readback.get('status')!='ACTIVE':raise ValueError('Native job readback does not match its saved configuration')
        checked=observed(readback.get('checked_at'),stamp,'native readback time')
        if checked<authorized:raise ValueError('Native scheduler verification predates its chat authorization')
        nonempty(readback.get('reference'),'native scheduler tool readback reference')
    expected_light=set(saved['light']['local_times']) if saved['light']['enabled'] else set()
    if by_kind['light']!=expected_light or by_kind['daily']!={saved['daily']['local_time']}:raise ValueError('Native jobs do not cover the exact enabled cadence')
    saved.update(state='verified' if all_verified else 'configured',enabled=all_verified,timezone=tz,timezone_verified=True,timezone_evidence=deepcopy(proof),jobs=deepcopy(jobs),updated_at=stamp,authorization={'state':'chat_authorization_recorded','reference':reference,'authorized_at':receipt['authorized_at']})
    result=deepcopy(profile);result['schedules']=saved
    result.setdefault('organization',{})['timezone']=tz
    return result

def _strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,dict):
        for child in value.values():yield from _strings(child)
    elif isinstance(value,list):
        for child in value:yield from _strings(child)

def task_rows(packet):
    """Only actual task collections, never arbitrary note/call IDs."""
    result={}
    plan=packet.get('morning_plan') or {}
    collections=[packet.get('tasks',[]),packet.get('internal_work',[])]+[plan.get(k,[]) for k in ['priorities','internal','deal_work','first_touchpoints']]
    def combine(old,new):
        out=deepcopy(old)
        for key,value in new.items():out[key]=combine(out.get(key,{}) if isinstance(out.get(key),dict) else {},value) if isinstance(value,dict) else deepcopy(value)
        return out
    for rows in collections:
        if not isinstance(rows,list):continue
        for row in rows:
            if not isinstance(row,dict):continue
            ident=row.get('task_id') or row.get('id')
            if isinstance(ident,str) and ident:result[ident]=combine(result.get(ident,{}),row)
    briefs=(packet.get('task_briefs') or {}).get('items') or {}
    for ident,row in result.items():
        if isinstance(briefs.get(ident),dict):row['decision_brief']=combine(row.get('decision_brief',{}),briefs[ident])
    return result

def evidence_matches(task,check):
    """Author, time and excerpt must belong to the same exact native source."""
    if isinstance(task,list):return any(evidence_matches(v,check) for v in task)
    if not isinstance(task,dict):return False
    url=task.get('source_url') or task.get('url')
    quote=task.get('source_quote') or task.get('quote')
    author=task.get('source_author') or task.get('person') or task.get('author')
    at=task.get('source_at') or task.get('at') or task.get('timestamp')
    if url==check['source_url'] and isinstance(quote,str) and check['source_quote'] in quote and author==check['source_author']:
        try:
            if timestamp(at)==timestamp(check['source_at']):return True
        except ValueError:pass
    return any(evidence_matches(child,check) for child in task.values() if isinstance(child,(dict,list)))

def real_task(task):
    if not isinstance(task,dict):return False
    if any(task.get(k) is True for k in ['synthetic','is_demo','is_example','orientation_guide','is_guide']):return False
    if any(str(task.get(k,'')).lower() in {'synthetic','fictional','demo','example','guide','orientation_guide','local_guide'} for k in ['provenance','origin','source_kind','kind','task_type']):return False
    ident=str(task.get('task_id') or task.get('id') or '').lower()
    if ident.startswith(('demo-','sample-','example-','guide-','orientation-')):return False
    return bool(ident)

def record_orientation(profile,receipt,tasks,imports,stamp):
    """Validate a first audit against actual saved imports, never a task quota."""
    if not isinstance(receipt,dict) or receipt.get('schema_version')!=1:raise ValueError('Use a schema1 orientation receipt')
    nonempty(receipt.get('authorization_reference'),'explicit chat read-authorization reference')
    start=observed(receipt.get('started_at'),stamp,'audit start');end=observed(receipt.get('completed_at'),stamp,'audit completion')
    if end<start:raise ValueError('Audit completion must follow its start')
    selected={k for k,v in profile.get('read_requests',{}).items() if v.get('requested')}
    if not selected:raise ValueError('Choose the bounded orientation sources first')
    rows=receipt.get('coverage');coverage={}
    if not isinstance(rows,list):raise ValueError('Record source-by-source audit coverage')
    for row in rows:
        if not isinstance(row,dict) or row.get('source') not in selected or row['source'] in coverage or row.get('status') not in {'complete','partial','unavailable','skipped'}:raise ValueError('Record one honest disposition per selected source')
        nonempty(row.get('details'),'source coverage and gaps');at=observed(row.get('observed_at'),stamp,'source observation time')
        if at>end+timedelta(minutes=5) or at<start-timedelta(minutes=5):raise ValueError('Source observation must belong to this actual audit window')
        urls=row.get('source_urls')
        if not isinstance(urls,list) or any(not native_url(u) for u in urls):raise ValueError('Use exact native HTTPS evidence links, never sample URLs')
        if row['status'] in {'complete','partial'} and not urls:raise ValueError('Available source coverage needs an actual source link')
        coverage[row['source']]=deepcopy(row)
    fingerprints=receipt.get('import_fingerprints')
    if not isinstance(fingerprints,list) or not fingerprints or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) or not (Path(imports)/(v+'.json')).is_file() for v in fingerprints):raise ValueError('Import the actual audit packet first and cite its saved fingerprint')
    imported={}
    for fingerprint in fingerprints:
        packet=json.loads((Path(imports)/(fingerprint+'.json')).read_text())
        if hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()!=fingerprint:raise ValueError('The cited import changed after its recorded fingerprint')
        for ident,row in task_rows(packet).items():imported.setdefault(ident,[]).append(row)
    imported_ids=set(imported)
    verified=receipt.get('verified_tasks')
    if not isinstance(verified,list):raise ValueError('Record the actual imported task checks; an honest quiet audit may have none')
    seen=set()
    for check in verified:
        if not isinstance(check,dict):raise ValueError('Use task verification objects')
        ident=nonempty(check.get('task_id'),'stable imported task ID',250);task=tasks.get(ident)
        if ident in seen or ident not in imported_ids or not real_task(task):raise ValueError('Verify distinct real imported tasks, excluding examples and optional guides')
        seen.add(ident)
        if not native_url(check.get('source_url')):raise ValueError('Verify the exact original native task source')
        quote=nonempty(check.get('source_quote'),'original assignment excerpt');nonempty(check.get('source_author'),'original source author')
        source_at=observed(check.get('source_at'),stamp,'original source time');verified_at=observed(check.get('verified_at'),stamp,'task readback time')
        if source_at>verified_at or verified_at>end+timedelta(minutes=5) or verified_at<start-timedelta(minutes=5):raise ValueError('Task evidence and native verification clocks are inconsistent')
        if not evidence_matches(task,check) or not any(evidence_matches(row,check) for row in imported[ident]):raise ValueError('Verify the same native URL, original excerpt, author and timestamp in both cited import and current task')
    unverified={ident for ident,rows in imported.items() if any(real_task(row) for row in rows) and real_task(tasks.get(ident))}-seen
    if not seen and not unverified:nonempty(receipt.get('quiet_reason'),'honest quiet-audit explanation')
    available=any(r['status'] in {'complete','partial'} for r in coverage.values())
    complete=selected==set(coverage) and all(r['status']=='complete' for r in coverage.values()) and not unverified
    status=('ready' if seen else 'quiet') if complete else 'partial' if available else 'blocked'
    result=deepcopy(profile);first={'state':status,'completed':complete,'real_task_count':len(seen),'verified_task_ids':sorted(seen),'unverified_task_ids':sorted(unverified),'coverage':list(coverage.values()),'missing_sources':sorted(selected-set(coverage)),'started_at':receipt['started_at'],'completed_at':receipt['completed_at'],'authorization_reference':receipt['authorization_reference'],'import_fingerprints':list(fingerprints),'quiet_reason':receipt.get('quiet_reason') if not seen else None,'receipt_recorded_at':stamp}
    result.setdefault('onboarding',{}).update(stage='ready' if complete else 'orientation_partial' if available else 'orientation_blocked',first_run=first,updated_at=stamp)
    return result

def orientation_status(profile):
    first=profile.get('onboarding',{}).get('first_run') or {}
    if not first:note='Your assistant has not recorded the first source-backed audit yet. An empty workspace does not prove a review ran.'
    elif first.get('unverified_task_ids'):note=f"Source review is recorded. {len(first['unverified_task_ids'])} imported task(s) still need their original source verified."
    elif first.get('state')=='blocked':note='The first audit is blocked by source access or coverage. No complete review is claimed.'
    elif first.get('state')=='partial':note='The first audit has partial source coverage. Available work is preserved; the remaining gaps are listed below.'
    elif first.get('state')=='quiet':note='The approved source review is complete. No new assigned tasks were found in the checked scope.'
    else:note='The source review and imported personal tasks have been checked against their original evidence.'
    return {'stage':profile.get('onboarding',{}).get('stage','not_started'),'state':first.get('state','not_run'),'completed':first.get('completed') is True and first.get('state') in {'ready','quiet'},'real_task_count':first.get('real_task_count',0),'verified_task_ids':first.get('verified_task_ids',[]),'unverified_task_ids':first.get('unverified_task_ids',[]),'coverage':first.get('coverage',[]),'missing_sources':first.get('missing_sources',[]),'quiet_reason':first.get('quiet_reason'),'note':note}
