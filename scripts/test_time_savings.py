import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from datetime import datetime, timezone
from copy import deepcopy
from task_progress import apply_task_progress
from time_savings import completion_estimate, savings_summary


class SavingsTests(unittest.TestCase):
    def test_completion_retry_undo_and_recompletion_count_once(self):
        p = {'tasks': {}}; catalog = {'a': {'time_savings_category': 'demo_prep'}}
        update = lambda done: apply_task_progress(p, {'task_id': 'a', 'done': done}, {'a'}, '2026-11-18T18:00:00Z', catalog)
        now = datetime(2026, 11, 18, 20, tzinfo=timezone.utc)
        update(True); original = deepcopy(p); update(True)
        self.assertEqual(p, original)
        self.assertEqual(savings_summary(p, now)['week']['minutes_low'], 45)
        update(False)
        self.assertEqual(savings_summary(p, now)['week']['estimated_tasks'], 0)
        update(True)
        self.assertEqual(savings_summary(p, now)['week']['estimated_tasks'], 1)

    def test_unknown_history_acceptance_and_title_cannot_inflate_estimate(self):
        self.assertIsNone(completion_estimate({'completion_kind': 'accept_recommendation'}))
        self.assertEqual(completion_estimate({'title': 'Build a huge demo'})['minutes_low'], 5)
        p = {'tasks': {'old': {'done': True, 'updated_at': '2026-11-18T18:00:00Z'}}}
        s = savings_summary(p, datetime(2026, 11, 18, 20, tzinfo=timezone.utc))
        self.assertEqual(s['month']['unestimated_tasks'], 1)
        self.assertEqual(s['month']['hours_low'], 0)

    def test_feedback_suggests_same_week_without_mutating_progress(self):
        from product_feedback import summary
        import tempfile
        p = {'tasks': {'a': {'done': True, 'updated_at': '2026-11-18T18:00:00Z',
                            'time_savings': completion_estimate({'time_savings_category': 'demo_prep'})}}}
        original = deepcopy(p)
        with tempfile.TemporaryDirectory() as folder:
            result = summary(folder, p, datetime(2026, 11, 18, 20, tzinfo=timezone.utc))
        self.assertEqual(result['time_savings']['week']['hours_low'], .75)
        self.assertEqual(result['counts']['tasks_marked_done'], 1)
        self.assertEqual(p, original)

    def test_timezone_future_and_invalid_ranges(self):
        def row(at, **extra):
            return {'done': True, 'updated_at': at, 'time_savings': {**completion_estimate({'time_savings_category': 'meeting_prep'}), **extra}}
        p = {'tasks': {'sunday': row('2026-11-16T02:00:00Z'), 'monday': row('2026-11-16T06:00:00Z'),
                       'future': row('2026-11-22T06:00:00Z'), 'bad': row('2026-11-16T06:00:00Z', minutes_low=float('nan'))}}
        s = savings_summary(p, datetime(2026, 11, 18, 20, tzinfo=timezone.utc))
        self.assertEqual(s['week']['estimated_tasks'], 1)
        self.assertEqual(s['week']['unestimated_tasks'], 1)
        self.assertEqual(s['month']['estimated_tasks'], 2)


if __name__ == '__main__': unittest.main()
