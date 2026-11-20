"""Local setup preferences. No remote access, writes or credentials."""
from copy import deepcopy
from compensation import apply_compensation, catalog_payload, country_code, role_key, preset_from_verified_profile, COUNTRIES
from datetime import datetime, timezone
import re
import math
from orientation import DEFAULT_SOURCES, schedule_defaults, propose_cadence, orientation_status, schedule_status
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MODULES={'daily_closeout','call_hygiene','deal_followthrough','demo_prep','weekly_qci','scorecard'}
SOURCES={
 'email':'Recent work email: last 14 days, active-deal questions and commitments',
 'slack':'Own Slack profile and recent work Slack: last 14 days, DMs, group DMs, direct/alias tags, active-deal threads and exact latest replies',
 'hex':'Official Hex/scorecard: current month and current quarter, own activity and credited outcomes',
 'crm':'CRM: own active/assigned deals, current properties and latest 7 days of matched CALL activities with transcript links in the verified own portal',
 'calendar':'Work calendar: past 7 and next 14 days, work meeting context',
 'meeting_notes':'Zoom/Gong and meeting transcripts: attended work calls from the last 7 days only',
 'qci':'Current-quarter QCI/goals documents explicitly identified by the user',
 'automation_usage':'Local Codex automation-run IDs, timestamps, models and token metadata for your configured Workbench operating workflows. No chat message bodies',
 'compensation':'Your own current role/level and employer role-level compensation bands you identify, including geography, currency and effective date. No colleague salaries',
 'writing_voice':'Your own sent work Slack messages and emails from the last {months} months, plus existing voice-note transcripts; writing-style examples only'
}
FIELDS={'name','email','title','company','role_lane','segment','geography','country','timezone','manager_name','manager_email','director_name','director_email','goals','qci_goals','demo_flow','demo_preferences','writing_style','voice_lookback_months','transcription_source','feedback_cadence','feedback_sharing','role_level','rate_mode','hourly_rate','annual_amount','annual_hours','compensation_basis','compensation_method','role_key','currency','fx_usd_per_local','fx_as_of','fx_basis','fx_allow_stale','modules','additional_sources','transcription_method'}

def now():return datetime.now(timezone.utc).isoformat()
def text(value,limit=2000):
 if not isinstance(value,str) or len(value)>limit:raise ValueError('Use text within the displayed length limit')
 return value.strip() or None

def requested_reads(profile,choices,stamp):
 previous=profile.get('read_requests',{});rows={};changed=False
 for key,template in SOURCES.items():
  old=previous.get(key,{})
  scope=template.format(months=profile.get('preferences',{}).get('writing_voice',{}).get('lookback_months',3));requested=key in choices
  same=old.get('requested') is requested and old.get('scope')==scope
  rows[key]=deepcopy(old) if same else {'requested':requested,'scope':scope,'status':'awaiting_chat_approval' if requested else 'skipped','requested_at':stamp}
  if requested and not same or old.get('requested') is True and not requested:changed=True
 return rows,changed

