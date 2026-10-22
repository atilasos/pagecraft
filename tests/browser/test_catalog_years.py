"""Catálogo real e variantes descartáveis, só numa sessão própria do Hub.

PAGECRAFT_TEST_CDP=http://127.0.0.1:<porta-da-sessão> uv run \
  --project /home/proteu/pagecraft --with playwright python -m pytest \
  tests/browser/test_catalog_years.py -q
"""

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

from server.publish import regenerate_catalog


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def catalog_origin(tmp_path_factory):
    root = tmp_path_factory.mktemp('catalog-years')
    shutil.copytree(ROOT / 'server' / 'static', root / 'server' / 'static')
    for name in ['index.html', 'viewer.html', 'm28p.html']:
        shutil.copy2(ROOT / name, root / name)
    for slug in ['tinkercad-pontes-3e4', 'menina', 'm28p-menina-blocos']:
        shutil.copytree(ROOT / 'activities' / slug, root / 'activities' / slug)
    # Different destination from its base, without editing a published activity.
    variant = root / 'activities' / 'menina-variante-teste'
    shutil.copytree(root / 'activities' / 'menina', variant)
    meta_path = variant / 'meta.json'
    meta = json.loads(meta_path.read_text())
    meta.update(slug=variant.name, title='M28P · Menina · Variante de teste',
                variantOf='menina', variantTitle='Variante de teste', years=[4])
    meta_path.write_text(json.dumps(meta))
    numeric = root / 'activities' / 'numeric-test'
    numeric.mkdir()
    (numeric / 'meta.json').write_text(json.dumps({'slug': numeric.name, 'title': 'Ano numérico', 'year': 3}))
    (root / 'activities' / 'second-year').mkdir()
    (root / 'activities' / 'second-year' / 'meta.json').write_text(json.dumps({'slug': 'second-year', 'year': 2}))
    regenerate_catalog(root)
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        port = connection.getsockname()[1]
    env = dict(os.environ, PAGECRAFT_REPO_ROOT=str(root), PAGECRAFT_DATA_DIR=str(root / 'data'),
               PAGECRAFT_ACTIVITIES_DIR=str(root / 'activities'), PAGECRAFT_CATALOG_PATH=str(root / 'catalog.json'),
               PAGECRAFT_PUBLIC_ORIGIN='', PAGECRAFT_TEACHER_ORIGIN='', PAGECRAFT_ACCESS_AUD='',
               PAGECRAFT_ACCESS_TEAM_DOMAIN='', PAGECRAFT_ACCESS_EMAIL='')
    origin = f'http://127.0.0.1:{port}'
    static = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    static_thread = threading.Thread(target=static.serve_forever, daemon=True)
    static_thread.start()
    with (root / 'server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server.app:app', '--host', '127.0.0.1', '--port', str(port)],
                                   cwd=ROOT, env=env, stdout=log, stderr=log)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail((root / 'server.log').read_text())
                try:
                    urllib.request.urlopen(origin + '/api/health', timeout=.2).close()
                    break
                except OSError:
                    time.sleep(.1)
            else:
                pytest.fail('Isolated catalog server did not start')
            yield {'public': f'http://127.0.0.1:{static.server_port}', 'studio': origin}
        finally:
            static.shutdown()
            static.server_close()
            static_thread.join()
            process.terminate()
            process.wait(timeout=10)


def public_year(page, value):
    page.locator(f'#yearFilters [data-year="{value}"]').click()


@pytest.mark.parametrize('viewport', [{'width': 1280, 'height': 900}, {'width': 390, 'height': 844}])
def test_public_tinkercad_in_both_years_and_numeric_year(page, catalog_origin, viewport):
    page.set_viewport_size(viewport)
    page.goto(catalog_origin['public'])
    page.locator('#search').fill('Tinkercad')
    for year in [3, 4]:
        public_year(page, year)
        assert page.locator('#generalList .card').count() == 1
        assert page.locator('#resultStatus').text_content() == '1 ficha visível · 1 atividade'
        assert page.locator('.stamp-main:visible').text_content() == '3.º e 4.º anos'
        assert page.locator('#generalList .action-open').get_attribute('href') == './activities/tinkercad-pontes-3e4/'
        assert page.locator('.stamp-main:visible').evaluate('(el) => el.scrollWidth <= el.clientWidth')
        if os.environ.get('PAGECRAFT_CATALOG_PROOF_DIR'):
            destination = Path(os.environ['PAGECRAFT_CATALOG_PROOF_DIR'])
            destination.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(destination / f'tinkercad-{year}-{viewport["width"]}.png'), full_page=True)
    public_year(page, 2)
    assert page.locator('#generalList .card').count() == 0
    assert page.locator('#resultStatus').text_content() == 'Sem resultados'
    public_year(page, 3)
    page.locator('#search').fill('Ano numérico')
    assert page.locator('#generalList .card').count() == 1
    assert page.locator('#generalList .meta').text_content().startswith('3.º ano')


