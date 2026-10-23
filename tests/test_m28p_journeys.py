"""Contrato de autoria e comportamento de estado dos novos percursos, sem publicar."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import pytest
from jsonschema import Draft202012Validator
from server.activity_support import support_configuration
from server.api.classroom import EventsRequest
from server.api.learning import ActivityInput, Event

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('m28p_journeys', ROOT / 'scripts/build_m28p_journeys.py')
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


@pytest.fixture
def content():
    hints = [{'individual': 'Compara uma parte de cada vez.', 'group': 'Comparem uma parte de cada vez.'},
             {'individual': 'Explica ao adulto o que já tentaste.', 'group': 'Expliquem ao adulto o que já tentaram.'}]
    def page(phase, kind, index, **extra):
        result = {'id': f'passo-{index}', 'session': min(4, (index - 1) // 4 + 1), 'phase': phase,
                  'type': kind, 'title': 'Descobrir palavras', 'prompt': 'Experimenta o pedido.', 'hints': copy.deepcopy(hints)}
        if kind == 'choice':result.update(options=['menina', 'menino', 'mana'], answer='menina')
        if kind == 'order':result.update(pieces=['na', 'me', 'ni'], answer=['me', 'ni', 'na'])
        if kind == 'oral' or phase == 'code':result['adultPrompt'] = 'O adulto modela e escuta. O botão é uma declaração.'
        return dict(result, **extra)
    pages = [page('context','oral',1),page('recognition','choice',2),page('syllables','order',3),
             page('code','oral',4),page('code','choice',5),page('transfer','choice',6),page('transfer','oral',7),
             page('comprehension','choice',8),page('comprehension','choice',9),page('writing','write',10),
             page('writing','oral',11),page('communication','oral',12),page('review','choice',13),page('review','oral',14)]
    return {'slug':'menina','word':'menina','order':1,'syllables':['me','ni','na'],
            'phonologyNotes':'Não confundir sílaba oral e translineação.', 'prerequisites':['Conversa com adulto.'],
            'assistedReading':'O adulto lê os pedidos. Nos itens de revisão escuta a criança.',
            'objectives':['Analisar a palavra.', 'Ler e escrever com sentido.'],
            'criteria':['Relaciono com uma experiência.', 'Leio e explico.', 'Escrevo para alguém.'],
            'sessions':[{'title':f'Sessão {i}', 'minutes':8} for i in range(1,5)],'pages':pages}


def test_generates_real_support_font_canonical_bridge_and_valid_docspec(content, tmp_path):
    folder=tmp_path/'menina';folder.mkdir();source=folder/'content.json';source.write_text(json.dumps(content))
    result=motor.build(source)
    assert result['pages']==14
    spec=json.loads((folder/'m28p-v2-menina-docspec.json').read_text())
    Draft202012Validator(json.loads((ROOT/'server/pipeline/schemas/docspec.schema.json').read_text())).validate(spec)
    assert sum(unit['duration'] for unit in spec['units'])==spec['duration']==32
    for session_number,session in enumerate(content['sessions'],1):
        assert sum(spec['units'][i]['duration'] for i,p in enumerate(content['pages']) if p['session']==session_number)==session['minutes']
    output=(folder/'m28p-v2-menina.html').read_text()
    assert 'PageCraftSupport.configure(' in output and 'data:font/woff2;base64,' in output
    assert motor.canonical_bridge() in output
    assert 'fetch(' not in output and '<script src=' not in output
    assert 'data-pagecraft-support' in output
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    motor.build(source)
    assert before=={p.name:p.read_bytes() for p in folder.iterdir()}
    manifest=json.loads((folder/'m28p-v2-menina-run-manifest.json').read_text())
    assert manifest['checks']['browserEvaluation']=='pending'
    assert manifest['publication']=='not-published'
    registration=ActivityInput.model_validate(json.loads((folder/'m28p-v2-menina-activity.json').read_text()))
    assert registration.slug=='m28p-v2-menina'
    assert registration.requires_completion is True


def test_untrusted_content_cannot_break_out_of_script(content):
    content['pages'][0]['text']='</script><img src=x onerror=alert(1)>'
    output=motor.render_html(content,motor.docspec_for(content))
    assert '</script><img src=x' not in output
    encoded=re.search(r'<script id="m28p-content" type="application/json">(.*?)</script>',output,re.S).group(1)
    assert json.loads(encoded)['pages'][0]['text']==content['pages'][0]['text']


@pytest.mark.parametrize('change,message',[
    (lambda d:d.update(syllables=['me','nina','a']),'recompor'),
    (lambda d:d['pages'][3].pop('adultPrompt'),'adultPrompt'),
    (lambda d:d['pages'][0].update(answer='sim'),'não têm resposta correta'),
    (lambda d:d['pages'][1].update(answer='casa'),'não pertence'),
    (lambda d:d['pages'][2].update(answer=['me','ni','ni']),'mesmas peças'),
    (lambda d:d['pages'][13].update(type='choice',options=['a','b'],answer='a'),'observação oral'),
    (lambda d:d['pages'][0].update(session=2),'Sessões devem estar em ordem'),
    (lambda d:d['pages'][0]['hints'][1].update(individual=d['pages'][0]['hints'][0]['individual']),'distintas'),
])
def test_rejects_authoring_errors(content,change,message):
    change(content)
    with pytest.raises(ValueError,match=message):motor.validate_content(content)


def test_oral_digraphs_are_preserved_not_resegmented(content):
    content.update(slug='cigarra',word='cigarra',syllables=['ci','ga','rra'])
    motor.validate_content(content)
    assert content['syllables']==['ci','ga','rra']


def test_checkpoint_will_fit_the_host_before_generating(content):
    for page in content['pages']:
        page['type']='write'
        page.pop('answer',None)
    with pytest.raises(ValueError,match='4096 bytes'):
        motor.validate_content(content)


@pytest.mark.parametrize('writing', ['€'*180, '🦉'*90, '\t\n\r'*59+'fim'])
def test_maximum_valid_writing_checkpoint_fits_both_http_boundaries(content, writing):
    for index in [3, 10]:
        content['pages'][index]['type']='write'
    motor.validate_content(content)
    answers={p['id']: p['answer'] if p['type']=='choice' else list(range(len(p['pieces'])))
             if p['type']=='order' else True if p['type']=='oral' else writing for p in content['pages']}
    payload={'activity':'m28p-v2-menina','version':1,'readyForReflection':False,
             'state':{'version':1,'page':13,'level':'intermediate','answers':answers,
                      'confirmed':dict.fromkeys(answers,True)}}
    event={'id':'maximum-writing','type':'activity_state','payload':payload}
    Event.model_validate(event)
    EventsRequest.model_validate({'events':[event]})


def test_pure_runtime_preserves_wrong_answers_levels_and_safe_restore(content):
    template=(ROOT/'scripts/templates/m28p-journey.html').read_text()
    core=template.split('/* BEGIN M28P MODEL:')[1].split('*/',1)[1].split('/* END M28P MODEL */')[0]
    script=core+'\nconst data='+json.dumps(content)+';\n'+r'''
const assert=require('node:assert/strict');
let state=JourneyModel.initial();
assert.equal(JourneyModel.accessible(data,state,1),false);
assert.equal(JourneyModel.complete(data,state),false);
state.answers['passo-1']=true;state.confirmed['passo-1']=true;
assert.equal(JourneyModel.accessible(data,state,1),true);
state.answers['passo-2']='menino';state.confirmed['passo-2']=true;
assert.equal(JourneyModel.correct(data.pages[1],'menino'),false);
assert.equal(JourneyModel.answered(data,state,1),true);
assert.equal(JourneyModel.accessible(data,state,2),true);
state.page=2;state.level='challenge';
const restored=JourneyModel.sanitize(data,state);
assert.deepEqual(restored,state);
assert.equal(restored.answers['passo-2'],'menino');
state.answers['passo-3']=[1,2,0];state.confirmed['passo-3']=true;
assert.equal(JourneyModel.correct(data.pages[2],state.answers['passo-3']),true);
assert.equal(JourneyModel.validAnswer(data.pages[2],[1,1,0]),false);
assert.equal(JourneyModel.correct(data.pages[0],true),null);
assert.equal(JourneyModel.correct(data.pages[9],'O meu texto'),null);
assert.equal(JourneyModel.validAnswer(data.pages[9],'   '),false);
assert.equal(JourneyModel.validAnswer(data.pages[9],'Quero contar algo.'),true);
assert.equal(JourneyModel.validAnswer(data.pages[9],'a\u0000b'),false);
assert.equal(JourneyModel.normalizeWriting('a\u0000\u000bb\n\t\rc'),'ab\n\t\rc');
assert.equal(JourneyModel.normalizeWriting('a'.repeat(179)+'🦉'),'a'.repeat(179));
assert.equal(JourneyModel.normalizeWriting('a\ud800b\udc00'),'ab');
const pasted=JourneyModel.sanitize(data,{version:1,answers:{'passo-10':'a\u0000b'},confirmed:{'passo-10':true}});
assert.equal(pasted.answers['passo-10'],'ab');assert.equal(pasted.confirmed['passo-10'],true);
assert.equal(JourneyModel.noHints(data.pages[5]),true);
assert.equal(JourneyModel.noHints(data.pages[12]),true);
assert.equal(JourneyModel.noHints(data.pages[1]),false);
const broken=JourneyModel.sanitize(data,{version:1,page:13,level:'inventado',answers:{'passo-1':'sim','passo-2':'desconhecido','passo-3':[1,1,99]},confirmed:{'passo-1':true,'passo-2':true,'passo-3':true}});
assert.equal(broken.page,-1);assert.equal(broken.level,'intermediate');
assert.equal(Object.keys(broken.confirmed).length,0);
assert.deepEqual(broken.answers['passo-3'],[1]);
console.log('runtime state checks passed');
'''
    result=subprocess.run(['node','-e',script],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'runtime state checks passed' in result.stdout


def test_validate_only_does_not_write_and_index_is_private(content,tmp_path):
    folder=tmp_path/'menina';folder.mkdir();source=folder/'content.json';source.write_text(json.dumps(content))
    result=motor.build(source,validate_only=True)
    assert list(folder.iterdir())==[source]
    motor.build_index(tmp_path,[result])
    index=(tmp_path/'index.html').read_text()
    assert 'menina/m28p-v2-menina.html' in index
    assert 'menina/guia-docente.md' in index
    assert 'ainda não estão publicados para os alunos' in index


def test_runtime_restore_and_hint_revision_against_the_shared_support(content):
    configuration=support_configuration(motor.docspec_for(content), 'm28p-v2-menina')
    result=subprocess.run(['node', str(ROOT/'tests/js/m28p_journey.test.cjs')],
                          input=json.dumps({'content': content, 'support': configuration}),
                          capture_output=True, text=True, cwd=ROOT)
    assert result.returncode==0, result.stdout+'\n'+result.stderr
