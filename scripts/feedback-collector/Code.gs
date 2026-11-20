/** Workbench feedback relay. Deploy only after reviewing scopes and destination. */
const FORM_ID = 'REPLACE_WITH_APPROVED_FORM_ID';
const TITLES = {rating:'How likely are you to recommend Workbench to another SE?',hours:'Estimated hours saved this week',comments:'What helped? What should change?',usage:'Week and included usage counts',email:'Work email (optional)'};
function json_(data){return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);}
function clean_(p){
 if(!p||p.schema!==1||typeof p.submission_id!=='string'||!/^[a-f0-9]{64}$/.test(p.submission_id))throw Error('Invalid submission');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(p.week||'')||new Date(p.week+'T12:00:00Z').getUTCDay()!==1)throw Error('Invalid week');
 if(!Number.isInteger(p.rating)||p.rating<0||p.rating>10)throw Error('Choose 0 to 10');
 if(p.hours!==null&&(typeof p.hours!=='number'||!Number.isFinite(p.hours)||p.hours<0||p.hours>168))throw Error('Invalid estimate');
 if(typeof p.comments!=='string'||p.comments.length>2000)throw Error('Feedback is too long');
 if(typeof p.email!=='string'||p.email.length>254||(p.email&&!/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(p.email)))throw Error('Invalid email');
 if(!/^\d+\.\d+\.\d+$/.test(p.version||''))throw Error('Invalid version');
 if(p.counts!==null){if(!p.counts||Object.keys(p.counts).sort().join(',')!=='active_days,tasks_marked_done'||![p.counts.active_days,p.counts.tasks_marked_done].every(x=>Number.isInteger(x)&&x>=0)||p.counts.active_days>7)throw Error('Invalid counts');}
 const allowed=['schema','submission_id','week','rating','hours','comments','email','counts','version','metadata'];if(Object.keys(p).some(k=>!allowed.includes(k)))throw Error('Unexpected fields');
 if(p.metadata!==undefined){
  const m=p.metadata,keys=['schema','os','python','browser','viewport','active_days_total','active_days_30d','estimated_tasks_week','unestimated_tasks_week','estimated_tasks_month','unestimated_tasks_month','hours_estimated_week','hours_estimated_month','estimate_method','estimate_is_measured','task_events_week','feedback_cadence_weeks'];
  if(!m||Object.keys(m).some(k=>!keys.includes(k))||m.schema!==1||m.estimate_is_measured!==false||m.estimate_method!=='midpoint_of_category_assumptions_v1')throw Error('Invalid metadata');
  if(!['win32','darwin','linux','other'].includes(m.os)||!/^\d+\.\d+$/.test(m.python)||!['Edge','Firefox','Chrome','Safari','Other'].includes(m.browser)||!['small','medium','large','unknown'].includes(m.viewport))throw Error('Invalid runtime metadata');
  for(const k of ['active_days_total','active_days_30d','estimated_tasks_week','unestimated_tasks_week','estimated_tasks_month','unestimated_tasks_month'])if(!Number.isInteger(m[k])||m[k]<0)throw Error('Invalid usage metadata');
  for(const k of ['hours_estimated_week','hours_estimated_month'])if(m[k]!==null&&(typeof m[k]!=='number'||!Number.isFinite(m[k])||m[k]<0||m[k]>168))throw Error('Invalid estimated hours');
  if(![1,2].includes(m.feedback_cadence_weeks)||!m.task_events_week||Object.keys(m.task_events_week).sort().join(',')!=='done,notes,reopened'||!Object.values(m.task_events_week).every(x=>Number.isInteger(x)&&x>=0))throw Error('Invalid event counts');
 }
 return p;
}
function usage_(p){const lines=['Week of '+p.week,'Workbench '+p.version];if(p.counts)lines.push('Days opened: '+p.counts.active_days,'Tasks marked done: '+p.counts.tasks_marked_done,'Checkbox completions are user-reported, not verified deliveries.');else lines.push('Usage counts not included.');if(p.metadata)lines.push('Usage metadata: '+JSON.stringify(p.metadata));lines.push('Submission reference: '+p.submission_id);return lines.join('\n');}
function cellText_(text){return /^[\s]*[=+@-]/.test(text)?"'"+text:text;}
function receipt_(form,response,key,duplicate){const saved=form.getResponse(response.getId());return {ok:true,submission_id:key,response_id:saved.getId(),submitted_at:saved.getTimestamp().toISOString(),duplicate:duplicate};}
function doPost(e){
 let lock,writeAttempted=false;
 try{
  if(!e||!e.postData||e.postData.contents.length>14000)throw Error('Invalid request size');
  const p=clean_(JSON.parse(e.postData.contents));lock=LockService.getScriptLock();if(!lock.tryLock(10000))throw Error('Busy, retry shortly');
  const form=FormApp.openById(FORM_ID),props=PropertiesService.getScriptProperties();
  if(props.getProperty('enabled')==='false')throw Error('Collector paused');
  const day=new Date().toISOString().slice(0,10),dayKey='wb-day:'+day,dayCount=Number(props.getProperty(dayKey)||'0');
  const known=props.getProperty(p.submission_id);
  const stored=props.getProperties();for(const key of Object.keys(stored)){if(/^[a-f0-9]{64}$/.test(key)){try{if(JSON.parse(stored[key]).at<Date.now()-8*86400000)props.deleteProperty(key);}catch(_){}}else if(key.startsWith('wb-day:')&&key.slice(7)<new Date(Date.now()-8*86400000).toISOString().slice(0,10))props.deleteProperty(key);}
  if(known){try{return json_(receipt_(form,form.getResponse(JSON.parse(known).id),p.submission_id,true));}catch(_){throw Error('Saved response needs maintainer review');}}
  // Recover an accepted write if the prior request ended before saving its receipt.
  const since=new Date(Date.now()-35*86400000),recent=form.getResponses(since);
  for(const row of recent){if(row.getItemResponses().some(x=>x.getItem().getTitle()===TITLES.usage&&String(x.getResponse()).includes('Submission reference: '+p.submission_id))){props.setProperty(p.submission_id,JSON.stringify({id:row.getId(),at:Date.now()}));return json_(receipt_(form,row,p.submission_id,true));}}
  if(!Number.isFinite(dayCount)||dayCount>=200)throw Error('Daily pilot limit reached');
  const items={};form.getItems().forEach(item=>items[item.getTitle()]=item);
  for(const name of Object.values(TITLES))if(!items[name])throw Error('Form fields changed; contact maintainer');
  let response=form.createResponse().withItemResponse(items[TITLES.rating].asScaleItem().createResponse(p.rating));
  if(p.hours!==null)response=response.withItemResponse(items[TITLES.hours].asTextItem().createResponse(String(p.hours)));
  if(p.comments)response=response.withItemResponse(items[TITLES.comments].asParagraphTextItem().createResponse(cellText_(p.comments)));
  response=response.withItemResponse(items[TITLES.usage].asParagraphTextItem().createResponse(usage_(p)));
  if(p.email)response=response.withItemResponse(items[TITLES.email].asTextItem().createResponse(cellText_(p.email)));
  writeAttempted=true;const saved=response.submit();props.setProperty(dayKey,String(dayCount+1));props.setProperty(p.submission_id,JSON.stringify({id:saved.getId(),at:Date.now()}));return json_(receipt_(form,saved,p.submission_id,false));
 }catch(error){return json_({ok:false,accepted:writeAttempted?'unknown':false,error:'Feedback was not confirmed. Please retry or use the Google Form.'});}
 finally{if(lock)lock.releaseLock();}
}
function doGet(){return json_({service:'workbench-feedback',schema:1,ready:true,metadata:true});}
