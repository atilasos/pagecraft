/* node --test tests/js/canva_support.test.cjs */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const crypto = require('node:crypto');
function pilot() {
  const box = vm.createContext({console, crypto, assert});
  vm.runInContext(`
    const events=[];let spoken=0;
    const window={parent:{},addEventListener(){},speechSynthesis:{}};
    const document={addEventListener(){},createElement(){return {setAttribute(){}}}};
    const SpeechSynthesisUtterance=function(text){this.text=text};
    const speechSynthesis={cancel(){},speak(){spoken++}};
    const SLUG='pilot';const DATA={units:Array.from({length:8},(_,i)=>({title:'Etapa '+i,differentiation:{standard:'Organiza as ideias'}})),criteria:[{id:'plano',pt:'Plano partilhado'}]};
    const state={step:0,level:'intermediate',values:{product:'poster',reason:'Para a turma'},invalid:[]};
    const fields=[['product',0,'Produto'],['reason',0,'Porquê']];
    const fieldMap=Object.fromEntries(fields.map(f=>[f[0],f]));
    const fieldsFor=step=>fields.filter(f=>f[1]===step);
    const emit=(type,payload={},unitId='u'+(state.step+1))=>events.push({type,payload,unitId});
    const PageCraftBridge={assessment:(unitId,result,detail)=>emit('assessment_result',{result,detail},unitId)};
    const dirty=new Set();
    const $=()=>null;const esc=String;const flush=()=>{};
    let setLevel=level=>state.level=level,render=()=>{},inputValue=(k,v,commit)=>{state.values[k]=v;if(commit)fieldEvent(k)},go=step=>state.step=step,restoreEvents=()=>{};
  `,box);
  vm.runInContext(fs.readFileSync('pilots/canva-autonomia/support.js','utf8'),box);
  return code=>vm.runInContext(code,box);
}
test('pistas progridem, registam utilidade e não falam automaticamente',()=>{
  const run=pilot();
  run(`nextHint();const first=currentHint.text;assert.equal(spoken,0);hintFeedback('not_helped');nextHint();assert.notEqual(currentHint.text,first);assert.equal(supportHistory.length,2);nextHint();assert.equal(supportHistory.length,2);assert.match(supportNotice,/professor/);listenHint();assert.equal(spoken,1);`);
});
test('pedido inclui contexto, e uma revisão invalida a resposta atrasada',()=>{
  const run=pilot();
  run(`supportRoute='studio';nextHint();requestAIHint();const request=pendingHint.request_id;const original=currentHint.text;state.values.reason='Outra razão';receiveHint({request_id:request,unit_id:'u1',text:'Pista antiga'});assert.equal(currentHint.text,original);assert.ok(events.find(e=>e.type==='feedback_request').payload.previous_hints.length);assert.equal(events.filter(e=>e.payload.text==='Pista antiga').length,0);`);
});
test('só a resposta do pedido, produto, modo e etapa atuais é apresentada',()=>{
  for(const edit of ["go(1);go(0)","inputValue('product','book')","supportMode=2","state.level='support'"]){
    const run=pilot();
    run(`supportRoute='permanent';requestAIHint();const id=pendingHint.request_id;${edit};receiveHint({request_id:id,unit_id:'u1',text:'Antiga'});assert.equal(events.filter(e=>e.type==='hint_presented').length,0);`);
  }
  const run=pilot();run(`supportRoute='permanent';requestAIHint();const id=pendingHint.request_id;receiveHint({request_id:'outro',unit_id:'u1',text:'Errada'});assert.equal(currentHint,null);receiveHint({request_id:id,unit_id:'u1',text:'Atual'});assert.equal(currentHint.text,'Atual');`);
});
test('resposta revista fica ligada à pista, sem atribuir qualidade ao Canva',()=>{
  const run=pilot();
  run(`nextHint();const id=currentHint.hint_id;inputValue('reason','Outra razão');fieldEvent('reason');const record=events.find(e=>e.type==='assessment_result');assert.equal(record.payload.detail.after_hint_id,id);assert.equal(events.filter(e=>e.type==='feedback_request').length,0);`);
});
test('ajuda e resolução são atos explícitos e correlacionados',()=>{
  const run=pilot();
  run(`requestTeacherHelp();const id=pendingTeacher.request_id;assert.ok(id);assert.equal(events.at(-1).payload.help_request_id,id);nextHint();assert.equal(pendingTeacher.request_id,id);setWorkLocation('canva');assert.equal(events.at(-1).payload.location,'canva');`);
});
