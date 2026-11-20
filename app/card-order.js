/* Local display order only. Pointer and keyboard share the same saved operation. */
(function(root){
  function ordered(items,record={}){
    const ranks=new Map((record.ids||[]).map((id,n)=>[id,n]));
    return items.map((item,n)=>({item,n})).sort((a,b)=>(ranks.get(a.item.task_id)??Infinity)-(ranks.get(b.item.task_id)??Infinity)||a.n-b.n).map(x=>x.item);
  }
  function moved(ids,from,to,after=false){
    if(from===to||!ids.includes(from)||!ids.includes(to))return ids.slice();
    const next=ids.filter(id=>id!==from);next.splice(next.indexOf(to)+(after?1:0),0,from);return next;
  }
  function skipped(ids,id){return ids.includes(id)?ids.filter(x=>x!==id).concat(id):ids.slice()}
  function decorateSkipControls(doc){
    for(const card of doc.querySelectorAll('#external-work [data-task-card],#internal-work [data-task-card]')){
      let footer=card.querySelector(':scope > .card-footer-actions');
      let button=card.querySelector(':scope > .skip-for-now')||footer?.querySelector(':scope > .skip-for-now');
      if(!footer){footer=doc.createElement('footer');footer.className='card-footer-actions';footer.setAttribute('aria-label','Card display actions');card.append(footer)}
      if(!button){const lane=card.closest('#external-work')?'external':'internal';button=doc.createElement('button');button.type='button';button.className='skip-for-now';button.dataset.skipCard=card.dataset.taskCard;button.dataset.skipLane=lane;button.title='Skip for now · move to the bottom';button.setAttribute('aria-label','Skip for now: '+(card.querySelector('h2,h3,strong')?.textContent||'this card'));button.innerHTML='<span aria-hidden="true">↓</span><span class="skip-label">Skip for now</span>'}
      if(button.parentElement!==footer)footer.append(button);
    }
  }
  function install({save,notify}){
    let drag=null,busy=false;
    const cards=(lane,anchor)=>{const section=lane==='external'?anchor?.closest?.('[data-external-section]'):null;return [...(section||document).querySelectorAll(section?'[data-task-card]':'#'+lane+'-work [data-task-card]')].filter(n=>!n.hidden)};
    const clear=()=>{document.querySelectorAll('.order-dragging,.order-before,.order-after').forEach(n=>n.classList.remove('order-dragging','order-before','order-after'));document.body.classList.remove('ordering-cards')};
    async function commit(lane,ids,focusId,intent=null){
      if(busy)return;busy=true;document.body.classList.add('order-saving');
      try{await save(lane,ids,intent);notify(intent==='skip'?'Moved to the bottom':ids.length?'Order saved':'Recommended order restored')}
      catch(error){notify(error.message||'Could not save order. Your previous order is unchanged.')}
      finally{busy=false;document.body.classList.remove('order-saving');if(focusId)document.querySelector('[data-order-handle="'+CSS.escape(focusId)+'"]')?.focus({preventScroll:true})}
    }
    document.addEventListener('pointerdown',e=>{
      const handle=e.target.closest('[data-order-handle]');if(!handle||busy||e.button!==0)return;
      const card=handle.closest('[data-task-card]'),lane=handle.dataset.orderLane;
      if(cards(lane,card).length<2)return;
      drag={handle,card,lane,id:handle.dataset.orderHandle,x:e.clientX,y:e.clientY,target:null,active:false,pointer:e.pointerId};
      handle.setPointerCapture(e.pointerId);e.preventDefault();handle.focus({preventScroll:true});
    });
    document.addEventListener('pointermove',e=>{
      if(!drag||drag.pointer!==e.pointerId)return;
      if(!drag.active&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<6)return;
      drag.active=true;e.preventDefault();clear();document.body.classList.add('ordering-cards');drag.card.classList.add('order-dragging');
      const list=cards(drag.lane,drag.card),others=list.filter(n=>n!==drag.card);if(!others.length)return;
      const target=others.find(n=>e.clientY<n.getBoundingClientRect().bottom)||others.at(-1),box=target.getBoundingClientRect(),after=e.clientY>box.top+box.height/2;
      target.classList.add(after?'order-after':'order-before');drag.target={id:target.dataset.taskCard,after};
      if(e.clientY<65)window.scrollBy(0,-20);else if(e.clientY>window.innerHeight-65)window.scrollBy(0,20);
    },{passive:false});
    document.addEventListener('pointerup',e=>{
      if(!drag||drag.pointer!==e.pointerId)return;const d=drag;drag=null;clear();
      if(d.active&&d.target){const ids=cards(d.lane,d.card).map(n=>n.dataset.taskCard),next=moved(ids,d.id,d.target.id,d.target.after);if(next.join('\n')!==ids.join('\n'))void commit(d.lane,next,d.id)}
    });
    document.addEventListener('pointercancel',()=>{drag=null;clear()});
    document.addEventListener('keydown',e=>{
      if(e.key==='Escape'&&drag){drag=null;clear();return}
      const handle=e.target.closest('[data-order-handle]');if(!handle||busy||!['ArrowUp','ArrowDown','Home','End'].includes(e.key))return;
      e.preventDefault();const lane=handle.dataset.orderLane,ids=cards(lane,handle.closest('[data-task-card]')).map(n=>n.dataset.taskCard),id=handle.dataset.orderHandle,n=ids.indexOf(id),to=e.key==='Home'?0:e.key==='End'?ids.length-1:n+(e.key==='ArrowDown'?1:-1);
      if(to>=0&&to<ids.length&&to!==n)void commit(lane,moved(ids,id,ids[to],to>n),id);
    });
    document.addEventListener('click',e=>{const skip=e.target.closest('[data-skip-card]');if(skip&&!busy){const card=skip.closest('[data-task-card]'),lane=skip.dataset.skipLane,ids=[...document.querySelectorAll('#'+lane+'-work [data-task-card]')].filter(n=>!n.hidden).map(n=>n.dataset.taskCard);if(ids.length>1)void commit(lane,skipped(ids,card.dataset.taskCard),null,'skip');else notify('This is the only card in this list.');return}const reset=e.target.closest('[data-order-reset]');if(reset&&!busy)void commit(reset.dataset.orderReset,[])});
    const decorate=()=>decorateSkipControls(document);if(typeof MutationObserver!=='undefined'){new MutationObserver(decorate).observe(document.querySelector('.workspace')||document.body,{childList:true,subtree:true});decorate();}return {isBusy:()=>busy||!!drag};
  }
  root.WorkbenchOrder={ordered,moved,skipped,install,decorateSkipControls};
  if(typeof module!=='undefined')module.exports=root.WorkbenchOrder;
})(typeof globalThis!=='undefined'?globalThis:this);
