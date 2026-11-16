"""Contrato editorial e modelo das quatro operações do ciclo."""
import copy
import json
import re
import subprocess
from types import SimpleNamespace

import pytest
from scripts import build_m28p_tic as motor
from scripts.m28p_cycle import validate_cycle


def source():
    return json.loads((motor.BASE/'cycle.json').read_text())


def test_cumulative_repertoire_and_generation_limits():
    pools=validate_cycle(source(),motor.read_words())
    assert len(pools['menina']['words'])==4
    assert len(pools['menino']['words'])==5
    assert len(pools['uva']['sentences'])==7
    assert 'vê' not in pools['menino']['families']
    assert 'vê' in pools['uva']['families']
    for word in motor.read_words()[:3]:
        for game in motor.CYCLE_GAMES:
            data,reason=motor.cycle_content(word,game,pools[word['slug']])
            if data:
                assert len(data['rounds'])==4
                assert len({r['target']['slug'] for r in data['rounds']})==4
                if game=='read-choose':
                    assert all(r['target']['picturable'] for r in data['rounds'])
                spec=motor.spec_for(data,word)
                output=motor.render(data,spec)
                assert 'data:audio/mpeg;base64,' in output
                assert json.loads(re.search(r'<script id="m28p-content" type="application/json">(.*?)</script>',output,re.S)[1])==data
                assert '@@' not in output
            else:
                assert 'necessários 4' in reason


@pytest.mark.parametrize('change,match',[
    (lambda c:c['keywords']['menina']['newWords'][0].update(syllables=['no','ma']),'concatenação'),
    (lambda c:c['keywords']['menina']['newWords'][0].update(label='nova',syllables=['no','va']),'repertório'),
    (lambda c:c['keywords']['menina']['newWords'][0].update(label='neuma',syllables=['neu','ma']),'repertório'),
    (lambda c:c['keywords']['menina']['sentences'][0].update(text='A menina vê.',tokens=['A','menina','vê']),'token'),
    (lambda c:c['keywords']['menina']['sentences'][0].update(tokens=['A','menina']),'tokens'),
])
def test_refuses_invalid_editorial_data(change,match):
    cycle=copy.deepcopy(source());change(cycle)
    with pytest.raises(ValueError,match=match):
        validate_cycle(cycle,motor.read_words())


def test_js_cycle_state_and_recovery():
    pools=validate_cycle(source(),motor.read_words())
    fixtures=[motor.cycle_content(motor.read_words()[2],game,pools['uva'])[0] for game in motor.CYCLE_GAMES]
    template=(motor.ROOT/'scripts/templates/m28p-tic.html').read_text()
    model=template.split('/* BEGIN M28P TIC MODEL: funções puras verificáveis em Node. */')[1].split('/* END M28P TIC MODEL */')[0]
    js=model+'''
const assert=require('node:assert/strict');
for(const data of FIXTURES){
 const r=data.rounds[0],s=TicModel.initial();
 if(r.kind==='discover'){
  const w=r.lexicon.find(w=>w.syllables.length===2);
  const used=[];for(const label of w.syllables)used.push(r.pieces.find(p=>p.label===label&&!used.includes(p.id)).id);
  TicModel.edit(s,r,used);TicModel.confirm(s,r);
  assert.deepEqual(s.discoveries[r.id],[w.label]);assert(TicModel.answered(data,s,0));
  const saved=TicModel.sanitize(data,s);assert.deepEqual(saved.discoveries,s.discoveries);
  TicModel.edit(s,r,['finish']);TicModel.confirm(s,r);assert(TicModel.answered(data,s,0));
 }else{
  const wrong=TicModel.ordered(r)?r.answer.slice().reverse():[r.options.find(o=>!r.answer.includes(o.id)).id];
  TicModel.edit(s,r,wrong);assert(TicModel.confirm(s,r).accepted);assert(TicModel.answered(data,s,0));
  const saved=TicModel.sanitize(data,s);assert.deepEqual(saved.answers,s.answers);
  s.level='support';assert.deepEqual(saved.answers,s.answers);
  TicModel.edit(s,r,r.answer);assert(TicModel.confirm(s,r).correct);
  assert.equal(TicModel.confirm(s,r).emit,false);
 }
}
'''.replace('FIXTURES',json.dumps(fixtures,ensure_ascii=False))
    result=subprocess.run(['node'],input=js,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
