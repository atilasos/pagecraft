/* Apoio comum PageCraft. O DocSpec fornece o conteúdo de cada atividade. */
(function () {
  'use strict';
  const COPY = {
    pt: {title:'Um próximo passo', hint:'Preciso de uma pista', groupHint:'Precisamos de uma pista',
      obstacle:'Onde precisas de ajuda?', groupObstacle:'Onde precisam de ajuda?', listen:'Ouvir', next:'Outra pista',
      helped:'Esta pista ajudou', stuck:'Ainda estou preso', groupStuck:'Ainda estamos presos', teacher:'Pedir ajuda ao professor',
      ai:'Esclarecer com IA', settings:'Mudar o tipo de ajuda', alone:'Mudar para trabalho individual', pair:'Mudar para trabalho a pares',
      back:'Regressar ao guião', reading:'Estou a ler', discussion:'Estamos a ler ou conversar',
      external:'Estou a trabalhar em ', groupExternal:'Estamos a trabalhar em ',
      resolved:'Já consigo continuar', groupResolved:'Já conseguimos continuar',
      wait:'A preparar uma pista. Podes continuar enquanto esperas.',
      escalate:'Mostra ao professor o que tentaste e onde ficaste preso. Usa «Pedir ajuda ao professor».',
      groupEscalate:'Mostrem ao professor o que tentaram e onde ficaram presos. Usem «Pedir ajuda ao professor».',
      requested:'Pedido preparado para guardar. Confirma a gravação no topo da página. Podes também chamar o professor.',
      resolvedNotice:'Registámos que já consegues continuar, segundo a tua indicação.',
      groupResolvedNotice:'Registámos que já conseguem continuar, segundo a vossa indicação.',
      helpedNotice:'Registámos que a pista ajudou, segundo a tua indicação.', groupHelpedNotice:'Registámos que a pista ajudou, segundo a vossa indicação.',
      voiceMissing:'A leitura em voz alta não está disponível neste dispositivo.', voiceError:'Não foi possível ler esta pista.',
      outside:'Local de trabalho declarado.', observation:'O PageCraft só conhece o que foi feito ou declarado nesta página.',
      returned:'De volta ao guião. Regista o que fizeste ou pede uma pista.'},
    en: {title:'One next step', hint:'I need a hint', groupHint:'We need a hint', obstacle:'Where do you need help?',
      groupObstacle:'Where do you need help?', listen:'Listen', next:'Another hint', helped:'This hint helped',
      stuck:'I am still stuck', groupStuck:'We are still stuck', teacher:'Ask the teacher for help', ai:'Clarify with AI',
      settings:'Change the kind of help', alone:'Switch to individual work', pair:'Switch to working together',
      back:'Return to the guide', reading:'I am reading', discussion:'We are reading or discussing', external:'I am working in ',
      groupExternal:'We are working in ', resolved:'I can continue now', groupResolved:'We can continue now',
      wait:'Preparing a hint. You can keep working while you wait.',
      escalate:'Show your teacher what you tried and where you got stuck. Choose “Ask the teacher for help”.',
      groupEscalate:'Show your teacher what you tried and where you got stuck. Choose “Ask the teacher for help”.',
      requested:'Help request prepared for saving. Check that it is saved at the top of the page. You can also call your teacher.',
      resolvedNotice:'We recorded that you say you can continue now.', groupResolvedNotice:'We recorded that you say you can continue now.',
      helpedNotice:'We recorded that you say the hint helped.', groupHelpedNotice:'We recorded that you say the hint helped.',
      voiceMissing:'Reading aloud is not available on this device.', voiceError:'This hint could not be read aloud.',
      outside:'Declared place of work.', observation:'PageCraft only knows what was done or reported on this page.',
      returned:'Back to the guide. Record what you did or ask for a hint.'}
  };
  let config, unitId, language='pt', members=1, locked=false, route='standalone';
  let context={}, history=[], current=null, pending=null, teacherRequest=null, location='pagecraft', notice='';
  const contexts = new Map(), panels = new Map();
  const esc = value => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const id = () => crypto.randomUUID();
  const t = key => COPY[language][members>1 && COPY[language]['group'+key[0].toUpperCase()+key.slice(1)] ? 'group'+key[0].toUpperCase()+key.slice(1) : key];
  const plan = () => config?.units[unitId];
  const obstacle = () => plan()?.obstacles.find(o=>o.id===context.obstacle) || plan()?.obstacles[0];
  const signature = () => JSON.stringify([unitId,context.answer,context.question,context.product,context.level,context.obstacle,context.revision,context.attempt,members,language]);
  const relevant = () => history.filter(h=>h.unit_id===unitId && h.obstacle===obstacle().id && h.product===(context.product||'') && h.language===language);
  function emit(type, payload={}, unit=unitId) {
    if(window.parent===window)return;
    window.parent.postMessage({pagecraft:1,type,unitId:unit,payload:{activity:config.activity,activity_version:config.activity_version,...payload},ts:Date.now()},'*');
  }
  function requestContext() {
    return {activity:config.activity,activity_version:config.activity_version,objective:config.objective,
      stage:plan().title,stage_objective:plan().objective,criteria:plan().criteria,product:context.product||'',
      participant_count:members,language,obstacle:obstacle().id,question:context.question||obstacle().label[language],
      answer:String(context.answer||'').slice(0,1500),level:context.level||'intermediate',
      previous_hints:relevant().slice(-2).map(h=>({text:h.text,usefulness:h.usefulness||'not_reported'})),
      observation:'Respostas e ações PageCraft; trabalho externo apenas declarado.'};
  }
  function update(next) {
    if(!config || !config.units[next.unit_id||unitId])return;
    const before=signature(), oldUnit=unitId;
    unitId=next.unit_id||unitId;
    context={...(oldUnit===unitId?context:contexts.get(unitId)||{}),...next};
    contexts.set(unitId,context);
    if(before!==signature()){pending=null;current=null;notice='';if(window.speechSynthesis)window.speechSynthesis.cancel();}
    mount();render();
  }
  function present(text, source, requestId=null, hintKey=null) {
    const originalContext=requestContext();
    current={hint_id:id(),unit_id:unitId,obstacle:obstacle().id,product:context.product||'',text,source,
      request_id:requestId,hint_key:hintKey,language,signature:signature(),usefulness:null};
    pending=null;notice='';
    if(!render()){current=null;return;}
    history.push(current);
    emit('hint_presented',{hint_id:current.hint_id,hint_key:hintKey,text,source,request_id:requestId,
      obstacle:current.obstacle,product:current.product,language,context:originalContext});
    const action=panels.get(unitId)?.querySelector('.pc-support-action');
    if(action){action.focus({preventScroll:true});action.scrollIntoView({block:'center',behavior:'auto'});}
  }
  function requestHint(unit) {
    if(unit)update({unit_id:unit});
    if(!plan())return;
    pending=null;
    const used=new Set(relevant().filter(h=>h.source==='guide').map(h=>h.hint_key));
    const next=obstacle().hints.find(h=>!used.has(h.id));
    if(!next){notice=t('escalate');render();return;}
    present(next.text[language][members>1?'group':'individual'],'guide',null,next.id);
  }
  function feedback(usefulness) {
    if(!current || !['helped','not_helped'].includes(usefulness) || current.usefulness===usefulness)return;
    current.usefulness=usefulness;
    emit('hint_feedback',{hint_id:current.hint_id,usefulness,obstacle:current.obstacle});
    notice=usefulness==='helped'?t('helpedNotice'):'';render();
  }
  function requestAI() {
    if(pending || route==='standalone' || !plan())return;
    pending={request_id:id(),unit_id:unitId,signature:signature()};
    notice=t('wait');emit('feedback_request',{...requestContext(),request_id:pending.request_id});render();
  }
  function receive(payload) {
    if(!pending || payload.request_id!==pending.request_id || payload.unit_id!==unitId || pending.signature!==signature() || typeof payload.text!=='string')return;
    if(relevant().some(h=>h.text.trim()===payload.text.trim())){pending=null;requestHint();return;}
    present(payload.text.slice(0,400),payload.source||'ai',payload.request_id);
  }
  function help() {
    if(!plan())return;
    teacherRequest ||= {request_id:id()};
    emit('help_needed',{help_request_id:teacherRequest.request_id,note:obstacle().label[language],context:requestContext(),hint_id:current?.hint_id||null});
    notice=t('requested');render();
  }
  function resolved() {
    emit('help_resolved',{help_request_id:teacherRequest?.request_id,note:t('resolvedNotice')});
    teacherRequest=null;notice=t('resolvedNotice');render();
  }
  function setLocation(value) {
    if(!['pagecraft','external','reading','discussion'].includes(value))return;
    if(value==='external'&&!config.externalWork)return;
    location=value;pending=null;
    emit('work_location',{location:value,label:value==='external'?config.externalWork?.[language]:undefined});
    notice=value==='pagecraft'?t('returned'):t('outside');render();
  }
  function listen() {
    if(!current)return;
    if(!window.speechSynthesis || typeof SpeechSynthesisUtterance==='undefined'){notice=t('voiceMissing');render();return;}
    const hintId=current.hint_id, utterance=new SpeechSynthesisUtterance(current.text);
    utterance.lang=language==='pt'?'pt-PT':'en-GB';
    utterance.onerror=()=>{if(current?.hint_id===hintId){notice=t('voiceError');render();}};
    window.speechSynthesis.cancel();window.speechSynthesis.speak(utterance);
    emit('hint_listened',{hint_id:hintId});
  }
  function render() {
    const panel=panels.get(unitId);
    if(!panel || panel.isConnected===false || !plan())return false;
    const button=(action,label,disabled=false)=>'<button type="button" data-support-action="'+action+'" '+(disabled?'disabled':'')+'>'+esc(label)+'</button>';
    const active=document.activeElement?.closest?.('[data-pagecraft-support]')===panel?document.activeElement.dataset.supportAction:null;
    const settings=(!locked?button('mode',members>1?t('alone'):t('pair')):'')+
      '<label>'+esc(t('obstacle'))+'<select data-support-obstacle>'+plan().obstacles.map(o=>'<option value="'+o.id+'" '+(obstacle().id===o.id?'selected':'')+'>'+esc(o.label[language])+'</option>').join('')+'</select></label>';
    panel.innerHTML='<h3>'+esc(t('title'))+'</h3>'+(current?
      '<div class="pc-support-action" tabindex="-1" role="status" aria-live="polite">'+esc(current.text)+'</div>'+
      '<div class="pc-support-controls">'+button('listen',t('listen'))+button('next',t('next'))+'</div>'+
      '<div class="pc-support-controls">'+button('helped',t('helped'))+button('stuck',t('stuck'))+'</div>'+
      '<div class="pc-support-controls">'+button('teacher',t('teacher'))+button('ai',t('ai'),!!pending||route==='standalone')+'</div>'+
      '<details><summary>'+esc(t('settings'))+'</summary>'+settings+'</details>':settings+'<div class="pc-support-controls">'+button('hint',t('hint'))+button('teacher',t('teacher'))+'</div>')+
      '<div class="pc-support-controls">'+(config.externalWork?button('external',location==='pagecraft'?t('external')+config.externalWork[language]:t('back')):'')+
      button('reading',location==='pagecraft'?t(members>1?'discussion':'reading'):t('back'))+(teacherRequest?button('resolved',t('resolved')):'')+'</div>'+
      '<p class="pc-support-notice" role="status">'+esc(notice)+'</p><p class="pc-support-note">'+esc(t('observation'))+'</p>';
    if(active)panel.querySelector('[data-support-action="'+active+'"]')?.focus({preventScroll:true});
    return true;
  }
  function mount() {
    document.querySelectorAll('[data-pagecraft-support]').forEach(panel=>{
      const unit=panel.dataset.pagecraftSupport;
      if(!config.units[unit] || panels.get(unit)===panel)return;
      panels.set(unit,panel);panel.classList.add('pc-support');panel.setAttribute('aria-label',COPY[language].title);
      if(unit!==unitId)panel.innerHTML='<button type="button" data-support-action="hint">'+esc(t('hint'))+'</button>';
      panel.addEventListener('click',event=>{
        const action=event.target.closest('[data-support-action]')?.dataset.supportAction;
        if(!action)return;
        if(unit!==unitId)update({unit_id:unit});
        if(action==='hint'||action==='next')requestHint();
        if(action==='stuck'){feedback('not_helped');requestHint();}
        if(action==='helped')feedback('helped');
        if(action==='teacher')help();
        if(action==='resolved')resolved();
        if(action==='ai')requestAI();
        if(action==='listen')listen();
        if(action==='mode'&&!locked){members=members===1?2:1;pending=null;current=null;render();}
        if(action==='external')setLocation(location==='pagecraft'?'external':'pagecraft');
        if(action==='reading')setLocation(location==='pagecraft'?(members>1?'discussion':'reading'):'pagecraft');
      });
      panel.addEventListener('change',event=>{
        if(!event.target.matches('[data-support-obstacle]'))return;
        update({unit_id:unit,obstacle:event.target.value});pending=null;current=null;render();
      });
      if(unit===unitId)render();
    });
  }
  function restore(events) {
    history=[];current=null;pending=null;teacherRequest=null;
    for(const event of events||[]){
      const p=event.payload||{};
      if(p.activity && p.activity!==config.activity)continue;
      if(event.type==='hint_presented' && p.activity_version===config.activity_version)history.push({...p,unit_id:event.unit_id||event.unitId,usefulness:null});
      if(event.type==='hint_feedback'){const hint=history.find(h=>h.hint_id===p.hint_id);if(hint)hint.usefulness=p.usefulness;}
      if(event.type==='work_location')location=p.location;
      if(event.type==='help_needed')teacherRequest={request_id:p.help_request_id};
      if(event.type==='help_resolved')teacherRequest=null;
    }
    render();
  }
  window.addEventListener('message',event=>{
    if(event.source!==window.parent || event.data?.pagecraft!==1 || !config)return;
    const {type,payload:p={}}=event.data;
    if(type==='ai_feedback')receive(p);
    if(type==='learning_restore')restore(p.events);
    if(type==='support_teacher_requested'){teacherRequest={request_id:p.help_request_id};render();}
    if(type==='learning_preferences'||type==='work_group_preferences'){
      const before=signature();
      if(p.route)route=p.route;
      if(p.route==='studio'&&Number.isInteger(p.participant_count)){members=Math.max(1,p.participant_count);locked=true;}
      if(config.languages.includes(p.language))language=p.language;
      if(p.level)context.level=p.level;
      if(before!==signature()){pending=null;current=null;}
      render();
    }
  });
  // Ações registadas pela atividade e edições invalidam respostas antigas antes da confirmação.
  document.addEventListener('pagecraft:activity-event',event=>{
    if(!config)return;
    const {type,unitId:unit,payload:p={}}=event.detail;
    if(type==='unit_started')update({unit_id:unit});
    if(type==='level_changed')update({unit_id:unit||unitId,level:p.level});
    if(type==='assessment_result'||type==='attempt'){
      const detail=typeof p.detail==='object'?p.detail:null;
      update({unit_id:unit||unitId,answer:detail?.value??p.detail??p.result??'',question:detail?.note||'',revision:id()});
    }
  });
  document.addEventListener('input',event=>{
    if(!config || event.target.closest('[data-pagecraft-support]'))return;
    const container=event.target.closest('[data-unit],section[id]');
    const unit=container?.dataset.unit||container?.id;
    if(config.units[unit])update({unit_id:unit,revision:id()});
  });
  window.PageCraftSupport={configure(value){config=value;unitId=Object.keys(config.units)[0];context={};mount();render();
      if(typeof MutationObserver!=='undefined')new MutationObserver(()=>{mount();}).observe(document.body,{childList:true,subtree:true});
      document.dispatchEvent(new CustomEvent('pagecraft-support-ready'));},
    update,restore,receive,requestHint,requestAI,feedback,help,resolved,setLocation,listen,
    version:()=>config?.activity_version,currentHintId:()=>current?.hint_id||null};
})();
