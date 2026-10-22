/* node --test tests/js/activity_support.test.cjs */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm'), fs=require('node:fs'), crypto=require('node:crypto');
const examples=JSON.parse(fs.readFileSync('tests/fixtures/support-examples.json','utf8'));
function activity(spec=examples[0]){
  const config={activity:spec.slug,activity_version:spec.support.version,objective:spec.objectives.join('; '),
    age_range:spec.ageRange,topic:spec.topic,automatic_after_failures:spec.support.automaticAfterFailures??3,
    languages:spec.support.languages||['pt'],externalWork:spec.support.externalWork||null,
    units:Object.fromEntries(spec.units.map((u,i)=>['u'+(i+1),{...u.support,title:u.summary}]))};
  const box=vm.createContext({assert,crypto,console,config,TextEncoder});
  vm.runInContext(`
    const emitted=[],messages=[],documentEvents={};let spoken=0;
    const panel={dataset:{pagecraftSupport:'u1'},innerHTML:'',classList:{add(){}},setAttribute(){},addEventListener(){},
      querySelector(){return {focus(){},scrollIntoView(){}}}};
    const document={activeElement:null,body:{},querySelectorAll(){return [panel]},
      addEventListener(type,fn){(documentEvents[type]||=[]).push(fn)},
      dispatchEvent(event){for(const fn of documentEvents[event.type]||[])fn(event)}};
    const window={parent:{postMessage(data){emitted.push(data)}},speechSynthesis:{cancel(){},speak(){spoken++}},
      addEventListener(type,fn){if(type==='message')messages.push(fn)}};
    const CustomEvent=class {constructor(type,opts={}){this.type=type;this.detail=opts.detail}};
    const SpeechSynthesisUtterance=class {constructor(text){this.text=text}};
    function host(type,payload,source=window.parent){messages.forEach(fn=>fn({source,data:{pagecraft:1,type,payload}}))}
  `,box);
  vm.runInContext(fs.readFileSync('server/pipeline/prompts/activity-support.js','utf8'),box);
  vm.runInContext(`const support=window.PageCraftSupport;support.configure(config);support.update({unit_id:'u1',answer:'Uma tentativa',level:'intermediate'});`,box);
  return code=>vm.runInContext(code,box);
}
for(const spec of examples)test(spec.slug+': conteúdo próprio, duas abordagens e escalada',()=>{
  const run=activity(spec);
  run(`support.requestHint();const first=emitted.at(-1);assert.equal(first.type,'hint_presented');assert.equal(first.payload.context.stage_objective,config.units.u1.objective);assert.ok(panel.innerHTML.includes(first.payload.text));support.feedback('not_helped');support.requestHint();assert.notEqual(emitted.at(-1).payload.text,first.payload.text);const count=emitted.length;support.requestHint();assert.equal(emitted.length,count);assert.match(panel.innerHTML,/professor/);assert.equal(spoken,0);support.listen();assert.equal(spoken,1);`);
});
test('a IA recebe objetivo, produto, critérios e utilidade das pistas anteriores',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});support.requestHint();support.feedback('not_helped');support.update({product:'duas barras'});support.requestAI();const p=emitted.at(-1).payload;assert.equal(p.product,'duas barras');assert.equal(p.previous_hints.length,0);support.requestHint();support.feedback('not_helped');support.requestAI();assert.equal(emitted.at(-1).payload.previous_hints[0].usefulness,'not_helped');assert.ok(emitted.at(-1).payload.criteria.length);`);
});
test('mudanças de tentativa, produto, nível, idioma e composição rejeitam a pista antiga',()=>{
  for(const edit of ["support.update({answer:'Outra tentativa'})","support.update({product:'novo'})","support.update({level:'challenge'})","support.update({revision:'nova'})","host('learning_preferences',{language:'en'})","host('work_group_preferences',{route:'studio',participant_count:2})"]){
    const run=activity();
    run(`host('learning_preferences',{route:'permanent'});support.requestAI();const id=emitted.at(-1).payload.request_id;${edit};support.receive({request_id:id,unit_id:'u1',text:'Antiga'});assert.equal(emitted.filter(e=>e.type==='hint_presented').length,0);`);
  }
});
test('apenas o pedido atual, recebido do anfitrião, pode apresentar ajuda',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});support.requestAI();const id=emitted.at(-1).payload.request_id;host('ai_feedback',{request_id:id,unit_id:'u1',text:'Outra origem'},{});assert.equal(support.currentHintId(),null);host('ai_feedback',{request_id:'outro',unit_id:'u1',text:'Outro pedido'});assert.equal(support.currentHintId(),null);host('ai_feedback',{request_id:id,unit_id:'u1',text:'Atual'});assert.equal(emitted.at(-1).payload.text,'Atual');`);
});
test('repetição literal do modelo usa a próxima pista do plano',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});support.requestHint();const text=emitted.at(-1).payload.text;support.requestAI();const id=emitted.at(-1).payload.request_id;support.receive({request_id:id,unit_id:'u1',text});assert.notEqual(emitted.at(-1).payload.text,text);assert.equal(emitted.at(-1).payload.source,'guide');`);
});
test('língua e tratamento são conteúdo do plano, sem trocar verbos automaticamente',()=>{
  const run=activity();
  run(`host('work_group_preferences',{route:'studio',participant_count:2});host('learning_preferences',{language:'en'});support.requestHint();assert.equal(emitted.at(-1).payload.text,config.units.u1.obstacles[0].hints[0].text.en.group);assert.equal(emitted.at(-1).payload.context.participant_count,2);assert.equal(emitted.at(-1).payload.context.language,'en');`);
});
test('trabalho externo e resolução são declarados explicitamente',()=>{
  const run=activity(examples[2]);
  run(`support.help();const request=emitted.at(-1).payload.help_request_id;support.requestHint();assert.ok(panel.innerHTML.includes('Já consigo continuar'));support.setLocation('external');assert.equal(emitted.at(-1).payload.label,'Scratch');support.setLocation('pagecraft');support.resolved();assert.equal(emitted.at(-1).payload.help_request_id,request);`);
});
test('restaurar o histórico conserva a progressão sem reapresentar uma pista',()=>{
  const run=activity();
  run(`support.requestHint();const first=emitted.at(-1);const count=emitted.length;support.restore([{type:first.type,unitId:first.unitId,payload:first.payload}]);assert.equal(emitted.length,count);support.requestHint();assert.notEqual(emitted.at(-1).payload.hint_key,first.payload.hint_key);`);
});
test('alterar uma resposta invalida a ajuda sem chamar o modelo',()=>{
  const run=activity();
  run(`support.requestHint();document.dispatchEvent({type:'input',target:{closest(selector){return selector==='[data-pagecraft-support]'?null:{dataset:{unit:'u1'}}}}});assert.equal(support.currentHintId(),null);assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);`);
});
test('o texto de feedback local não se torna resposta do aluno',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});document.dispatchEvent(new CustomEvent('pagecraft:activity-event',{detail:{type:'attempt',unitId:'u1',payload:{correct:false,detail:'Experimenta comparar as barras'}}}));support.requestAI();assert.equal(emitted.at(-1).payload.answer,'Uma tentativa');`);
});

