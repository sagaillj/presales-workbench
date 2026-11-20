/* Local settings and journal only. Never sends content to a remote service. */
(function(){'use strict';
const keys=['workbench-appearance','workbench-month-trail'];
async function settings(){
 const r=await fetch('/api/automation-features');if(r.ok)window.WorkbenchAutomationSettings?.mount({automation_features:await r.json()});
 const p=await fetch('/api/onboarding');if(p.ok){const data=await p.json(),field=document.getElementById('additional-sources');if(field&&document.activeElement!==field)field.value=(data.profile?.preferences?.additional_sources||[]).join(', ');}
}
async function persist(){try{const ui_preferences={};for(const key of keys){const v=localStorage.getItem(key);if(v!==null)ui_preferences[key]=v;}await fetch('/api/local-changes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ui_preferences})});}catch(_){}}
document.addEventListener('DOMContentLoaded',async()=>{
 try{const r=await fetch('/api/local-changes');if(r.ok){const saved=(await r.json()).ui_preferences||{};let restored=false;for(const key of keys)if(localStorage.getItem(key)===null&&saved[key]!==undefined){localStorage.setItem(key,saved[key]);restored=true;}if(restored)window.WorkbenchAppearance?.mount(document,localStorage);}}catch(_){}
 try{await settings();}catch(_){}
 document.getElementById('settings-toggle')?.addEventListener('click',()=>settings().catch(()=>{}));
 document.getElementById('save-additional-sources')?.addEventListener('click',async()=>{const status=document.getElementById('additional-sources-status');try{const sources=document.getElementById('additional-sources').value.split(',').map(x=>x.trim()).filter(Boolean);const r=await fetch('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'preferences',additional_sources:sources})});const data=await r.json();if(!r.ok)throw Error(data.error||'Could not save');status.textContent='Saved. Ask your assistant to check these tools and agree the read scope. No access was granted.';}catch(e){status.textContent=e.message;}});
});
document.addEventListener('change',e=>{if(e.target.closest('#appearance-settings'))setTimeout(persist,0);});
document.addEventListener('click',e=>{if(e.target.closest('#appearance-settings'))setTimeout(persist,0);});
})();
