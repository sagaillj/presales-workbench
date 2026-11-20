"""Saved-for-later work is separate from completion and earned savings."""
from copy import deepcopy


class ArchiveConflict(ValueError):
    pass


def archive_state(progress):
    items, deleted = [], []
    for task_id, saved in progress.get('tasks', {}).items():
        if saved.get('archived'):
            item = {'id': task_id, 'archived_at': saved.get('archived_at'),
                    'deleted_at': saved.get('archive_deleted_at'),
                    **deepcopy(saved.get('archive_snapshot', {}))}
            (deleted if saved.get('archive_deleted') else items).append(item)
    items.sort(key=lambda item: item.get('archived_at') or '', reverse=True)
    deleted.sort(key=lambda item: item.get('deleted_at') or '', reverse=True)
    return {'revision': progress.get('revision', 0), 'items': items, 'deleted': deleted}


def apply_archive(progress, body, catalog, briefs, now, data=None):
    ids, action = body.get('task_ids'), body.get('action')
    if (action not in ('archive', 'restore', 'delete', 'recover') or not isinstance(ids, list)
            or not 0 < len(ids) <= 50
            or any(not isinstance(key, str) for key in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError('Choose the exact items to archive, restore or delete.')
    if type(body.get('revision')) is not int or body['revision'] != progress.get('revision', 0):
        raise ArchiveConflict('Your work changed. Review the refreshed item and try again.')
    tasks = progress.setdefault('tasks', {})
    for key in ids:
        saved = tasks.get(key, {})
        if action == 'archive':
            if key not in catalog or saved.get('done') or saved.get('archived'):
                raise ArchiveConflict('This item is no longer an active task. Refresh before archiving.')
        elif (not saved.get('archived') or
              bool(saved.get('archive_deleted')) != (action == 'recover')):
            raise ArchiveConflict('This item changed. Refresh before continuing.')
    # Validate the whole selection before changing any original task.
    for key in ids:
        saved = tasks.setdefault(key, {})
        if action == 'archive':
            task = catalog[key]
            queue = next((item for item in (data or {}).get('queue', {}).get('items', [])
                          if item.get('key') == task.get('deal_key')), None)
            saved.update(archived=True, archive_deleted=False, archived_at=now,
                         archive_provenance='user_saved_for_later',
                         archive_snapshot={'task': deepcopy(task),
                                           'brief': deepcopy(briefs.get(key, {})),
                                           'queue_item': deepcopy(queue)})
        elif action == 'restore':
            saved.update(archived=False, restored_at=now)
        elif action == 'delete':
            saved.update(archive_deleted=True, archive_deleted_at=now)
        else:
            saved.update(archive_deleted=False, archive_recovered_at=now)
    return progress


def project_archive(state, progress):
    """Keep private snapshots through source refreshes; archived work never re-enters tasks."""
    result = deepcopy(state)
    task_rows = result.setdefault('tasks', [])
    briefs = result.setdefault('task_briefs', {}).setdefault('items', {})
    plan = result.setdefault('morning_plan', {})
    for ident, saved in progress.get('tasks', {}).items():
        snapshot = saved.get('archive_snapshot', {})
        task = snapshot.get('task')
        if not isinstance(task, dict) or task.get('id') != ident:
            continue
        if not any((row.get('task_id') or row.get('id')) == ident for row in task_rows):
            task_rows.append(deepcopy(task))
        if snapshot.get('brief'):
            briefs.setdefault(ident, deepcopy(snapshot['brief']))
        card, field = snapshot.get('plan_card'), snapshot.get('plan_field')
        if not saved.get('archived') and isinstance(card, dict) and field in {'priorities', 'internal'}:
            rows = plan.setdefault(field, [])
            key = card.get('task_id') or card.get('id')
            if not any((row.get('task_id') or row.get('id')) == key for row in rows):
                rows.append(deepcopy(card))
    for field in ['priorities', 'internal', 'deal_work', 'first_touchpoints']:
        visible = []
        for row in plan.get(field, []):
            ids = row.get('task_ids') or [row.get('task_id') or row.get('id')]
            active = [ident for ident in ids if not progress.get('tasks', {}).get(ident, {}).get('archived')]
            if not active:
                continue
            if active != ids:
                row = deepcopy(row)
                row['task_ids'] = active
                if isinstance(row.get('topics'), list):
                    row['topics'] = [topic for topic in row['topics'] if (topic.get('task_id') or topic.get('id')) in active]
            visible.append(row)
        plan[field] = visible
    result['task_archive'] = archive_state(progress)
    return result