test('três tentativas confirmadas distintas pedem IA contextual nos dois percursos',()=>{
  for(const route of ['studio','permanent']){
    const run=activity();
    run(`host('learning_preferences',{route:'${route}'});
      for(const answer of ['A','B'])support.recordAttempt({answer,correct:false});
      assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);
      support.recordAttempt({answer:'C',correct:false});
      const request=emitted.find(e=>e.type==='feedback_request').payload;
      assert.equal(request.trigger,'consecutive_incorrect_attempts');
      assert.equal(request.age_range,'8-9 anos');assert.equal(request.observed_difficulties.length,3);
      assert.deepEqual(request.observed_difficulties.map(a=>a.answer),['A','B','C']);
      assert.equal(request.activity_characteristics.topic,config.topic);
      assert.equal(emitted.filter(e=>e.type==='support_modal').length,0);
      support.receive({request_id:request.request_id,unit_id:'u1',text:'Aponta o início das duas barras.'});
      assert.equal(emitted.at(-1).type,'support_modal');assert.equal(emitted.at(-1).payload.action,'open');
      assert.equal(emitted.filter(e=>e.type==='hint_presented').at(-1).payload.presentation,'modal');
      assert.equal(spoken,0);
      host('support_modal_action',{hint_id:support.currentHintId(),action:'listen'});assert.equal(spoken,1);
      host('support_modal_action',{hint_id:support.currentHintId(),action:'continue'});
      assert.equal(emitted.filter(e=>e.type==='hint_acknowledged').length,1);
      assert.equal(emitted.filter(e=>e.type==='hint_feedback').length,0);
      assert.equal(emitted.at(-1).payload.action,'close');`);
  }
});
test('limiar configurável, acerto, tarefa nova e cliques repetidos reiniciam ou conservam a contagem',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    support.recordAttempt({correct:false,answer:'A',attempt_id:'one'});
    support.recordAttempt({correct:false,answer:'A',attempt_id:'two'});
    support.recordAttempt({correct:false,answer:'B',attempt_id:'one'});
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);
    support.recordAttempt({correct:true,answer:'C'});
    support.recordAttempt({correct:false,answer:'D'});
    support.update({task_id:'segunda'});
    support.recordAttempt({correct:false,answer:'E'});
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);
    support.recordAttempt({correct:false,answer:'F'});
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,1);`);
});
test('declarações, autoavaliação, edições e trabalho externo não ativam IA automática',()=>{
  const run=activity(examples[2]);
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    for(const value of ['A','B','C']){
      document.dispatchEvent(new CustomEvent('pagecraft:activity-event',{detail:{type:'assessment_result',unitId:'u1',payload:{result:0,detail:{value}}}}));
      support.update({answer:value,revision:value});
    }
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);
    support.setLocation('external');
    for(const answer of ['D','E','F'])support.recordAttempt({correct:false,answer});
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);
    support.setLocation('pagecraft');config.automatic_after_failures=0;
    for(const answer of ['G','H','I'])support.recordAttempt({correct:false,answer});
    assert.equal(emitted.filter(e=>e.type==='feedback_request').length,0);`);
});
test('o evento attempt usa resposta observada e nunca a mensagem de feedback como tentativa',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});
    for(const value of ['A','B','C'])document.dispatchEvent(new CustomEvent('pagecraft:activity-event',{
      detail:{type:'attempt',unitId:'u1',payload:{correct:false,detail:{value,question:'Qual barra?'}}}}));
    const p=emitted.find(e=>e.type==='feedback_request').payload;
    assert.equal(p.answer,'C');assert.equal(p.question,'Qual barra?');
    assert.deepEqual(p.observed_difficulties.map(a=>a.answer),['A','B','C']);`);
});
test('ajuda automática atrasada é ignorada e um modal aberto fecha quando muda a tentativa',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    support.recordAttempt({answer:'A',correct:false});support.recordAttempt({answer:'B',correct:false});
    const req=emitted.find(e=>e.type==='feedback_request').payload.request_id;
    support.update({answer:'C'});support.receive({request_id:req,unit_id:'u1',text:'Antiga'});
    assert.equal(emitted.filter(e=>e.type==='support_modal').length,0);
    support.recordAttempt({answer:'D',correct:false});support.recordAttempt({answer:'E',correct:false});
    const req2=emitted.filter(e=>e.type==='feedback_request').at(-1).payload.request_id;
    support.receive({request_id:req2,unit_id:'u1',text:'Atual'});
    support.update({answer:'F'});assert.equal(emitted.at(-1).payload.action,'close');
    host('support_modal_action',{hint_id:'antiga',action:'teacher'});
    assert.equal(emitted.filter(e=>e.type==='help_needed').length,0);`);
});
test('falha do fornecedor usa pistas revistas no modal e permite outra abordagem e professor',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    support.recordAttempt({answer:'A',correct:false});support.recordAttempt({answer:'B',correct:false});
    const req=emitted.find(e=>e.type==='feedback_request').payload.request_id;
    support.receive({request_id:req,unit_id:'u1',source:'unavailable',text:'Falha técnica'});
    assert.equal(emitted.filter(e=>e.type==='hint_presented').at(-1).payload.source,'guide');
    const first=support.currentHintId();
    host('support_modal_action',{hint_id:first,action:'stuck'});
    assert.equal(emitted.filter(e=>e.type==='hint_feedback').at(-1).payload.usefulness,'not_helped');
    assert.notEqual(support.currentHintId(),first);assert.equal(emitted.at(-1).payload.action,'open');
    host('support_modal_action',{hint_id:support.currentHintId(),action:'teacher'});
    assert.equal(emitted.at(-1).type,'help_needed');`);
});


test('contexto extenso continua a caber no contrato de eventos sem perder idade e correlação',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});
    config.objective='🟩'.repeat(700);config.topic='Tema'.repeat(100);
    config.units.u1.criteria=Array(4).fill('🟩'.repeat(250));
    for(let i=0;i<3;i++)support.recordAttempt({correct:false,answer:'🟩'.repeat(1500)+i});
    const p=emitted.find(e=>e.type==='feedback_request').payload;
    assert.equal(p.context_truncated,true);assert.equal(p.age_range,'8-9 anos');
    assert.ok(new TextEncoder().encode(JSON.stringify(p)).length<9000);
    assert.equal(p.observed_difficulties.length,3);assert.ok(p.request_id);
    support.receive({request_id:p.request_id,unit_id:'u1',text:'🟩'.repeat(200)});
    const hint=emitted.filter(e=>e.type==='hint_presented').at(-1).payload;
    assert.ok(new TextEncoder().encode(JSON.stringify(hint)).length<12000);`);
});


