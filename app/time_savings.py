"""Prospective completion-based estimates, never measured time or ROI."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Assumed net minutes saved after human review. Larger work requires explicit
# task metadata; titles alone never qualify a task as a demo build.
RANGES = {'context_review': (5, 10), 'prepared_reply': (5, 15),
          'meeting_prep': (15, 30), 'demo_prep': (45, 90), 'call_logging': (5, 15)}
VERSION = 1


def completion_estimate(task):
    if not task or task.get('orientation_guide') is True or task.get('completion_kind') in {'accept_recommendation','orientation'}:
        return None
    category = task.get('time_savings_category', 'context_review')
    if category not in RANGES:
        return None
    low, high = RANGES[category]
    return {'version': VERSION, 'category': category, 'minutes_low': low,
            'minutes_high': high, 'basis': 'Assumed net minutes saved; not timed.'}


def savings_summary(progress, now=None, zone='America/New_York', month=None, retrospective=None):
    # Project approved retrospective assumptions without editing user progress.
    if retrospective and retrospective.get('authorized') is True:
        tasks={k:dict(v) for k,v in progress.get('tasks',{}).items() if isinstance(v,dict)}
        for entry in retrospective.get('entries',[]):
            task_id=entry.get('task_id');key=task_id or 'verified-call:'+str(entry.get('call_id'))
            if task_id:
                row=tasks.get(task_id,{})
                if not row.get('done') or row.get('updated_at')!=entry.get('source_updated_at') or row.get('time_savings'):continue
            elif entry.get('native_call_verified') is True and entry.get('call_id'):
                row={'done':True,'updated_at':entry.get('at')}
            else:continue
            estimate=completion_estimate({'time_savings_category':entry.get('category')})
            if estimate:tasks[key]={**row,'time_savings':estimate}
        progress={**progress,'tasks':tasks}
    now = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(zone))
    today = now.date(); week = today - timedelta(days=today.weekday())
    requested_month = month
    month = month or today.strftime('%Y-%m')
    result = {}
    for period in ('week', 'month', 'all_time'):
        low = high = estimated = unestimated = 0
        for row in progress.get('tasks', {}).values():
            if not isinstance(row, dict) or not row.get('done') or row.get('completion_kind')=='orientation':
                continue
            try:
                at = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
                if at.tzinfo is None: continue
                date = at.astimezone(ZoneInfo(zone)).date()
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
            if at > now or (period == 'week' and not week <= date <= today) or (period == 'month' and date.strftime('%Y-%m') != month):
                continue
            estimate = row.get('time_savings') or {}
            a, b = estimate.get('minutes_low'), estimate.get('minutes_high')
            if estimate.get('version') != VERSION or type(a) not in (int, float) or type(b) not in (int, float) or not 0 <= a <= b <= 480:
                unestimated += 1; continue
            low += a; high += b; estimated += 1
        result[period] = {'minutes_low': low, 'minutes_high': high,
                          'hours_low': round(low / 60, 2), 'hours_high': round(high / 60, 2),
                          'estimated_tasks': estimated, 'unestimated_tasks': unestimated}
    months = {}
    if requested_month is None:
        keys = {month}
        for row in progress.get('tasks', {}).values():
            try:
                at = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
                if row.get('done') and at.tzinfo and at <= now:
                    keys.add(at.astimezone(ZoneInfo(zone)).strftime('%Y-%m'))
            except (KeyError, ValueError, TypeError, AttributeError):
                pass
        months = {key: savings_summary(progress, now, zone, key)['month'] for key in sorted(keys)}
    return {**result, 'months': months, 'version': VERSION, 'month_key': month, 'week_of': week.isoformat(),
            'retrospective_included': bool(retrospective and retrospective.get('authorized') is True),
            'basis': 'Assumed net time saved, not measured time. Includes explicitly authorized retrospective estimates where source completion or native logged-call evidence is retained; other older completions are excluded.',
            'assumptions': {k: list(v) for k, v in RANGES.items()}}
