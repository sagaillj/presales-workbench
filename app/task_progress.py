"""Validate a whole local completion before updating any original task."""
from copy import deepcopy
def apply_task_progress(progress, body, allowed, now, task_catalog=None):
    ids = body.get('task_ids') if 'task_ids' in body else [body.get('task_id')]
    if (not isinstance(ids, list) or not 0 < len(ids) <= 50 or
        any(not isinstance(key, str) or key not in allowed for key in ids) or
        len(set(ids)) != len(ids) or type(body.get('done')) is not bool):
        raise ValueError('Invalid task update')
    for key in ids:
        if body['done'] and progress['tasks'].get(key, {}).get('done'):
            continue
        progress['tasks'][key] = {'done': body['done'], 'updated_at': now,
                                  'provenance': 'user_reported_local_checkbox'}
        if body['done'] and task_catalog and key in task_catalog:
            task = task_catalog[key]
            progress['tasks'][key]['task_snapshot'] = deepcopy({
                field: task[field] for field in ['title', 'label', 'lane', 'deal_key',
                    'link', 'deal_url', 'deal_id', 'deal_name', 'deal_links', 'recommendation', 'done_when', 'completion_kind', 'review_phase']
                if field in task})
            if task.get('completion_kind') == 'accept_recommendation':
                progress['tasks'][key].update(
                    completion_kind='accept_recommendation',
                    provenance='user_accepted_local_recommendation')
