const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function app(){const saved=new Map(),ctx=vm.createContext({Intl,Date,Map,Set,Number,String,Math,Object,parseFloat,localStorage:{getItem:k=>saved.get(k),setItem:(k,v)=>saved.set(k,v)}});for(const f of ['presentation.js','coaching-focus.js','metrics-focus.js','insight-views.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../app',f),'utf8'),ctx);return ctx.WorkbenchInsightViews}
const revenue={actual:6900,month:'2026-11',full_month_goal_display:'$10.3K',full_month_attainment_display:'67%',deals:[{id:'1',name:'One',tier:'Led',mrr:2880},{id:'1',name:'One',tier:'Led',mrr:2880},{id:'2',name:'Two',tier:'Supported',mrr:4020}]};
test('the selected metrics layout retains a Sankey and leaves compact coaching unchanged',()=>{
 const a=app(),state={snapshot:{month:'2026-11',metrics:{revenue}}},now=new Date('2026-11-17T18:00Z'),coaching=a.coaching({},'quarter',now);
 assert.match(a.metrics(state,revenue,'2026-11'),/mf-sankey/);
 assert.equal(a.coaching({},'quarter',now),coaching);
 assert.match(coaching,/class="coaching-focus cf-design-0 review-refined"/);
 assert.match(coaching,/class="cf-hero"/);
 assert.match(coaching,/>Last<\/span>/);
 assert.doesNotMatch(coaching,/cf-toolbar|data-design-kind="coaching"|data-design-step/);
});

test('selected-month calls cannot borrow the current-month total',()=>{const a=app(),html=a.metrics({snapshot:{month:'2026-11',metrics:{calls:{external:12}}}},revenue,'2026-10');assert.equal(a.metricModel({snapshot:{month:'2026-11',metrics:{calls:{external:12}}}},revenue,'2026-10').calls.external,undefined);assert.match(html,/<strong>—<\/strong><span>customer calls logged/)});
test('rounded source goals remain rounded and deal counts deduplicate',()=>{const r={...revenue,components:{rows:[[{display:'MRR'},{display:'$6.9K'},{},{},{},{display:'$10.3K'},{},{display:'67%'}]]}},state={snapshot:{month:'2026-11',metrics:{revenue:r}}},h=app().metrics(state,r,'2026-11');assert.match(h,/67%/);assert.match(h,/<small class="mf-goal-ring-amounts">≈ \$6\.9K \/ \$10\.3K<\/small>/);assert.match(h,/Rounded source values/);assert.equal(app().metricModel({},revenue,'2026-11').ids.size,2);assert.match(h,/<strong>2<\/strong><span>credited deals/);assert.doesNotMatch(h,/10,300/)});
test('conflicting duplicate deal roles do not invent credit counts',()=>{const r={...revenue,deals:[...revenue.deals,{id:'1',tier:'Assisted'}]},h=app().metrics({snapshot:{month:'2026-11',metrics:{revenue:r}}},r,'2026-11');assert.match(h,/<strong>—<\/strong><span>credited deals/);assert.doesNotMatch(h,/class="mf-tier"/)});
test('coaching filters the requested lookback and escapes displayed source authors and text',()=>{
 const h=app().coaching({feedback:[
  {received_date:'2026-07-01',text:'OUTSIDE_REQUESTED_LOOKBACK',source_url:'https://example.com/too-old'},
  {received_date:'2026-09-01',manager:'<img src=x onerror=alert(1)>',text:'IN_REQUESTED_LOOKBACK',source_url:'https://example.com/old'},
  {received_date:'2026-11-01',text:'<script>alert(1)</script>',source_url:'https://example.com/source'},
  {received_date:'2026-11-02',text:'UNSAFE_SOURCE_SCHEME',source_url:'javascript:alert(1)'}
 ]},'quarter',new Date('2026-11-17T18:00Z'));
 assert.match(h,/Aug 17 – Nov 17, 2026/);
 assert.match(h,/IN_REQUESTED_LOOKBACK/);
 assert.doesNotMatch(h,/OUTSIDE_REQUESTED_LOOKBACK|UNSAFE_SOURCE_SCHEME/);
 assert.doesNotMatch(h,/<script\b|<img\b|href=["']javascript:/i);
 assert.match(h,/&lt;img src=x onerror=alert\(1\)&gt;/);
 assert.match(h,/&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
});

test('feedback summaries remain prose and explicit source quotes alone get quote markup',()=>{const h=app().coaching({feedback:[{received_date:'2026-11-01',text:'A summary of feedback',manager:'Manager',source_url:'https://example.com/summary'},{received_date:'2026-11-02',quote:'Exact source wording',manager:'Manager',source_url:'https://example.com/quote'}]},'quarter',new Date('2026-11-17T18:00Z'));assert.match(h,/<p>A summary of feedback<\/p>/);assert.doesNotMatch(h,/<blockquote>A summary/);assert.match(h,/<blockquote>Exact source wording<\/blockquote>/)});
