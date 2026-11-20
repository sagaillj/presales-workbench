import json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import workbench_updates as updates

class UpdateQueueTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.now=datetime(2026,11,18,20,tzinfo=timezone.utc);self.hits=0
 def fetch(self,req):
  self.hits+=1;self.assertEqual(req.full_url,'https://api.github.com/repos/sagaillj/presales-workbench/releases/latest')
  tag='v9.1.0';return {'id':123,'tag_name':tag,'html_url':'https://github.com/sagaillj/presales-workbench/releases/tag/'+tag,'assets':[{'name':n,'browser_download_url':'https://github.com/sagaillj/presales-workbench/releases/download/'+tag+'/'+n} for n in ['presales-workbench-starter-latest.zip','presales-workbench-starter-latest.sha256']]}
 def check(self,**kw):return updates.state(self.root,now=self.now,fetch=self.fetch,installed='0.5.1',**kw)
 def action(self,**body):return updates.update(self.root,body,now=self.now,fetch=self.fetch,installed='0.5.1')
 def test_daily_cache_and_opt_out(self):
  self.assertTrue(self.check()['available']);self.check();self.assertEqual(self.hits,1)
  self.now+=timedelta(days=1);self.check();self.assertEqual(self.hits,2)
  self.action(action='daily_enabled',enabled=False);self.now+=timedelta(days=1);self.check();self.assertEqual(self.hits,2)
  self.check(force=True);self.assertEqual(self.hits,3)
 def test_only_exact_fresh_available_release_can_be_approved(self):
  with self.assertRaises(ValueError):self.action(action='approve',version='9.1.0')
  self.check()
  with self.assertRaises(ValueError):self.action(action='approve',version='10.0.0')
  self.now+=timedelta(days=1)
  with self.assertRaises(ValueError):self.action(action='approve',version='9.1.0')
 def test_approval_is_idempotent_version_pinned_and_cancellable(self):
  self.check();one=self.action(action='approve',version='9.1.0');two=self.action(action='approve',version='9.1.0');self.assertEqual(one['approval'],two['approval']);self.assertEqual(one['approval']['release_id'],123);self.assertEqual(one['approval']['status'],'queued');self.assertIsNone(self.action(action='cancel')['approval'])
  history=json.loads((self.root/updates.FILE).read_text())['history'];self.assertEqual(len(history),1)
 def test_failure_does_not_authorize_or_erase_existing_approval(self):
  self.check();self.action(action='approve',version='9.1.0')
  result=updates.state(self.root,now=self.now,force=True,installed='0.5.1',fetch=lambda req: (_ for _ in ()).throw(OSError('offline')))
  self.assertEqual(result['status'],'unavailable');self.assertEqual(result['approval']['version'],'9.1.0');self.assertEqual(result['approval']['status'],'queued')
 def test_outcomes_require_the_approved_version_and_keep_personal_files(self):
  progress=self.root/'progress.json';progress.write_text('{"tasks":{"human":{"done":true}}}');before=progress.read_bytes()
  self.check();self.action(action='approve',version='9.1.0')
  with self.assertRaises(ValueError):updates.finish(self.root,'9.2.0','installed','wrong')
  result=updates.finish(self.root,'9.1.0','blocked','Local app edits need review',now=self.now);self.assertEqual(result['approval']['status'],'blocked');self.assertEqual(progress.read_bytes(),before)
  result=updates.finish(self.root,'9.1.0','installed','Version and first-test checks passed',now=self.now);self.assertFalse(result['available']);self.assertEqual(result['installed'],'9.1.0')

if __name__=='__main__':unittest.main()