def test_public_variant_independent_year_counts_and_unknown(page, catalog_origin):
    page.goto(catalog_origin['public'])
    page.locator('#search').fill('Variante de teste')
    public_year(page, 4)
    assert page.locator('#m28pList .variant:visible').count() == 1
    assert page.locator('#resultStatus').text_content() == '1 ficha visível · 1 atividade'
    assert page.locator('#m28pList .variant .action-open').get_attribute('href') == './activities/menina-variante-teste/'
    assert page.locator('#m28pList .card-row > .actions > .action-open').count() == 0
    assert page.locator('#m28pList .stamp-main').text_content() == '4.º ano'
    page.locator('#m28pList .variant .action-open').click()
    assert page.url.endswith('/activities/menina-variante-teste/')
    page.goto(catalog_origin['public'])
    page.locator('#search').fill('Variante de teste')
    public_year(page, 1)
    assert page.locator('#resultStatus').text_content() == 'Sem resultados'
    public_year(page, 'todos')
    page.locator('#search').fill('m28p-menina-blocos')
    assert page.locator('#m28pList .variant:visible').count() == 1
    assert page.locator('#m28pList .variant').inner_text().find('Sem ano indicado') >= 0
    for year in [1, 2, 3, 4]:
        public_year(page, year)
        assert page.locator('#resultStatus').text_content() == 'Sem resultados'


def teacher_year(page, year):
    page.get_by_role('button', name=f'{year}.º ano', exact=True).click()


def test_teacher_membership_labels_hidden_selection_and_unknown(page, catalog_origin):
    page.goto(catalog_origin['studio'] + '/teacher/class.html')
    page.locator('#picker-search').fill('Tinkercad')
    for year in [3, 4]:
        teacher_year(page, year)
        option = page.locator('#picker-list .activity-option')
        assert option.count() == 1
        assert '3.º e 4.º anos' in option.inner_text()
        teacher_year(page, year)  # toggle back to all
    teacher_year(page, 3)
    created = page.request.post(catalog_origin['studio'] + '/api/classes', data={'name': 'Turma descartável', 'year': 3, 'students': ['Teste']})
    assert created.ok
    page.reload()
    page.locator('#picker-search').fill('Tinkercad')
    teacher_year(page, 3)
    page.locator('#launch-class').select_option(created.json()['id'])
    page.locator('#picker-list .activity-option').click()
    assert page.locator('#picker-list [aria-pressed="true"]').count() == 1
    assert page.locator('#launch-btn').is_enabled()
    teacher_year(page, 2)
    assert page.locator('#picker-list .activity-option').count() == 0
    assert page.locator('#launch-btn').is_disabled()
    teacher_year(page, 2)
    page.locator('#picker-search').fill('Variante de teste')
    teacher_year(page, 4)
    assert page.locator('#picker-list .activity-option').count() == 1
    assert '4.º ano' in page.locator('#picker-list').inner_text()
    teacher_year(page, 4)
    teacher_year(page, 1)
    assert page.locator('#picker-list .activity-option').count() == 0
    teacher_year(page, 1)
    page.locator('#picker-search').fill('Mundo de blocos')
    assert page.locator('#picker-list .activity-option').count() == 1
    assert 'Sem ano indicado' in page.locator('#picker-list').inner_text()
    teacher_year(page, 1)
    assert page.locator('#picker-list .activity-option').count() == 0


def test_teacher_creation_catalog_shows_all_declared_years(page, catalog_origin):
    page.goto(catalog_origin['studio'] + '/teacher/')
    bridge = page.locator('#catalog li').filter(has_text='Tinkercad')
    assert '3.º e 4.º anos' in bridge.inner_text()
    blocks = page.locator('#catalog li').filter(has_text='Mundo de blocos')
    assert 'Sem ano indicado' in blocks.inner_text()
