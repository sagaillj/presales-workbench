const {test}=require('node:test');
const assert=require('node:assert/strict');
require('../app/card-order.js');
const {ordered,moved,install}=globalThis.WorkbenchOrder;
test('3 can move ahead of 2, or 1 can move to the bottom, without mutating input',()=>{
 const ids=['a','b','c'];assert.deepEqual(moved(ids,'c','b'),['a','c','b']);assert.deepEqual(moved(ids,'a','c',true),['b','c','a']);assert.deepEqual(ids,['a','b','c']);
});
test('saved order uses stable IDs, ignores hidden IDs and appends new work',()=>{
 const items=['new','a','b'].map(task_id=>({task_id}));assert.deepEqual(ordered(items,{ids:['hidden','b','a']}).map(i=>i.task_id),['b','a','new']);assert.deepEqual(items.map(i=>i.task_id),['new','a','b']);
});
test('pointer drop and keyboard reorder persist the same operation',async()=>{
 const listeners={},saved=[],classes={add(){},remove(){}},handles={};
 const cards=['a','b','c'].map((id,n)=>({hidden:false,dataset:{taskCard:id},classList:classes,getBoundingClientRect:()=>({top:n*100,bottom:(n+1)*100,height:100})}));
 for(const card of cards)handles[card.dataset.taskCard]={dataset:{orderHandle:card.dataset.taskCard,orderLane:'external'},closest:s=>s==='[data-task-card]'?card:null,setPointerCapture(){},focus(){}};
 global.CSS={escape:s=>s};global.window={innerHeight:800,scrollBy(){}};
 global.document={body:{classList:classes},querySelectorAll:s=>s.startsWith('#')?cards:[],querySelector:()=>null,addEventListener:(name,fn)=>listeners[name]=fn};
 const notify=[];const controller=install({save:async(lane,ids)=>saved.push({lane,ids}),notify:x=>notify.push(x)});
 const event=(id,extra={})=>({target:{closest:()=>handles[id]},button:0,pointerId:1,clientX:10,clientY:250,preventDefault(){},...extra});
 listeners.pointerdown(event('c'));listeners.pointermove(event('c',{clientY:110}));listeners.pointerup(event('c',{clientY:110}));await new Promise(resolve=>setImmediate(resolve));
 assert.deepEqual(saved[0],{lane:'external',ids:['a','c','b']});assert.equal(controller.isBusy(),false);
 listeners.keydown(event('b',{key:'Home'}));await new Promise(resolve=>setImmediate(resolve));assert.deepEqual(saved[1].ids,['b','a','c']);
 listeners.pointerdown(event('a'));listeners.pointercancel();assert.equal(saved.length,2);assert.equal(controller.isBusy(),false);
});
