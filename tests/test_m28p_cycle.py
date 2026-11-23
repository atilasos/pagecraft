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
    assert len(pools['uva']['sentences'])==6
    assert 'vê' not in pools['menino']['families']
    assert 'vê' in pools['uva']['families']
    for word in motor.read_words()[:3]:
        for game in motor.CYCLE_GAMES:
            data,reason=motor.cycle_content(word,game,pools[word['slug']])
            if data:
                # A palavra-chave é o exemplo da demonstração e nunca uma ronda.
                assert word['slug'] not in {r['target'].get('slug') for r in data['rounds']}
                assert all(word['label'] not in {w['label'] for w in r.get('lexicon',[])} for r in data['rounds'])
                assert data['demo']
            if data and game=='discover':
                assert 1<=len(data['rounds'])<=4
                for r in data['rounds']:
                    assert 2<=len(r['lexicon'])<=3 and len(r['pieces'])<=len({s for w in r['lexicon'] for s in w['syllables']})+1
                spec=motor.spec_for(data,word)
                assert '@@' not in motor.render(data,spec)
            elif data:
                assert 1<=len(data['rounds'])<=4 if game=='sentence' else 3<=len(data['rounds'])<=4
                assert len({r['target']['slug'] for r in data['rounds']})==len(data['rounds'])
                if game=='read-choose':
                    assert all(r['target']['picturable'] for r in data['rounds'])
                spec=motor.spec_for(data,word)
                output=motor.render(data,spec)
                assert 'data:audio/mpeg;base64,' in output
                assert json.loads(re.search(r'<script id="m28p-content" type="application/json">(.*?)</script>',output,re.S)[1])==data
                assert '@@' not in output
            else:
                assert 'necessárias' in reason


@pytest.mark.parametrize('change,match',[
    (lambda c:c['keywords']['menina']['newWords'][0].update(syllables=['no','ma']),'concatenação'),
    (lambda c:c['keywords']['menina']['newWords'][0].update(label='nova',syllables=['no','va']),'repertório'),
    (lambda c:c['keywords']['menina']['newWords'][0].update(label='neuma',syllables=['neu','ma']),'repertório'),
    (lambda c:c['keywords']['menina']['sentences'][0].update(text='A menina vê.',tokens=['A','menina','vê']),'token'),
    (lambda c:c['keywords']['menina']['sentences'][0].update(tokens=['A','menina']),'tokens'),
    (lambda c:c['keywords']['menina']['sentences'][0].pop('alternatives'),'ordem inversa'),
    (lambda c:c['keywords']['menina']['sentences'][0].pop('scene'),'cena'),
    (lambda c:c['keywords']['uva']['newWords'].append(dict(label='ama',syllables=['a','ma'],picturable=False)),'formável em menina'),
    (lambda c:c['keywords']['uva']['newWords'].append(dict(label='nóvo',syllables=['nó','vo'],picturable=False)),'partilhariam'),
    (lambda c:c['functionWords'].append(dict(word='ai',syllables=['a','i'])),'funcional'),
    (lambda c:(c['repertoire']['byKeyword']['uva']['onsets'].update(s='aeiou'),c['keywords']['uva']['newWords'].append(dict(label='vaso',syllables=['va','so'],picturable=True))),'s entre vogais'),
    (lambda c:c['keywords']['uva']['sentences'].append(dict(text='A uva mu.',tokens=['A','uva','mu'],scene=[{'image':'uva'},{'image':'uva'}])),'token'),
    (lambda c:c['functionWords'].append(dict(word='da',**{'from':'menina'})),'funcional'),
    (lambda c:c['keywords']['uva']['sentences'].append(dict(text='A uva é da avó.',tokens=['A','uva','é','da','avó'],scene=[{'image':'uva'}])),'token'),
])
def test_refuses_invalid_editorial_data(change,match):
    cycle=copy.deepcopy(source());change(cycle)
    with pytest.raises(ValueError,match=match):
        validate_cycle(cycle,motor.read_words())


