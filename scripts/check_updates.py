#!/usr/bin/env python3
"""Daily release maintenance. No new job, account access or external action grants."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import product_feedback,workbench_updates,automatic_updates

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--data-dir',type=Path,default=ROOT/'workspace/personal')
 p.add_argument('--force',action='store_true')
 p.add_argument('--check-only',action='store_true',help='Metadata only; never download or install')
 p.add_argument('--install-staged',action='store_true',help='Run after stopping only this Workbench; preserve workspace and local edits')
 p.add_argument('--outcome',choices=['installed','blocked','running']);p.add_argument('--version');p.add_argument('--detail',default='');args=p.parse_args()
 if args.outcome:
  if not args.version:p.error('--version required for an outcome')
  if args.outcome=='installed' and (ROOT/'VERSION').read_text().strip()!=args.version:p.error('Installed VERSION does not match the queued release')
  result=workbench_updates.finish(args.data_dir,args.version,args.outcome,args.detail)
 elif args.check_only:result=workbench_updates.state(args.data_dir,force=args.force)
 else:result=automatic_updates.daily(ROOT,args.data_dir,force=args.force,install_now=args.install_staged)
 print(json.dumps(result))
if __name__=='__main__':main()
