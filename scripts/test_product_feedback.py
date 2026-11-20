from datetime import datetime,timezone,timedelta
from pathlib import Path
import json,sys,tempfile,unittest
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import product_feedback as f
class FeedbackTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name);self.now=datetime(2026,11,20,18,tzinfo=timezone.utc);self.posts=[];f.write(self.folder/'product-feedback.json',{'active_dates':['2026-10-'+str(n).zfill(2) for n in range(1,11)]})
  self.contact={'feedback_form':{'url':'https://docs.google.com/forms/d/e/TEST_FORM/viewform','endpoint':'https://script.google.com/macros/s/TEST_SERVICE/exec','entries':dict(zip(['rating','hours','comments','usage','email'],['entry.'+str(i) for i in range(1,6)]))}}
  self.progress={'tasks':{'a':{'done':True,'updated_at':'2026-11-18T14:00:00Z','task_snapshot':{'title':'PRIVATE DEAL SECRET'}},'b':{'done':False,'updated_at':'2026-11-18T14:00:00Z'},'c':{'done':True,'updated_at':'2026-11-10T14:00:00Z'},'d':{'done':True,'updated_at':123}}}
 def tearDown(self):self.temp.cleanup()
 def receipt(self,url,p):
  self.posts.append((url,p));return {'ok':True,'submission_id':p['submission_id'],'response_id':'saved-response-id','submitted_at':'2026-11-20T18:00:00Z'}
 def action(self,action,**kw):return f.update(self.folder,{'action':action,**kw},self.progress,self.contact,'operator@example.com',self.now,'America/New_York',self.receipt)
 def submit(self,**kw):return self.action('submit',week='2026-11-16',rating=0,**kw)
 def state(self,now=None):return f.summary(self.folder,self.progress,now or self.now,'America/New_York',self.contact,'operator@example.com')
 def test_weekly_due_and_tuesday_quiet(self):
  self.assertTrue(self.state()['due']);self.assertTrue(self.state(datetime(2026,11,17,tzinfo=timezone.utc))['due']);self.assertEqual(self.posts,[])
 def test_new_user_and_forced_hash_do_not_prompt_before_ten_use_days(self):
  f.write(self.folder/'product-feedback.json',{'active_dates':['2026-11-20']*20+['2099-01-01','invalid']})
  self.assertFalse(self.state()['due']);self.assertEqual(self.state()['usage_days'],1)
  self.assertFalse(f.summary(self.folder,self.progress,self.now,'America/New_York',self.contact,force=True)['due'])
  f.write(self.folder/'product-feedback.json',{'active_dates':['2026-10-'+str(n).zfill(2) for n in range(1,10)]})
  self.assertFalse(self.state()['due']);self.action('visit');self.assertTrue(self.state()['due'])
 def test_first_prompt_is_available_on_tenth_use_day_even_before_friday(self):
  self.assertTrue(self.state(datetime(2026,11,18,18,tzinfo=timezone.utc))['due'])
 def test_visit_deduplicates_locally_and_never_submits(self):
  self.action('visit');self.action('visit');self.assertEqual(self.state()['counts'],{'active_days':1,'tasks_marked_done':1});self.assertEqual(self.posts,[])
 def test_one_submit_has_exact_allowed_data_and_verified_receipt(self):
  self.action('visit');state=self.submit();self.assertEqual(state['record']['status'],'submitted_verified');self.assertFalse(state['due']);self.assertEqual(len(self.posts),1)
  sent=self.posts[0][1];self.assertEqual(sent['rating'],0);self.assertEqual(sent['email'],'operator@example.com');self.assertEqual(set(sent),{'schema','submission_id','week','rating','hours','comments','email','counts','version'});self.assertNotIn('PRIVATE',json.dumps(sent))
 def test_count_opt_out_and_optional_email(self):
  self.submit(include_counts=False,email='',hours=2.5);p=self.posts[0][1];self.assertIsNone(p['counts']);self.assertEqual(p['email'],'');self.assertEqual(p['hours'],2.5)
 def test_bad_inputs_never_submit(self):
  for rating in [-1,11,True,'5',None]:
   with self.assertRaises(ValueError):self.action('submit',week='2026-11-16',rating=rating)
  for h in [-1,169,float('nan'),float('inf'),True,10**400]:
   with self.assertRaises(ValueError):self.submit(hours=h)
  with self.assertRaises(ValueError):self.submit(email='x@example.com\nBcc:a@example.com')
  with self.assertRaises(ValueError):self.submit(comments='x'*2001)
  self.assertEqual(self.posts,[])
 def test_stale_week_has_no_writes(self):
  with self.assertRaises(ValueError):self.action('submit',week='2026-11-09',rating=5)
  self.assertEqual(f.read(self.folder/'product-feedback.json',{})['active_dates'],['2026-10-'+str(n).zfill(2) for n in range(1,11)])
 def test_form_fallback_prefills_every_field_without_submission(self):
  out=self.action('form',week='2026-11-16',rating=7,hours=3,comments='Clearer cards',email='me@example.com',include_counts=False);q=parse_qs(urlsplit(out['url']).query)
  self.assertEqual(q['entry.1'],['7']);self.assertEqual(q['entry.2'],['3']);self.assertEqual(q['entry.3'],['Clearer cards']);self.assertEqual(q['entry.5'],['me@example.com']);self.assertIn('Usage counts not included.',q['entry.4'][0]);self.assertEqual(self.posts,[]);self.assertTrue(out['state']['due'])
 def test_no_endpoint_uses_working_form_instead(self):
  self.contact['feedback_form']['endpoint']=None;out=self.submit();self.assertIn('url',out);self.assertFalse(out['submitted']);self.assertEqual(self.posts,[])
 def test_form_confirmation_is_user_reported(self):
  with self.assertRaises(ValueError):self.action('submitted',week='2026-11-16')
  self.action('form',week='2026-11-16',rating=4);self.assertEqual(self.state()['record']['status'],'form_opened');result=self.action('submitted',week='2026-11-16');self.assertEqual(result['record']['status'],'submitted_user_reported');self.assertFalse(result['due'])
 def test_refresh_restores_form_link_and_answers(self):
  out=self.action('form',week='2026-11-16',rating=5,comments='Saved note');self.assertEqual(self.state()['record']['form_url'],out['url']);self.assertEqual(self.state()['record']['comments'],'Saved note')
 def test_success_cannot_be_erased_by_skip_or_duplicate(self):
  self.submit()
  with self.assertRaises(ValueError):self.action('skip',week='2026-11-16')
  with self.assertRaises(ValueError):self.submit()
  self.assertEqual(len(self.posts),1)
 def test_uncertain_write_retries_identical_payload_and_stable_id(self):
  seen=[]
  def fail(url,p):seen.append(p);raise OSError('timeout')
  result=f.update(self.folder,{'action':'submit','week':'2026-11-16','rating':5},self.progress,self.contact,'operator@example.com',self.now,'America/New_York',fail);self.assertTrue(result['pending']);self.assertTrue(self.state()['due'])
  self.action('submit',week='2026-11-16',rating=5);self.assertEqual(seen[0],self.posts[0][1]);self.assertEqual(self.state()['record']['status'],'submitted_verified')
 def test_uncertain_submission_blocks_changed_data_and_skip(self):
  def fail(*_):raise OSError('offline')
  f.update(self.folder,{'action':'submit','week':'2026-11-16','rating':5},self.progress,self.contact,'operator@example.com',self.now,'America/New_York',fail)
  with self.assertRaises(ValueError):self.action('submit',week='2026-11-16',rating=6)
  with self.assertRaises(ValueError):self.action('skip',week='2026-11-16')
 def test_uncertain_submission_cannot_switch_to_form_or_become_known_failed(self):
  def fail(*_):raise OSError('timeout after possible acceptance')
  body={'action':'submit','week':'2026-11-16','rating':5}
  f.update(self.folder,body,self.progress,self.contact,None,self.now,post=fail)
  with self.assertRaises(ValueError):self.action('form',week='2026-11-16',rating=5)
  result=f.update(self.folder,body,self.progress,self.contact,None,self.now,post=lambda *_:{'ok':False,'accepted':False})
  self.assertTrue(result['pending']);self.assertEqual(self.state()['record']['status'],'submission_pending')
 def test_wrong_receipt_does_not_claim_success(self):
  r=f.update(self.folder,{'action':'submit','week':'2026-11-16','rating':5},self.progress,self.contact,None,self.now,post=lambda *_:{'ok':True,'submission_id':'wrong','response_id':'x','submitted_at':'2026-11-20T18:00:00Z'});self.assertTrue(r['pending']);self.assertEqual(self.state()['record']['status'],'submission_pending')
 def test_unknown_endpoints_and_missing_configuration_disabled(self):
  self.contact['feedback_form']['endpoint']='https://evil.example/exec';self.contact['feedback_form']['url']='https://evil.example/form'
  self.assertFalse(self.state()['destination']['configured'])
  with self.assertRaises(ValueError):self.submit()
  self.assertEqual(self.posts,[])
 def test_oversized_unicode_form_prefill_asks_to_shorten_without_copying(self):
  with self.assertRaisesRegex(ValueError,'shorten'):self.action('form',week='2026-11-16',rating=5,comments='界'*2000)
 def test_biweekly_cadence_and_disable(self):
  self.action('cadence',weeks=2);self.assertTrue(self.state()['due']);self.assertFalse(self.state(self.now+timedelta(days=7))['due']);self.assertTrue(self.state(self.now+timedelta(days=14))['due']);self.action('enabled',enabled=False);self.assertFalse(self.state()['due']);self.assertEqual(self.posts,[])
 def test_local_timezone_week_boundary(self):
  self.assertEqual(self.state(datetime(2026,11,23,1,tzinfo=timezone.utc))['week'],'2026-11-16')
 def test_progress_is_never_modified(self):
  before=json.dumps(self.progress,sort_keys=True);self.submit();self.assertEqual(before,json.dumps(self.progress,sort_keys=True))
 def test_simple_checkin_uses_known_identity_and_one_computed_estimate(self):
  self.progress['tasks']['a']['time_savings']={'version':1,'category':'prepared_reply','minutes_low':5,'minutes_high':15}
  self.submit(simple_checkin=True,comments='Less friction',email='spoof@example.com',hours=99,include_counts=False,client_runtime={'browser':'Chrome','viewport':'large','url':'PRIVATE'})
  p=self.posts[0][1];self.assertEqual(p['email'],'operator@example.com');self.assertEqual(p['hours'],.17);self.assertIsNotNone(p['counts']);self.assertEqual(p['metadata']['estimated_tasks_week'],1);self.assertFalse(p['metadata']['estimate_is_measured']);self.assertNotIn('PRIVATE',json.dumps(p));self.assertNotIn('spoof',json.dumps(p));self.assertIn('Usage metadata:',f.usage_text(p))
 def test_simple_unknown_estimate_is_null_and_pending_retries_pin_metadata(self):
  self.submit(simple_checkin=True);self.assertIsNone(self.posts[0][1]['hours'])
 def test_simple_pending_retries_use_original_estimate_and_identity(self):
  original=[]
  def fail(url,p):original.append(p);raise OSError('timeout')
  body={'action':'submit','week':'2026-11-16','rating':5,'simple_checkin':True,'comments':'Keep it'}
  f.update(self.folder,body,self.progress,self.contact,'operator@example.com',self.now,post=fail)
  self.progress['tasks']['a']['time_savings']={'version':1,'minutes_low':5,'minutes_high':15}
  f.update(self.folder,body,self.progress,self.contact,'changed@example.com',self.now,post=self.receipt)
  self.assertEqual(self.posts[0][1],original[0])
 def release(self,tag='v0.6.0'):
  base='https://github.com/'+f.REPOSITORY;return {'tag_name':tag,'html_url':base+'/releases/tag/'+tag,'assets':[{'name':n,'browser_download_url':base+'/releases/download/'+tag+'/'+n} for n in ['presales-workbench-starter-latest.zip','presales-workbench-starter-latest.sha256']]}
 def test_update_check_pins_checked_release_and_sends_no_private_data(self):
  urls=[]
  def fetch(req):urls.append(req.full_url);return self.release()
  r=f.release_status(installed='0.5.1',fetch=fetch);self.assertTrue(r['available']);self.assertIn('/releases/tag/v0.6.0',r['upgrade_prompt']);self.assertEqual(urls,['https://api.github.com/repos/sagaillj/presales-workbench/releases/latest'])
 def test_bad_release_offline_and_old_versions_are_safe(self):
  for change in [{'prerelease':True},{'html_url':'https://evil.example/'},{'assets':[]}]:self.assertEqual(f.release_status(fetch=lambda _:{**self.release(),**change})['status'],'unavailable')
  self.assertFalse(f.release_status(fetch=lambda _:self.release('v0.4.0'))['available'])
  def fail(_):raise OSError('offline')
  self.assertEqual(f.release_status(fetch=fail)['status'],'unavailable')
if __name__=='__main__':unittest.main(verbosity=2)