def test_digraphs_cannot_be_split_across_syllables():
    from scripts.m28p_cycle import readable_at
    cycle=source();slugs=[w['slug'] for w in sorted(motor.read_words(),key=lambda w:w['order'])]
    rep=cycle['repertoire']
    # «passo» como pas + so (s de escada + s) e «carro» como car + ro (r de árvore + r) antecipariam ss e rr.
    assert not readable_at('passo',['pas','so'],slugs.index('escada'),rep,slugs)
    assert not readable_at('carro',['car','ro'],slugs.index('arvore'),rep,slugs)
    assert readable_at('carro',['ca','rro'],slugs.index('cigarra'),rep,slugs)
    assert not readable_at('roupa',['rou','pa'],slugs.index('rato'),rep,slugs)
    # Ditongos com acento também não se partem («véu» não é vé + u).
    assert not readable_at('véu',['vé','u'],slugs.index('uva'),rep,slugs)
    assert readable_at('saída',['sa','í','da'],slugs.index('casa'),rep,slugs)


def test_function_words_and_sentence_words_follow_their_keyword():
    cycle=source()
    cycle['functionWords'].append({'word':'da','from':'dedo'})
    cycle['keywords']['uva']['sentenceWords'].append({'label':'ama','syllables':['a','ma']})
    cycle['keywords']['uva']['sentences'].append(dict(text='A avó ama a uva.',tokens=['A','avó','ama','a','uva'],scene=[{'image':'avo'},{'image':'uva'}]))
    pools=validate_cycle(cycle,motor.read_words())
    assert 'ama' in {w['label'] for w in pools['uva']['sentenceWords']}
    cycle['keywords']['uva']['sentences'].append(dict(text='A uva é da avó.',tokens=['A','uva','é','da','avó'],scene=[{'image':'uva'}]))
    with pytest.raises(ValueError,match='token'):
        validate_cycle(cycle,motor.read_words())


def test_syllable_boundaries_hiatus_and_reserved_keywords():
    from scripts.m28p_cycle import readable_at, readable_word
    cycle=source();slugs=[w['slug'] for w in sorted(motor.read_words(),key=lambda w:w['order'])];rep=cycle['repertoire']
    # A consoante entre vogais vai para a sílaba seguinte: «sal-a» não é divisão de «sala».
    assert not readable_at('sala',['sal','a'],slugs.index('funil'),rep,slugs)
    assert readable_at('sala',['sa','la'],slugs.index('leque'),rep,slugs)
    assert readable_word('sala',slugs.index('leque'),rep,slugs) and not readable_word('sala',slugs.index('sapato'),rep,slugs)
    # Palavras longas verificam-se sem explosão combinatória.
    assert not readable_word('mana'*40+'x',slugs.index('uva'),rep,slugs)
    # «gu» e «qu» seguidos de vogal não se separam.
    assert not readable_word('fogueira',slugs.index('bandeira'),rep,slugs)
    assert readable_word('fogueira',slugs.index('fogueira'),rep,slugs)
    assert not readable_word('água',slugs.index('quadro'),rep,slugs)
    bad=copy.deepcopy(cycle);bad['keywords']['menina']['newWords'].append(dict(label='menino',syllables=['me','ni','no'],picturable=True))
    with pytest.raises(ValueError,match='palavra-chave'):
        validate_cycle(bad,motor.read_words())
    # Um hiato declarado não dispensa as outras fronteiras («sal-a» continua inválido).
    from scripts.m28p_cycle import _boundary_errors
    assert _boundary_errors('sala',['sal','a'],hiatus=True)
    assert not _boundary_errors('saída',['sa','í','da'],hiatus=True)
    assert readable_at('rainha',['ra','i','nha'],slugs.index('rato'),rep,slugs,hiatus=True)
    assert not readable_at('rainha',['ra','i','nha'],slugs.index('rato'),rep,slugs)


def test_demo_audio_matches_the_demo_target():
    pools=validate_cycle(source(),motor.read_words())
    for word in motor.read_words()[:3]:
        for game in motor.CYCLE_GAMES:
            data,_=motor.cycle_content(word,game,pools[word['slug']])
            if not data:
                continue
            expected=motor.data_audio(f"exemplo-{word['slug']}") if game=='sentence' else data['demo']['target']['audio']
            assert data['demo']['audio']==expected


