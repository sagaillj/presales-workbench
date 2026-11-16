"""Saved ordering must survive imports/restarts without changing task progress."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ordering_app',ROOT/'workbench.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class OrderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'app';self.root.mkdir()
        for p in app.bundle_files(ROOT):
            dest=self.root/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        demo=app.Store(self.root,'demo').state()
        self.store=app.Store(self.root,'personal');self.store.import_packet({'tasks':demo['tasks'],'morning_plan':demo['morning_plan']})
        self.ids=[i['task_id'] for i in self.store.state()['morning_plan']['priorities'] if not i.get('waiting')]
    def tearDown(self):self.temp.cleanup()
    def test_order_survives_restart_import_and_completion(self):
        before=self.store.state()['progress'];ids=list(reversed(self.ids))
        self.store.order({'lane':'external','ids':ids,'revision':0})
        self.store.import_packet({'updated_at':'2026-11-09T19:00:00Z'})
        state=app.Store(self.root,'personal').state()
        self.assertEqual(state['card_order']['lanes']['external']['ids'],ids)
        self.assertEqual(state['progress'],before)
        self.store.progress({'task_id':ids[0],'done':True})
        self.assertEqual(self.store.state()['card_order']['lanes']['external']['ids'],ids)
        self.assertEqual(app.Store(self.root,'demo').state()['card_order']['revision'],0)
    def test_conflict_invalid_ids_and_reset_do_not_modify_progress(self):
        self.store.order({'lane':'external','ids':self.ids,'revision':0})
        for body in [{'lane':'external','ids':self.ids,'revision':0},{'lane':'external','ids':['unknown'],'revision':1},{'lane':'external','ids':[self.ids[0]]*2,'revision':1},{'lane':'coaching','ids':[],'revision':1}]:
            with self.assertRaises(ValueError):self.store.order(body)
        self.assertEqual(self.store.state()['card_order']['revision'],1)
        self.store.order({'lane':'external','ids':[],'revision':1})
        self.assertEqual(self.store.state()['card_order']['lanes']['external']['ids'],[])
        self.assertEqual(self.store.state()['progress']['tasks'],{})
        with self.assertRaises(ValueError):self.store.import_packet({'card_order':{}})

if __name__=='__main__':unittest.main()
