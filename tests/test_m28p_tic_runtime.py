"""Invariantes do trabalho autónomo, sem requerer um browser nos testes de estado."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'scripts/templates/m28p-tic.html'


def run_model(script):
    source = TEMPLATE.read_text()
    model = source.split('/* BEGIN M28P TIC MODEL:')[1].split('*/', 1)[1].split('/* END M28P TIC MODEL */')[0]
    result = subprocess.run(['node', '-e', model + "\nconst assert=require('node:assert/strict');\n" + script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_wrong_confirmed_answers_unlock_without_counting_repeated_clicks_or_level_changes():
    run_model(r'''
const data={rounds:[
  {id:'r1',kind:'match',options:[{id:'a'},{id:'b'}],answer:['a']},
  {id:'r2',kind:'hunt',options:[{id:'a'},{id:'b'},{id:'c'}],answer:['a','c']}
]};
const state=TicModel.initial(),r=data.rounds[0];
assert.equal(TicModel.accessible(data,state,1),false);
assert.equal(TicModel.confirm(state,r).accepted,false);
TicModel.edit(state,r,['b']);
assert.deepEqual(TicModel.confirm(state,r),{accepted:true,emit:true,correct:false});
assert.equal(TicModel.accessible(data,state,1),true);
assert.equal(TicModel.confirm(state,r).emit,false);
assert.equal(state.counts.r1,1);
state.level='support';
assert.equal(TicModel.answered(data,state,0),true);
assert.equal(TicModel.confirm(state,r).emit,false);
TicModel.edit(state,r,['b']);
assert.equal(TicModel.confirm(state,r).emit,false);
TicModel.edit(state,r,['a']);
assert.equal(TicModel.confirm(state,r).emit,true);
assert.equal(state.counts.r1,2);
TicModel.edit(state,data.rounds[1],['b']);
assert.equal(TicModel.confirm(state,data.rounds[1]).correct,false);
assert.equal(TicModel.complete(data,state),true);
''')


def test_pairs_require_all_connections_but_allow_wrong_complete_answers():
    run_model(r'''
const pair={id:'r1',kind:'pairs',options:[{id:'p1'},{id:'p2'}],answer:['p1','p2']};
const state=TicModel.initial();
TicModel.edit(state,pair,['p1=p2']);
assert.deepEqual(TicModel.confirm(state,pair),{accepted:false,emit:false});
TicModel.edit(state,pair,['p1=p2','p2=p1']);
assert.deepEqual(TicModel.confirm(state,pair),{accepted:true,emit:true,correct:false});
assert.equal(TicModel.correct(pair,['p2=p2','p1=p1']),true);
assert.equal(TicModel.validAnswer(pair,['p1=p1','p2=p1']),false);
assert.deepEqual(TicModel.cleanAnswer(pair,['p1=p1','p2=p1','p2=p2','p3=p3']),['p1=p1','p2=p2']);
const order={id:'r2',kind:'recall',pieces:[{id:'a'},{id:'b'},{id:'c'}],answer:['b','a','c']};
assert.equal(TicModel.validAnswer(order,['a','b']),false);
assert.equal(TicModel.validAnswer(order,['a','a','c']),false);
assert.equal(TicModel.validAnswer(order,['a','b','c']),true);
assert.equal(TicModel.correct(order,['a','b','c']),false);
assert.equal(TicModel.correct(order,['b','a','c']),true);
const repeated={id:'r3',kind:'syllables',pieces:[{id:'a',label:'ba'},{id:'b',label:'na'},{id:'c',label:'na'}],answer:['a','b','c']};
assert.equal(TicModel.correct(repeated,['a','c','b']),true);
''')


def test_restore_sanitizes_untrusted_state_and_preserves_last_submission_without_events():
    run_model(r'''
const data={rounds:[
  {id:'r1',kind:'match',options:[{id:'a'},{id:'b'}],answer:['a']},
  {id:'r2',kind:'syllables',pieces:[{id:'me'},{id:'ni'},{id:'na'}],answer:['me','ni','na']}
]};
const state=TicModel.initial();state.page=0;
TicModel.edit(state,data.rounds[0],['b']);TicModel.confirm(state,data.rounds[0]);
state.page=1;state.level='challenge';
TicModel.edit(state,data.rounds[1],['na','ni']);
const copy=TicModel.sanitize(data,JSON.parse(JSON.stringify(state)));
assert.deepEqual(copy,state);
assert.equal(copy.counts.r1,1);
assert.equal(TicModel.confirm(copy,data.rounds[0]).emit,false);
const bad=TicModel.sanitize(data,{version:3,page:900,level:'bad',done:true,
 answers:{r1:['foreign'],r2:['me','me','na','foreign']},confirmed:{r1:true,r2:true},counts:{r1:-1,r2:Infinity},last:{r1:['foreign']}});
assert.equal(bad.page,0);assert.equal(bad.level,'intermediate');assert.equal(bad.done,false);
assert.deepEqual(bad.answers,{r2:['me','na']});assert.deepEqual(bad.confirmed,{});assert.deepEqual(bad.counts,{});
assert.deepEqual(TicModel.sanitize(data,{version:2}),TicModel.initial());
''')


def test_largest_expected_checkpoint_fits_host_boundary():
    run_model(r'''
const data={rounds:Array.from({length:4},(_,index)=>({id:'r'+(index+1),kind:'hunt',
 options:Array.from({length:12},(_,i)=>({id:'option-'+i})),answer:['option-1']}))};
const state=TicModel.initial();state.page=3;state.level='challenge';
for(const round of data.rounds){TicModel.edit(state,round,round.options.map(option=>option.id));TicModel.confirm(state,round);state.counts[round.id]=999;}
state.done=true;
const payload={activity:'m28p-v3-carrossel-encontrar-palavras',version:3,readyForReflection:true,state};
assert.ok(Buffer.byteLength(JSON.stringify(payload),'utf8')<4096);
assert.deepEqual(TicModel.sanitize(data,state),state);
''')


def test_runtime_script_parses():
    source = TEMPLATE.read_text().split("<script>\n'use strict';")[1].split('</script>')[0]
    result = subprocess.run(['node', '--check'], input=source, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_host_restore_preferences_attempts_and_audio_requests_use_real_runtime():
    """Exercita os listeners e checkpoints; não substitui o ensaio visual no browser."""
    source = TEMPLATE.read_text()
    runtime = source.split("<script>\n'use strict';")[1].split('</script>')[0]
    fixture = {
        'slug': 'm28p-v3-menina-match', 'title': 'Palavra igual', 'game': 'match',
        'word': {'label': 'menina', 'syllables': ['me', 'ni', 'na'], 'image': '<svg></svg>'},
        'audio': {'word': 'data:audio/mpeg;base64,AA', 'instruction': 'data:audio/mpeg;base64,AA'},
        'rounds': [{'id': 'r1', 'kind': 'match', 'prompt': 'Toca na palavra igual.', 'model': True,
                    'options': [{'id': 'yes', 'label': 'menina'}, {'id': 'no', 'label': 'me'}], 'answer': ['yes']}],
    }
    script = r'''
const vm=require('node:vm'),assert=require('node:assert/strict'),fs=require('node:fs');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const ctx=vm.createContext({assert,input,console});
vm.runInContext(`
const sent=[],listeners={},all=[],roots=new Map();
const key=name=>name.replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase());
function matches(element,selector){
 if(selector.includes(' '))selector=selector.split(' ').at(-1);
 if(selector==='button:not(:disabled)')return element.tagName==='button'&&!element.disabled;
 if(selector.startsWith('.'))return element.className.split(' ').includes(selector.slice(1));
 if(selector.startsWith('[data-'))return element.dataset[key(selector.slice(6,-1))]!==undefined;
 return element.tagName===selector;
}
class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.listeners={};this.style={};this.className='';this.hidden=false;this.disabled=false;this.textContent='';all.push(this);
  this.classList={add:(...names)=>{this.className=[...new Set(this.className.split(' ').concat(names))].join(' ')},remove:name=>{this.className=this.className.split(' ').filter(n=>n!==name).join(' ')},toggle:(name,on)=>{this.classList[on?'add':'remove'](name)}};
 }
 get isConnected(){return this.root||this.parentNode?.isConnected;}
 appendChild(child){child.parentNode=this;this.children.push(child);return child;}
 append(...children){children.forEach(child=>this.appendChild(child));}
 prepend(child){child.parentNode=this;this.children.unshift(child);}
 replaceChildren(){this.children.forEach(child=>child.parentNode=null);this.children=[];}
 setAttribute(key,value){this[key]=value;}
 addEventListener(type,fn){(this.listeners[type]||=[]).push(fn);}
 fire(type){for(const fn of this.listeners[type]||[])fn({target:this});}
 focus(){document.activeElement=this;}
 scrollIntoView(){}
 querySelectorAll(selector){return this.children.flatMap(child=>[...(matches(child,selector)?[child]:[]),...child.querySelectorAll(selector)]);}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
for(const id of input.ids){const element=new Element('div');element.id=id;element.root=true;roots.set(id,element);}
roots.get('m28p-content').textContent=JSON.stringify(input.fixture);
const levels=['support','intermediate','challenge'].map(level=>{const e=new Element('button');e.dataset.level=level;e.root=true;return e;});
const reflections=['again','help','alone'].map(reflection=>{const e=new Element('button');e.dataset.reflection=reflection;e.root=true;return e;});
const document={activeElement:null,getElementById:id=>roots.get(id),createElement:tag=>new Element(tag),
 querySelectorAll:selector=>all.filter(element=>element.isConnected&&matches(element,selector)),
 querySelector:selector=>document.querySelectorAll(selector)[0],addEventListener(){}};
const window=globalThis;window.parent={};window.addEventListener=(type,fn)=>(listeners[type]||=[]).push(fn);
window.matchMedia=()=>({matches:true});
const setTimeout=()=>0,clearTimeout=()=>{};
const Audio=class{addEventListener(){}pause(){}play(){return Promise.resolve()}};
window.PageCraftBridge={emit(type,unitId,payload){sent.push({type,unitId,payload:JSON.parse(JSON.stringify(payload))});},
 attempt(unitId,correct,detail){this.emit('attempt',unitId,{correct,detail});},
 unitStarted(unitId){this.emit('unit_started',unitId,{})},levelChanged(unitId,level){this.emit('level_changed',unitId,{level})}};
function host(type,payload,source=window.parent){for(const fn of listeners.message||[])fn({source,data:{pagecraft:1,type,payload}});}
function get(id){return roots.get(id);}
function checkpoint(){return sent.filter(message=>message.type==='activity_state').at(-1);}
function evidence(){return sent.filter(message=>message.type==='attempt');}
function clickOption(id){all.findLast(element=>element.isConnected&&element.dataset.option===id).fire('click');}
`,ctx);
vm.runInContext(input.runtime,ctx);
vm.runInContext(`
assert.equal(checkpoint(),undefined);
host('learning_preferences',{level:'support'});assert.equal(checkpoint(),undefined);
host('learning_restore',{events:[]});
assert.equal(checkpoint().payload.state.level,'support');
assert.equal(checkpoint().payload.readyForReflection,false);
get('start').fire('click');get('demo-close').fire('click');
assert.equal(evidence().length,0);
clickOption('no');get('confirm').fire('click');
assert.equal(evidence().length,1);assert.equal(evidence()[0].payload.correct,false);
assert.equal(evidence()[0].payload.detail.aids.demo_shown,true);
assert.equal(checkpoint().payload.readyForReflection,true);
assert.equal(get('next').hidden,false);
get('confirm').fire('click');assert.equal(evidence().length,1);
const saved=JSON.parse(JSON.stringify(checkpoint().payload.state));
host('learning_restore',{events:[{type:'activity_state',payload:{activity:input.fixture.slug,version:3,state:saved}}]});
assert.equal(evidence().length,1);assert.equal(checkpoint().payload.readyForReflection,true);
get('confirm').fire('click');assert.equal(evidence().length,1);
host('state_restore',{activity:'other-activity',state:{version:3}});
assert.equal(checkpoint().payload.state.page,0);
host('learning_preferences',{level:'challenge'});
assert.equal(evidence().length,1);assert.equal(get('next').hidden,false);
get('hear').fire('click');assert.equal(evidence().length,1);
assert.equal(checkpoint().payload.state.aids.r1.audio_instruction_requested,true);
assert.equal(checkpoint().payload.state.counts.r1,1);
get('next').fire('click');assert.equal(checkpoint().payload.state.done,true);
get('finish-button').fire('click');assert.equal(sent.at(-1).type,'open_reflection');
`,ctx);
'''
    import re
    payload = {'runtime': runtime, 'fixture': fixture, 'ids': re.findall(r'\bid="([^"]+)"', source)}
    result = subprocess.run(['node', '-e', script], input=json.dumps(payload), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
