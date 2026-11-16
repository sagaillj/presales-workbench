/* Journal the Undo window so reloads cannot discard a completion. */
(function (root) {
  function taskListCounts(plan = {}, progress = {}, pending = []) {
    const open = item => !item.waiting && !completionHidden(item.task_ids || [item.task_id || item.id], pending, progress);
    return {
      firstTouchpoints: (plan.priorities || []).filter(i => (i.external_view || 'deal-work') === 'first-touchpoints' && open(i)).length,
      dealWork: (plan.priorities || []).filter(i => (i.external_view || 'deal-work') === 'deal-work' && open(i)).length,
      internal: (plan.internal || []).filter(open).length
    };
  }
  function completionMilestones(before, after) {
    if (!before || !after) return {cleared: [], allClear: false};
    const keys = ['firstTouchpoints', 'dealWork', 'internal'];
    const cleared = keys.filter(key => before[key] > 0 && after[key] === 0);
    return {cleared, allClear: cleared.length > 0 && keys.every(key => after[key] === 0)};
  }
  function externalWorkGroups(items = [], progress = {}, pending = []) {
    const open = items.filter(item => !item.waiting && !completionHidden(
      item.task_ids || [item.task_id || item.id], pending, progress));
    return [
      {key: 'dealWork', title: 'Deal work', items: open.filter(i => (i.external_view || 'deal-work') === 'deal-work')},
      {key: 'firstTouchpoints', title: 'First touchpoints', items: open.filter(i => i.external_view === 'first-touchpoints')}
    ].filter(group => group.items.length);
  }
  function completionHidden(taskIds, pending, progress = {}) {
    return taskIds.length > 0 && taskIds.every(id => progress[id]?.done ||
      pending.some(item => item.taskIds.includes(id)));
  }
  function createCompletionQueue({persist, onChange = () => {}, onCommit = () => {}, onError = () => {}, delay = 5000, schedule = setTimeout, cancel = clearTimeout, journal = null, now = Date.now}) {
    const pending = new Map();
    function items() { return [...pending.values()].map(({timer, ...item}) => item); }
    function notify() { onChange(items()); }
    return {
      items,
      restore(progress = {}) {
        for (const item of journal?.read() || []) {
          if (!item || typeof item.id !== 'string' || typeof item.label !== 'string' ||
              !Array.isArray(item.taskIds) || !item.taskIds.length ||
              item.taskIds.some(id => typeof id !== 'string') || !Number.isFinite(item.dueAt)) continue;
          if (item.taskIds.every(id => progress[id]?.done)) { journal.remove(item.id); continue; }
          this.add(item.id, item.label, item.taskIds, item.dueAt);
        }
      },
      add(id, label, taskIds = [id], dueAt = now() + delay) {
        if (pending.has(id) || [...pending.values()].some(item => item.taskIds.some(key => taskIds.includes(key)))) return false;
        const item = {id, label, taskIds: [...taskIds], phase: 'pending', dueAt};
        try { journal?.put(item); }
        catch (error) { onError(error, item); return false; }
        pending.set(id, item);
        item.timer = schedule(async () => {
          // Another tab may have undone this same journaled completion.
          if (journal && !journal.read().some(saved => saved.id === id && saved.dueAt === dueAt)) {
            pending.delete(id); notify(); return;
          }
          item.phase = 'saving';
          notify();
          try { await persist(id, item.taskIds); }
          catch (error) { journal?.remove(id); pending.delete(id); notify(); onError(error, item); return; }
          journal?.remove(id);
          pending.delete(id);
          notify();
          onCommit(item);
        }, Math.max(0, dueAt - now()));
        notify();
        return true;
      },
      undo(id) {
        const item = pending.get(id);
        if (!item || item.phase !== 'pending') return false;
        journal?.remove(id);
        cancel(item.timer);
        pending.delete(id);
        notify();
        return true;
      }
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createCompletionQueue, completionHidden, taskListCounts, completionMilestones, externalWorkGroups};
  else { root.createCompletionQueue = createCompletionQueue; root.completionHidden = completionHidden; root.taskListCounts = taskListCounts; root.completionMilestones = completionMilestones; root.externalWorkGroups = externalWorkGroups; }
})(typeof window !== 'undefined' ? window : globalThis);
