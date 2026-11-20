/* Read-only design exploration. All figures retain their source and reporting period. */
(function(root){'use strict';
const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const designs=[['flight','Flight Path'],['ribbon','Color Ribbon'],['almanac','Almanac'],['orbit','Orbit'],['editorial','Field Notes'],['steps','Three Steps'],['thread','Conversation'],['split','Signal & Practice'],['spine','Timeline'],['spectrum','Spectrum']];
const metricNames=['Revenue Streams','Contribution Studio','Activity Pulse','Goal Observatory','Performance Mosaic','Contribution Steps','Conversation Mix','Portfolio Atlas','Scorecard Studio','Color Compass'];
const read=k=>{try{return Math.max(0,Math.min(9,Number(localStorage.getItem('workbench-design-'+k))||0))}catch(_){return 0}};
const date=v=>v?new Date(String(v).slice(0,10)+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'}):'';
const day=v=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(v);
const iso=d=>d.toISOString().slice(0,10),utc=d=>new Date(d+'T12:00:00Z'),add=(d,n)=>new Date(d.getTime()+n*86400000);
const link=(u,t)=>/^https?:\/\//.test(u||'')||/^\/qci\/\d{4}-\d{2}-\d{2}$/.test(u||'')?'<a href="'+E(u)+'" target="_blank" rel="noopener">'+E(t)+' ↗</a>':'';
const money=v=>v==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v);
const empty=t=>'<p class="iv-empty">'+E(t)+'</p>';
const panel=(key,title,body)=>'<section class="iv-panel iv-'+key+'"><h3>'+title+'</h3>'+body+'</section>';
function chrome(kind,title,subtitle,hero,body){const n=read(kind),d=designs[n];return `<div class="insight-view iv-design-${d[0]} iv-${kind}" data-insight-kind="${kind}"><div class="iv-toolbar"><span class="iv-design-label">${E(kind==='metrics'?metricNames[n]:d[1])} <small>Round 2</small></span><div class="iv-switch" role="group" aria-label="${kind} design options"><button data-design-step="-1" data-design-kind="${kind}" aria-label="Previous ${kind} design">‹</button><span aria-live="polite">${n+1} / 10</span><button data-design-step="1" data-design-kind="${kind}" aria-label="Next ${kind} design">›</button></div></div><div class="iv-hero"><div class="iv-heading"><span class="iv-eyebrow">${kind==='coaching'?'Reflect. Refine. Repeat.':'The shape of your impact'}</span><h2>${E(title)}</h2><div class="iv-subtitle">${subtitle}</div></div>${hero}</div>${body}</div>`}
function periodModel(c,mode='quarter',now=new Date(),offset=0){
 const today=day(now),t=utc(today),span=mode==='year'?12:mode==='half'?6:3;
 const first=new Date(Date.UTC(t.getUTCFullYear(),Math.floor(t.getUTCMonth()/span)*span+Math.min(0,offset)*span,1,12)),end=new Date(Date.UTC(first.getUTCFullYear(),first.getUTCMonth()+span,1,12));
 const from=iso(first),through=iso(add(end,-1)),cutoff=today<through?today:through;
 const q=Math.floor(t.getUTCMonth()/3)+1,qs=new Date(Date.UTC(t.getUTCFullYear(),(q-1)*3,1,12)),qe=new Date(Date.UTC(t.getUTCFullYear(),q*3,1,12));
 const week=Math.min(13,Math.floor((t-qs)/86400000/7)+1),progress=Math.max(0,Math.min(100,(t-qs)/(qe-qs)*100));
 const all=new Map();for(const w of c.weekly_archive||[])if(w.week_end)all.set(w.week_end,{...w});for(const w of c.weekly_reviews||[])if(w.week_end)all.set(w.week_end,{...all.get(w.week_end),...w});
 const weeks=[...all.values()].filter(w=>w.week_end>=from&&w.week_end<=cutoff).sort((a,b)=>b.week_end.localeCompare(a.week_end));
 const feedback=[...(c.feedback||[]),...(c.feedback_notes||[])].filter(f=>f.received_date>=from&&f.received_date<=cutoff&&(f.text||f.quote)).sort((a,b)=>b.received_date.localeCompare(a.received_date));
 const evidence=new Map((c.evidence||[]).map(e=>[e.id,e]));
 const count=mode==='year'?4:mode==='half'?6:13;
 const bins=Array.from({length:count},(_,i)=>{const a=mode==='quarter'?add(first,i*7):new Date(Date.UTC(first.getUTCFullYear(),first.getUTCMonth()+i*(mode==='year'?3:1),1,12));const b=i===count-1?end:mode==='quarter'?add(first,(i+1)*7):new Date(Date.UTC(first.getUTCFullYear(),first.getUTCMonth()+(i+1)*(mode==='year'?3:1),1,12));return {from:iso(a),through:iso(add(b,-1)),label:mode==='quarter'?'W'+(i+1):mode==='year'?'Q'+(i+1):a.toLocaleDateString('en-US',{month:'short',timeZone:'UTC'}),current:iso(a)<=today&&today<iso(b),future:iso(a)>today,weeks:weeks.filter(w=>w.week_end>=iso(a)&&w.week_end<iso(b)),feedback:feedback.filter(f=>f.received_date>=iso(a)&&f.received_date<iso(b))}});
 const title=mode==='year'?String(first.getUTCFullYear()):mode==='half'?'H'+(first.getUTCMonth()<6?1:2)+' '+first.getUTCFullYear():'Q'+(Math.floor(first.getUTCMonth()/3)+1)+' '+first.getUTCFullYear();
 return {from,through,cutoff,weeks,feedback,evidence,bins,title,week,progress,currentQuarter:'Q'+q+' '+t.getUTCFullYear(),goals:c.qci_goals||[],latest:weeks[0]};
}
const text=v=>typeof v==='string'?v:v?.text||'';
function feedbackHTML(f){return `<figure class="iv-quote">${f.quote?'<blockquote>'+E(f.quote)+'</blockquote>':'<p>'+E(f.text)+'</p>'}<figcaption>${E(f.manager||f.person||f.author||'Feedback')} · ${E(date(f.received_date))}${f.source_timestamp?' · '+E(f.source_timestamp):''} ${link(f.source_url,'Source')}</figcaption></figure>`}
function bucketHTML(b,m){const hs=b.weeks.flatMap(w=>(w.highlights||[]).map(h=>({...h,source_url:m.evidence.get(h.evidence_id)?.source_url||w.source_url}))),ls=b.weeks.flatMap(w=>w.lowlights||[]);return `<strong>${E(b.label)} · ${date(b.from)}–${date(b.through)}</strong>${b.future?empty('Ahead of us. No review yet.'):!b.weeks.length&&!b.feedback.length?empty('No saved review or feedback for this interval.'):''}${hs.length?'<h4>Highlights</h4>'+hs.slice(0,2).map(h=>'<p>'+E(text(h))+' '+link(h.source_url,'Evidence')+'</p>').join(''):''}${ls.length?'<h4>Constructive feedback</h4>'+ls.slice(0,2).map(h=>'<p>'+E(text(h))+'</p>').join(''):''}${b.feedback.slice(0,2).map(feedbackHTML).join('')}${b.weeks.map(w=>link(w.source_url,'Review '+date(w.week_end))).join(' ')}`}
function coaching(c,mode='quarter',now=new Date()){return root.WorkbenchCoaching.render(c,mode,now)}

function metricModel(state,r,month){
 const same=state.snapshot?.month===month,calls=same?state.snapshot?.metrics?.calls||{}:{},roster=state.snapshot?.metrics?.roster||{};
 const ids=new Map();let valid=Array.isArray(r.deals);for(const d of r.deals||[]){if(!d.id||!['Led','Assisted','Supported'].includes(d.tier)||ids.has(String(d.id))&&ids.get(String(d.id)).tier!==d.tier){valid=false;break}ids.set(String(d.id),d)}
 const tiers=['Led','Assisted','Supported'].map((name,i)=>{const rows=[...ids.values()].filter(d=>d.tier===name);return {name,rows,count:valid?rows.length:null,total:valid&&rows.every(d=>Number.isFinite(d.mrr))?rows.reduce((s,d)=>s+d.mrr,0):null,color:['var(--iv-teal)','var(--iv-violet)','var(--iv-gold)'][i]}});
 return {calls,roster,tiers,valid,ids,same};
}
function bars(items,format=v=>v??'—'){const max=Math.max(1,...items.map(x=>Number(x.value)||0));return '<div class="iv-bars">'+items.map(x=>`<div class="iv-bar-row"><span>${E(x.name)}</span><div><i style="width:${x.value==null?0:Math.max(0,x.value)/max*100}%;background:${x.color}"></i></div><strong>${E(format(x.value))}</strong></div>`).join('')+'</div>'}
function flow(m,r){
 const known=m.valid&&m.tiers.every(t=>t.total!=null&&t.total>=0),total=m.tiers.reduce((s,t)=>s+(t.total||0),0);if(!known||total<=0||!Number.isFinite(r.actual)||Math.abs(total-r.actual)>.01)return empty('Revenue stream unavailable until deal amounts reconcile to the scorecard.');
 let cursor=30;const paths=m.tiers.map(t=>{const h=t.total/total*150,y=cursor;cursor+=h;return `<path d="M 65 ${y+h/2} C 220 ${y+h/2}, 250 ${45+m.tiers.indexOf(t)*77}, 405 ${45+m.tiers.indexOf(t)*77}" stroke="${t.color}" stroke-width="${h}" fill="none" opacity=".65"><title>${E(t.name+' · '+money(t.total))}</title></path>`}).join('');
 return `<div class="iv-flow"><svg viewBox="0 0 570 250" role="img" aria-label="Credited revenue split by Led, Assisted and Supported"><rect x="45" y="30" width="20" height="150" rx="4" fill="var(--iv-teal)"/>${paths}${m.tiers.map((t,i)=>`<text x="420" y="${45+i*77}" fill="currentColor" font-size="15">${t.name}</text><text x="420" y="${65+i*77}" fill="currentColor" font-size="19" font-weight="700">${money(t.total)}</text>`).join('')}<text x="45" y="220" fill="currentColor" font-size="16">${money(total)} influenced MRR</text></svg></div><small class="iv-caption">Sankey · credited revenue split by role, ${E(r.currency||'USD')}. Zero-value roles carry no flow.</small>`;
}
function metrics(state,r,month){return root.WorkbenchMetrics.render(state,r,month)}

function cycle(kind,step){if(kind==='coaching')return root.WorkbenchCoaching.cycle(step);const i=(read(kind)+step+10)%10;try{localStorage.setItem('workbench-design-'+kind,String(i))}catch(_){}return i}
root.WorkbenchInsightViews={coaching,metrics,cycle,designs,periodModel,metricModel};
})(typeof globalThis!=='undefined'?globalThis:this);