def test_class_sentence_warnings_use_the_reading_rules():
    from server.classroom.sentences import prepare_sentence
    text,tokens,warnings=prepare_sentence('Avó, vê o guarda-chuva!','uva')
    assert text=='Avó, vê o guarda-chuva!' and 'guarda-chuva' in tokens
    _,_,warnings=prepare_sentence('O meu ovo','uva')
    assert any('meu' in w for w in warnings)
    _,_,warnings=prepare_sentence('A avó vê o ovo','uva')
    assert warnings==[]
    # Palavras funcionais só a partir da sua etapa: «da» entra em dedo.
    from server.classroom import sentences
    words,cycle,pools=sentences.repertoire()
    assert 'da' not in pools['uva']['functionWords']


def test_round_and_piece_ids_follow_content():
    pools=validate_cycle(source(),motor.read_words())
    word=motor.read_words()[2]
    for game in motor.CYCLE_GAMES:
        data,_=motor.cycle_content(word,game,pools['uva'])
        for r in data['rounds']:
            assert not re.fullmatch(r'r\d+',r['id'])
            if r.get('pieces'):
                assert all(p['id'].split('#')[0]==p['label'] for p in r['pieces'])
            for w in r.get('lexicon',[]):
                labels=[p['label'] for p in r['pieces']]
                assert not any(labels[i:i+len(w['syllables'])]==w['syllables'] for i in range(len(labels)-len(w['syllables'])+1)),(labels,w['label'])
            if r.get('answer') and r.get('pieces') and game!='discover':
                labels=[p['label'] for p in r['pieces']]
                answer=[next(p['label'] for p in r['pieces'] if p['id']==i) for i in r['answer']]
                # A resposta nunca aparece já montada em peças seguidas.
                assert not any(labels[i:i+len(answer)]==answer for i in range(len(labels)-len(answer)+1)),(labels,answer)


