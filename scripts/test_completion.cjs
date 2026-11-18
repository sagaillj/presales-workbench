const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const context={module:{exports:{}},setTimeout,clearTimeout};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/completion.js'),'utf8'),context);
const {createCompletionQueue,completionHidden}=context.module.exports;
function fixture(fail=false){
  const timers=new Map(),writes=[],commits=[],errors=[];let next=0;
  const queue=createCompletionQueue({now:()=>0,persist:async id=>{writes.push(id);if(fail)throw Error('offline')},onCommit:item=>commits.push(item.id),onError:(_,item)=>errors.push(item.id),schedule:(fn,ms)=>{assert.equal(ms,5000);timers.set(++next,fn);return next},cancel:id=>timers.delete(id)});
  return {queue,writes,commits,errors,timers,expire:async()=>{const [id,fn]=timers.entries().next().value;timers.delete(id);await fn()}};
}
test('completion waits five seconds and ignores duplicate clicks',async()=>{const f=fixture();assert.equal(f.queue.add('one','One'),true);assert.equal(f.queue.add('one','One'),false);assert.deepEqual(f.writes,[]);await f.expire();assert.deepEqual(f.writes,['one']);assert.deepEqual(f.commits,['one']);assert.equal(f.queue.items().length,0)});
test('Undo during the grace period prevents any completion write',()=>{const f=fixture();f.queue.add('one','One');assert.equal(f.queue.undo('one'),true);assert.equal(f.timers.size,0);assert.deepEqual(f.writes,[]);assert.equal(f.queue.items().length,0)});
test('multiple task completions have independent Undo windows',async()=>{const f=fixture();f.queue.add('one','One');f.queue.add('two','Two');f.queue.undo('one');await f.expire();assert.deepEqual(f.writes,['two'])});
test('failed saves leave no pending or archived completion',async()=>{const f=fixture(true);f.queue.add('one','One');await f.expire();assert.deepEqual(f.commits,[]);assert.deepEqual(f.errors,['one']);assert.equal(f.queue.items().length,0)});
test('Undo cannot race an in-flight save',async()=>{let release;const queue=createCompletionQueue({persist:()=>new Promise(r=>release=r),schedule:fn=>{queue.expire=fn;return 1}});queue.add('one','One');const saving=queue.expire();assert.equal(queue.items()[0].phase,'saving');assert.equal(queue.undo('one'),false);release();await saving;assert.equal(queue.items().length,0)});
test('one shared Undo cancels all topics without a progress write',()=>{const f=fixture();f.queue.add('manager','Manager',['a','b']);assert.equal(f.queue.add('a','Anderson'),false);assert.equal(f.queue.undo('manager'),true);assert.equal(f.timers.size,0);assert.deepEqual(f.writes,[])});
test('the bundle commits its exact original task ids together',async()=>{let commit;const ids=['a','b'];const queue=createCompletionQueue({persist:async(id,topics)=>{assert.equal(id,'manager');assert.deepEqual(Array.from(topics),['a','b'])},schedule:fn=>{commit=fn;return 1}});queue.add('manager','Manager',ids);ids.push('unrelated');await commit();assert.equal(queue.items().length,0)});
test('a pending completion hides immediately and Undo restores it before any write',()=>{const f=fixture();f.queue.add('one','One');assert.equal(completionHidden(['one'],f.queue.items()),true);assert.deepEqual(f.writes,[]);f.queue.undo('one');assert.equal(completionHidden(['one'],f.queue.items()),false)});
test('one pending topic leaves its other grouped topic visible',()=>{const f=fixture();f.queue.add('a','A');assert.equal(completionHidden(['a'],f.queue.items()),true);assert.equal(completionHidden(['a','b'],f.queue.items()),false);assert.equal(completionHidden(['a','b'],f.queue.items(),{b:{done:true}}),true)});
test('a failed save makes the task visible again',async()=>{const f=fixture(true);f.queue.add('one','One');assert.equal(completionHidden(['one'],f.queue.items()),true);await f.expire();assert.equal(completionHidden(['one'],f.queue.items()),false)});
test('a saved task stays hidden after leaving the Undo queue even if reloading fails',()=>{assert.equal(completionHidden(['one'],[],{one:{done:true}}),true)});

function durableFixture(){
 const saved=new Map();let clock=0;const journal={read:()=>[...saved.values()],put:item=>saved.set(item.id,JSON.parse(JSON.stringify(item))),remove:id=>saved.delete(id)};
 function page(){const timers=new Map(),writes=[];let index=0;const queue=createCompletionQueue({journal,now:()=>clock,persist:async(id,ids)=>writes.push([id,Array.from(ids)]),schedule:(fn,ms)=>{timers.set(++index,{fn,ms});return index},cancel:id=>timers.delete(id)});return {queue,timers,writes,expire:async()=>{const [id,t]=timers.entries().next().value;timers.delete(id);await t.fn()}}}
 return {saved,journal,page,setClock:value=>clock=value};
}
test('completion survives a reload during the Undo window with original ids and remaining time',async()=>{
 const f=durableFixture(),before=f.page();before.queue.add('sandra','Sandra',['rau-next']);
 before.timers.clear();f.setClock(2000);const after=f.page();after.queue.restore({});
 assert.equal(completionHidden(['rau-next'],after.queue.items()),true);
 assert.equal([...after.timers.values()][0].ms,3000);await after.expire();
 assert.deepEqual(after.writes,[['sandra',['rau-next']]]);assert.equal(f.saved.size,0);
});
test('Undo after a reload clears the durable intent without saving',()=>{
 const f=durableFixture(),before=f.page();before.queue.add('sandra','Sandra');before.timers.clear();
 const after=f.page();after.queue.restore({});assert.equal(after.queue.undo('sandra'),true);
 assert.equal(f.saved.size,0);assert.equal(after.timers.size,0);assert.deepEqual(after.writes,[]);
});
test('reload after the server saved does not replay or reopen the completion',()=>{
 const f=durableFixture(),before=f.page();before.queue.add('sandra','Sandra');before.timers.clear();
 const after=f.page();after.queue.restore({sandra:{done:true}});
 assert.equal(f.saved.size,0);assert.equal(after.timers.size,0);assert.deepEqual(after.writes,[]);
});
test('Undo in another open tab cancels the old tab timer too',async()=>{
 const f=durableFixture(),first=f.page();first.queue.add('sandra','Sandra');
 const second=f.page();second.queue.restore({});second.queue.undo('sandra');await first.expire();
 assert.deepEqual(first.writes,[]);assert.equal(first.queue.items().length,0);
});
test('one tab cannot clear another task waiting to save',async()=>{
 const f=durableFixture(),first=f.page(),second=f.page();first.queue.add('sandra','Sandra');second.queue.add('riley','Riley');
 await first.expire();assert.equal(f.saved.has('riley'),true);await second.expire();assert.equal(f.saved.size,0);
});
