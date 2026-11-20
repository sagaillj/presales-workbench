#!/usr/bin/env python3
"""Daily metadata check and version-specific handoff for an approved update."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import product_feedback,workbench_updates

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-dir',type=Path,default=ROOT/'workspace/personal');p.add_argument('--force',action='store_true');p.add_argument('--outcome',choices=['installed','blocked','running']);p.add_argument('--version');p.add_argument('--detail',default='');args=p.parse_args()
 if args.outcome:
  if not args.version:p.error('--version required for an outcome')
  if args.outcome=='installed':
   version=(ROOT/'VERSION').read_text().strip()
   if product_feedback.version_tuple(version)!=product_feedback.version_tuple(args.version):p.error('Installed VERSION does not match the approved release')
  result=workbench_updates.finish(args.data_dir,args.version,args.outcome,args.detail)
 else:result=workbench_updates.state(args.data_dir,force=args.force)
 approval=result.get('approval') or {}
 if approval.get('status')=='queued':
  result['workflow_action']='The user approved this specific release in Workbench. Follow approval.prompt during this workflow: recheck the fixed GitHub release/tag and release ID, verify the ZIP checksum and bundle manifest, back up the app, stop only this Workbench, run the included upgrade_existing.py preflight and installer, preserve the entire workspace, restart and run first-test checks. If files have local edits, installation is unmanaged, or access/permissions change, record the exact blocker instead of overwriting. Never replace a private development checkout with the generic starter. Record installed only after exact version and saved progress readback. Do not update to a different version without approval.'
 print(json.dumps(result))
if __name__=='__main__':main()
