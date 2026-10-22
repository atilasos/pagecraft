/* Apoio do piloto. Injetado no HTML para continuar self-contained. */
const SUPPORT_VERSION = 'canva-autonomia-2026-10-22-v1';
const OBSTACLES = {
  instruction: 'Perceber a instrução', command: 'Encontrar um comando',
  ideas: 'Organizar ideias', review: 'Rever o trabalho', save: 'Guardar o produto',
};
const STAGE_HINTS = [
  ['Aponta a quem se destina o produto. Que formato ajuda esses colegas a perceber os dois animais?',
   'Compara só dois formatos. Qual permite mostrar uma imagem e os factos de cada animal?'],
  ['Aponta no esboço onde começa cada animal. Há espaço entre as duas zonas?',
   'Usa dois retângulos em papel, um por animal. Distribui os factos antes de mexer no Canva.'],
  ['Abre o passo ilustrado «Começar no Canva» desta etapa. Compara o teu ecrã com a captura.',
   'Confirma primeiro se estás na página inicial ou dentro do editor. Mostra essa diferença ao professor se o passo não corresponder.'],
  ['Confere só um animal com o Word. Qual é o primeiro facto que ainda falta no produto?',
   'Aponta cada facto no Word e depois no produto. Marca no papel o que já encontraste, sem alterar as frases.'],
  ['Aponta uma parte do produto e pede uma sugestão que comece por uma ação.',
   'Experimenta perguntar: «Que texto custa a ler nesta parte?» Regista a alteração que queres experimentar.'],
  ['Afasta-te um pouco do ecrã. Consegues ler a mensagem principal? Se não, aumenta primeiro esse texto.',
   'Mostra só a zona que mudaste. Compara com a sugestão recebida e explica se agora ajuda os colegas a ler.'],
  ['Escolhe uma decisão do produto. Aponta um exemplo enquanto explicas por que a tomaste.',
   'Ensaiem uma parte de cada vez: produto, decisão, melhoria e cooperação. Comecem pela parte que ainda custa explicar.'],
  ['Escolhe um critério e lembra um momento em que participaste. Conta o que fizeste nesse momento.',
   'Completa com um exemplo teu: «Eu fiz… e da próxima vez quero…». Podes pedir que leiam a pergunta.'],
];
const CATEGORY_HINTS = {
  command: ['Abre o passo ilustrado desta etapa. Procura primeiro o botão assinalado na captura.',
    'Compara o nome e o ícone da captura com o teu ecrã. Se forem diferentes, chama o professor e aponta onde deixaram de corresponder.'],
  ideas: ['Aponta no Word uma ideia que queres comunicar. Em que zona do produto vai ficar?',
    'Faz duas organizações pequenas em papel. Escolhe a que ajuda os colegas a encontrar os dois animais.'],
  review: ['Afasta-te um pouco do ecrã. Consegues ler a mensagem principal? Se não, aumenta primeiro esse texto.',
    'Aponta o texto que mais custa a ler. Experimenta mudar só o tamanho e compara antes de continuar.'],
  save: ['Abre o passo ilustrado «Guardar» do guião. Confirma o formato do teu produto antes de seguir a captura.',
    'Confirma onde estás: ainda no editor ou já com uma cópia aberta? Mostra essa etapa ao professor se não encontrares a cópia.'],
};
const GROUP_COPY = [
  ['Aponta', 'Apontem'], ['Consegues', 'Conseguem'], ['consegues', 'conseguem'],
  ['Afasta-te', 'Afastem-se'], ['aumenta', 'aumentem'], ['Abre', 'Abram'],
  ['Compara', 'Comparem'], ['Confirma', 'Confirmem'], ['Mostra', 'Mostrem'],
  ['Confere', 'Confiram'], ['Usa', 'Usem'], ['Distribui', 'Distribuam'],
  ['Escolhe', 'Escolham'], ['Regista', 'Registem'], ['Experimenta', 'Experimentem'],
  ['Faz', 'Façam'], ['Diz', 'Digam'], ['Conta', 'Contem'], ['Completa', 'Completem'],
  ['chama', 'chamem'], ['procura', 'procurem'], ['Procura', 'Procurem'],
  ['pede', 'peçam'], ['Marca', 'Marquem'], ['explica', 'expliquem'], ['lembra', 'lembrem'],
  ['queres', 'querem'], ['precisas', 'precisam'], ['Podes', 'Podem'], ['podes', 'podem'], ['participaste', 'participaram'], ['vais', 'vão'], ['teu', 'vosso'], ['tua', 'vossa'],
  ['estás', 'estão'], ['tomaste', 'tomaram'], ['mudaste', 'mudaram'],
];
let supportMode = 1, supportModeLocked = false, supportRoute = 'standalone';
let obstacle = 'instruction', supportHistory = [], currentHint = null, pendingHint = null;
let supportLocation = 'pagecraft', pendingTeacher = null, supportNotice = '';
const revisionHints = new Map();
function supportText(text) {
  if (supportMode === 1 || state.step === 7) return text.replace('Ensaiem', 'Ensaia').replace('Comecem', 'Começa');
  // Trocas por palavras completas para não alterar outras palavras ou citações.
  return GROUP_COPY.reduce((result, [single, group]) => result.replace(new RegExp('(?<![\\p{L}])'+single+'(?![\\p{L}])', 'gu'), group), text);
}
function attemptSignature() {
  return JSON.stringify([state.step, state.level, supportMode, state.values.product,
    fieldsFor(state.step).map(f => [f[0], state.values[f[0]] || '', state.invalid.includes(f[0])])]);
}
function relevantHistory() {
  return supportHistory.filter(h => h.unit_id === 'u'+(state.step+1) && h.obstacle === obstacle && h.product === (state.values.product || ''));
}
function supportContext() {
  const unit = DATA.units[state.step];
  const criteriaIds = [['plano'], ['plano','clareza'], ['plano'], ['conteudo'], ['clareza','revisao'], ['clareza','revisao'], ['processo'], ['processo']][state.step];
  return {
    activity: SLUG, activity_version: SUPPORT_VERSION, objective: 'Comunicar dois animais, dez factos e duas ilustrações aos colegas.',
    stage: unit.title, stage_objective: unit.differentiation[state.level === 'intermediate' ? 'standard' : state.level],
    product: state.values.product || 'a escolher', criteria: DATA.criteria.filter(c => criteriaIds.includes(c.id)).map(c => c.pt),
    participant_count: state.step === 7 ? 1 : supportMode, obstacle, question: OBSTACLES[obstacle],
    answer: fieldsFor(state.step).map(f => f[2]+': '+(state.values[f[0]]||'sem resposta').slice(0,80)).join('\n').slice(0,650),
    previous_hints: relevantHistory().slice(-2).map(h => ({text:h.text.slice(0,200), usefulness:h.usefulness || 'not_reported'})),
    observation: 'Respostas PageCraft e declarações do grupo; produto Canva não observado.',
  };
}
function supportEvent(type, extra = {}) {
  emit(type, {activity:SLUG, activity_version:SUPPORT_VERSION, ...extra});
}
function showHint(text, source, requestId = null) {
  pendingHint = null;
  currentHint = {hint_id:crypto.randomUUID(), unit_id:'u'+(state.step+1), obstacle,
    product:state.values.product||'', text, source, request_id:requestId,
    signature:attemptSignature(), usefulness:null};
  const context = supportContext();
  supportHistory.push(currentHint);
  supportEvent('hint_presented', {hint_id:currentHint.hint_id, text, source, request_id:requestId,
    obstacle, product:currentHint.product, context});
  supportNotice = '';
  renderSupport();
}
function hintFeedback(usefulness) {
  if (!currentHint || currentHint.usefulness === usefulness) return;
  currentHint.usefulness = usefulness;
  supportEvent('hint_feedback', {hint_id:currentHint.hint_id, usefulness, obstacle});
  supportNotice = usefulness === 'helped' ? 'Registámos que a pista ajudou, segundo a '+(supportMode===1?'tua':'vossa')+' indicação.' : 'Registámos que esta pista não ajudou.';
}
function nextHint() {
  pendingHint = null;
  const seen = relevantHistory().filter(h => h.source === 'guide').length;
  if (seen >= 2) {
    supportNotice = supportMode === 1 ? 'Mostra ao professor o que tentaste e onde ficaste preso. Usa «Pedir ajuda ao professor».' : 'Mostrem ao professor o que tentaram e onde ficaram presos. Usem «Pedir ajuda ao professor».';
    renderSupport();
    return;
  }
  const text = obstacle === 'instruction' ? STAGE_HINTS[state.step][seen] : CATEGORY_HINTS[obstacle][seen];
  showHint(supportText(text), 'guide');
}
function requestTeacherHelp() {
  pendingTeacher ||= {request_id:crypto.randomUUID()};
  supportEvent('help_needed', {help_request_id:pendingTeacher.request_id, note:(supportMode===1?'Pedido individual':'Pedido do grupo')+': '+OBSTACLES[obstacle],
    obstacle, context:supportContext(), hint_id:currentHint?.hint_id || null});
  supportNotice = 'Pedido preparado para guardar. Confirma a gravação no topo da página. Podes também chamar o professor.';
  renderSupport();
}
function requestAIHint() {
  if (pendingHint || supportRoute === 'standalone') return;
  flush();
  const request_id = crypto.randomUUID();
  pendingHint = {request_id, signature:attemptSignature(), unit_id:'u'+(state.step+1)};
  supportNotice = 'A preparar uma pista. Podes continuar o trabalho enquanto esperas.';
  emit('feedback_request', { ...supportContext(), request_id });
  renderSupport();
}
function receiveHint(payload) {
  if (!pendingHint || payload.request_id !== pendingHint.request_id || payload.unit_id !== pendingHint.unit_id ||
      pendingHint.signature !== attemptSignature()) return;
  if (typeof payload.text !== 'string') return;
  if(relevantHistory().some(h=>h.text.trim()===payload.text.trim())){pendingHint=null;nextHint();return;}
  showHint(payload.text.slice(0,400), payload.source || 'ai', payload.request_id);
}
function invalidateSupport() {
  pendingHint = null;
  if (currentHint && currentHint.signature !== attemptSignature()) {
    currentHint = null;
    supportNotice = '';
  }
  renderSupport();
}
function setWorkLocation(location) {
  supportLocation = location;
  pendingHint = null;
  supportEvent('work_location', {location});
  supportNotice = location === 'pagecraft' ? 'De volta ao guião. Regista o que fizeste ou pede uma pista.' : 'Trabalho fora do guião indicado. Podes regressar quando terminares esta parte.';
  renderSupport();
}
function listenHint() {
  if (!currentHint) return;
  if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
    supportNotice = 'A leitura em voz alta não está disponível neste dispositivo.';
    renderSupport();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(currentHint.text);
  utterance.lang = 'pt-PT';
  utterance.onerror = () => { supportNotice = 'Não foi possível ler esta pista neste dispositivo.'; renderSupport(); };
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
  supportEvent('hint_listened', {hint_id:currentHint.hint_id});
}
function renderSupport() {
  const panel = $('context-support');
  if (!panel) return;
  if (currentHint && currentHint.signature !== attemptSignature()) currentHint = null;
  const plural = supportMode > 1;
  const stuck = plural ? 'Ainda estamos presos' : 'Ainda estou preso';
  const outside = supportLocation !== 'pagecraft';
  const focused = document.activeElement?.closest?.('#context-support') ? document.activeElement.dataset.support || document.activeElement.id : null;
  panel.innerHTML = '<h3>Um próximo passo</h3>'+
    '<div class="support-controls"><button data-support="mode" '+(supportModeLocked?'disabled':'')+'>'+(plural?'Trabalho a pares ou em grupo':'Trabalho individual')+'</button></div>'+
    '<label for="support-obstacle">'+(plural?'Onde estamos presos?':'Onde estou preso?')+'</label>'+
    '<select id="support-obstacle">'+Object.entries(OBSTACLES).map(([key,label])=>'<option value="'+key+'" '+(key===obstacle?'selected':'')+'>'+label+'</option>').join('')+'</select>'+
    '<div class="support-controls"><button data-support="first">'+(plural?'Precisamos de uma pista':'Preciso de uma pista')+'</button>'+
    '<button data-support="location">'+(outside?'Regressar ao guião':plural?'Estamos a trabalhar no Canva':'Estou a trabalhar no Canva')+'</button>'+
    '<button data-support="reading">'+(plural?'Estamos a ler ou conversar':'Estou a ler')+'</button></div>'+
    '<div class="hint-action" role="status" aria-live="polite">'+(currentHint?esc(currentHint.text):'')+'</div>'+
    (currentHint?'<div class="support-controls"><button data-support="listen">Ouvir</button><button data-support="helped" aria-pressed="'+(currentHint.usefulness==='helped')+'">Esta pista ajudou</button><button data-support="next">Outra pista</button><button data-support="stuck">'+stuck+'</button></div>':'')+
    '<div class="support-controls"><button data-support="teacher">Pedir ajuda ao professor</button>'+
    (currentHint?'<button data-support="ai" '+(pendingHint||supportRoute==='standalone'?'disabled':'')+'>Esclarecer com IA</button>':'')+
    (pendingTeacher?'<button data-support="resolved">'+(plural?'Já conseguimos continuar':'Já consigo continuar')+'</button>':'')+'</div>'+
    '<p class="micro" role="status">'+esc(supportNotice)+'</p><p class="micro">'+(outside?'Local de trabalho declarado. ':'')+'O PageCraft não vê o produto no Canva. Ouvir só começa quando carregas no botão.</p>';
  if(focused) { const target=focused==='support-obstacle'?$('support-obstacle'):panel.querySelector('[data-support="'+focused+'"]'); target?.focus({preventScroll:true}); }
  $('support-obstacle').onchange = e => { obstacle=e.target.value; currentHint=null; pendingHint=null; supportNotice=''; renderSupport(); };
}
// Conserva as interações do guião e muda apenas o contrato de apoio neste piloto.
const renderLesson = render;
render = function() {
  renderLesson();
  const panel = document.createElement('aside');
  panel.id='context-support'; panel.className='context-support'; panel.setAttribute('aria-label','Ajuda para esta etapa');
  $('pagecraft-feedback').remove();
  ($('sheet').querySelector('.action') || $('support-panel')).after(panel);
  renderSupport();
};
fieldEvent = function(key) {
  const f=fieldMap[key]; if(!f)return;
  dirty.delete(key);
  PageCraftBridge.assessment('u'+(f[1]+1),supportMode===1?'Declaração individual':'Declaração do grupo',{activity:SLUG,activity_version:SUPPORT_VERSION,
    field:key,value:state.values[key]||'',confirmed:!state.invalid.includes(key),note:f[2],
    after_hint_id:revisionHints.get(key)||currentHint?.hint_id||null});
  revisionHints.delete(key);
};
const editLesson = inputValue;
inputValue = function(...args) {
  if(currentHint && !revisionHints.has(args[0]))revisionHints.set(args[0],currentHint.hint_id);
  editLesson(...args); invalidateSupport();
};
const goLesson = go;
go = function(step) {
  pendingHint=null; currentHint=null; supportNotice='';
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  goLesson(step);
};
const levelLesson = setLevel;
setLevel = function(...args) {pendingHint=null;levelLesson(...args);invalidateSupport();};
const restoreLesson = restoreEvents;
restoreEvents = function(events) {
  supportHistory=[]; currentHint=null; pendingHint=null; pendingTeacher=null;
  for (const event of events || []) {
    const p=event.payload||{};
    if(p.activity && p.activity!==SLUG)continue;
    if(event.type==='hint_presented') supportHistory.push({hint_id:p.hint_id,unit_id:event.unit_id||event.unitId,
      obstacle:p.obstacle,product:p.product,text:p.text,source:p.source,usefulness:null});
    if(event.type==='hint_feedback') { const h=supportHistory.find(h=>h.hint_id===p.hint_id); if(h)h.usefulness=p.usefulness; }
    if(event.type==='work_location')supportLocation=p.location;
    if(event.type==='help_needed')pendingTeacher={request_id:p.help_request_id};
    if(event.type==='help_resolved')pendingTeacher=null;
  }
  restoreLesson(events);
  renderSupport();
};
window.addEventListener('message', e => {
  if(e.source!==window.parent || e.data?.pagecraft!==1)return;
  const p=e.data.payload||{};
  if(e.data.type==='support_teacher_requested'){pendingTeacher={request_id:p.help_request_id};renderSupport();}
  if(['learning_preferences','work_group_preferences'].includes(e.data.type)) {
    if(p.route)supportRoute=p.route;
    if(p.route==='studio' && Number.isInteger(p.participant_count)) {
      supportMode=Math.max(1,p.participant_count); supportModeLocked=true; invalidateSupport();
    }
    renderSupport();
  }
});
document.addEventListener('click', e => {
  const action=e.target.closest('[data-support]')?.dataset.support;
  if(!action)return;
  if(action==='first'||action==='next')nextHint();
  if(action==='stuck'){hintFeedback('not_helped');nextHint();}
  if(action==='helped'){hintFeedback('helped');renderSupport();}
  if(action==='listen')listenHint();
  if(action==='teacher')requestTeacherHelp();
  if(action==='resolved'){const help_request_id=pendingTeacher?.request_id;pendingTeacher=null;supportEvent('help_resolved',{help_request_id,note:'O grupo declara que já consegue continuar.'});supportNotice='Registámos que já conseguem continuar, segundo a vossa indicação.';renderSupport();}
  if(action==='ai')requestAIHint();
  if(action==='location')setWorkLocation(supportLocation==='pagecraft'?'canva':'pagecraft');
  if(action==='reading')setWorkLocation(pluralMode()?'discussion':'reading');
  if(action==='mode'&&!supportModeLocked){supportMode=supportMode===1?2:1;invalidateSupport();}
});
function pluralMode(){return supportMode>1;}
