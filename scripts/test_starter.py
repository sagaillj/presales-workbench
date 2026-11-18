#!/usr/bin/env python3
"""Offline checks for a clean install, preserved decisions and clean re-export."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workbench',ROOT/'workbench.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class StarterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='workbench-clean-install-');self.root=Path(self.temp.name)/'folder with spaces';self.root.mkdir()
        for file in app.bundle_files(ROOT):
            target=self.root/file.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
    def tearDown(self):self.temp.cleanup()
    def packet(self):return json.loads((self.root/'examples/import-packet.json').read_text())
    def test_demo_does_not_configure_a_person_or_grant_writes(self):
        s=app.Store(self.root,'demo').state()
        self.assertEqual(s['workspace_mode'],'demo');self.assertFalse(s['profile']['identity']['verified'])
        self.assertIsNone(s['profile']['identity']['name']);self.assertIsNone(s['profile']['organization']['manager']['name'])
        self.assertTrue(all(v is False for v in s['profile']['permissions'].values()))
        self.assertEqual(len(s['product_roadblocks']['roadblocks']),7)
    def test_personal_workspace_starts_empty_and_uses_its_own_profile(self):
        profile=json.loads((self.root/'profile.example.json').read_text());profile['mode']='personal';profile['identity'].update(name='Casey Example',email='casey@example.invalid',verified=True);profile['organization']['manager']['name']='Robin Example'
        app.atomic_json(self.root/'workspace/profile.json',profile)
        s=app.Store(self.root).state();self.assertEqual(s['tasks'],[]);self.assertEqual(s['profile']['identity']['name'],'Casey Example');self.assertEqual(s['profile']['organization']['manager']['name'],'Robin Example')
    def test_refresh_and_retirement_preserve_completed_decisions(self):
        store=app.Store(self.root,'personal');packet=self.packet();store.import_packet(packet);id=packet['tasks'][0]['id']
        store.progress({'task_id':id,'done':True});saved=store.state()['progress']['tasks'][id]
        packet['tasks'][0]['title']='Refined title';store.import_packet(packet)
        self.assertEqual(store.state()['progress']['tasks'][id],saved)
        store.import_packet({'remove_task_ids':[id]});state=store.state()
        self.assertEqual(state['tasks'],[]);self.assertEqual(state['progress']['tasks'][id],saved);self.assertIn('task_snapshot',saved)
    def test_progress_and_identity_cannot_be_overwritten_by_an_import(self):
        store=app.Store(self.root,'personal')
        for key in ['progress','profile','permissions']:
            with self.assertRaises(ValueError):store.import_packet({key:{}})
    def test_invalid_grouped_completion_cannot_partially_complete(self):
        store=app.Store(self.root,'personal');store.import_packet(self.packet())
        with self.assertRaises(ValueError):store.progress({'task_ids':['sample-follow-up','unknown'],'done':True})
        self.assertEqual(store.state()['progress']['tasks'],{})
    def test_http_ui_and_cross_origin_write_boundary(self):
        server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);server.store=app.Store(self.root,'demo');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_address[1])
        try:
            self.assertIn(b'Presales Workbench',urllib.request.urlopen(url).read())
            state=json.loads(urllib.request.urlopen(url+'/api/state').read());self.assertEqual(state['workspace_mode'],'demo')
            req=urllib.request.Request(url+'/api/progress',data=b'{"task_id":"demo-flow","done":true}',headers={'Origin':'https://example.invalid','Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code,403);ctx.exception.close();self.assertEqual(server.store.state()['progress']['revision'],0)
            with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(url+'/workspace/profile.json')
            self.assertEqual(ctx.exception.code,404);ctx.exception.close()
        finally:server.shutdown();server.server_close();thread.join()
    def test_concurrent_local_completions_survive(self):
        store=app.Store(self.root,'demo')
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda id:store.progress({'task_id':id,'done':True}),['demo-flow','demo-resources']))
        progress=store.state()['progress'];self.assertEqual(progress['revision'],2);self.assertTrue(progress['tasks']['demo-flow']['done']);self.assertTrue(progress['tasks']['demo-resources']['done'])
    def answers(self):
        return {'action':'preferences','name':'Taylor Example','email':'taylor@example.invalid','segment':'Test segment','geography':'Test region','timezone':'Europe/Paris','manager_name':'Robin Example','goals':'Priority A','qci_goals':'Improve discovery','demo_flow':'Outcome, proof, recap','modules':{k:k!='weekly_qci' for k in app.onboarding.MODULES}}
    def test_onboarding_stores_own_preferences_without_write_grants(self):
        store=app.Store(self.root,'demo');result=store.setup(self.answers());profile=result['profile']
        self.assertEqual(profile['identity']['name'],'Taylor Example');self.assertFalse(profile['identity']['verified']);self.assertEqual(profile['organization']['manager']['name'],'Robin Example')
        self.assertEqual(profile['preferences']['demo_flow'],'Outcome, proof, recap');self.assertFalse(profile['preferences']['modules']['weekly_qci']);self.assertFalse(profile['schedules']['enabled']);self.assertTrue(all(v is False for v in profile['permissions'].values()))
        self.assertEqual(app.Store(self.root,'personal').state()['tasks'],[])
    def test_onboarding_requires_preview_and_never_claims_source_access(self):
        store=app.Store(self.root,'demo');store.setup(self.answers())
        with self.assertRaises(ValueError):store.setup({'action':'sources','sources':['email']})
        store.setup({'action':'preview_seen'});p=store.setup({'action':'sources','sources':['email','hex']})['profile']
        self.assertEqual(p['read_requests']['email']['status'],'awaiting_chat_approval');self.assertEqual(p['read_requests']['slack']['status'],'skipped');self.assertEqual(p['sources'],{})
        self.assertIn('ask me to approve',app.onboarding.handoff(p))
    def test_voice_scope_is_optional_private_and_limited_to_selected_months(self):
        store=app.Store(self.root,'demo')
        p=store.setup(dict(self.answers(),writing_style='Short Slack; warm email',voice_lookback_months=6))['profile']
        self.assertEqual(p['preferences']['writing_voice']['state'],'not_sampled')
        self.assertEqual(p['preferences']['writing_voice']['user_notes'],'Short Slack; warm email')
        store.setup({'action':'preview_seen'})
        p=store.setup({'action':'sources','sources':['writing_voice']})['profile']
        self.assertIn('last 6 months',p['read_requests']['writing_voice']['scope'])
        self.assertEqual(p['read_requests']['writing_voice']['status'],'awaiting_chat_approval')
        self.assertEqual(p['sources'],{})
        self.assertIn('workspace/voice-profile.json',app.onboarding.handoff(p))
        self.assertTrue(all(v is False for v in p['permissions'].values()))
        for value in [0,12,'6',True]:
            with self.assertRaises(ValueError):store.setup(dict(self.answers(),voice_lookback_months=value))

    def test_setup_rejects_unsupported_grants_bad_inputs_and_identity_conflicts(self):
        store=app.Store(self.root,'demo')
        for extra in [{'permissions':{'send_messages':True}},{'identity':{'verified':True}},{'sources':{'email':True}},{'timezone':'Invalid/Zone'},{'email':'not-an-email'},{'modules':{'daily_closeout':True}}]:
            with self.assertRaises(ValueError):store.setup(dict(self.answers(),**extra))
        p=store.setup(self.answers())['profile'];p['identity']['verified']=True;app.atomic_json(store.profile_path,p)
        with self.assertRaises(ValueError):store.setup(dict(self.answers(),name='Someone Else'))
        self.assertEqual(app.read_json(store.profile_path)['identity']['name'],'Taylor Example')
    def test_preferences_refresh_preserves_private_mapping_and_progress(self):
        store=app.Store(self.root,'personal');store.import_packet(self.packet());store.progress({'task_id':'sample-follow-up','done':True})
        p=app.read_json(store.profile_path,app.read_json(self.root/'profile.example.json'));p['hubspot']['portal_id']='demo-test-portal';app.atomic_json(store.profile_path,p)
        store.setup(self.answers());store.setup(dict(self.answers(),goals='Priority B'))
        self.assertEqual(store.state()['profile']['hubspot']['portal_id'],'demo-test-portal');self.assertTrue(store.state()['progress']['tasks']['sample-follow-up']['done'])
    def test_server_keeps_demo_personal_reads_and_writes_separate(self):
        server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);server.store=app.Store(self.root,'demo');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_address[1])
        try:
            self.assertIn(b'Set up your SE Workbench',urllib.request.urlopen(url+'/setup').read())
            req=urllib.request.Request(url+'/api/progress?mode=demo',data=b'{"task_id":"demo-flow","done":true}',headers={'Origin':url,'Content-Type':'application/json'})
            urllib.request.urlopen(req).close()
            sample=json.loads(urllib.request.urlopen(url+'/api/state?mode=demo').read());personal=json.loads(urllib.request.urlopen(url+'/api/state?mode=personal').read())
            self.assertTrue(sample['progress']['tasks']['demo-flow']['done']);self.assertEqual(personal['progress']['tasks'],{});self.assertEqual(personal['tasks'],[])
            req=urllib.request.Request(url+'/api/onboarding',data=json.dumps(self.answers()).encode(),headers={'Origin':'https://example.invalid','Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as ctx:urllib.request.urlopen(req)
            self.assertEqual(ctx.exception.code,403);ctx.exception.close();self.assertFalse(server.store.profile_path.exists())
        finally:server.shutdown();server.server_close();thread.join()
    def test_export_excludes_private_workspace_credentials_and_unrecognized_files(self):
        secret='PRIVATE_TEST_'+os.urandom(12).hex();private=self.root/'workspace/personal/private.json';private.parent.mkdir(parents=True);private.write_text(secret)
        (self.root/'.env').write_text(secret);(self.root/'my-notes.txt').write_text(secret)
        dest=Path(self.temp.name)/'team.zip';app.export_bundle(self.root,dest)
        with zipfile.ZipFile(dest) as z:
            names=z.namelist();self.assertTrue(any(x.endswith('/README.md') for x in names));self.assertTrue(any('/.agents/skills/' in x for x in names));self.assertTrue(any('/.claude/skills/' in x for x in names))
            self.assertFalse(any('/workspace/' in x or x.endswith('/.env') or x.endswith('/my-notes.txt') for x in names))
            self.assertFalse(any(secret.encode() in z.read(name) for name in names))

if __name__=='__main__':unittest.main(verbosity=2)
