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


def test_pairs_allow_one_wrong_connection_and_ordering_requires_all_unique_pieces():
    run_model(r'''
const pair={id:'r1',kind:'pairs',options:[{id:'p1'},{id:'p2'}],answer:['p1','p2']};
const state=TicModel.initial();
TicModel.edit(state,pair,['p1=p2']);
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
