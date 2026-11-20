"""User-owned display order, independent of task completion and source imports."""
from copy import deepcopy


def update_order(current, body, plan, progress, now):
    lane = body.get('lane')
    ids = body.get('ids')
    if lane not in ('external', 'internal'):
        raise ValueError('Invalid work list')
    if not isinstance(ids, list) or len(ids) > 1000 or any(not isinstance(x, str) or not x or len(x) > 250 for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('Invalid card order')
    revision = current.get('revision', 0)
    if type(body.get('revision')) is not int or body['revision'] != revision:
        raise ValueError('Order changed in another window. Refresh and try again.')
    rows = plan.get('priorities' if lane == 'external' else 'internal', [])
    allowed = {i.get('task_id') or i.get('id') for i in rows if not i.get('waiting') and not progress.get('tasks', {}).get(i.get('task_id') or i.get('id'), {}).get('done')}
    if any(x not in allowed for x in ids):
        raise ValueError('The work list changed. Refresh and try again.')
    result = deepcopy(current)
    previous = result.get('lanes', {}).get(lane, {}).get('ids', [])
    # Retain hidden/completed IDs for future reopening; they never create cards.
    saved = ids + [x for x in previous if x not in ids] if ids else []
    result.setdefault('lanes', {})[lane] = {'ids': saved, 'updated_at': now, 'basis': 'user_display_order', 'cross_group_order': bool(saved) and (body.get('intent') == 'skip' or current.get('lanes', {}).get(lane, {}).get('cross_group_order', False))}
    result['revision'] = revision + 1
    return result
