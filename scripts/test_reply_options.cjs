const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../app/index.html'),'utf8');
for(const [,code] of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(code);
const names=['readableProse','messageText','formatMessage','responseVariants','replyCarousel','messageWithDealLinks'];
const code=html.split('\n').filter(line=>names.some(name=>line.startsWith('function '+name+'('))).join('\n');
const ctx=vm.createContext({esc:s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))});vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/reply-links.js'),'utf8'),ctx);vm.runInContext(code,ctx);
const demo=JSON.parse(fs.readFileSync(path.join(__dirname,'../examples/demo-state.json'),'utf8')),draft=demo.communications.items.find(c=>c.response_variants?.length===3);
assert.ok(draft,'Fictional example must provide three authored options');
const result=ctx.replyCarousel(draft);assert.equal((result.match(/role="tab" /g)||[]).length,3);assert.equal((result.match(/role="tabpanel" /g)||[]).length,3);assert.match(result,/Default/);assert.match(result,/1 of 3/);assert.match(result,/data-reply-copy/);assert.match(ctx.formatMessage('1. First\n2. Second'),/<ol start="1">/);
assert.match(ctx.formatMessage('Hello\n\n1. First\n\n2. Second'),/<ol start="2">/);
const unsafe=ctx.formatMessage('<script>alert(1)</script>\n\n- <img src=x onerror=alert(1)>');assert.ok(!unsafe.includes('<script>'));assert.ok(!unsafe.includes('<img '));assert.match(unsafe,/<ul>/);
const edited=ctx.responseVariants({...draft,feedback:{draft_text:'My edited words'},display_body:'My edited words'});assert.equal(edited.length,1);assert.equal(edited[0].body,'My edited words');
const changed=ctx.responseVariants({...draft,scope_changed:true,body:'New membership'});assert.equal(changed.length,1);assert.equal(changed[0].body,'New membership');
assert.equal(draft.response_variants.length,3,'rendering must not mutate source variants');
assert.ok(ctx.replyCarousel({...draft,response_variants:[]}).includes('1 of 1'),'legacy text must not become three fake alternatives');
console.log('Three authored options, formatting, safe escaping, preserved edits and scope changes: passed');

assert.equal(ctx.messageText('Hey Morgan: 1. First question? 2. Second question?'),'Hey Morgan:\n1. First question?\n2. Second question?');

assert.equal(ctx.responseVariants({...draft,scope_changed:true,feedback:{draft_text:'Earlier edit'},body:'New scope'})[0].label,'Prepared response');

assert.equal(ctx.responseVariants({...draft,body:'A different new request'}).length,1);
assert.equal(ctx.responseVariants({...draft,recipient_name:'Different recipient',recipient_key:'different'}).length,1);
