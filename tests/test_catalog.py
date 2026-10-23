import json
import shutil
from pathlib import Path

import httpx
import pytest

from server.app import create_app
from server.api.catalog import list_activities
from server.catalog_years import activity_years, declared_years, validate_years
from server.publish import build_catalog


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(('value', 'expected'), [
    (3, [3]), ('3', [3]), (' 3 ', [3]), ('3.º ano', [3]),
    ('1.º ano (6-7 anos)', [1]), ('9-10 anos (4.º ano do 1.º CEB)', [4]),
    ('8-9 anos (3.º ano)', [3]), ('3.º e 4.º anos (8–10 anos)', [3, 4]),
    ('3º e 4º anos', [3, 4]), ('3.o / 4.o ano', [3, 4]),
    ('4.º, 3.º e 4.º anos', [3, 4]), ('1.º ao 4.º ano', [1, 2, 3, 4]),
    ('2.º–4.º anos', [2, 3, 4]), ('3 ano', [3]),
])
def test_declared_school_year_formats(value, expected):
    assert declared_years(value) == expected


@pytest.mark.parametrize('value', [
    '6-8 anos, ajustável', '3-4 anos', '3 e 4 anos', '8–10 anos',
    '', None, True, False, 7, 3.0, '13.º ano', '14 ano', '1.º ciclo',
])
def test_does_not_infer_school_years(value):
    assert declared_years(value) == []


@pytest.mark.parametrize('value', [None, 3, '3', [True], [False], [3.0], ['3'], [0], [5], {}])
def test_explicit_years_reject_invalid_declarations(value):
    with pytest.raises(ValueError, match='years'):
        validate_years(value)
    with pytest.raises(ValueError, match='years'):
        activity_years({'years': value, 'year': 3}, {'ageRange': '4.º ano'})


def test_explicit_years_have_precedence_including_empty():
    assert activity_years({'years': [4, 3, 4], 'year': 1}, {'ageRange': '2.º ano'}) == [3, 4]
    assert activity_years({'years': [], 'year': 1}, {'ageRange': '2.º ano'}) == []
    assert activity_years({'year': 3}, {'ageRange': '4.º ano'}) == [3]
    assert activity_years({'year': '8–10 anos'}, {'ageRange': '3.º e 4.º anos'}) == [3, 4]
    assert activity_years({'tags': ['3ano'], 'ageRange': '4.º ano'}, {
        'curriculum': {'ae': [{'year': '1.º ano'}]}, 'ageRange': '8–10 anos',
    }) == []


def test_real_catalog_and_api_share_years_without_changing_sources():
    catalog = {item['slug']: item for item in build_catalog(ROOT)['items']}
    api = {item['slug']: item for item in list_activities(ROOT / 'activities')}
    assert catalog.keys() == api.keys()
    for slug in api:
        assert catalog[slug]['years'] == api[slug]['years'], slug
        assert catalog[slug]['yearLabel'] == api[slug]['yearLabel'], slug
    bridge = api['tinkercad-pontes-3e4']
    assert bridge['years'] == [3, 4]
    assert bridge['year'] is None
    assert bridge['yearLabel'] == '3.º e 4.º anos (8–10 anos)'
    blocks = [item for item in api.values() if item['slug'].startswith('m28p-') and item['slug'].endswith('-blocos')]
    assert not blocks  # A coleção anterior foi arquivada, mantendo os ficheiros.
    for meta_path in (ROOT / 'activities').glob('*/meta.json'):
        meta = json.loads(meta_path.read_text())
        if meta.get('status') == 'archived':
            assert meta['slug'] not in api
            assert (meta_path.parent / 'index.html').is_file()


def test_archive_hides_both_catalogs_without_removing_content(tmp_path):
    for slug, status in [('active', 'published'), ('old', 'archived')]:
        directory = tmp_path / 'activities' / slug
        directory.mkdir(parents=True)
        (directory / 'meta.json').write_text(json.dumps({'slug': slug, 'status': status}))
        (directory / 'index.html').write_text('<p>Trabalho preservado</p>')
    assert [item['slug'] for item in build_catalog(tmp_path)['items']] == ['active']
    assert [item['slug'] for item in list_activities(tmp_path / 'activities')] == ['active']
    assert (tmp_path / 'activities' / 'old' / 'index.html').read_text() == '<p>Trabalho preservado</p>'


async def test_api_contract_facets_meta_and_teacher_boundary(tmp_path, monkeypatch):
    activities = tmp_path / 'activities'
    shutil.copytree(ROOT / 'activities' / 'tinkercad-pontes-3e4', activities / 'tinkercad-pontes-3e4')
    for slug, meta, docspec in [
        ('numeric', {'year': 2}, {}),
        ('unknown', {'year': '6–8 anos', 'tags': ['1ano']}, {'curriculum': {'ae': [{'year': 1}]}}),
        ('explicit', {'years': [4, 3, 4], 'year': 1}, {}),
        ('empty', {'years': [], 'year': 1}, {}),
        ('historical', {}, {'ageRange': '3.º ano'}),
    ]:
        dst = activities / slug
        dst.mkdir()
        (dst / 'meta.json').write_text(json.dumps({'slug': slug, **meta}))
        (dst / 'docspec.json').write_text(json.dumps(docspec))
    monkeypatch.setenv('PAGECRAFT_ACTIVITIES_DIR', str(activities))
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.get('/api/activities')).status_code == 401
            assert (await client.get('/teacher/')).status_code == 200
            response = await client.get('/api/activities')
            assert response.status_code == 200
            data = response.json()
            assert data['years'] == [2, 3, 4]  # AE year 1 is not a destination
            items = {item['slug']: item for item in data['items']}
            assert items['tinkercad-pontes-3e4']['years'] == [3, 4]
            assert items['numeric']['years'] == [2]
            assert items['numeric']['year'] == 2
            assert items['unknown']['years'] == items['empty']['years'] == []
            assert items['explicit']['years'] == [3, 4]
            assert items['explicit']['year'] is None
            assert items['historical']['years'] == [3]
            assert (await client.get('/api/meta')).json()['activities'] == data['items']
