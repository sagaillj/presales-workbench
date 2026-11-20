"""Read-only scheduled-run token accounting. Follow-up chat turns never count."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RATE_SOURCE = 'https://help.openai.com/en/articles/20001415-chatgpt-rate-card-enterprise-token-based-pricing'
# Published Standard rates, USD per million tokens, checked November 18, 2026.
RATES = {'gpt-6.1-sol': (2,.1,10), 'gpt-6.1-terra': (1,.05,5), 'gpt-6-astra': (10,1,50), 'gpt-6-sol': (2,.2,10), 'gpt-6-luna': (.1,.01,.5), 'gpt-5.6-sol': (4,.4,20), 'gpt-5.6-terra': (2,.2,12), 'gpt-5.6-luna': (.2,.02,1.2), 'gpt-5.3-codex': (1.75,.175,14)}

def scheduled_usage(path, start, end):
    """Attribute cumulative deltas to the initial scheduled turn, stopping at follow-up."""
    first = active = model = None
    previous = dict(input_tokens=0,cached_input_tokens=0,output_tokens=0)
    models = defaultdict(lambda: dict(input_tokens=0,cached_input_tokens=0,output_tokens=0))
    events = 0; excluded_followup = False; gaps = []
    with Path(path).open() as stream:
        for line in stream:
            if not any(t in line for t in ['"turn_context"','"token_count"']):
                continue
            try: item=json.loads(line)
            except ValueError: gaps.append('Malformed usage record'); continue
            payload=item.get('payload',{})
            if item.get('type')=='turn_context':
                active=payload.get('turn_id') or payload.get('root_turn_id')
                if not active: gaps.append('Scheduled turn identity missing'); continue
                if first is None: first=active
                if active!=first: excluded_followup=True; break
                model=payload.get('model') or model
            elif item.get('type')=='event_msg' and payload.get('type')=='token_count':
                total=(payload.get('info') or {}).get('total_token_usage')
                if not total: continue
                values={k:total.get(k) for k in previous}
                if any(type(v) is not int or v<0 for v in values.values()): gaps.append('Invalid token counters'); continue
                if values['cached_input_tokens']>values['input_tokens']: gaps.append('Cached tokens exceed total input'); continue
                delta={k:values[k]-previous[k] for k in values}
                if any(v<0 for v in delta.values()): gaps.append('Usage counter reset'); previous=values; continue
                previous=values
                stamp=item.get('timestamp','')
                if not first or not model: gaps.append('Unattributed usage'); continue
                if start<=stamp<end and any(delta.values()):
                    for key,value in delta.items(): models[model][key]+=value
                    events+=1
    rows=[]
    for name,usage in sorted(models.items()):
        rate=RATES.get(name)
        cost=((usage['input_tokens']-usage['cached_input_tokens'])*rate[0]+usage['cached_input_tokens']*rate[1]+usage['output_tokens']*rate[2])/1e6 if rate else None
        rows.append(dict(model=name,**usage,standard_token_estimate_usd=round(cost,6) if cost is not None else None))
    return dict(first_turn_id=first,models=rows,usage_events=events,followup_turns_excluded=excluded_followup,gaps=sorted(set(gaps)))

def cost_summary(runs, month, generated_at=None):
    priced=[m for run in runs for m in run.get('models',[])]
    missing=[r.get('thread_id') for r in runs if r.get('missing') or r.get('gaps')]
    unknown=sorted({m['model'] for m in priced if m['standard_token_estimate_usd'] is None})
    amount=sum(m['standard_token_estimate_usd'] for m in priced if m['standard_token_estimate_usd'] is not None)
    return dict(month=month,generated_at=generated_at or datetime.now(timezone.utc).isoformat(),currency='USD',scope='scheduled_automation_initial_turns',runs=len(runs),runs_with_usage=sum(bool(r.get('usage_events')) for r in runs),followup_chats_excluded=sum(bool(r.get('followup_turns_excluded')) for r in runs),billed_usd=None,standard_token_estimate_usd=round(amount,4) if priced and not missing and not unknown else None,known_standard_token_estimate_usd=round(amount,4),missing_run_ids=missing,unpriced_models=unknown,rate_source=RATE_SOURCE,rate_checked_date='2026-11-18',basis='Recorded scheduled-run model tokens at published Standard rates. Excludes follow-up chat turns, Workbench development, manual sessions and account-wide spending. Contract discounts, speed multipliers, separate tools and unrecorded usage are not reconciled. This is not billed automation cost.',records=runs)
