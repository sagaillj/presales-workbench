import hashlib,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import automatic_updates as auto
import product_feedback as feedback
import workbench_updates as updates
import local_changes
from runtime_lock import exclusive
SOURCE=Path(__file__).resolve().parents[1]

def manifest(root,version):
 files={str(p.relative_to(root)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in root.rglob('*') if p.is_file() and p.name!='BUNDLE-MANIFEST.json' and 'workspace' not in p.relative_to(root).parts}
 (root/'BUNDLE-MANIFEST.json').write_text(json.dumps({'release':version,'files':files}))

class AutomaticUpdateTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'existing';self.root.mkdir();self.folder=self.root/'workspace/personal';self.folder.mkdir(parents=True)
  (self.root/'VERSION').write_text('1.0.0');(self.root/'workbench.py').write_text('old header\nkeep\nfooter\n');manifest(self.root,'1.0.0')
  self.progress=self.folder/'progress.json';self.progress.write_text('{"tasks":{"mine":{"done":true}}}')
  self.calls=[];self.hits=0;self.latest='1.1.0'
  new=Path(self.tmp.name)/'new';(new/'scripts').mkdir(parents=True);(new/'app').mkdir()
  for name in ['scripts/upgrade_existing.py','app/local_changes.py']:(new/name).write_bytes((SOURCE/name).read_bytes())
  (new/'VERSION').write_text(self.latest);(new/'workbench.py').write_text('new header\nkeep\nfooter\n');manifest(new,self.latest)
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:
   for p in new.rglob('*'):
    if p.is_file():z.write(p,'presales-workbench-starter/'+str(p.relative_to(new)))
  self.archive=data.getvalue();self.sha=hashlib.sha256(self.archive).hexdigest()
 def metadata(self,req):
  self.hits+=1;tag='v'+self.latest
  return {'id':123,'tag_name':tag,'html_url':'https://github.com/'+feedback.REPOSITORY+'/releases/tag/'+tag,'assets':[{'name':name,'browser_download_url':'https://github.com/'+feedback.REPOSITORY+'/releases/download/'+tag+'/'+name} for name in [auto.ARCHIVE,auto.CHECKSUM]]}
 def download(self,url,limit):
  self.calls.append(url)
  return (self.sha+'  '+auto.ARCHIVE+'\n').encode() if url.endswith('.sha256') else self.archive
 def run_daily(self,**kwargs):return auto.daily(self.root,self.folder,fetch=self.metadata,fetch_bytes=self.download,**kwargs)
 def test_default_downloads_once_and_queues_exact_version(self):
  result=self.run_daily();self.assertTrue(result['auto_install_enabled']);self.assertTrue(result['approval']['download_verified']);self.assertTrue(result['approval']['automatic']);self.assertIn('--install-staged',result['workflow_action'])
  self.run_daily();self.assertEqual(len(self.calls),2);self.assertEqual(self.hits,1);self.assertEqual((self.root/'VERSION').read_text(),'1.0.0')
 def test_opt_out_keeps_available_card_without_downloading(self):
  updates.update(self.folder,{'action':'auto_install_enabled','enabled':False});result=self.run_daily();self.assertTrue(result['available']);self.assertIsNone(result['approval']);self.assertFalse(self.calls)
  updates.update(self.folder,{'action':'approve','version':self.latest});self.assertTrue(self.run_daily()['approval']['download_verified'])
 def test_existing_disabled_checks_and_generic_opt_out_are_honored(self):
  updates.update(self.folder,{'action':'daily_enabled','enabled':False});self.run_daily();self.assertEqual(self.hits,0)
  updates.update(self.folder,{'action':'daily_enabled','enabled':True});(self.root/'workspace/profile.json').write_text(json.dumps({'preferences':{'automatic_features':{'features':{'workbench_update_checks':False}}}}));self.run_daily();self.assertEqual(self.hits,0)
 def test_current_version_does_nothing(self):
  self.latest='1.0.0';result=self.run_daily();self.assertFalse(result['available']);self.assertFalse(self.calls);self.assertIsNone(result['approval'])
 def test_checksum_failure_blocks_without_changing_app(self):
  self.sha='0'*64;result=self.run_daily(install_now=True);self.assertEqual(result['approval']['status'],'blocked');self.assertIn('checksum',result['approval']['detail']);self.assertEqual((self.root/'VERSION').read_text(),'1.0.0')
 def test_running_app_stops_installation(self):
  with exclusive(self.root/'workspace/.app-runtime.lock'):result=self.run_daily(install_now=True)
  self.assertEqual(result['approval']['status'],'blocked');self.assertIn('still running',result['approval']['detail']);self.assertEqual((self.root/'VERSION').read_text(),'1.0.0')
 def test_real_install_preserves_progress_and_reapplies_local_edit(self):
  before=self.progress.read_bytes();local_changes.capture(self.root);(self.root/'workbench.py').write_text('old header\nkeep\nmy local footer\n')
  result=self.run_daily(install_now=True);self.assertEqual(result['approval']['status'],'installed',result);self.assertEqual((self.root/'VERSION').read_text(),self.latest);self.assertEqual(self.progress.read_bytes(),before);self.assertEqual((self.root/'workbench.py').read_text(),'new header\nkeep\nmy local footer\n');self.assertTrue(result['installation']['restart_required']);self.assertFalse(result['available'])
 def test_overlapping_edits_stop_and_unmanaged_install_is_never_replaced(self):
  local_changes.capture(self.root);(self.root/'workbench.py').write_text('my own header\nkeep\nfooter\n');result=self.run_daily(install_now=True);self.assertEqual(result['approval']['status'],'blocked');self.assertIn('LOCAL-CHANGES.md',result['approval']['detail']);self.assertEqual((self.root/'VERSION').read_text(),'1.0.0')
  (self.root/'BUNDLE-MANIFEST.json').unlink();result=self.run_daily(install_now=True);self.assertIn('managed standalone',result['approval']['detail'])
 def test_opt_out_cancels_pending_automatic_update(self):
  self.run_daily();updates.update(self.folder,{'action':'auto_install_enabled','enabled':False});self.assertIsNone(self.run_daily()['approval']);self.assertEqual((self.root/'VERSION').read_text(),'1.0.0')
 def test_unsafe_zip_is_rejected_even_with_matching_checksum(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:z.writestr('presales-workbench-starter/../../escape','unsafe')
  with self.assertRaisesRegex(ValueError,'Unsafe'):auto.verify(data.getvalue(),self.latest,hashlib.sha256(data.getvalue()).hexdigest())

if __name__=='__main__':unittest.main()
