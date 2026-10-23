"""A coleção inteira preserva os itens novos e o HTML corresponde à autoria."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from scripts.audit_m28p_corpus import audit

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def corpus_copy(tmp_path):
    for source in (ROOT / 'drafts/m28p-v2').glob('*/content.json'):
        target = tmp_path / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (tmp_path / 'docs').mkdir()
    shutil.copyfile(ROOT / 'docs/m28p-corpus-reservado.json', tmp_path / 'docs/m28p-corpus-reservado.json')
    return tmp_path


def test_real_collection_has_two_unexposed_items_per_word():
    report = audit(ROOT)
    assert report['percursos'] == 28
    assert report['reservas'] == report['reservas_distintas'] == 56
    assert report['erros'] == []


def test_a_later_item_cannot_be_exposed_earlier(corpus_copy):
    source = corpus_copy / 'drafts/m28p-v2/menina/content.json'
    data = json.loads(source.read_text())
    data['pages'][0]['text'] = 'floreira'
    source.write_text(json.dumps(data))
    assert any('floreira' in error and 'menina:1:text' in error for error in audit(corpus_copy)['erros'])


def test_a_card_shown_by_the_adult_counts_as_prior_exposure(corpus_copy):
    source = corpus_copy / 'docs/m28p-corpus-reservado.json'
    rows = json.loads(source.read_text())
    rows[0]['cartoes'][0]['itens'].append('floreira')
    source.write_text(json.dumps(rows))
    content = corpus_copy / 'drafts/m28p-v2/menina/content.json'
    data = json.loads(content.read_text())
    data['pages'][rows[0]['cartoes'][0]['pagina'] - 1]['adultPrompt'] += ' Mostre também floreira.'
    content.write_text(json.dumps(data))
    assert any('floreira' in error and 'menina:8:cartao' in error for error in audit(corpus_copy)['erros'])


def test_the_reservations_cannot_be_reused(corpus_copy):
    source = corpus_copy / 'docs/m28p-corpus-reservado.json'
    rows = json.loads(source.read_text())
    rows[1]['inicial']['item'] = rows[0]['inicial']['item']
    source.write_text(json.dumps(rows))
    assert any('duplicados' in error for error in audit(corpus_copy)['erros'])


def test_committed_journeys_are_generated_from_the_current_content():
    module_spec = importlib.util.spec_from_file_location('m28p_motor', ROOT / 'scripts/build_m28p_journeys.py')
    motor = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(motor)
    for source in (ROOT / 'drafts/m28p-v2').glob('*/content.json'):
        data = json.loads(source.read_text())
        motor.validate_content(data)
        spec = motor.docspec_for(data)
        stem = 'm28p-v2-' + data['slug']
        assert json.loads((source.parent / (stem + '-docspec.json')).read_text()) == spec
        assert (source.parent / (stem + '.html')).read_text() == motor.render_html(data, spec)
