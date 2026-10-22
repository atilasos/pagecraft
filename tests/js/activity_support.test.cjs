/* node --test tests/js/activity_support.test.cjs */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm'), fs=require('node:fs'), crypto=require('node:crypto');
const examples=JSON.parse(fs.readFileSync('tests/fixtures/support-examples.json','utf8'));
function activity(spec=examples[0]){
  const config={activity:spec.slug,activity_version:spec.support.version,objective:spec.objectives.join('; '),
    languages:spec.support.languages||['pt'],externalWork:spec.support.externalWork||null,
    units:Object.fromEntries(spec.units.map((u,i)=>['u'+(i+1),{...u.support,title:u.summary}]))};
  const box=vm.createContext({assert,crypto,console,config});
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
