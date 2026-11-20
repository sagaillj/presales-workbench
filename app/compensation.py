"""Private role benchmarks and explicit currency assumptions; no network or identity reads."""
import json
import math
import re
from copy import deepcopy
from pathlib import Path

ROLES = {'ase':'Associate Solutions Engineer','se':'Solutions Engineer','senior':'Senior Solutions Engineer','lead':'Lead Solutions Engineer'}
COUNTRIES = {'US':('United States','USD'),'CA':('Canada','CAD'),'BR':('Brazil','BRL'),'CO':('Colombia','COP'),'AU':('Australia','AUD'),'BE':('Belgium','EUR'),'FR':('France','EUR'),'DE':('Germany','EUR'),'IN':('India','INR'),'IE':('Ireland','EUR'),'JP':('Japan','JPY'),'NL':('Netherlands','EUR'),'SG':('Singapore','SGD'),'ES':('Spain','EUR'),'GB':('United Kingdom','GBP'),'OTHER':('Other country / custom','')}
COUNTRY_ALIASES = {'USA':'US','UNITED STATES OF AMERICA':'US','UK':'GB','GREAT BRITAIN':'GB'}

def role_key(title):
    value=re.sub(r'\s+',' ',str(title or '').strip()).lower()
    for key,patterns in [('ase',('associate solutions engineer','associate solution engineer','ase')),('senior',('senior solutions engineer','senior solution engineer','senior se')),('lead',('lead solutions engineer','lead solution engineer','lead se')),('se',('solutions engineer','solution engineer','se'))]:
        if any(re.fullmatch(re.escape(p)+r'(?:\s+l\d+)?',value) for p in patterns): return key
    return None

def country_code(value):
    value=str(value or '').strip()
    if value.upper() in COUNTRIES: return value.upper()
    if value.upper() in COUNTRY_ALIASES:return COUNTRY_ALIASES[value.upper()]
    return next((key for key,(name,_) in COUNTRIES.items() if value.casefold()==name.casefold()),None)

def catalog_payload(source=None):
    """Return only role-level inputs from an explicitly supplied private catalog."""
    if isinstance(source,dict):raw=source
    else:
        try:raw=json.loads(Path(source).read_text()) if source else {}
        except (OSError,ValueError,TypeError):raw={}
    groups={}
    for entry in raw.get('entries',[]):
        role=role_key(entry.get('role'));country=country_code(entry.get('country'));base=entry.get('base');ote=entry.get('ote')
        if not role or not country or country=='OTHER' or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (base,ote)):continue
        currency=entry.get('currency') or COUNTRIES[country][1]
        if not re.fullmatch('[A-Z]{3}',currency):continue
        key=(role,country,currency);groups.setdefault(key,[]).append(entry)
    presets=[]
    for (role,country,currency),rows in sorted(groups.items()):
        sources=list(dict.fromkeys(r.get('source_url') for r in rows if r.get('source_url')))
        if not sources:continue
        presets.append({'role_key':role,'role':ROLES[role],'country':country,'country_name':COUNTRIES[country][0],'currency':currency,'base_min':min(r['base'] for r in rows),'base_max':max(r['base'] for r in rows),'ote_min':min(r['ote'] for r in rows),'ote_max':max(r['ote'] for r in rows),'source_url':sources[0],'source_title':raw.get('source_title','Approved role pay grid'),'source_ranges':[r.get('source_range') for r in rows if r.get('source_range')],'checked_at':raw.get('verified_at') or max((r.get('source_checked_at','') for r in rows),default=''),'currency_basis':rows[0].get('currency_status','Country-local currency assumption; confirm against your source.'),'levels':[r['role'] for r in rows]})
    return {'roles':[{'id':k,'label':v} for k,v in ROLES.items()],'countries':[{'id':k,'label':v[0],'currency':v[1]} for k,v in COUNTRIES.items()],'presets':presets,'private':True,'available':bool(presets)}

def positive(value,name,maximum):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<=maximum:raise ValueError('Use a positive '+name+' within the supported range')
    return value

