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
    def test_local_edits_stop_before_any_write(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'new',Path(t)/'existing';make(a,'new');make(b,'old');(b/'workbench.py').write_text('my edit')
            with self.assertRaises(ValueError):m.upgrade(a,b)
            self.assertEqual((b/'workbench.py').read_text(),'my edit');self.assertFalse((b/'workspace').exists())
if __name__=='__main__':unittest.main(verbosity=2)
