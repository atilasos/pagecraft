"""Audita a coleção gerada, as fronteiras e o repertório usado nos jogos."""
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('m28p_tic', ROOT / 'scripts/build_m28p_tic.py')
motor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motor)


def content(path):
    return json.loads(re.search(r'<script id="m28p-content" type="application/json">(.*?)</script>', path.read_text(), re.S)[1])


def test_all_generated_games_are_complete_private_artifacts_with_offline_assets():
    from server.api.learning import ActivityInput
    paths = list((ROOT / 'drafts/m28p-v3').glob('*/*.html'))
    assert len(paths) == 168
    for path in paths:
        data = content(path)
        assert len(data['rounds']) == 4
        assert set(data['audio']) == {'start','word','instruction','hint','success','retry','finish'}
        assert all(value.startswith('data:audio/mpeg;base64,') and len(value) > 1000 for value in data['audio'].values())
        assert '<svg' in data['word']['image']
        markup = path.read_text()
        assert not re.search(r'<(?:script|link|img|audio)[^>]*(?:src|href)=["\']https?://', markup)
        metadata = ActivityInput.model_validate_json(path.with_name(path.stem + '-activity.json').read_text())
        assert metadata.requires_completion
        assert metadata.duration == 5
        assert (ROOT / 'drafts' / path.name).resolve() == path
        assert (ROOT / 'drafts' / (path.stem + '.md')).is_file()
        assert not (ROOT / 'activities' / path.stem).exists()


def test_generated_distractors_are_cumulative_and_each_answer_is_possible():
    words = motor.read_words()
    for word in words:
        allowed = {w['label'] for w in words if w['order'] <= word['order']}
        if word['order'] == 1:
            allowed.update(word['syllables'])
        for game in motor.GAMES:
            data = content(ROOT / f"drafts/m28p-v3/{word['slug']}/m28p-v3-{word['slug']}-{game}.html")
            for item in data['rounds']:
                if game in {'match','pairs','hunt'}:
                    assert {o['label'] for o in item['options']} <= allowed
                ids = {o['id'] for o in item.get('pieces', item['options'])}
                assert set(item['answer']) <= ids
                assert item['answer']
                if game in {'syllables','recall'}:
                    pieces = {o['id']:o['label'] for o in item['pieces']}
                    assert ''.join(pieces[i] for i in item['answer']) == word['label']


def test_first_word_does_not_require_future_words_and_flor_uses_letters():
    words = motor.read_words()
    girl = words[0]
    assert girl['label'] == 'menina'
    assert all(len(r['options']) == 1 for r in motor.rounds_for(girl,'pairs',words))
    assert [r['flipColumns'] for r in motor.rounds_for(girl,'pairs',words)] == [False,True,False,True]
    flower = next(w for w in words if w['slug'] == 'flor')
    assert flower['syllables'] == ['flor']
    for game in ['syllables','gap','recall']:
        for item in motor.rounds_for(flower,game,words):
            assert item['unit'] == 'letter'
            units = item.get('pieces', item['options'])
            assert {p['label'] for p in units} == set('flor')


@pytest.mark.parametrize('duration', [3,5,8])
def test_docspec_accepts_short_sessions_without_falsifying_duration(duration):
    from jsonschema import Draft202012Validator
    word = motor.read_words()[0]
    data = motor.content_for(word,'match',motor.read_words())
    doc = motor.spec_for(data,word)
    doc['duration'] = duration
    Draft202012Validator(json.loads((ROOT/'server/pipeline/schemas/docspec.schema.json').read_text())).validate(doc)


def test_content_cannot_escape_the_json_script_boundary():
    words=motor.read_words()
    data=motor.content_for(words[0],'match',words)
    doc=motor.spec_for(data,words[0])
    data['word']['image']='</script><img src=x onerror=alert(1)>'
    output=motor.render(data,doc)
    assert '</script><img src=x' not in output
    assert json.loads(re.search(r'<script id="m28p-content" type="application/json">(.*?)</script>',output,re.S)[1])['word']['image']==data['word']['image']


def test_verification_becomes_pending_when_the_artifact_changes(tmp_path,monkeypatch):
    import hashlib
    words=motor.read_words()
    word=words[0]
    data=motor.content_for(word,'match',words)
    doc=motor.spec_for(data,word)
    output=motor.render(data,doc)
    # Isolar aliases de drafts e avaliação para este ensaio de proveniência.
    monkeypatch.setattr(motor,'BASE',tmp_path/'drafts/m28p-v3')
    monkeypatch.setattr(motor,'ROOT',tmp_path)
    (tmp_path/'drafts').mkdir()
    motor.BASE.mkdir()
    (motor.BASE/'evaluation.json').write_text(json.dumps({'activities':{data['slug']:{'htmlSha256':hashlib.sha256(output.encode()).hexdigest()}}}))
    # spec/render dependem das fontes canónicas, já verificadas acima.
    monkeypatch.setattr(motor,'spec_for',lambda *_:doc)
    monkeypatch.setattr(motor,'render',lambda *_:output)
    motor.build(word,'match',words)
    manifest=motor.BASE/word['slug']/(data['slug']+'-run-manifest.json')
    assert json.loads(manifest.read_text())['checks']['browserEvaluation']=='passed'
    monkeypatch.setattr(motor,'render',lambda *_:output+' ')
    motor.build(word,'match',words)
    assert json.loads(manifest.read_text())['checks']['browserEvaluation']=='pending'