def apply_compensation(current,patch,catalog=None):
    if not isinstance(patch,dict) or set(patch)-{'method','role_key','country','country_name','currency','annual_basis','annual_hours','custom_value','fx_usd_per_local','fx_as_of','fx_basis','fx_allow_stale'}:raise ValueError('Unknown compensation setting')
    result=deepcopy(current);method=patch.get('method','role');role=patch.get('role_key');country=country_code(patch.get('country'));currency=patch.get('currency') or (COUNTRIES[country][1] if country else 'USD');basis=patch.get('annual_basis','ote');hours=positive(patch.get('annual_hours',2080),'annual hours',8784)
    if method not in {'role','hourly','annual'} or role not in ROLES or not country or basis not in {'base','ote'} or not isinstance(currency,str) or not re.fullmatch('[A-Z]{3}',currency):raise ValueError('Choose a valid role, country, currency and value method')
    custom_country=patch.get('country_name') or result.get('country_name')
    if country=='OTHER':
        if method=='role':raise ValueError('Other countries require a custom value; no pay benchmark is assumed')
        if not isinstance(custom_country,str) or not 2<=len(custom_country.strip())<=100:raise ValueError('Enter the country name for your custom value')
        custom_country=custom_country.strip()
        if not patch.get('currency'):raise ValueError('Choose the currency for your custom country')
    preset=next((p for p in (catalog or {}).get('presets',[]) if p['role_key']==role and p['country']==country),None)
    result.update(compensation_method=method,country_name=custom_country if country=='OTHER' else COUNTRIES[country][0],role_key=role,role_level=ROLES[role],country=country,currency=currency,annual_basis=basis,annual_hours=hours)
    if method=='role':
        if not preset:raise ValueError('No approved pay benchmark for this role and country. Choose a custom value or research a local benchmark.')
        if currency!=preset['currency']:raise ValueError('Role preset currency must match the source country. Choose custom to use another currency.')
        low,high=preset[basis+'_min'],preset[basis+'_max']
        result.update(mode='band',band_verified=True,band_min=low,band_max=high,source_url=preset['source_url'],hourly_rate=(low+high)/2/hours,basis=preset['country_name']+' '+ROLES[role]+' '+basis.upper()+' midpoint')
        result['compensation_benchmark']={**preset,'country':preset['country_name'],'note':'Published role grid, not individual salary. Exact sublevel is unknown; uses the midpoint across available levels. '+preset['currency_basis']}
    else:
        amount=positive(patch.get('custom_value'),'custom amount',1e10)
        result.update(mode=method,band_verified=False,hourly_rate=amount if method=='hourly' else amount/hours,annual_amount=amount if method=='annual' else None,basis='Your custom '+('hourly' if method=='hourly' else 'annual '+basis.upper())+' planning value')
        result.pop('compensation_benchmark',None)
    fx=patch.get('fx_usd_per_local')
    if currency=='USD':result.update(fx_usd_per_local=1,fx_currency='USD',fx_basis='USD cost currency',fx_as_of=None)
    elif fx not in (None,''):
        result['fx_usd_per_local']=positive(fx,'USD per local currency unit',10000);result['fx_currency']=currency
        asof=patch.get('fx_as_of','');source=patch.get('fx_basis','')
        if not isinstance(asof,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',asof) or not isinstance(source,str) or not 1<=len(source.strip())<=300:raise ValueError('Add the exchange-rate date and source or assumption')
        
        from datetime import date
        try:date.fromisoformat(asof)
        except ValueError:raise ValueError('Use a valid exchange-rate date')
        stale=patch.get('fx_allow_stale',False)
        if type(stale) is not bool:raise ValueError('Choose whether to use an older planning rate')
        result.update(fx_as_of=asof,fx_basis=source.strip(),fx_allow_stale=stale)
    else:
        for key in ('fx_usd_per_local','fx_currency','fx_as_of','fx_basis','fx_allow_stale'):result.pop(key,None)
    return result

def preset_from_verified_profile(profile,catalog):
    """Use already verified Slack evidence. Never invent a source lookup or overwrite edits."""
    comp=profile.get('compensation',{})
    if comp.get('user_overridden') or comp.get('compensation_method') in {'hourly','annual'} or (comp.get('mode') in {'hourly','annual'} and (comp.get('annual_amount') or str(comp.get('basis','')).lower().startswith(('your','user-provided')))):return None
    identity=profile.get('identity',{});org=profile.get('organization',{})
    if identity.get('verified') is not True:return None
    role=role_key(identity.get('title'));country=country_code(org.get('country'))
    if not role or not country:return None
    preset=next((p for p in catalog.get('presets',[]) if p['role_key']==role and p['country']==country),None)
    return apply_compensation(comp,{'method':'role','role_key':role,'country':country,'currency':preset['currency'],'annual_basis':'ote','annual_hours':comp.get('annual_hours',2080)},catalog) if preset else None