def test_js_cycle_state_and_recovery():
    pools=validate_cycle(source(),motor.read_words())
    fixtures=[motor.cycle_content(motor.read_words()[2],game,pools['uva'])[0] for game in motor.CYCLE_GAMES]
    fixtures.append(motor.cycle_content(motor.read_words()[0],'sentence',pools['menina'])[0])
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
  // Depois de concluída ou revelada, a ronda não volta a abrir.
  assert.equal(TicModel.edit(s,r,[]),false);assert(s.confirmed[r.id]);
  assert.equal(TicModel.edit(other,r,ids(first)),false);assert.deepEqual(other.answers[r.id],['finish']);
 }else{
  const wrong=TicModel.ordered(r)?r.answer.slice().reverse():[r.options.find(o=>!r.answer.includes(o.id)).id];
  TicModel.edit(s,r,wrong);assert(TicModel.confirm(s,r).accepted);assert(TicModel.answered(data,s,0));
  const saved=TicModel.sanitize(data,s);assert.deepEqual(saved.answers,s.answers);
  s.level='support';assert.deepEqual(saved.answers,s.answers);
  TicModel.edit(s,r,r.answer);assert(TicModel.confirm(s,r).correct);
  assert.equal(TicModel.confirm(s,r).emit,false);
  for(const labels of r.alternatives||[]){
   const used=[],ids=labels.map(label=>{const p=r.pieces.find(p=>p.label===label&&!used.includes(p.id));used.push(p.id);return p.id;});
   const t=TicModel.initial();TicModel.edit(t,r,ids);assert(TicModel.confirm(t,r).correct,'ordem alternativa aceite');
  }
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


def test_every_keyword_is_covered_by_the_repertoire_table():
    from scripts.m28p_cycle import readable_at
    cycle=source();words=sorted(motor.read_words(),key=lambda w:w['order']);slugs=[w['slug'] for w in words]
    for index,word in enumerate(words):
        assert readable_at(word['label'],word['syllables'],index,cycle['repertoire'],slugs),word['label']
        if index:
            assert not readable_at(word['label'],word['syllables'],index-1,cycle['repertoire'],slugs) or word['slug'] in {'menino'},word['label']


def test_discover_rounds_show_only_needed_syllables_and_honest_counts():
    from scripts.m28p_cycle import discover_rounds, formable
    import random
    pools=validate_cycle(source(),motor.read_words())
    for word in motor.read_words()[:3]:
        pool=pools[word['slug']]
        groups=discover_rounds(pool,random.Random(0))
        assert groups
        for group in groups:
            assert len(group['pieces'])<=8 and 2<=len(group['hidden'])<=3
            assert word['label'] not in {w['label'] for w in group['hidden']}
            assert all(formable(w['label'],group['pieces']) for w in group['hidden'])
            hidden={w['label'] for w in group['hidden']}
            # Nenhuma palavra do vocabulário (nem a palavra-chave da demonstração) se forma sem estar escondida.
            assert not [w['label'] for w in pool['words'] if len(w['syllables'])<=3 and w['label'] not in hidden and formable(w['label'],group['pieces'])]
    assert formable('ovo',['o','vo']) and not formable('ovo',['vo']) and not formable('nono',['no'])


def test_js_class_sentences_and_restore_in_either_order():
    template=(motor.ROOT/'scripts/templates/m28p-tic.html').read_text()
    model=template.split('/* BEGIN M28P TIC MODEL: funções puras verificáveis em Node. */')[1].split('/* END M28P TIC MODEL */')[0]
    js=model+"""
const assert=require('node:assert/strict');
const fixed=[{id:'r1',kind:'sentence',pieces:[{id:'p0',label:'A'},{id:'p1',label:'menina'}],answer:['p0','p1']}];
const sentences=[{id:'abc',text:'A menina!',tokens:['A','menina']}];
assert.equal(TicModel.classRounds(fixed,[{id:'h',text:'Avó, vê o guarda-chuva!',tokens:['Avó','vê','o','guarda-chuva']}])[0].target.text,'Avó, vê o guarda-chuva!');
const rounds=TicModel.classRounds(fixed,sentences);
assert.equal(rounds[0].id,'c-abc');assert.equal(rounds[0].target.text,'A menina!');
assert.deepEqual(rounds,TicModel.classRounds(fixed,sentences));
assert.equal(TicModel.classRounds(fixed,Array.from({length:5},(_,i)=>({...sentences[0],id:String(i)}))).length,4);
// Com várias frases da turma, a retoma volta à segunda frase em qualquer ordem de chegada.
{const many=[{id:'a1',text:'A uva.',tokens:['A','uva']},{id:'a2',text:'O ovo.',tokens:['O','ovo']}];
 const full=TicModel.classRounds(fixed,many);const st=TicModel.initial();
 TicModel.edit(st,full[0],full[0].answer);TicModel.confirm(st,full[0]);st.page=1;st.pageId='c-a2';
 const early=TicModel.sanitize({rounds:fixed},JSON.parse(JSON.stringify(st)));assert.equal(early.pageId,'c-a2');
 const merged=TicModel.retainState(st,early,fixed);
 assert.equal(TicModel.sanitize({rounds:full},merged).page,1);
 assert.equal(TicModel.sanitize({rounds:full},st).page,1);}
const raw=TicModel.initial();raw.page=0;raw.pageId='c-abc';
TicModel.edit(raw,rounds[0],rounds[0].answer);TicModel.confirm(raw,rounds[0]);
// A retoma volta à mesma frase mesmo quando as frases da turma chegam depois.
{const later={...TicModel.initial(),page:1,pageId:'r1'};const two=TicModel.classRounds(fixed,sentences);
 const st=TicModel.initial();TicModel.edit(st,two[0],two[0].answer);TicModel.confirm(st,two[0]);
 const restored=TicModel.sanitize({rounds:two},{...st,page:0,pageId:'r1'});assert.equal(restored.page,1);}
for(const restoreFirst of [true,false]){
 let saved=raw;
 if(restoreFirst){const early=TicModel.sanitize({rounds:fixed},raw);saved=TicModel.retainState(raw,early,fixed);}
 const clean=TicModel.sanitize({rounds},saved);
 assert.deepEqual(clean.answers['c-abc'],['p0','p1']);assert(clean.confirmed['c-abc']);
 TicModel.edit(clean,rounds[0],[]);
 const edited=TicModel.retainState(saved,clean,rounds);
 assert(!edited.confirmed['c-abc']);
}
"""
    result=subprocess.run(['node'],input=js,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
