import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('upgrade',Path(__file__).with_name('upgrade_existing.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def make(root,text):
    root.mkdir();(root/'workbench.py').write_text(text);(root/'VERSION').write_text('0.0.1')
    (root/'BUNDLE-MANIFEST.json').write_text(json.dumps({'files':{n:{'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in ['workbench.py','VERSION']}}))
class UpgradeTests(unittest.TestCase):
    def test_upgrade_preserves_private_profile_and_progress(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'new');make(b,'old')
            p=b/'workspace/personal/progress.json';p.parent.mkdir(parents=True);p.write_text('{"done":true}')
            m.upgrade(a,b);self.assertEqual((b/'workbench.py').read_text(),'new');self.assertEqual(p.read_text(),'{"done":true}')
    def test_upgrade_preserves_saved_daytime_on_off_and_legacy_native_jobs(self):
        for choice in [True,False,None]:
            with self.subTest(choice=choice),tempfile.TemporaryDirectory() as t:
                a,b=Path(t)/'new',Path(t)/'existing';make(a,'new');make(b,'old')
                profile={'schedules':{'light':{'local_times':['10:00','14:00']},'jobs':[{'kind':'light','native_id':'existing-user-job','provider':'codex','readback':{'status':'ACTIVE'}}]}}
                if choice is not None:profile['schedules']['light']['enabled']=choice
                p=b/'workspace/profile.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(profile));before=p.read_bytes()
                m.upgrade(a,b)
                self.assertEqual(p.read_bytes(),before)

    def test_local_edits_stop_before_any_write(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'new');make(b,'old');(b/'workbench.py').write_text('my edit')
            with self.assertRaises(ValueError):m.upgrade(a,b)
            self.assertEqual((b/'workbench.py').read_text(),'my edit');self.assertTrue((b/'workspace/LOCAL-CHANGES.md').exists())

    def test_disjoint_local_edits_reapply_and_journal_survives_second_update(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'upstream\nkeep\nfooter\n');make(b,'header\nkeep\nfooter\n')
            m.local_changes.capture(b)
            (b/'workbench.py').write_text('header\nkeep\nmy local line\n')
            result=m.upgrade(a,b)
            self.assertEqual((b/'workbench.py').read_text(),'upstream\nkeep\nmy local line\n')
            self.assertIn('workbench.py',result['customizations_reapplied'])
            packet=m.local_changes.load(b);self.assertEqual(packet['files'][0]['path'],'workbench.py')
            self.assertIn('base_base64',packet['files'][0])
            (a/'workbench.py').write_text('upstream\nkeep updated\nfooter\n')
            (a/'BUNDLE-MANIFEST.json').write_text(json.dumps({'files':{n:{'sha256':hashlib.sha256((a/n).read_bytes()).hexdigest()} for n in ['workbench.py','VERSION']}}))
            m.upgrade(a,b)
            self.assertEqual((b/'workbench.py').read_text(),'upstream\nkeep updated\nmy local line\n')

    def test_verified_old_release_can_supply_baseline_for_existing_edits(self):
        with tempfile.TemporaryDirectory() as t:
            a,b,old=Path(t)/'new',Path(t)/'existing',Path(t)/'old-release'
            make(a,'upstream\nkeep\nfooter\n');make(b,'header\nkeep\nfooter\n');make(old,'header\nkeep\nfooter\n')
            (b/'workbench.py').write_text('header\nkeep\nmy local line\n')
            m.upgrade(a,b,baseline_source=old)
            self.assertEqual((b/'workbench.py').read_text(),'upstream\nkeep\nmy local line\n')

    def test_overlapping_changes_stop_without_overwriting_custom_code(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'release line\n');make(b,'original line\n')
            m.local_changes.capture(b);(b/'workbench.py').write_text('my line\n')
            with self.assertRaisesRegex(ValueError,'LOCAL-CHANGES.md'):m.upgrade(a,b)
            self.assertEqual((b/'workbench.py').read_text(),'my line\n')
    def test_case_variants_workspace_and_traversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ['Workspace/profile.json','WORKSPACE/personal/state.json','../escape','/tmp/escape']:
                with self.subTest(name=name),self.assertRaises(ValueError):m.safe(Path(t),name)
    def test_unchanged_release_file_keeps_local_edit(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'original');make(b,'original');(b/'workbench.py').write_text('my edit')
            m.upgrade(a,b);self.assertEqual((b/'workbench.py').read_text(),'my edit')
    def test_missing_manifest_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'no bundle manifest'):m.entries(Path(t))
if __name__=='__main__':unittest.main(verbosity=2)
