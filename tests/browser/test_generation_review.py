"""Review uses each job's actual bytes, on a disposable Studio and Hub browser."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def generation_studio(tmp_path_factory):
    root = tmp_path_factory.mktemp('generation-review-studio')
    shutil.copytree(ROOT / 'server/static', root / 'server/static')
    (root / 'activities').mkdir()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    # Only fixtures answer generation and knowledge requests. No real AI calls.
    launcher = root / 'launch.py'
    launcher.write_text('''
import os
import uvicorn
from server import app as app_module
from fakes import FakeProvider
from test_runner import EVAL_OK, EVAL_FAIL, GOOD_HTML, NoKnowledge, pipeline_responses
responses = []
for marker, evaluation in [('A revista', EVAL_OK), ('B falhada', EVAL_FAIL), ('C alterada', EVAL_OK)]:
    html = GOOD_HTML.replace('<main ', '<h1>Geração ' + marker + '</h1><main ')
    responses += pipeline_responses(evaluation, built={'html': html, 'notes': ''})
provider = FakeProvider(responses)
NoKnowledge.list_subjects = lambda self: []
app_module.build_generation_provider = lambda config: provider
app_module.build_feedback_provider = lambda config: FakeProvider([])
app_module.WikiClient = lambda *args, **kwargs: NoKnowledge()
app_module.AEClient = lambda *args, **kwargs: NoKnowledge()
uvicorn.run(app_module.create_app(), host='127.0.0.1', port=int(os.environ['GENERATION_TEST_PORT']))
''')
    env = dict(os.environ, PAGECRAFT_REPO_ROOT=str(root), PAGECRAFT_DATA_DIR=str(root / 'data'),
               PAGECRAFT_OUTPUTS_DIR=str(root / 'outputs'), PAGECRAFT_ACTIVITIES_DIR=str(root / 'activities'),
               PAGECRAFT_CATALOG_PATH=str(root / 'catalog.json'), PAGECRAFT_MAX_ITERATIONS='1',
               PAGECRAFT_PUBLIC_ORIGIN='', PAGECRAFT_TEACHER_ORIGIN='', PAGECRAFT_ACCESS_AUD='',
               PAGECRAFT_ACCESS_TEAM_DOMAIN='', PAGECRAFT_ACCESS_EMAIL='',
               GENERATION_TEST_PORT=str(port), PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / 'tests')]))
    origin = f'http://127.0.0.1:{port}'
    with (root / 'server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, str(launcher)], cwd=ROOT, env=env, stdout=log, stderr=log)
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
                pytest.fail('Disposable generation Studio did not start')
            yield origin, root
        finally:
            process.terminate()
            process.wait(timeout=10)


def test_review_preview_approval_and_changed_artifacts_in_studio(page, generation_studio):
    from playwright.sync_api import expect

    origin, root = generation_studio
    page.goto(origin + '/teacher/')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def generate():
        if not page.locator('#create-activity').get_attribute('open') == '':
            page.locator('#create-activity > summary').click()
        page.locator('#topic').fill('Frações')
        page.locator('#subject').select_option('Matemática')
        page.locator('#year').select_option('3')
        with page.expect_response(lambda r: r.url.endswith('/api/jobs') and r.request.method == 'POST') as created:
            page.get_by_role('button', name='Gerar atividade', exact=True).click()
        response = created.value
        assert response.ok
        job_id = response.json()['id']
        for _ in range(100):
            job = page.request.get(origin + '/api/jobs/' + job_id).json()
            if job['status'] in {'awaiting_review', 'failed'}:
                return job
            time.sleep(.05)
        pytest.fail('Generation did not finish')

    a, b = generate(), generate()
    assert a['status'] == 'awaiting_review' and b['status'] == 'failed'
    assert a['slug'] != b['slug']
    page.reload()
    card_a = page.locator('#job-' + a['id'])
    card_b = page.locator('#job-' + b['id'])
    expect(card_a.get_by_role('link', name='pré-visualizar')).to_have_attribute('href', a['preview_url'])
    expect(card_b.get_by_role('link', name='pré-visualizar')).to_have_attribute('href', b['preview_url'])
    with page.expect_popup() as popup:
        card_a.get_by_role('link', name='pré-visualizar').click()
    preview = popup.value
    expect(preview.get_by_role('heading', name='Geração A revista')).to_be_visible()
    assert 'Geração B falhada' not in preview.content()
    preview.close()
    reviewed = Path(a['artifacts']['html']).read_bytes()
    card_a.get_by_role('button', name='Aprovar e publicar').click()
    expect(page.locator('#jobs-feedback')).to_contain_text('Atividade publicada')
    page.locator('#job-history > summary').click()
    expect(card_a.get_by_text('publicada', exact=True)).to_be_visible()
    assert (root / 'activities' / a['slug'] / 'index.html').read_bytes() == reviewed
    expect(card_b.get_by_role('button', name='Publicar mesmo assim (decisão do professor)')).to_be_visible()
    assert not (root / 'activities' / b['slug']).exists()
    assert json.loads((root / 'catalog.json').read_text())['count'] == 1

    c = generate()
    page.reload()
    card_c = page.locator('#job-' + c['id'])
    expect(card_c.get_by_role('button', name='Aprovar e publicar')).to_be_visible()
    Path(c['artifacts']['html']).write_text('alterada após a revisão')
    card_c.get_by_role('button', name='Aprovar e publicar').click()
    expect(card_c.locator('[aria-live]')).to_contain_text('mudaram após a revisão')
    expect(card_c.get_by_role('button', name='Aprovar e publicar')).to_be_enabled()
    response = page.request.get(origin + c['preview_url'])
    assert response.status == 409
    assert not (root / 'activities' / c['slug']).exists()
    assert (root / 'activities' / a['slug'] / 'index.html').read_bytes() == reviewed
    assert errors == []
    screenshot = root / 'generation-review.png'
    page.screenshot(path=str(screenshot), full_page=True)
    print(f'Browser evidence: {screenshot}')
