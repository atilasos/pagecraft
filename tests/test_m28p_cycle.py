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
            if data and game=='discover':
                assert 2<=len(data['rounds'])<=4
                for r in data['rounds']:
                    assert 2<=len(r['lexicon'])<=3 and len(r['pieces'])<=len({s for w in r['lexicon'] for s in w['syllables']})+1
                spec=motor.spec_for(data,word)
                assert '@@' not in motor.render(data,spec)
            elif data:
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
  const ids=w=>{const used=[];for(const label of w.syllables)used.push(r.pieces.find(p=>p.label===label&&!used.includes(p.id)).id);return used;};
  const [first,...rest]=r.lexicon;
  TicModel.edit(s,r,ids(first));TicModel.confirm(s,r);
  assert.deepEqual(s.discoveries[r.id],[first.label]);
  // Encontrar uma palavra não termina a ronda: o tabuleiro esvazia e o progresso fica guardado.
  assert(!TicModel.answered(data,s,0));assert.deepEqual(s.answers[r.id],[]);
  let saved=TicModel.sanitize(data,s);assert.deepEqual(saved.discoveries,s.discoveries);assert(!saved.confirmed[r.id]);
  for(const w of rest){TicModel.edit(s,r,ids(w));TicModel.confirm(s,r);}
  assert(TicModel.answered(data,s,0));
  saved=TicModel.sanitize(data,s);assert(saved.confirmed[r.id]);
  const other=TicModel.initial();TicModel.edit(other,r,['finish']);TicModel.confirm(other,r);assert(TicModel.answered(data,other,0));
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


def test_revisions_are_not_bound_to_pilot_positions_or_syllable_count():
    cycle=source()
    cycle['keywords']=dict(reversed(list(cycle['keywords'].items())))
    cycle['keywords']['uva']['newWords'].append(dict(label='novamente',syllables=['no','va','men','te'],picturable=False))
    with pytest.raises(ValueError,match='repertório'):
        validate_cycle(cycle,motor.read_words())
    cycle['keywords']['uva']['newWords'].pop()
    pools=validate_cycle(cycle,motor.read_words())
    assert len(pools['uva']['words'])==13


def test_missing_audio_and_images_refuse_generation(tmp_path,monkeypatch):
    pools=validate_cycle(source(),motor.read_words())
    monkeypatch.setattr(motor,'ASSETS',tmp_path)
    with pytest.raises(ValueError,match='Áudio em falta'):
        motor.cycle_content(motor.read_words()[0],'listen-build',pools['menina'])
    monkeypatch.setattr(motor,'data_audio',lambda _: 'data:audio/mpeg;base64,test')
    with pytest.raises(ValueError,match='Imagem em falta'):
        motor.cycle_content(motor.read_words()[0],'listen-build',pools['menina'])


def test_image_choices_never_share_a_visual_conflict():
    cycle=source()
    pools=validate_cycle(cycle,motor.read_words())
    for word in motor.read_words()[:3]:
        for game in motor.CYCLE_GAMES:
            data,_=motor.cycle_content(word,game,pools[word['slug']])
            for round_ in data['rounds'] if data else []:
                labels={o['label'] for o in round_['options'] if o.get('image')}
                assert all(len(labels.intersection(group))<=1 for group in cycle['visualConflicts'])


def test_menino_read_choose_is_omitted_without_valid_distractors():
    pools=validate_cycle(source(),motor.read_words())
    data,reason=motor.cycle_content(motor.read_words()[1],'read-choose',pools['menino'])
    assert data is None
    assert 'distratores' in reason


def test_unknown_visual_conflicts_are_rejected():
    cycle=source()
    cycle['visualConflicts'].append(['dragão'])
    with pytest.raises(ValueError,match='visualConflicts'):
        validate_cycle(cycle,motor.read_words())


def test_distractors_must_also_be_distinguishable_from_each_other():
    from scripts.m28p_cycle import image_choices
    items=[dict(slug=s,label=s) for s in ('uva','mana','mano','ovo')]
    chosen=image_choices(items[0],items,[['mana','mano']])
    assert [w['label'] for w in chosen]==['uva','mana','ovo']


def test_discover_rounds_show_only_needed_syllables_and_honest_counts():
    from scripts.m28p_cycle import discover_rounds, formable
    import random
    pools=validate_cycle(source(),motor.read_words())
    for word in motor.read_words()[:3]:
        pool=pools[word['slug']]
        groups=discover_rounds(word['slug'],pool['words'],pool['families'],random.Random(0))
        assert groups
        for group in groups:
            assert len(group['pieces'])<=8
            assert all(formable(w['label'],group['pieces']) for w in group['hidden'])
            hidden={w['label'] for w in group['hidden']}
            assert not [w['label'] for w in pool['words'] if 2<=len(w['syllables'])<=3 and w['label'] not in hidden and formable(w['label'],group['pieces'])]
    assert formable('ovo',['o','vo']) and not formable('ovo',['vo']) and not formable('nono',['no'])
