#!/usr/bin/env python3
"""Isolated orientation-first checks. Every workspace and native-source record is a test fixture."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('starter_orientation_subject',ROOT/'workbench.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
DEFAULT_SOURCES=['email','slack','crm','calendar','meeting_notes','hex']

class OrientationFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='workbench-orientation-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'independent setup';self.root.mkdir()
        for file in app.bundle_files(ROOT):
            target=self.root/file.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
        self.store=app.Store(self.root,'demo')

    def request(self,**extra):
        return self.store.setup({'action':'orientation_request','sources':DEFAULT_SOURCES,'recurring_requested':True,**extra})

    def test_orientation_starts_without_identity_form_and_is_only_a_read_request(self):
        result=self.request();profile=result['profile']
        self.assertIsNone(profile['identity']['name']);self.assertFalse(profile['identity']['verified'])
        self.assertEqual(profile['onboarding']['stage'],'awaiting_orientation_approval')
        self.assertEqual({k for k,v in profile['read_requests'].items() if v.get('requested')},set(DEFAULT_SOURCES))
        self.assertTrue(all(profile['read_requests'][k]['status']=='awaiting_chat_approval' for k in DEFAULT_SOURCES))
        self.assertEqual(profile['sources'],{})
        self.assertTrue(all(value is False for value in profile['permissions'].values()))
        self.assertEqual(profile['write_authorizations'],[])
        self.assertFalse(profile['schedules']['enabled'])
        self.assertEqual(len(app.Store(self.root,'personal').state()['tasks']),2)
        self.assertIn('09:00',json.dumps(profile['schedules']))
        self.assertIn('12:00',json.dumps(profile['schedules']))
        self.assertIn('15:00',json.dumps(profile['schedules']))
        self.assertIn('17:30',json.dumps(profile['schedules']))

    def test_personal_orientation_cards_are_markable_idempotent_and_never_real_work_or_savings(self):
        personal=app.Store(self.root,'personal');state=personal.state()
        self.assertFalse(personal.profile_path.exists())
        guides=[row for row in state['tasks'] if row.get('orientation_guide')]
        self.assertEqual({row['lane'] for row in guides},{'external','internal'})
        self.assertEqual(len(guides),2)
        for row in guides:
            self.assertFalse(app.orientation.real_task(row))
            personal.progress({'task_id':row['id'],'done':True})
        self.assertFalse(personal.profile_path.exists(), 'Practice completion must not create source or audit receipts')
        before=personal.progress_path.read_bytes()
        personal.import_packet({'tasks':[{'id':'actual-followup','title':'A source-backed follow-up'}]})
        again=app.Store(self.root,'personal');state=again.state()
        self.assertEqual(len([row for row in state['tasks'] if row.get('orientation_guide')]),2)
        self.assertEqual(again.progress_path.read_bytes(),before)
        self.assertTrue(all(state['progress']['tasks'][row['id']]['done'] for row in guides))
        for period in ['week','month','all_time']:
            self.assertEqual(state['time_savings'][period]['estimated_tasks'],0)
            self.assertEqual(state['time_savings'][period]['unestimated_tasks'],0)
        again.progress({'task_id':guides[0]['id'],'done':False})
        self.assertFalse(again.state()['progress']['tasks'][guides[0]['id']]['done'])

    def test_narrow_source_choice_does_not_authorize_unselected_sources(self):
        profile=self.request(sources=['calendar'],recurring_requested=False)['profile']
        self.assertTrue(profile['read_requests']['calendar']['requested'])
        self.assertTrue(all(not value.get('requested') for key,value in profile['read_requests'].items() if key!='calendar'))
        self.assertEqual(profile['sources'],{})
        self.assertFalse(profile['schedules']['enabled'])
        self.assertTrue(all(value is False for value in profile['permissions'].values()))

    def test_web_orientation_rejects_access_or_completion_flags_atomically(self):
        for extra in [{'sources':{'crm':True}},{'sources':['unlisted_source']},{'approved':True},{'permissions':{'send_messages':True}},{'identity':{'verified':True}},{'receipt':{'status':'complete'}},{'recurring_requested':'yes'},{'light_enabled':True}]:
            with self.subTest(extra=extra):
                with self.assertRaises(ValueError):self.request(**extra)
                self.assertFalse(self.store.profile_path.exists())

    def test_cadence_edits_remain_proposed_without_creating_native_jobs(self):
        self.request()
        body={'action':'cadence_preferences','light_times':['10:00','13:00','16:00'],'daily_time':'18:15','weekdays_only':True,'timezone':'Europe/Paris','recurring_requested':True}
        profile=self.store.setup(body)['profile'];saved=json.dumps(profile['schedules'])
        for value in ['10:00','13:00','16:00','18:15']:self.assertIn(value,saved)
        self.assertFalse(profile['schedules']['enabled'])
        self.assertNotIn('"status": "ACTIVE"',saved)
        self.assertTrue(all(value is False for value in profile['permissions'].values()))
        self.assertEqual(profile['sources'],{})

    def test_invalid_cadence_and_browser_native_status_cannot_overwrite_saved_preferences(self):
        self.request();before=self.store.profile_path.read_bytes()
        base={'action':'cadence_preferences','light_times':['09:00','12:00','15:00'],'daily_time':'17:30','weekdays_only':True}
        for change in [{'light_times':['25:00']},{'daily_time':'17:99'},{'timezone':'Not/A_Zone'},{'enabled':True},{'verified':True},{'jobs':[{'status':'ACTIVE'}]},{'weekdays_only':'true'},{'light_enabled':'yes'}]:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.store.setup({**base,**change})
                self.assertEqual(self.store.profile_path.read_bytes(),before)

    def test_existing_personal_identity_work_and_permissions_are_not_replaced(self):
        profile=app.read_json(self.root/'profile.example.json');profile['mode']='personal'
        profile['identity'].update(name='Avery',email='avery@example.invalid',verified=True)
        profile['organization']['manager']['name']='Robin'
        profile['preferences']['goals']=['Retain my existing goal']
        profile['hubspot']['portal_id']='test-portal'
        app.atomic_json(self.store.profile_path,profile)
        personal=app.Store(self.root,'personal')
        packet=app.read_json(self.root/'examples/import-packet.json');personal.import_packet(packet)
        personal.progress({'task_id':packet['tasks'][0]['id'],'done':True})
        before_state=personal.state_path.read_bytes();before_progress=personal.progress_path.read_bytes()
        after=self.request()['profile']
        self.assertEqual(after['identity'],profile['identity'])
        self.assertEqual(after['hubspot'],profile['hubspot'])
        self.assertEqual(after['preferences']['goals'],profile['preferences']['goals'])
        self.assertEqual(after['permissions'],profile['permissions'])
        self.assertEqual(personal.state_path.read_bytes(),before_state)
        self.assertEqual(personal.progress_path.read_bytes(),before_progress)

    def test_http_cannot_record_receipts_or_accept_cross_origin_setup(self):
        server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);server.store=self.store
        worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True);worker.start()
        base='http://127.0.0.1:'+str(server.server_address[1])
        try:
            for payload in [{'action':'record_orientation','receipt':{'status':'complete'}},{'action':'record_schedule','receipt':{'status':'verified'}}]:
                with self.assertRaises(HTTPError) as error:urlopen(Request(base+'/api/onboarding',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':base}))
                self.assertIn(error.exception.code,[400,404,405]);error.exception.close()
            with self.assertRaises(HTTPError) as error:urlopen(Request(base+'/api/onboarding',data=json.dumps({'action':'orientation_request','sources':DEFAULT_SOURCES,'recurring_requested':True}).encode(),headers={'Content-Type':'application/json','Origin':'https://example.invalid'}))
            self.assertEqual(error.exception.code,403);error.exception.close()
            self.assertFalse(self.store.profile_path.exists())
        finally:server.shutdown();server.server_close();worker.join()

    @staticmethod
    def stamped(minutes=0,days=0):
        return (datetime.now(timezone.utc)+timedelta(minutes=minutes,days=days)).isoformat()

    def personal_with_task(self):
        self.request()
        personal=app.Store(self.root,'personal')
        task={'id':'routing-followup','task_id':'routing-followup','title':'Review the inbound routing request','label':'Review the inbound routing request','owner':'Avery','status':'open','source_url':'https://work.slack.com/archives/C_ROUTING/p1000000000000001','source_quote':'Please confirm the inbound routing owner before our technical review.','source_author':'Alex','source_at':self.stamped(days=-1)}
        packet={'tasks':[task],'morning_plan':{'internal':[deepcopy(task)]}}
        fingerprint=personal.import_packet(packet)['fingerprint']
        return personal,task,fingerprint

    def orientation_receipt(self,fingerprint,task=None):
        urls={'email':'https://mail.google.com/mail/u/0/#inbox/audit-request','slack':'https://work.slack.com/archives/C_ROUTING/p1000000000000001','crm':'https://app.hubspot.com/contacts/900001/record/0-3/900002','calendar':'https://calendar.google.com/calendar/u/0/r/eventedit/audit-meeting','meeting_notes':'https://app.gong.io/call?id=audit-call','hex':'https://app.hex.tech/workspace/app/scorecard'}
        checks=[] if task is None else [{k:task[k] for k in ['source_url','source_quote','source_author','source_at']}|{'task_id':task['id'],'verified_at':self.stamped(minutes=-1)}]
        return {'schema_version':1,'authorization_reference':'Current chat: bounded read-only orientation approval','started_at':self.stamped(minutes=-5),'completed_at':self.stamped(),'coverage':[{'source':source,'status':'complete','source_urls':[urls[source]],'observed_at':self.stamped(minutes=-2),'details':'Reviewed the approved source scope and recorded remaining limits.'} for source in DEFAULT_SOURCES],'import_fingerprints':[fingerprint],'verified_tasks':checks,'quiet_reason':'The checked source scope contained no new assigned actions.' if task is None else ''}

    @staticmethod
    def profile_result(value):
        return value.get('profile',value)

    def schedule_receipt(self,readbacks=True,light=False):
        tz='Europe/Paris'
        jobs=[{'kind':'light','native_id':'native-light-job','provider':'codex','rrule':'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,12,15;BYMINUTE=0'}, {'kind':'daily','native_id':'native-daily-job','provider':'codex','rrule':'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=17;BYMINUTE=30'}]
        if not light:jobs=[job for job in jobs if job['kind']=='daily']
        if readbacks:
            for job in jobs:job['readback']={'native_id':job['native_id'],'rrule':job['rrule'],'timezone':tz,'status':'ACTIVE','checked_at':self.stamped(minutes=-1),'reference':'Native scheduler lookup for '+job['native_id']}
        return {'schema_version':1,'authorization_reference':'Current chat: explicit approval for the selected native cadence','authorized_at':self.stamped(minutes=-10),'timezone':tz,'timezone_evidence':{'source_url':'https://calendar.google.com/calendar/u/0/r/settings','quote':'Primary work time zone: Europe/Paris','observed_at':self.stamped(minutes=-9)},'jobs':jobs}

    def test_first_audit_requires_imported_source_evidence_and_preserves_write_permissions(self):
        personal,task,fingerprint=self.personal_with_task();before=app.read_json(personal.profile_path)['permissions']
        profile=self.profile_result(personal.record_orientation(self.orientation_receipt(fingerprint,task)))
        first=profile['onboarding']['first_run']
        self.assertEqual(first['state'],'ready');self.assertTrue(first['completed'])
        self.assertEqual(first['real_task_count'],1);self.assertEqual(first['verified_task_ids'],[task['id']])
        self.assertEqual(profile['permissions'],before);self.assertEqual(profile['sources'],{})
        self.assertFalse(profile['schedules']['enabled'])
        self.assertIn(task['id'],[row['id'] for row in personal.state()['tasks'] if app.orientation.real_task(row)])

    def test_complete_quiet_audit_needs_no_task_quota_or_fabricated_card(self):
        self.request();personal=app.Store(self.root,'personal')
        fingerprint=personal.import_packet({'source_limits':['Approved read-only sources reviewed; no new assigned work was found.']})['fingerprint']
        profile=self.profile_result(personal.record_orientation(self.orientation_receipt(fingerprint)))
        first=profile['onboarding']['first_run'];self.assertEqual(first['state'],'quiet');self.assertTrue(first['completed']);self.assertEqual(first['real_task_count'],0)
        self.assertEqual([row for row in personal.state()['tasks'] if app.orientation.real_task(row)],[])

    def test_incomplete_or_unavailable_sources_cannot_be_first_audit_success(self):
        personal,task,fingerprint=self.personal_with_task();receipt=self.orientation_receipt(fingerprint)
        receipt['coverage']=receipt['coverage'][:1]
        profile=self.profile_result(personal.record_orientation(receipt));first=profile['onboarding']['first_run']
        self.assertEqual(first['state'],'partial');self.assertFalse(first['completed']);self.assertEqual(len(first['missing_sources']),5)
        receipt=self.orientation_receipt(fingerprint)
        for row in receipt['coverage']:row.update(status='unavailable',source_urls=[],details='Native source access was unavailable in this pass.')
        profile=self.profile_result(personal.record_orientation(receipt));self.assertEqual(profile['onboarding']['first_run']['state'],'blocked');self.assertFalse(profile['onboarding']['first_run']['completed'])

    def test_unrelated_import_or_forged_task_source_cannot_verify_a_first_audit(self):
        personal,task,fingerprint=self.personal_with_task();receipt=self.orientation_receipt(fingerprint,task)
        unrelated=personal.import_packet({'source_limits':['An unrelated bounded update.']})['fingerprint']
        mutations=[{'import_fingerprints':['0'*64]},{'import_fingerprints':[unrelated]}]
        for key,value in [('source_url','https://example.org/request'),('source_quote','A quote absent from the saved task'),('source_author','Different author'),('source_at',self.stamped(days=-2)),('task_id','missing-task')]:
            checks=deepcopy(receipt['verified_tasks']);checks[0][key]=value;mutations.append({'verified_tasks':checks})
        for change in mutations:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):personal.record_orientation({**receipt,**change})
        self.assertFalse(app.read_json(personal.profile_path)['onboarding'].get('first_run'))

    def test_example_imports_do_not_count_as_real_first_audit_tasks(self):
        self.request();personal=app.Store(self.root,'personal');packet=app.read_json(self.root/'examples/import-packet.json');fingerprint=personal.import_packet(packet)['fingerprint']
        check={'task_id':packet['tasks'][0]['id'],'source_url':'https://work.slack.com/archives/C_ROUTING/p1000000000000001','source_quote':'Please confirm routing','source_author':'Alex','source_at':self.stamped(days=-1),'verified_at':self.stamped(minutes=-1)}
        receipt=self.orientation_receipt(fingerprint);receipt['verified_tasks']=[check]
        with self.assertRaises(ValueError):personal.record_orientation(receipt)
        self.assertFalse(app.read_json(personal.profile_path)['onboarding'].get('first_run'))

    def test_future_audit_and_source_verification_dates_are_rejected(self):
        personal,task,fingerprint=self.personal_with_task();receipt=self.orientation_receipt(fingerprint,task)
        cases=[{'completed_at':'2099-01-01T00:00:00Z'},{'started_at':'2099-01-01T00:00:00Z'}]
        checks=deepcopy(receipt['verified_tasks']);checks[0]['verified_at']='2099-01-01T00:00:00Z';cases.append({'verified_tasks':checks})
        rows=deepcopy(receipt['coverage']);rows[0]['observed_at']='2099-01-01T00:00:00Z';cases.append({'coverage':rows})
        for change in cases:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):personal.record_orientation({**receipt,**change})

    def test_native_ids_are_configured_but_only_matching_readbacks_are_verified(self):
        self.request();self.store=app.Store(self.root,'personal');self.store.setup({'action':'cadence_preferences','timezone':'Europe/Paris'})
        pending=self.profile_result(self.store.record_schedule(self.schedule_receipt(False)))
        self.assertEqual(pending['schedules']['state'],'configured');self.assertFalse(pending['schedules']['enabled'])
        verified=self.profile_result(self.store.record_schedule(self.schedule_receipt(True)))
        self.assertEqual(verified['schedules']['state'],'verified');self.assertTrue(verified['schedules']['enabled']);self.assertTrue(verified['schedules']['timezone_verified'])
        self.assertEqual(verified['sources'],{});self.assertTrue(all(v is False for v in verified['permissions'].values()))
        self.assertFalse(verified['onboarding'].get('first_run'))

    def test_mismatched_jobs_or_future_readbacks_cannot_enable_native_schedules(self):
        self.request();self.store=app.Store(self.root,'personal');self.store.setup({'action':'cadence_preferences','timezone':'Europe/Paris'});receipt=self.schedule_receipt(True)
        cases=[]
        for key,value in [('native_id','different-job'),('timezone','America/New_York'),('status','PAUSED'),('checked_at','2099-01-01T00:00:00Z')]:
            bad=deepcopy(receipt);bad['jobs'][0]['readback'][key]=value;cases.append(bad)
        bad=deepcopy(receipt);bad['jobs']=[];cases.append(bad)
        bad=deepcopy(receipt);bad['jobs'][0]['rrule']='FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8,12,15;BYMINUTE=0';bad['jobs'][0]['readback']['rrule']=bad['jobs'][0]['rrule'];cases.append(bad)
        bad=deepcopy(receipt);bad['authorized_at']='2099-01-01T00:00:00Z';cases.append(bad)
        for body in cases:
            with self.subTest(receipt=body):
                with self.assertRaises(ValueError):self.store.record_schedule(body)
        self.assertFalse(app.read_json(self.store.profile_path)['schedules']['enabled'])

    def test_new_user_daytime_checks_are_off_and_daily_only_receipt_is_complete(self):
        profile=self.request()['profile']
        self.assertFalse(profile['schedules']['light']['enabled'])
        self.assertEqual(profile['schedules']['light']['local_times'],['09:00','12:00','15:00'])
        self.assertEqual(profile['schedules']['daily']['local_time'],'17:30')
        self.assertIn('OFF for new users',app.onboarding.handoff(profile))
        self.store=app.Store(self.root,'personal')
        self.store.setup({'action':'cadence_preferences','timezone':'Europe/Paris'})
        result=self.profile_result(self.store.record_schedule(self.schedule_receipt()))
        self.assertEqual([job['kind'] for job in result['schedules']['jobs']],['daily'])
        self.assertTrue(result['schedules']['enabled'])
        self.assertFalse(result['schedules']['light']['enabled'])

    def test_saved_daytime_times_and_upkeep_consent_do_not_opt_in(self):
        self.request();self.store=app.Store(self.root,'personal')
        profile=self.store.setup({'action':'cadence_preferences','light_times':['10:00','14:00'],'recurring_requested':True})['profile']
        self.assertFalse(profile['schedules']['light']['enabled'])
        self.assertEqual(profile['schedules']['light']['local_times'],['10:00','14:00'])
        before=self.store.profile_path.read_bytes()
        with self.assertRaisesRegex(ValueError,'daytime checks are off'):self.store.record_schedule(self.schedule_receipt(light=True))
        self.assertEqual(self.store.profile_path.read_bytes(),before)

    def test_explicit_daytime_opt_in_is_required_and_verifies_both_enabled_kinds(self):
        self.request();self.store=app.Store(self.root,'personal')
        profile=self.store.setup({'action':'cadence_preferences','light_enabled':True,'timezone':'Europe/Paris'})['profile']
        self.assertTrue(profile['schedules']['light']['enabled'])
        self.assertFalse(profile['schedules']['enabled'])
        self.assertEqual(profile['schedules']['jobs'],[])
        self.assertTrue(all(v is False for v in profile['permissions'].values()))
        with self.assertRaises(ValueError):self.store.record_schedule(self.schedule_receipt())
        result=self.profile_result(self.store.record_schedule(self.schedule_receipt(light=True)))
        self.assertEqual({job['kind'] for job in result['schedules']['jobs']},{'light','daily'})
        self.assertTrue(result['schedules']['enabled'])

    def test_legacy_verified_light_job_and_explicit_choices_survive_defaults(self):
        profile=self.request()['profile'];profile['schedules']['light'].pop('enabled')
        receipt=self.schedule_receipt(light=True)
        profile['schedules'].update(jobs=receipt['jobs'],state='verified',enabled=True,timezone='Europe/Paris',timezone_verified=True)
        before=deepcopy(profile)
        normalized=app.orientation.schedule_defaults(profile)
        self.assertTrue(normalized['light']['enabled'])
        self.assertEqual(normalized['jobs'],before['schedules']['jobs'])
        self.assertEqual(profile,before)
        unverified=deepcopy(profile)
        for job in unverified['schedules']['jobs']:job['readback']=None
        self.assertFalse(app.orientation.schedule_defaults(unverified)['light']['enabled'])
        same=app.onboarding.update(profile,{'action':'orientation_request','sources':DEFAULT_SOURCES,'recurring_requested':True})
        self.assertTrue(same['schedules']['light']['enabled'])
        self.assertEqual(same['schedules']['jobs'],receipt['jobs'])
        self.assertEqual(same['schedules']['state'],'verified')
        off=app.onboarding.update(same,{'action':'cadence_preferences','light_enabled':False})
        self.assertFalse(off['schedules']['light']['enabled'])
        self.assertEqual(off['schedules']['jobs'],receipt['jobs'])
        self.assertEqual(off['schedules']['state'],'changes_pending')
        self.assertFalse(off['schedules']['enabled'])

    def test_editing_verified_cadence_reports_changes_pending_until_native_update(self):
        self.request();self.store=app.Store(self.root,'personal');self.store.setup({'action':'cadence_preferences','timezone':'Europe/Paris'})
        verified=self.profile_result(self.store.record_schedule(self.schedule_receipt(True)))
        before_jobs=deepcopy(verified['schedules']['jobs'])
        changed=self.store.setup({'action':'cadence_preferences','daily_time':'18:00'})['profile']
        self.assertEqual(changed['schedules']['state'],'changes_pending');self.assertFalse(changed['schedules']['enabled'])
        self.assertEqual(changed['schedules']['jobs'],before_jobs)
        self.assertEqual(changed['schedules']['daily']['local_time'],'18:00')
        with self.assertRaises(ValueError):self.store.record_schedule(self.schedule_receipt(True))

    def assert_not_ready_receipt(self,personal,receipt):
        try:
            result=self.profile_result(personal.record_orientation(receipt))
        except ValueError:
            result=app.read_json(personal.profile_path)
        first=result.get('onboarding',{}).get('first_run') or {}
        self.assertFalse(first.get('completed',False))
        self.assertNotIn(first.get('state'),['ready','quiet'])

    def test_quiet_receipt_cannot_hide_real_imported_actions(self):
        personal,task,fingerprint=self.personal_with_task()
        self.assert_not_ready_receipt(personal,self.orientation_receipt(fingerprint))

    def test_verified_subset_cannot_hide_another_new_real_action(self):
        personal,task,_=self.personal_with_task()
        other={**deepcopy(task),'id':'reporting-followup','task_id':'reporting-followup','title':'Review the reporting request','source_url':'https://work.slack.com/archives/C_REPORTING/p1000000000000002','source_quote':'Please confirm the reporting owner before the operations review.'}
        fingerprint=personal.import_packet({'tasks':[task,other],'morning_plan':{'internal':[task,other]}})['fingerprint']
        self.assert_not_ready_receipt(personal,self.orientation_receipt(fingerprint,task))

    def test_note_id_cannot_impersonate_a_task_in_the_cited_import(self):
        personal,task,_=self.personal_with_task()
        notes_fingerprint=personal.import_packet({'notes':[{'id':task['id'],'title':'Unrelated review note','body':'A saved note is not a task import.'}]})['fingerprint']
        with self.assertRaises(ValueError):personal.record_orientation(self.orientation_receipt(notes_fingerprint,task))

    def test_cited_import_must_contain_the_verified_current_task_evidence(self):
        personal,task,old_fingerprint=self.personal_with_task()
        changed={**deepcopy(task),'source_url':'https://work.slack.com/archives/C_ROUTING/p1000000000000003','source_quote':'Please confirm the revised routing rules after the change review.'}
        personal.import_packet({'tasks':[changed],'morning_plan':{'internal':[changed]}})
        with self.assertRaises(ValueError):personal.record_orientation(self.orientation_receipt(old_fingerprint,changed))

    def test_record_receipt_cli_works_in_its_own_folder_and_exports_no_private_receipts(self):
        import secrets, subprocess, sys, zipfile
        personal,task,fingerprint=self.personal_with_task();receipt=self.orientation_receipt(fingerprint,task)
        private_marker='LOCAL_APPROVAL_'+secrets.token_hex(12);receipt['authorization_reference']=private_marker
        input_path=self.root/'workspace/personal/orientation-input.json';app.atomic_json(input_path,receipt)
        result=subprocess.run([sys.executable,str(self.root/'workbench.py'),'record-orientation',str(input_path)],cwd=self.root,capture_output=True,text=True,check=True)
        payload=json.loads(result.stdout);self.assertTrue(payload['orientation_status']['completed']);self.assertEqual(payload['orientation_status']['real_task_count'],1)
        personal.setup({'action':'cadence_preferences','timezone':'Europe/Paris'})
        scheduled=self.schedule_receipt(True);scheduled['authorization_reference']=private_marker
        schedule_path=self.root/'workspace/personal/schedule-input.json';app.atomic_json(schedule_path,scheduled)
        result=subprocess.run([sys.executable,str(self.root/'workbench.py'),'record-schedule',str(schedule_path)],cwd=self.root,capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['schedule_status']['state'],'verified')
        target=Path(self.temp.name)/'reusable-starter.zip';app.export_bundle(self.root,target)
        with zipfile.ZipFile(target) as archive:
            self.assertFalse(any('/workspace/' in name for name in archive.namelist()))
            self.assertFalse(any(private_marker.encode() in archive.read(name) for name in archive.namelist()))

    def test_readonly_setup_api_exposes_receipt_status_without_confusing_it_with_source_auth(self):
        personal,task,fingerprint=self.personal_with_task();server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);server.store=personal
        worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True);worker.start();base='http://127.0.0.1:'+str(server.server_address[1])
        try:
            pending=json.load(urlopen(base+'/api/onboarding'));self.assertFalse(pending['orientation_status']['completed']);self.assertFalse(pending['schedule_status']['enabled'])
            personal.record_orientation(self.orientation_receipt(fingerprint,task))
            completed=json.load(urlopen(base+'/api/onboarding'));self.assertTrue(completed['orientation_status']['completed']);self.assertEqual(completed['profile']['sources'],{});self.assertFalse(completed['schedule_status']['enabled'])
            self.assertTrue(all(value is False for value in completed['profile']['permissions'].values()))
        finally:server.shutdown();server.server_close();worker.join()

if __name__=='__main__':unittest.main(verbosity=2)
