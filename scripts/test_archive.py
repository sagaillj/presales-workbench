#!/usr/bin/env python3
"""Local Archive survives source refreshes without completion, data loss or writes."""
from copy import deepcopy
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive_starter',ROOT/'workbench.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='portable-archive-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'private app';self.root.mkdir()
        for source in app.bundle_files(ROOT):
            target=self.root/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        self.store=app.Store(self.root,'personal')
        self.notes={'id':'notes','lane':'internal','title':'Read this later','label':'Full reference notes','time_savings_category':None}
        self.card={**self.notes,'short_action':'Return to this useful reference.'}
        self.brief={'review_notes':{'title':'Saved notes','sections':[{'title':'Useful detail','text':'Keep this exact original text.'}]},'sources':[{'label':'Original','url':'https://example.invalid/reference'}]}
        self.store.import_packet({'tasks':[self.notes],'morning_plan':{'internal':[self.card]},'task_briefs':{'items':{'notes':self.brief}}})

    def operation(self,action,ids=None,revision=None):
        return self.store.archive({'action':action,'task_ids':ids or ['notes'],'revision':self.store.state()['progress']['revision'] if revision is None else revision})

    def test_archive_keeps_snapshot_and_has_no_completion_or_earned_savings(self):
        before=self.store.state();grants=json.dumps(before['profile']['permissions'],sort_keys=True)
        result=self.operation('archive');state=self.store.state();saved=state['progress']['tasks']['notes']
        self.assertEqual(len(result['items']),1);self.assertEqual(result['items'][0]['brief'],self.brief)
        self.assertFalse(saved.get('done'));self.assertNotIn('time_savings',saved)
        self.assertNotIn('notes',[row['id'] for row in state['morning_plan']['internal']])
        self.assertEqual(state['time_savings'],before['time_savings'])
        self.assertEqual(json.dumps(state['profile']['permissions'],sort_keys=True),grants)
        self.assertEqual(state['task_archive']['revision'],state['progress']['revision'])

    def test_archive_survives_restart_import_removal_delete_recover_and_restore(self):
        self.operation('archive');snapshot=deepcopy(self.store.state()['task_archive']['items'][0])
        self.store.import_packet({'remove_task_ids':['notes']})
        self.store=app.Store(self.root,'personal')
        self.assertEqual(self.store.state()['task_archive']['items'][0],snapshot)
        self.assertFalse(any(row['id']=='notes' for row in self.store.state()['morning_plan']['internal']))
        self.operation('delete');self.assertEqual(self.store.state()['task_archive']['items'],[])
        self.assertEqual(len(self.store.state()['task_archive']['deleted']),1)
        with self.assertRaises(app.ArchiveConflict):self.operation('restore')
        self.operation('recover');self.operation('restore')
        state=self.store.state();restored=next(row for row in state['morning_plan']['internal'] if row['id']=='notes')
        self.assertEqual(restored,self.card);self.assertEqual(state['task_briefs']['items']['notes'],self.brief)
        self.assertEqual(state['task_archive']['items'],[]);self.assertFalse(state['progress']['tasks']['notes']['archived'])
        self.store.progress({'task_id':'notes','done':True})
        self.assertTrue(self.store.state()['progress']['tasks']['notes']['done'])

    def test_invalid_or_stale_batch_is_atomic_and_cannot_complete_archived_item(self):
        self.store.progress({'task_id':'orientation-internal-work','done':True})
        before=self.store.progress_path.read_bytes()
        for ids in [['notes','missing'],['notes','orientation-internal-work']]:
            with self.assertRaises(app.ArchiveConflict):self.operation('archive',ids)
            self.assertEqual(self.store.progress_path.read_bytes(),before)
        with self.assertRaises(app.ArchiveConflict):self.operation('archive',revision=0)
        self.operation('archive');before=self.store.progress_path.read_bytes()
        with self.assertRaises(ValueError):self.store.progress({'task_id':'notes','done':True})
        self.assertEqual(self.store.progress_path.read_bytes(),before)
        with self.assertRaises(ValueError):self.operation('purge')
        self.assertEqual(self.store.progress_path.read_bytes(),before)

    def test_grouped_archive_keeps_original_ids_and_one_restore_returns_only_that_member(self):
        tasks=[{'id':key,'lane':'external','title':key,'label':key} for key in ['first','second']]
        card={'task_id':'group','task_ids':['first','second'],'title':'Two related asks','action':'Complete either actual ask.','topics':[{'task_id':'first','title':'First'},{'task_id':'second','title':'Second'}]}
        self.store.import_packet({'tasks':tasks,'morning_plan':{'priorities':[card]}})
        self.operation('archive',['first','second'])
        self.assertFalse(any(row['task_id']=='group' for row in self.store.state()['morning_plan']['priorities']))
        self.operation('restore',['first'])
        restored=next(row for row in self.store.state()['morning_plan']['priorities'] if row['task_id']=='group')
        self.assertEqual(restored['task_ids'],['first']);self.assertEqual(restored['topics'],[card['topics'][0]])
        self.assertFalse(self.store.state()['progress']['tasks']['first']['archived'])
        self.assertTrue(self.store.state()['progress']['tasks']['second']['archived'])

    def test_source_refresh_keeps_current_edits_and_archived_snapshot_distinct(self):
        self.operation('archive')
        edited={**self.card,'short_action':'New user wording'}
        self.store.import_packet({'tasks':[{**self.notes,'title':'Edited current title'}],'morning_plan':{'internal':[edited]}})
        self.assertEqual(self.store.state()['task_archive']['items'][0]['task']['title'],'Read this later')
        self.operation('restore')
        self.assertEqual(next(row for row in self.store.state()['morning_plan']['internal'] if row['id']=='notes')['short_action'],'New user wording')

    def test_release_upgrade_preserves_archived_notes_and_progress_bytes(self):
        self.operation('archive')
        saved=self.store.progress_path.read_bytes()
        spec=importlib.util.spec_from_file_location('archive_upgrade',ROOT/'scripts/upgrade_existing.py')
        upgrade=importlib.util.module_from_spec(spec);spec.loader.exec_module(upgrade)
        incoming=self.root.parent/'incoming';existing=self.root.parent/'existing'
        for folder,text in [(incoming,'new'),(existing,'old')]:
            folder.mkdir();(folder/'workbench.py').write_text(text);(folder/'VERSION').write_text('0.0.1')
            (folder/'BUNDLE-MANIFEST.json').write_text(json.dumps({'files':{name:{'sha256':hashlib.sha256((folder/name).read_bytes()).hexdigest()} for name in ['workbench.py','VERSION']}}))
        progress=existing/'workspace/personal/progress.json';progress.parent.mkdir(parents=True);progress.write_bytes(saved)
        upgrade.upgrade(incoming,existing)
        self.assertEqual(progress.read_bytes(),saved)
        self.assertEqual((existing/'workbench.py').read_text(),'new')
        snapshot=json.loads(progress.read_text())['tasks']['notes']['archive_snapshot']
        self.assertEqual(snapshot['brief'],self.brief)

    def test_http_archive_conflicts_origin_assets_and_modes(self):
        http=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);http.store=self.store
        thread=threading.Thread(target=http.serve_forever,kwargs={'poll_interval':.01},daemon=True);thread.start()
        base='http://127.0.0.1:'+str(http.server_address[1])
        def post(action,revision,origin=None):
            headers={'Content-Type':'application/json'}
            if origin:headers['Origin']=origin
            return urlopen(Request(base+'/api/archive?mode=personal',data=json.dumps({'action':action,'task_ids':['notes'],'revision':revision}).encode(),headers=headers))
        try:
            with self.assertRaises(HTTPError) as error:post('archive',0,'https://example.invalid')
            self.assertEqual(error.exception.code,403);error.exception.close()
            with post('archive',0,base) as response:self.assertEqual(json.load(response)['revision'],1)
            with self.assertRaises(HTTPError) as error:post('restore',0,base)
            self.assertEqual(error.exception.code,409);error.exception.close()
            with urlopen(base+'/api/archive?mode=personal') as response:self.assertEqual(len(json.load(response)['items']),1)
            with urlopen(base+'/api/archive?mode=demo') as response:self.assertEqual(json.load(response)['items'],[])
            for name in ['task-archive.js','task-archive.css']:
                with urlopen(base+'/'+name) as response:self.assertEqual(response.status,200)
            with post('delete',1,base) as response:self.assertEqual(len(json.load(response)['deleted']),1)
        finally:http.shutdown();http.server_close();thread.join()


if __name__=='__main__':unittest.main(verbosity=2)