def update(profile,body,catalog=None):
 if not isinstance(body,dict):raise ValueError('Expected an object')
 action=body.get('action');stamp=now();result=deepcopy(profile)
 if action=='orientation_request':
  if set(body)-{'action','sources','recurring_requested'}:raise ValueError('Unsupported orientation fields')
  choices=body.get('sources',list(DEFAULT_SOURCES))
  if not isinstance(choices,list) or any(not isinstance(x,str) for x in choices) or len(set(choices))!=len(choices) or any(x not in SOURCES for x in choices):raise ValueError('Choose bounded orientation sources from the list')
  recurring=body.get('recurring_requested',True)
  if type(recurring) is not bool:raise ValueError('Choose whether recurring upkeep is requested')
  result['read_requests'],changed=requested_reads(result,choices,stamp)
  setup=result.setdefault('onboarding',{})
  if not setup.get('first_run') or changed:
   if setup.get('first_run'):
    setup['previous_first_run']=deepcopy(setup['first_run']);setup['first_run']={'state':'partial','completed':False,'real_task_count':0,'verified_task_ids':[],'coverage':[],'missing_sources':list(choices)}
   setup.update(stage='awaiting_orientation_approval',updated_at=stamp)
  result=propose_cadence(result,{'action':'cadence_preferences','recurring_requested':recurring},stamp)
  result['mode']='personal';result['schema_version']=2
 elif action=='demo_prep_preferences':
  if set(body)-{'action','enabled'} or type(body.get('enabled')) is not bool:raise ValueError('Choose on or off for internal demo prep booking')
  saved=deepcopy(result.setdefault('preferences',{}).get('demo_prep_booking',{}))
  saved.update(enabled=body['enabled'],state='requested' if body['enabled'] else 'off',updated_at=stamp)
  result['preferences']['demo_prep_booking']=saved
 elif action=='cadence_preferences':
  result=propose_cadence(result,body,stamp)
 elif action=='preferences':
  bad=set(body)-FIELDS-{'action'}
  if bad:raise ValueError('Unsupported setup fields: '+', '.join(sorted(bad)))
  cleaned={k:text(v,4000 if k in {'goals','qci_goals','demo_flow','demo_preferences','writing_style'} else 250) for k,v in body.items() if k not in {'action','modules','additional_sources','voice_lookback_months','hourly_rate','annual_amount','annual_hours','fx_usd_per_local','fx_allow_stale'}}
  if 'voice_lookback_months' in body and (type(body['voice_lookback_months']) is not int or body['voice_lookback_months'] not in {3,6}):raise ValueError('Choose a 3- or 6-month writing sample')
  for key in ('email','manager_email','director_email'):
   if cleaned.get(key) and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',cleaned[key]):raise ValueError('Use a valid work email or leave optional email blank')
  if cleaned.get('timezone'):
   try:ZoneInfo(cleaned['timezone'])
   except (ZoneInfoNotFoundError,ValueError):raise ValueError('Choose a valid IANA time zone')
  modules=body.get('modules',result.get('preferences',{}).get('modules',{k:True for k in MODULES}))
  if not isinstance(modules,dict) or set(modules)!=MODULES or any(type(v) is not bool for v in modules.values()):raise ValueError('Choose on/off for every workflow')
  identity=result['identity'];org=result['organization'];evidence=result.setdefault('identity_evidence',[])
  for key in ('name','email','title'):
   if key in cleaned:
    if identity.get('verified') and identity.get(key) and cleaned[key]!=identity[key]:raise ValueError('Ask your assistant to resolve changes to a verified identity')
    identity[key]=cleaned[key]
  for key in ('company','role_lane','segment','geography','country','timezone'):
   if key in cleaned:org[key]=cleaned[key]
  for role in ('manager','director'):
   for key in ('name','email'):
    field=role+'_'+key
    if field in cleaned:org[role][key]=cleaned[field]
  evidence=[x for x in evidence if x.get('source')!='local_setup_form']
  evidence += [{'field':k,'value':v,'source':'local_setup_form','confidence':'user_reported','observed_at':stamp} for k,v in cleaned.items() if v and k not in {'goals','qci_goals','demo_flow','demo_preferences','writing_style'}]
  result['identity_evidence']=evidence
  prefs=result.setdefault('preferences',{})
  prefs.update(modules=modules)
  for key in ('goals','demo_flow','demo_preferences'):
   if key in cleaned:prefs[key]=[x.strip() for x in (cleaned[key] or '').splitlines() if x.strip()] if key=='goals' else cleaned[key]
  if 'transcription_source' in cleaned:
   if not re.fullmatch(r'[A-Za-z0-9 .;_-]{1,60}',cleaned['transcription_source'] or ''):raise ValueError('Name your call-capture tool')
   prefs['call_capture']={'provider':cleaned['transcription_source'],'state':'not_verified'}
  if 'transcription_method' in cleaned:prefs.setdefault('call_capture',{})['method']=cleaned['transcription_method']
  if 'additional_sources' in body:
   sources=body['additional_sources']
   if not isinstance(sources,list) or len(sources)>20 or any(not isinstance(x,str) or not 1<=len(x.strip())<=80 for x in sources):raise ValueError('Name up to20 additional tools')
   prefs['additional_sources']=list(dict.fromkeys(x.strip() for x in sources))
  if 'feedback_cadence' in cleaned or 'feedback_sharing' in cleaned:
   cadence=cleaned.get('feedback_cadence') or '1';sharing=cleaned.get('feedback_sharing') or 'ask'
   if cadence not in {'1','2'} or sharing not in {'ask','off'}:raise ValueError('Choose a feedback cadence and sharing preference')
   prefs['product_feedback']={'cadence_weeks':int(cadence),'mode':sharing,'automatic_submission':False}
  if any(k in body for k in ('role_level','role_key','rate_mode','compensation_method','hourly_rate','annual_amount','annual_hours','compensation_basis','currency')):
   comp=deepcopy(result.get('compensation',{}));method=cleaned.get('compensation_method') or {'band':'role'}.get(cleaned.get('rate_mode'),cleaned.get('rate_mode')) or comp.get('compensation_method','role')
   if method not in {'role','annual','hourly'}:raise ValueError('Choose a role default or custom amount')
   chosen_role=cleaned.get('role_key') or role_key(cleaned.get('role_level')) or role_key(identity.get('title'))
   country=country_code(cleaned.get('country') or org.get('country'))
   if not country and method in {'hourly','annual'} and (cleaned.get('country') or org.get('country')):country='OTHER'
   currency=cleaned.get('currency') or (COUNTRIES[country][1] if country else comp.get('currency','USD'))
   hours=body.get('annual_hours',comp.get('annual_hours',2080))
   if isinstance(hours,bool) or not isinstance(hours,(int,float)) or not math.isfinite(hours) or not 0<hours<=8784:raise ValueError('Use positive annual working hours')
   basis=cleaned.get('compensation_basis') or comp.get('annual_basis','ote')
   if basis not in {'base','ote','loaded'}:raise ValueError('Choose base pay, OTE or employer cost')
   # Validate any explicitly supplied numeric value even when that control is inactive.
   for numeric,maximum in [('hourly_rate',1e10),('annual_amount',1e10)]:
    value=body.get(numeric)
    if value not in (None,'') and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<value<=maximum):raise ValueError('Use a positive '+numeric.replace('_',' '))
   if chosen_role and country and (method!='role' or any(p['role_key']==chosen_role and p['country']==country for p in (catalog or {}).get('presets',[]))):
    patch={'method':method,'role_key':chosen_role,'country':country,'country_name':cleaned.get('country') or org.get('country') if country=='OTHER' else None,'currency':currency,'annual_hours':hours,'annual_basis':'ote' if basis=='loaded' else basis,'custom_value':body.get('annual_amount') if method=='annual' else body.get('hourly_rate'),'fx_usd_per_local':body.get('fx_usd_per_local'),'fx_as_of':cleaned.get('fx_as_of') or '','fx_basis':cleaned.get('fx_basis') or '','fx_allow_stale':body.get('fx_allow_stale',False)}
    comp=apply_compensation(comp,patch,catalog)
   else:
    # No catalog or identity match is a research gap, not a verified dollar rate.
    if method!='role':
     amount=body.get('annual_amount') if method=='annual' else body.get('hourly_rate')
     if not amount:raise ValueError('Enter a custom compensation amount')
     comp.update(mode=method,annual_amount=amount if method=='annual' else None,hourly_rate=amount/hours if method=='annual' else amount,basis='Your custom planning value')
    else:comp.update(mode='band',band_verified=False,hourly_rate=None,band_min=None,band_max=None,basis='Role band pending; select an approved country benchmark or a custom amount')
    comp.update(currency=currency,role_key=chosen_role,role_level=cleaned.get('role_level') or comp.get('role_level'),country=country,annual_basis=basis,annual_hours=hours,compensation_method=method)
   comp.update(updated_at=stamp,user_overridden=method in {'hourly','annual'} or bool(chosen_role and country and (cleaned.get('role_key') or cleaned.get('role_level'))))
   result['compensation']=comp
  elif catalog:
   automatic=preset_from_verified_profile(result,catalog)
   if automatic:result['compensation']=automatic
  voice=prefs.setdefault('writing_voice',{})
  if 'writing_style' in cleaned:voice['user_notes']=cleaned['writing_style']
  if 'voice_lookback_months' in body:voice['lookback_months']=body['voice_lookback_months']
  voice.setdefault('lookback_months',3);voice.setdefault('state','not_sampled')
  if 'qci_goals' in cleaned:result['qci']['goals']=[x.strip() for x in (cleaned['qci_goals'] or '').splitlines() if x.strip()]
  # Preferences never grant a write, install a schedule or mark identity verified.
  result['mode']='personal';result['schema_version']=2
  setup=result.setdefault('onboarding',{});setup['updated_at']=stamp
  if setup.get('stage','not_started') in {'not_started','preferences_saved'}:setup['stage']='preferences_saved'
 elif action=='preview_seen':
  if set(body)!={'action'}:raise ValueError('Unsupported preview fields')
  if result.get('onboarding',{}).get('stage')=='not_started':raise ValueError('Save your preferences first')
  setup=result.setdefault('onboarding',{});setup.update(preview_seen=True,updated_at=stamp)
  if setup.get('stage') in {'preferences_saved','previewed'}:setup['stage']='previewed'
 elif action=='sources':
  if set(body)!={'action','sources'}:raise ValueError('Unsupported source fields')
  if not result.get('onboarding',{}).get('preview_seen'):raise ValueError('Preview your Workbench before choosing sources')
  choices=body.get('sources')
  if not isinstance(choices,list) or any(x not in SOURCES for x in choices):raise ValueError('Choose sources from the list')
  result['read_requests'],changed=requested_reads(result,choices,stamp)
  setup=result.setdefault('onboarding',{})
  if not setup.get('first_run') or changed:
   if setup.get('first_run'):
    setup['previous_first_run']=deepcopy(setup['first_run']);setup['first_run']={'state':'partial','completed':False,'real_task_count':0,'verified_task_ids':[],'coverage':[],'missing_sources':list(choices)}
   setup.update(stage='awaiting_source_approval' if choices else 'local_ready',updated_at=stamp)
 else:raise ValueError('Unknown setup action')
 return result

