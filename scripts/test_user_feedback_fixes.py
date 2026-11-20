import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
import automation_preferences as features
import call_capture
import local_changes
import onboarding


class UserFeedbackTests(unittest.TestCase):
    def test_all_outside_world_features_default_off_and_stale_saves_fail(self):
        initial = features.state({})
        self.assertGreater(len(initial['catalog']), 20)
        for row in initial['catalog']:
            if row['kind'] == 'write':
                self.assertFalse(row['enabled'], row['id'])
        saved = features.update({}, {'action': 'set', 'revision': 0, 'changes': {'call_logging': True}})
        self.assertTrue(features.state(saved)['features']['call_logging'])
        self.assertNotIn('authorization', json.dumps(saved))
        with self.assertRaises(ValueError):
            features.update(saved, {'action': 'set', 'revision': 0, 'changes': {'call_logging': False}})

    def test_fellow_and_other_recorders_use_app_names_without_content_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'Fellow.app').mkdir()
            (root / 'Wispr Flow.app').mkdir()
            (root / 'recording.m4a').write_bytes(b'private recording')
            with patch.object(Path, 'read_bytes', side_effect=AssertionError('No contents')):
                result = call_capture.discover([root])
            self.assertEqual({row['provider'] for row in result['candidates']}, {'Fellow', 'Wispr Flow'})
            self.assertFalse(result['content_read'])
            self.assertTrue(all(not row['transcript_access_verified'] for row in result['candidates']))
            self.assertIn('Ask how', call_capture.discover([])['next_step'])

    def test_extra_sources_and_fellow_are_saved_without_granting_access(self):
        profile=json.loads((ROOT/'profile.example.json').read_text())
        result = onboarding.update(profile, {'action': 'preferences', 'additional_sources': ['Asana', 'Fellow'],
                                        'transcription_source': 'Fellow', 'transcription_method': 'Existing team transcript'})
        self.assertEqual(result['preferences']['additional_sources'], ['Asana', 'Fellow'])
        self.assertEqual(result['preferences']['call_capture']['provider'], 'Fellow')
        self.assertEqual(result.get('sources', {}), profile.get('sources', {}))
        self.assertNotIn('authorized', result['preferences']['call_capture'])

    def test_journal_keeps_restorable_edits_and_preferences_private(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'app').mkdir()
            path = root / 'app/theme.css'
            path.write_text('old\n')
            (root / 'VERSION').write_text('1.0.0')
            (root / 'BUNDLE-MANIFEST.json').write_text(json.dumps({'files': {
                'app/theme.css': {'sha256': local_changes.digest(path.read_bytes())}}}))
            local_changes.capture(root)
            path.write_text('my colors\n')
            (root / 'workspace/profile.json').write_text(json.dumps({'preferences': {
                'writing_voice': {'user_notes': 'Short replies'}, 'api_token': 'DO NOT JOURNAL'}}))
            local_changes.capture(root)
            journal = root / 'workspace/LOCAL-CHANGES.md'
            self.assertNotIn('DO NOT JOURNAL', journal.read_text())
            packet = local_changes.load(root)
            self.assertEqual(packet['preferences']['writing_voice']['user_notes'], 'Short replies')
            self.assertEqual(local_changes.rebase(packet['files'][0], b'old\n'), b'my colors\n')
            journal.write_text('user accidentally removed machine packet')
            self.assertEqual(local_changes.capture_status(root, True)['status'], 'needs_review')
            self.assertEqual(journal.read_text(), 'user accidentally removed machine packet')


if __name__ == '__main__':
    unittest.main(verbosity=2)
