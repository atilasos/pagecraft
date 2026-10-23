/* Executado pelo pytest com conteúdo e plano de apoio em stdin. Sem browser. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm'),fs=require('node:fs'),crypto=require('node:crypto');
const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
const template=fs.readFileSync('scripts/templates/m28p-journey.html','utf8');
const runtime=template.match(/<script>\s*'use strict';([\s\S]*?)<\/script>/)[1];
const base=fs.readFileSync('server/pipeline/prompts/template-base.html','utf8');
const bridge=base.slice(base.indexOf('    window.PageCraftBridge = (function () {'),base.indexOf('    /* Ouvir o embutidor'));
const support=fs.readFileSync('server/pipeline/prompts/activity-support.js','utf8');

function activity(){
  const box=vm.createContext({assert,crypto,console,TextEncoder,fixture:structuredClone(fixture)});
  vm.runInContext(`
    const messages=[],events={},documentEvents={},nodes=[];
    class Element {
      constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.listeners={};this.hidden=false;this.disabled=false;this.value='';this.style={};this.classList={add(){}};nodes.push(this);}
      get isConnected(){return !!this.parentNode||this.root===true;}
      appendChild(child){this.children.push(child);child.parentNode=this;return child;}
      replaceChildren(){for(const child of this.children)child.detach();this.children=[];}
      detach(){this.parentNode=null;for(const child of this.children)child.detach();}
      get options(){return this.children;}
      setAttribute(name,value){this[name]=value;}
      addEventListener(type,fn){(this.listeners[type]||=[]).push(fn);}
      fire(type){for(const fn of this.listeners[type]||[])fn({target:this});}
      focus(){document.activeElement=this;}
      scrollIntoView(){}
      closest(selector){if(selector.includes('[hidden]')&&(this.hidden||this.inert))return this;if(selector==='[data-pagecraft-support]'&&this.dataset.pagecraftSupport)return this;return this.parentNode?.closest(selector)||null;}
      querySelectorAll(){return [];}
      querySelector(selector){if(selector!=='.pc-support-action'||!this.innerHTML?.includes('pc-support-action'))return null;const action=new Element('div');action.parentNode=this;return action;}
    }
    const roots=new Map();
    for(const id of ['m28p-content','save-status','next','previous','navigation-status','progress-bar','stage-select','reflection','intro','workspace','session-label','page-content','intro-title','criteria','assisted-reading','phonology-notes','prerequisites','reflection-fields','start','return-work']){
      const node=new Element('div');node.id=id;node.root=true;roots.set(id,node);
    }
    roots.get('m28p-content').textContent=JSON.stringify(fixture.content);
    const levels=['support','intermediate','challenge'].map(level=>{const n=new Element('button');n.root=true;n.dataset.level=level;return n;});
    const document={title:'Caderno',body:{},activeElement:null,
      getElementById(id){return nodes.findLast(n=>n.id===id&&n.isConnected)||null;},
      createElement(tag){return new Element(tag);},
      querySelectorAll(selector){if(selector==='[data-level]')return levels;if(selector==='[data-pagecraft-support]')return nodes.filter(n=>n.isConnected&&n.dataset.pagecraftSupport);return [];},
      addEventListener(type,fn){(documentEvents[type]||=[]).push(fn);},
      dispatchEvent(event){for(const fn of documentEvents[event.type]||[])fn(event);}
    };
    const window=globalThis;window.parent={postMessage(message){messages.push(JSON.parse(JSON.stringify(message)));}};
    window.addEventListener=(type,fn)=>(events[type]||=[]).push(fn);
    const setInterval=()=>{};
    const CustomEvent=class{constructor(type,options={}){this.type=type;this.detail=options.detail;}};
    function host(type,payload){for(const fn of events.message||[])fn({source:window.parent,data:{pagecraft:1,type,payload}});}
    function checkpoint(){return messages.filter(m=>m.type==='activity_state').at(-1);}
    function evidence(){return messages.filter(m=>['attempt','assessment_result'].includes(m.type));}
    function get(id){return document.getElementById(id);}
    function findButton(text){return nodes.findLast(n=>n.tagName==='button'&&n.isConnected&&n.textContent===text);}
    function stateAt(index){
      const state={version:1,page:index,level:'intermediate',answers:{},confirmed:{}};
      for(const p of fixture.content.pages.slice(0,index)){
        state.answers[p.id]=p.type==='oral'?true:p.type==='write'?'O meu texto':p.type==='choice'?p.answer:p.answer.map((v,i)=>p.pieces.indexOf(v));
        state.confirmed[p.id]=true;
      }
      return state;
    }
    function restore(state){host('learning_restore',{events:[{type:'activity_state',payload:{activity:'m28p-v2-'+fixture.content.slug,version:1,state}}]});}
  `,box);
  vm.runInContext(bridge,box);
  vm.runInContext(runtime,box);
  vm.runInContext(support,box);
  vm.runInContext('PageCraftSupport.configure(fixture.support);',box);
  return code=>vm.runInContext(code,box);
}

test('não envia checkpoint vazio antes de recuperar; uma história vazia atualiza readiness',()=>{
  const run=activity();
  run(`assert.equal(checkpoint(),undefined);host('learning_preferences',{level:'support'});assert.equal(checkpoint(),undefined);
    host('learning_restore',{events:[]});assert.equal(checkpoint().payload.readyForReflection,false);
    assert.equal(checkpoint().payload.state.page,-1);assert.equal(evidence().length,0);`);
});

test('recupera a última resposta errada e não a regista novamente',()=>{
  const run=activity();
  run(`const saved=stateAt(2);saved.answers['passo-2']='menino';saved.confirmed['passo-2']=true;
    restore(saved);assert.equal(checkpoint().payload.state.answers['passo-2'],'menino');assert.equal(evidence().length,0);
    get('previous').fire('click');findButton('menino').fire('click');assert.equal(evidence().length,0);
    assert.equal(get('next').disabled,false);get('next').fire('click');assert.equal(checkpoint().payload.state.page,2);`);
});

test('conserva a pista antes de a escolha alterar o contexto, sem reutilizá-la noutra revisão',()=>{
  const run=activity();
  run(`restore(stateAt(1));PageCraftSupport.requestHint();const hint=PageCraftSupport.currentHintId();assert.ok(hint);
    findButton('menino').fire('click');assert.equal(evidence().at(-1).payload.detail.after_hint_id,hint);
    assert.equal(PageCraftSupport.currentHintId(),null);findButton('mana').fire('click');
    assert.equal(evidence().at(-1).payload.detail.after_hint_id,undefined);`);
});

test('conserva a pista ao longo de várias peças até confirmar a sequência',()=>{
  const run=activity();
  run(`restore(stateAt(2));PageCraftSupport.requestHint();const hint=PageCraftSupport.currentHintId();
    for(const part of ['me','ni','na'])findButton(part).fire('click');
    findButton('Confirmar a minha sequência').fire('click');assert.equal(evidence().at(-1).payload.detail.after_hint_id,hint);
    assert.equal(evidence().at(-1).payload.correct,true);`);
});

test('conserva a pista ao longo da escrita e regista produção sem veredicto',()=>{
  const run=activity();
  run(`restore(stateAt(9));PageCraftSupport.requestHint();const hint=PageCraftSupport.currentHintId();
    const input=get('open-answer');for(const text of ['O','O meu','O meu texto']){input.value=text;input.fire('input');}
    findButton('Guardar esta resposta').fire('click');const answer=evidence().at(-1);
    assert.equal(answer.payload.detail.after_hint_id,hint);assert.equal(answer.payload.detail.automatic_verdict,false);
    assert.equal(answer.payload.detail.value,'O meu texto');assert.equal(answer.type,'assessment_result');`);
});

test('colar texto retira controlos sem valor textual antes do checkpoint',()=>{
  const run=activity();
  run(`restore(stateAt(9));const input=get('open-answer');input.value='A\\u0000B\\n\\tC';input.fire('input');
    assert.equal(input.value,'AB\\n\\tC');assert.equal(checkpoint().payload.state.answers['passo-10'],input.value);`);
});

test('mudar de tarefa ou recuperar não atribui uma pista antiga à resposta seguinte',()=>{
  for(const change of ["get('previous').fire('click');get('next').fire('click');", "restore(stateAt(9));"]){
    const run=activity();
    run(`restore(stateAt(9));PageCraftSupport.requestHint();const input=get('open-answer');input.value='Antes';input.fire('input');
      ${change}get('open-answer').value='Depois';get('open-answer').fire('input');findButton('Guardar esta resposta').fire('click');
      assert.equal(evidence().at(-1).payload.detail.after_hint_id,undefined);`);
  }
});

test('recuperar o percurso completo ativa reflexão sem fabricar evidência',()=>{
  const run=activity();
  run(`const state=stateAt(fixture.content.pages.length);state.page=fixture.content.pages.length-1;restore(state);
    assert.equal(checkpoint().payload.readyForReflection,true);assert.equal(evidence().length,0);
    get('next').fire('click');assert.equal(messages.at(-1).type,'open_reflection');`);
});
