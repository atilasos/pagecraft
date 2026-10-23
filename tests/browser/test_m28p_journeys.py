"""Percorre os artefactos reais num browser aberto pelo Agent Browser Hub."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENTS = sorted((ROOT / 'drafts/m28p-v2').glob('*/content.json'))


@pytest.fixture(scope='module')
def journey_origin():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize('content_path', CONTENTS, ids=lambda p: p.parent.name)
def test_every_real_journey_accepts_answers_and_restores_without_attempts(page, journey_origin, content_path):
    data = json.loads(content_path.read_text())
    slug = data['slug']
    page.set_viewport_size({'width': 390 if data['order'] % 2 else 1280, 'height': 844})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.add_init_script("window.observed=[]; window.addEventListener('message',e=>{if(e.data?.pagecraft===1)window.observed.push(e.data)});")
    page.goto(f'{journey_origin}/drafts/m28p-v2/{slug}/m28p-v2-{slug}.html')
    page.locator('#start').click()
    for index, item in enumerate(data['pages']):
        assert page.locator('#stage-select').input_value() == str(index)
        assert page.locator('#next').is_disabled()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if item['phase'] in ['transfer', 'review']:
            assert page.locator('#support-panel').is_hidden()
        if item['type'] == 'choice':
            # Uma resposta errada continua a ser uma página respondida.
            wrong = next(value for value in item['options'] if value != item['answer'])
            page.locator('.choices').get_by_role('button', name=wrong, exact=True).click()
            assert 'Experimenta outra vez' in page.locator('#task-feedback').inner_text()
            assert page.locator('#next').is_enabled()
            for level in ['support', 'challenge', 'intermediate']:
                page.locator(f'[data-level="{level}"]').click()
                assert page.locator('.choices').get_by_role('button', name=wrong, exact=True).get_attribute('aria-pressed') == 'true'
                assert page.locator('#next').is_enabled()
        elif item['type'] == 'order':
            for piece in range(len(item['pieces'])):
                page.locator(f'[data-piece="{piece}"]').click()
            page.get_by_role('button', name='Confirmar a minha sequência', exact=True).click()
        elif item['type'] == 'write':
            page.locator('#open-answer').fill('É a minha mensagem, escrita com ajuda.')
            page.get_by_role('button', name='Guardar esta resposta', exact=True).click()
            assert 'guardado' in page.locator('#task-feedback').inner_text()
        else:
            page.get_by_role('button', name='Já conversei com um adulto', exact=True).click()
        assert page.locator('#next').is_enabled()
        if index == len(data['pages']) // 2:
            page.reload()
            assert page.locator('#stage-select').input_value() == str(index)
            assert page.locator('#next').is_enabled()
            assert not page.evaluate("observed.some(e=>['attempt','assessment_result','unit_started'].includes(e.type))")
        page.locator('#next').click()
    assert page.locator('#reflection').is_visible()
    assert page.locator('#reflection-fields select').count() == len(data['criteria'])
    assert not errors


def test_real_host_registers_private_draft_and_restores_responses(page, studio_origin):
    registration = json.loads((ROOT / 'drafts/m28p-v2-gema-activity.json').read_text())
    page.request.get(studio_origin + '/api/teacher-bootstrap')
    response = page.request.post(studio_origin + '/api/learning/activities', data=registration)
    assert response.status == 201, response.text()
    code = response.json()['code']
    # Um visitante sem cookie de professor não pode abrir o rascunho.
    visitor = page.context.browser.new_context()
    try:
        assert visitor.request.get(studio_origin + '/' + code).status == 404
    finally:
        visitor.close()
    page.goto(studio_origin + '/' + code)
    page.get_by_label('Como te chamas?').fill('Ensaio descartável M28P')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    lesson.locator('#start').click()
    lesson.get_by_role('button', name='Já conversei com um adulto', exact=True).click()
    lesson.locator('#next').click()
    data = json.loads((ROOT / 'drafts/m28p-v2/gema/content.json').read_text())
    item = data['pages'][1]
    wrong = next(option for option in item['options'] if option != item['answer'])
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok and any(
        event['type'] == 'attempt' for event in r.request.post_data_json['events']
    )):
        lesson.locator('.choices').get_by_role('button', name=wrong, exact=True).click()
    before = page.request.get(studio_origin + '/api/learning/me').json()
    attempts = len([event for event in before['events'] if event['type'] == 'attempt'])
    assert attempts == 1
    page.reload()
    lesson = page.frame_locator('#lesson')
    from playwright.sync_api import expect
    expect(lesson.locator('#stage-select')).to_have_value('1')
    expect(lesson.locator('.choices').get_by_role('button', name=wrong, exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(lesson.locator('#next')).to_be_enabled()
    lesson.locator('#next').click()
    after = page.request.get(studio_origin + '/api/learning/me').json()
    assert len([event for event in after['events'] if event['type'] == 'attempt']) == attempts
    assert after['preview'] is True
