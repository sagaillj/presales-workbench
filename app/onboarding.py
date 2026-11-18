"""Local setup preferences. No remote access, writes or credentials."""
from copy import deepcopy
from datetime import datetime, timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MODULES={'daily_closeout','call_hygiene','deal_followthrough','demo_prep','weekly_qci','scorecard'}
SOURCES={
 'email':'Recent work email: last 14 days, active-deal questions and commitments',
 'slack':'Recent work Slack: last 14 days, direct mentions and active-deal threads',
 'hex':'Official Hex/scorecard: current month and current quarter, own activity and credited outcomes',
 'crm':'CRM: own active/assigned deals, current properties and recent activity',
 'calendar':'Work calendar: past 7 and next 14 days, work meeting context',
 'meeting_notes':'Meeting notes/transcripts: attended work calls from the last 7 days',
 'qci':'Current-quarter QCI/goals documents explicitly identified by the user',
 'writing_voice':'Your own sent work Slack messages and emails from the last {months} months, plus existing voice-note transcripts; writing-style examples only'
}
FIELDS={'name','email','title','company','role_lane','segment','geography','country','timezone','manager_name','manager_email','director_name','director_email','goals','qci_goals','demo_flow','demo_preferences','writing_style','voice_lookback_months','transcription_source','feedback_cadence','feedback_sharing','modules'}

def now():return datetime.now(timezone.utc).isoformat()
def text(value,limit=2000):
 if not isinstance(value,str) or len(value)>limit:raise ValueError('Use text within the displayed length limit')
 return value.strip() or None

def update(profile,body):
 if not isinstance(body,dict):raise ValueError('Expected an object')
 action=body.get('action');stamp=now();result=deepcopy(profile)
 if action=='preferences':
  bad=set(body)-FIELDS-{'action'}
  if bad:raise ValueError('Unsupported setup fields: '+', '.join(sorted(bad)))
  cleaned={k:text(v,4000 if k in {'goals','qci_goals','demo_flow','demo_preferences','writing_style'} else 250) for k,v in body.items() if k not in {'action','modules','voice_lookback_months'}}
  if 'voice_lookback_months' in body and (type(body['voice_lookback_months']) is not int or body['voice_lookback_months'] not in {3,6}):raise ValueError('Choose a 3- or 6-month writing sample')
  for key in ('email','manager_email','director_email'):
   if cleaned.get(key) and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',cleaned[key]):raise ValueError('Use a valid work email or leave optional email blank')
  if not cleaned.get('name'):raise ValueError('Please enter your name')
  if cleaned.get('timezone'):
   try:ZoneInfo(cleaned['timezone'])
   except (ZoneInfoNotFoundError,ValueError):raise ValueError('Choose a valid IANA time zone')
  modules=body.get('modules')
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
   if cleaned['transcription_source'] not in {'unknown','wispr','granola','zoom','gong','other'}:raise ValueError('Choose a call-capture option')
   prefs['call_capture']={'provider':cleaned['transcription_source'],'state':'not_verified'}
  if 'feedback_cadence' in cleaned or 'feedback_sharing' in cleaned:
   cadence=cleaned.get('feedback_cadence') or '1';sharing=cleaned.get('feedback_sharing') or 'ask'
   if cadence not in {'1','2'} or sharing not in {'ask','off'}:raise ValueError('Choose a feedback cadence and sharing preference')
   prefs['product_feedback']={'cadence_weeks':int(cadence),'mode':sharing,'automatic_submission':False}
  voice=prefs.setdefault('writing_voice',{})
  if 'writing_style' in cleaned:voice['user_notes']=cleaned['writing_style']
  if 'voice_lookback_months' in body:voice['lookback_months']=body['voice_lookback_months']
  voice.setdefault('lookback_months',3);voice.setdefault('state','not_sampled')
  if 'qci_goals' in cleaned:result['qci']['goals']=[x.strip() for x in (cleaned['qci_goals'] or '').splitlines() if x.strip()]
  # Preferences never grant a write, install a schedule or mark identity verified.
  result['mode']='personal';result['schema_version']=2
  result.setdefault('onboarding',{}).update(stage='preferences_saved',updated_at=stamp)
 elif action=='preview_seen':
  if set(body)!={'action'}:raise ValueError('Unsupported preview fields')
  if result.get('onboarding',{}).get('stage')=='not_started':raise ValueError('Save your preferences first')
  result.setdefault('onboarding',{}).update(preview_seen=True,stage='previewed',updated_at=stamp)
 elif action=='sources':
  if set(body)!={'action','sources'}:raise ValueError('Unsupported source fields')
  if not result.get('onboarding',{}).get('preview_seen'):raise ValueError('Preview your Workbench before choosing sources')
  choices=body.get('sources')
  if not isinstance(choices,list) or any(x not in SOURCES for x in choices):raise ValueError('Choose sources from the list')
  result['read_requests']={k:{'requested':k in choices,'scope':v.format(months=result.get('preferences',{}).get('writing_voice',{}).get('lookback_months',3)),'status':'awaiting_chat_approval' if k in choices else 'skipped','requested_at':stamp} for k,v in SOURCES.items()}
  result['onboarding'].update(stage='awaiting_source_approval' if choices else 'local_ready',updated_at=stamp)
 else:raise ValueError('Unknown setup action')
 return result

def handoff(profile):
 selected=[v['scope'] for v in profile.get('read_requests',{}).values() if v.get('requested')]
 return ('Continue my SE Workbench setup from this folder. Read AGENTS.md, docs/ONBOARDING.md and my private workspace/profile.json. '
 'My local preferences are saved. '+('Before reading work content, ask me to approve read-only access to these selected scopes: '+ '; '.join(selected)+'. ' if selected else 'I have not chosen any work sources. Offer optional read-only source choices after my preview. ')+
 'Then verify my work identity, actual reporting line, segment, geography, timezone and CRM mappings using only approved sources. '
 'If I approve the writing-voice scope, sample only my own sent work Slack/email examples, including new-deal introductions, short replies and existing voice-note transcripts. Keep authored text separate from quoted replies and auto-generated reports. Save a private workspace/voice-profile.json with channel-specific style rules, dated sources and actual sample coverage. Show me three short example drafts to tune, then apply the profile to future drafts without overwriting saved wording or completed work. Skip this research when I have not approved it. '
 'Verify my preferred call-capture source (Granola, Wispr Flow, or reliable Zoom/Gong transcripts) before claiming transcript coverage. Explain the hour-plus setup expectation, weekly QCI/feedback and safe GitHub updates. '
 'Respect my selected workflows, goals and demo preferences. Show unknowns honestly, run docs/FIRST-TEST.md, and open my personal Workbench. '
 'Keep CRM writes, sends, demo creation and recurring schedules off unless I explicitly authorize their exact scope in chat.')
