#!/usr/bin/env python3
"""Refresh local scheduled automation usage without reading work-source message bodies."""
import argparse,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from automation_costs import scheduled_usage,cost_summary
p=argparse.ArgumentParser();p.add_argument('--month',default=datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m'));args=p.parse_args()
start=datetime.strptime(args.month+'-01','%Y-%m-%d').replace(tzinfo=ZoneInfo('America/New_York'));end=start.replace(year=start.year+(start.month==12),month=start.month%12+1)
low=start.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z');high=end.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
config=Path.home()/'.codex/sqlite/codex.db';state=Path.home()/'.codex/state_5.sqlite'
a=sqlite3.connect(f'file:{config}?mode=ro',uri=True);b=sqlite3.connect(f'file:{state}?mode=ro',uri=True)
scope=json.loads((ROOT/'workspace/personal/automation-cost-scope.json').read_text());allowed=set(scope.get('automation_ids',[]))
if not allowed:raise SystemExit('Configure operating-workflow IDs before collecting costs')
rows=a.execute('select thread_id,automation_id,created_at,updated_at from automation_runs where created_at<? and updated_at>=?',(int(end.timestamp()*1000),int(start.timestamp()*1000))).fetchall();runs=[]
for tid,aid,created,updated in rows:
 if aid not in allowed:continue
 match=b.execute('select rollout_path from threads where id=?',(tid,)).fetchone()
 if not match or not Path(match[0]).is_file():run=dict(missing=True,gaps=['Local usage log unavailable'],models=[])
 else:run=scheduled_usage(match[0],low,high)
 # Skip runs whose initial scheduled turn has no usage in this month; later manual work is irrelevant.
 if not run.get('usage_events') and not run.get('missing') and not run.get('gaps'):
  if int(start.timestamp()*1000)<=created<int(end.timestamp()*1000):run['gaps']=['No recorded token total for registered run']
  else:continue
 run.update(thread_id=tid,automation_id=aid,created_at=datetime.fromtimestamp(created/1000,timezone.utc).isoformat());runs.append(run)
a.close();b.close();summary=cost_summary(runs,args.month)
p=ROOT/'workspace/personal/automation-costs.json';saved=json.loads(p.read_text()) if p.exists() else {'months':{}};saved.setdefault('months',{})[args.month]=summary;p.write_text(json.dumps(saved,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
