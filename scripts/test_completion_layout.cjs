const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../app/index.html'),'utf8');
const completionModule={module:{exports:{}}};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/completion.js'),'utf8'),completionModule);const {completionHidden}=completionModule.module.exports;require('../app/card-order.js');
test('internal pending completion immediately changes the highlighted card and Undo restores order',()=>{
 const start=html.indexOf('function renderLane('),end=html.indexOf('function renderExternal(',start),root={};let pending=[];
 const c=vm.createContext({data:{progress:{tasks:{}}},completionHidden,completions:{items:()=>pending},WorkbenchOrder:globalThis.WorkbenchOrder,internalItems:()=>[{task_id:'first'},{task_id:'second'}],$:()=>root,focusCard:i=>'<focus>'+i.task_id+'</focus>',nextRow:i=>'<next>'+i.task_id+'</next>',orderBar:()=>'',restState:()=>''});
 vm.runInContext(html.slice(start,end),c);c.renderLane('internal');assert.match(root.innerHTML,/<focus>first/);
 pending=[{taskIds:['first']}];c.renderLane('internal');assert.match(root.innerHTML,/<focus>second/);assert.ok(!root.innerHTML.includes('first'));
 pending=[];c.renderLane('internal');assert.match(root.innerHTML,/<focus>first/);
});
test('pending promotion retains a removed card’s unsaved note for Undo',()=>{
 let pending=[],renders=0;const nodes=new Map([['draft-first',{id:'draft-first',value:'My unsaved note',defaultValue:''}]]);
 const c=vm.createContext({data:{},Map,completions:{items:()=>pending},document:{querySelectorAll:selector=>selector==='textarea[id]'?[...nodes.values()]:[],getElementById:id=>nodes.get(id)},renderExternal:()=>{renders++;nodes.clear();if(!pending.length)nodes.set('draft-first',{id:'draft-first',value:'',defaultValue:''})},renderLane:()=>{},paintCompletions:()=>{}});
 vm.runInContext(html.split('\n').filter(l=>l.startsWith('let completionViewState=')||l.startsWith('function refreshCompletionCards(')).join('\n'),c);
 pending=[{id:'first',taskIds:['first']}];c.refreshCompletionCards();assert.equal(nodes.has('draft-first'),false);
 c.refreshCompletionCards();assert.equal(renders,1,'saving-phase notification does not rebuild the form');
 pending=[];c.refreshCompletionCards();assert.equal(nodes.get('draft-first').value,'My unsaved note');
});