def handoff(profile):
 selected=[v['scope'] for v in profile.get('read_requests',{}).values() if v.get('requested')]
 return ('Continue my SE Workbench setup from this folder. Read AGENTS.md, docs/ONBOARDING.md and my private workspace/profile.json. '
 'This is an orientation-first setup; do not require me to type identity facts you can verify from approved sources. Check for supported Python 3.10+ and offer a short plain-language install explanation if missing; install only after I explicitly approve in chat, never through the local web server. My local preferences are saved. '+('Before reading work content, ask me to approve read-only access to these selected scopes: '+ '; '.join(selected)+'. ' if selected else 'No work sources are selected. Keep account reads off, open the local Workbench, and offer the single bounded orientation choice without a required preview or questionnaire. ')+
 'After I approve the bounded reads, verify my work identity, actual reporting line, segment, geography, timezone and CRM mappings using only approved sources. '
 'If I approve the writing-voice scope, sample only my own sent work Slack/email examples, including new-deal introductions, short replies and existing voice-note transcripts. Keep authored text separate from quoted replies and auto-generated reports. Save a private workspace/voice-profile.json with channel-specific style rules, dated sources and actual sample coverage. Show me three short example drafts to tune, then apply the profile to future drafts without overwriting saved wording or completed work. Skip this research when I have not approved it. '
 'Run python3 workbench.py discover-capture and inspect available native connector metadata to find call-capture sources such as Fellow, Granola, Wispr Flow, Zoom/Gong or another recorder/transcription tool. Check installed-app names only at first, not recordings or private files. An installed app is only a candidate, not proof of usable transcripts. If no usable source is found, ask how I currently record or transcribe calls; if I use nothing, recommend two or three current organization-approved options, preferring existing paid tools and checking official documentation, capability and policy before recommending an installation. Do not silently install or enable recording. Ask what other apps or sources I want included, such as Asana or Fellow; inspect actual available connectors/access and agree a bounded read scope before adding them. A missing default integration is not a permanent product exclusion. Verify my chosen source before claiming transcript coverage. Explain the hour-plus setup expectation, weekly QCI/feedback and safe GitHub updates. '
 'If I selected compensation research, read my current Slack profile through approved read-only access and verify my title, work country and currency against my own approved employer pay-band materials; preset ASE, Solutions Engineer, Senior Solutions Engineer or Lead Solutions Engineer and that country in the wizard without overwriting my manual choices. Keep any catalog in private workspace/compensation-role-catalog.json. Use the matching role/country midpoint when available, and a dated USD-per-local-currency assumption for comparing local labor value with USD automation costs. Never substitute one country’s salary or currency for another. A band midpoint is an estimate, not my actual salary. Offer base, OTE or employer-cost basis and confirm annual hours; leave value and ROI unavailable until a supported benchmark or custom value is selected. Never include individual compensation or internal pay tables in shared exports or feedback submissions. '
 'Respect my selected workflows, goals and demo preferences. Show unknowns honestly, run docs/FIRST-TEST.md, and open my personal Workbench. '
 'Complete the first bounded audit now using my own approved tools; preserve current work and completed decisions. Import actual source-backed tasks with stable IDs using workbench.py import --mode personal. Do not invent tasks to fill the page: a quiet audit is valid, and unavailable sources stay explicit gaps. Record source-by-source coverage and verify every real imported task against its exact native source and excerpt, then save a schema1 receipt with workbench.py record-orientation RECEIPT.json. Optional local Customer/Internal guide cards are separate from actual personal tasks and earn no time savings. '
 'If my recurring_requested preference is true, include the daily upkeep run in the explicit chat consent request. After consent and a verified local time zone, use the native assistant scheduler for daily upkeep (default 17:30). Optional daytime communication checks are OFF for new users to reduce token use; saved 09:00, 12:00 and 15:00 times are inactive suggestions only. Do not create light jobs unless I explicitly opt in through Settings or chat, and the saved schedules.light.enabled choice is true. Preserve explicit choices in existing installations or legacy verified active light-job evidence; never stop existing jobs merely because a new-user default changed. Do not ask separately to accept default times. Read back the actual native jobs and record their exact IDs, recurrence, timezone and tool evidence with workbench.py record-schedule RECEIPT.json. JSON preferences do not create jobs or grant permissions. Settings times are quietly editable; reconcile authorized native jobs when settings change. No custom cron or hidden server scheduler. '
 'Keep CRM writes, sends and demo creation off unless I explicitly authorize their exact scope in chat. A read or recurring-upkeep consent is not a write grant.')
