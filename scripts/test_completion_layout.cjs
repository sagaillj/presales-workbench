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

test('an empty lane retains Completed and Reopen without overriding responsive drawer layout',()=>{
 const nodes=new Map(),workspace={dataset:{sidebar:'closed'},className:'workspace resting'};
 const node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,attrs:{},setAttribute(k,v){this.attrs[k]=v}});return nodes.get(id)};
 const c=vm.createContext({data:{},document:{querySelector:()=>workspace,getElementById:node},$:selector=>selector==='.workspace'?workspace:node(selector.slice(1)),localStorage:{setItem(){}},completedItems:()=>[{id:'orientation-done',title:'Explore Workbench',reopenable:true}],esc:String,readableProse:String,dealRecordBlock:()=>'',handoffButtons:()=>''});
 vm.runInContext(html.split('\n').filter(l=>/^function (setSidebar|selectTimeline|renderCompleted)\(/.test(l)).join('\n'),c);
 c.setSidebar(true);c.selectTimeline('completed');c.renderCompleted();
 assert.equal(workspace.dataset.sidebar,'open');assert.equal(workspace.className,'workspace resting');
 assert.equal(node('completed-panel').hidden,false);assert.match(node('completed-actions').innerHTML,/data-reopen="orientation-done"/);
 // Empty-state art must not override the drawer's explicit state. Otherwise the
 // DOM above is correct but its ancestor is display:none and Reopen is unreachable.
 const inlineCSS=[...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m=>m[1]).join('\n');
 assert.doesNotMatch(inlineCSS,/\.workspace\.resting[^{}]*\{[^{}]*(?:display\s*:\s*none|grid-template-columns)/);
 const drawerCSS=fs.readFileSync(path.join(__dirname,'../app/header-variants.css'),'utf8');
 assert.match(drawerCSS,/\.workspace\[data-sidebar=closed\]>\.feed\{display:none\}/);
 assert.match(drawerCSS,/@media\(max-width:850px\)[^{]*\{[^]*?\.workspace\{grid-template-columns:minmax\(0,1fr\)\}/);
});
