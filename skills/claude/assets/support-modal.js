/* Modal comum: o host cobre todo o ecrã; HTML autónomo usa o mesmo componente. */
(function () {
  'use strict';
  let dialog, handler, activeId;
  function close(hintId) {
    if(hintId && hintId!==activeId)return;
    if(dialog?.open)dialog.close();
    activeId=null;handler=null;
  }
  function notice(hintId,text){
    if(hintId===activeId && dialog?.open)dialog.querySelector('.pc-help-status').textContent=String(text).slice(0,250);
  }
  function open(payload, onAction) {
    if(typeof payload.hint_id!=='string' || typeof payload.text!=='string')return;
    if(!dialog){
      const style=document.createElement('style');
      style.textContent=`.pc-help-modal{box-sizing:border-box;position:fixed;inset:0;margin:0;border:0;width:100vw;max-width:none;height:100dvh;max-height:none;padding:clamp(20px,5vw,64px);background:#f5f3ea;color:#233c32;font:inherit;overflow:auto}.pc-help-modal::backdrop{background:#233c32}.pc-help-modal .pc-help-card{max-width:720px;margin:auto;min-height:100%;display:flex;flex-direction:column;justify-content:center;gap:20px}.pc-help-modal h2{font-size:1.4em;margin:0}.pc-help-modal .pc-help-text{font-size:1.25em;line-height:1.5;overflow-wrap:anywhere;margin:0}.pc-help-modal .pc-help-buttons{display:flex;flex-wrap:wrap;gap:12px}.pc-help-modal button{font:inherit;min-height:56px;padding:12px 18px;border:2px solid #38624f;border-radius:10px;background:#fffefa;color:#233c32;cursor:pointer}.pc-help-modal button[data-action=continue]{background:#233c32;color:#fffefa}.pc-help-modal :focus-visible{outline:3px solid #285cc0;outline-offset:4px}`;
      document.head.append(style);
      dialog=document.createElement('dialog');dialog.className='pc-help-modal';
      dialog.setAttribute('aria-labelledby','pc-help-title');dialog.setAttribute('aria-describedby','pc-help-text');
      // Retomar exige uma escolha explícita; não existe áudio nem avanço automático.
      dialog.addEventListener('cancel',event=>event.preventDefault());
      dialog.addEventListener('click',event=>{
        const action=event.target.closest('[data-action]')?.dataset.action;
        if(!['listen','next','stuck','continue','teacher'].includes(action))return;
        const callback=handler,hintId=activeId;
        if(action!=='listen')close();
        callback?.(action,hintId);
      });
      document.body.append(dialog);
    }
    activeId=payload.hint_id;handler=onAction;dialog.lang=payload.language==='en'?'en':'pt-PT';
    dialog.replaceChildren();
    const card=document.createElement('div');card.className='pc-help-card';
    const title=document.createElement('h2');title.id='pc-help-title';title.textContent=String(payload.title||'Um próximo passo').slice(0,100);
    const text=document.createElement('p');text.id='pc-help-text';text.className='pc-help-text';text.textContent=payload.text.slice(0,400);
    const buttons=document.createElement('div');buttons.className='pc-help-buttons';
    for(const action of ['listen','next','stuck','teacher','continue']){
      const button=document.createElement('button');button.type='button';button.dataset.action=action;
      button.textContent=String(payload.labels?.[action]||action).slice(0,100);buttons.append(button);
    }
    const status=document.createElement('p');status.className='pc-help-status';status.setAttribute('role','status');
    card.append(title,text,buttons,status);dialog.append(card);
    if(!dialog.open)dialog.showModal();
    buttons.querySelector('[data-action=continue]').focus();
  }
  window.PageCraftSupportModal={open,close,notice};
  function attachHost(){
    const frame=document.getElementById('activity-frame')||document.getElementById('lesson');
    if(!frame)return;
    frame.addEventListener('load',()=>close());
    window.addEventListener('pagehide',()=>close());
    window.addEventListener('message',event=>{
      if(event.source!==frame.contentWindow || event.data?.pagecraft!==1 || event.data.type!=='support_modal')return;
      const p=event.data.payload||{};
      if(p.action==='close'){close(p.hint_id);return;}
      if(p.action==='notice'){notice(p.hint_id,p.text);return;}
      if(p.action!=='open' || document.getElementById('freeze-overlay')?.hidden===false)return;
      open(p,(action,hintId)=>frame.contentWindow?.postMessage({pagecraft:1,type:'support_modal_action',payload:{hint_id:hintId,action}},'*'));
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',attachHost,{once:true});else attachHost();
})();
