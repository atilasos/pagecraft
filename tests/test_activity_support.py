import copy
import json
from pathlib import Path
import subprocess

import pytest
from jsonschema import ValidationError

from server.activity_support import embed_activity_support, support_configuration

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / 'tests/fixtures/support-examples.json').read_text())
HTML = '<!doctype html><html lang="pt-PT"><body><section id="u1"><aside data-pagecraft-support="u1"></aside></section></body></html>'


@pytest.mark.parametrize('spec', EXAMPLES, ids=lambda spec:spec['slug'])
def test_each_topic_compiles_its_own_hints_without_a_canva_dependency(spec):
    config=support_configuration(spec)
    assert config['activity']==spec['slug']
    assert config['units']['u1']['objective']==spec['units'][0]['support']['objective']
    html=embed_activity_support(HTML,spec)
    assert spec['units'][0]['support']['obstacles'][0]['hints'][0]['text']['pt']['individual'] in html
    assert 'canva' not in html.lower()
    assert '<script src=' not in html and 'fetch(' not in html
    assert embed_activity_support(html,spec)==html


def test_archive_without_support_is_preserved_and_partial_support_is_rejected():
    assert embed_activity_support(HTML,{'units':[{}]})==HTML
    with pytest.raises(ValueError,match='Falta o plano'):
        support_configuration({'support':{'version':'v1'},'units':[{'summary':'Etapa'}]})
    with pytest.raises(ValueError,match='support.version'):
        support_configuration({'units':[{'support':{}}]})


def test_support_schema_requires_progression_modes_and_requested_languages():
    spec=copy.deepcopy(EXAMPLES[0])
    hints=spec['units'][0]['support']['obstacles'][0]['hints']
    hints.pop()
    with pytest.raises(ValidationError):support_configuration(spec)
    spec=copy.deepcopy(EXAMPLES[0])
    del spec['units'][0]['support']['obstacles'][0]['hints'][0]['text']['en']
    with pytest.raises(ValueError,match='en'):support_configuration(spec)
    spec=copy.deepcopy(EXAMPLES[0])
    hints=spec['units'][0]['support']['obstacles'][0]['hints']
    hints[1]['text']=copy.deepcopy(hints[0]['text'])
    with pytest.raises(ValueError,match='abordagens diferentes'):support_configuration(spec)


def test_embedded_plan_cannot_close_the_script():
    spec=copy.deepcopy(EXAMPLES[1]);spec['topic']='</script><img src=x>'
    spec['units'][0]['support']['objective']='</script><img src=x>'
    html=embed_activity_support(HTML,spec)
    assert '</script><img' not in html
    assert '\\u003c/script>' in html


def test_cli_embeds_the_plan_in_the_generated_html(tmp_path):
    spec=tmp_path/'rever-convite-docspec.json';spec.write_text(json.dumps(EXAMPLES[1]))
    activity=tmp_path/'rever-convite.html';activity.write_text(HTML)
    result=subprocess.run([str(Path(__import__('sys').executable)),str(ROOT/'scripts/embed_activity_support.py'),
                           '--activity',str(activity),'--docspec',str(spec)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert 'PageCraftSupport.configure(' in activity.read_text()