test('pedir outra pista no modal não declara automaticamente falta de utilidade',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    support.recordAttempt({answer:'A',correct:false});support.recordAttempt({answer:'B',correct:false});
    const req=emitted.find(e=>e.type==='feedback_request').payload.request_id;
    support.receive({request_id:req,unit_id:'u1',text:'Compara as partes.'});
    const first=support.currentHintId();host('support_modal_action',{hint_id:first,action:'next'});
    assert.equal(emitted.filter(e=>e.type==='hint_feedback').length,0);
    assert.notEqual(support.currentHintId(),first);`);
});


test('indisponibilidade da voz é comunicada dentro do modal sem o fechar',()=>{
  const run=activity();
  run(`host('learning_preferences',{route:'permanent'});config.automatic_after_failures=2;
    support.recordAttempt({answer:'A',correct:false});support.recordAttempt({answer:'B',correct:false});
    const req=emitted.find(e=>e.type==='feedback_request').payload.request_id;
    support.receive({request_id:req,unit_id:'u1',text:'Compara as partes.'});
    window.speechSynthesis=null;
    host('support_modal_action',{hint_id:support.currentHintId(),action:'listen'});
    assert.equal(emitted.at(-1).payload.action,'notice');
    assert.match(emitted.at(-1).payload.text,/não está disponível/);
    assert.equal(emitted.filter(e=>e.type==='hint_acknowledged').length,0);`);
});
