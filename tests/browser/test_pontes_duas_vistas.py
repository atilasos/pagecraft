"""Private bridge draft: real Chromium owned by Agent Browser Hub, no production writes.

Run after opening a Hub session: PAGECRAFT_TEST_CDP=<its cdp_url>
uv run --project /home/proteu/pagecraft --with playwright pytest tests/browser/test_pontes_duas_vistas.py -q
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SLUG = 'pontes-duas-vistas'
DRAFT = ROOT / 'drafts' / (SLUG + '.html')
PROOF = ROOT / 'drafts'


@pytest.fixture(scope='module')
def pontes_origin():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('?')[0]
            if path == '/host':
                content = b'''<!doctype html><html><body><iframe id="lesson" src="/lesson"></iframe><script>
window.events=[]; addEventListener('message',e=>{if(e.data?.pagecraft===1)events.push(e.data)});
window.restore=(events=[])=>{const frame=document.querySelector('iframe').contentWindow;frame.postMessage({pagecraft:1,type:'learning_preferences',payload:{route:'learning',language:'pt'}},'*');frame.postMessage({pagecraft:1,type:'learning_restore',payload:{events}},'*')};
</script></body></html>'''
            elif path == '/lesson':
                content = DRAFT.read_bytes()
            elif path == '/support-modal.js':
                content = (ROOT / 'server/static/student/support-modal.js').read_bytes()
            elif path in ['/canonical-learning', '/canonical-student']:
                frame_id = 'lesson' if path.endswith('learning') else 'activity-frame'
                content = ('<!doctype html><html><body><button>Controlo exterior</button>'
                           f'<iframe id="{frame_id}" src="/lesson"></iframe>'
                           '<script src="/support-modal.js"></script></body></html>').encode()
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', ('text/javascript' if path.endswith('.js') else 'text/html') + '; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture(scope='module')
def pontes_studio(tmp_path_factory):
    root = tmp_path_factory.mktemp('pontes-private-studio')
    (root / 'drafts').mkdir()
    (root / 'activities').mkdir()
    shutil.copytree(ROOT / 'server/static', root / 'server/static')
    shutil.copyfile(DRAFT, root / 'drafts' / DRAFT.name)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = dict(os.environ)
    for key, value in {'REPO_ROOT':root, 'DATA_DIR':root/'data', 'OUTPUTS_DIR':root/'outputs',
                       'ACTIVITIES_DIR':root/'activities', 'CATALOG_PATH':root/'catalog.json',
                       'PUBLIC_ORIGIN':'', 'TEACHER_ORIGIN':'', 'ACCESS_AUD':'',
                       'ACCESS_TEAM_DOMAIN':'', 'ACCESS_EMAIL':''}.items():
        env['PAGECRAFT_' + key] = str(value)
    origin = f'http://127.0.0.1:{port}'
    with (root / 'server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server.app:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=log)
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
                pytest.fail('Disposable bridge Studio did not start')
            yield origin
            assert not list((root / 'activities').iterdir())
            assert not (root / 'catalog.json').exists()
        finally:
            process.terminate()
            process.wait(timeout=10)


def choose(page, name, value):
    page.locator(f'input[name="{name}"][value="{value}"]').check()


def predict(page):
    choose(page, 'initialHypothesis', 'top')
    choose(page, 'predictionA', 'stopped')
    choose(page, 'predictionB', 'crossed')
    page.locator('#save-predictions').click()
    page.locator('#next').click()


def trials(page):
    predict(page)
    page.locator('#test-a').click()
    page.locator('#lower-right').click()
    page.locator('#test-b').click()
    page.locator('#next').click()


def explain(page, oral=False):
    choose(page, 'changedVariable', 'left')
    page.locator('#confirm-variable').click()
    choose(page, 'currentHypothesis', 'top')
    if oral:
        page.locator('#explained-orally').check()
    else:
        page.locator('#explanation').fill('De cima parecem iguais. Em A atravessa e em B para.')
    page.locator('#next').click()


def peer(page, conclusion='found', oral=False):
    page.locator('#test-peer').click()
    choose(page, 'peerConclusion', conclusion)
    if oral:
        page.locator('#peer-oral').check()
    else:
        page.locator('#peer-comment').fill('Com 1 bloco direito para, apesar de parecer igual de cima.')
        page.locator('#peer-comment').blur()


def saved(page):
    return page.evaluate("JSON.parse(sessionStorage.getItem('pagecraft-draft:pontes-duas-vistas'))")


def support(page, unit):
    from playwright.sync_api import expect
    panel = page.locator(f'[data-pagecraft-support="u{unit}"]')
    page.evaluate('()=>{window.speechCalls=[]; speechSynthesis.speak=(u)=>speechCalls.push(u.text)}')
    panel.locator('[data-support-action="hint"]').click()
    first = panel.locator('.pc-support-action').inner_text()
    spec = json.loads((ROOT / f'drafts/{SLUG}-docspec.json').read_text())
    hints = spec['units'][unit-1]['support']['obstacles'][0]['hints']
    assert first == hints[0]['text']['pt']['individual']
    assert page.evaluate('speechCalls') == []
    panel.locator('[data-support-action="listen"]').click()
    assert page.evaluate('speechCalls') == [first]
    panel.locator('[data-support-action="stuck"]').click()
    second = panel.locator('.pc-support-action').inner_text()
    assert second == hints[1]['text']['pt']['individual'] and second != first
    panel.locator('[data-support-action="teacher"]').click()
    expect(panel.locator('.pc-support-notice')).to_contain_text('professor')
    return first, second


def test_predictions_discovery_and_single_variable(page, pontes_origin):
    from playwright.sync_api import expect
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(pontes_origin + '/lesson')
    for target in ['#next', '[data-step="3"]']:
        page.locator(target).focus()
        page.keyboard.press('Enter')
        expect(page.locator('#u1')).to_be_visible()
        expect(page.locator('#navigation-status')).to_contain_text('hipótese inicial')
    assert page.locator('#u1 .side-view').count() == 0
    assert 'bloco' not in page.locator('#u1').inner_text()
    support(page, 1)
    choose(page, 'predictionA', 'stopped')
    choose(page, 'predictionB', 'crossed')
    choose(page, 'initialHypothesis', 'top')
    page.locator('#next').focus()
    page.keyboard.press('Enter')
    expect(page.locator('#navigation-status')).to_contain_text('Guardar previsões')
    page.locator('#save-predictions').click()
    assert saved(page)['state']['predictionsConfirmed']
    page.locator('#next').click()
    assert page.locator('#u2 .side-view').count() == 0
    assert 'bloco' not in page.locator('#experiment-views').inner_text()
    page.locator('#test-b').focus()
    page.keyboard.press('Enter')
    assert saved(page)['state']['savedB'] is False
    support(page, 2)
    page.locator('#test-a').click()
    assert page.locator('#u2 .side-view').count() == 1
    a = page.locator('#experiment-views article').nth(0)
    a_svg = a.locator('.side-view').evaluate('(el)=>el.outerHTML')
    expect(a).to_contain_text('Pensávamos: Para')
    expect(a).to_contain_text('A personagem atravessa')
    page.locator('#lower-right').click()
    assert page.locator('#u2 .side-view').count() == 1
    page.locator('#test-b').click()
    cards = page.locator('#experiment-views article')
    assert cards.nth(0).locator('.side-view').evaluate('(el)=>el.outerHTML') == a_svg
    assert cards.nth(0).locator('.top-view').evaluate('(el)=>el.outerHTML') == cards.nth(1).locator('.top-view').evaluate('(el)=>el.outerHTML')
    assert a_svg != cards.nth(1).locator('.side-view').evaluate('(el)=>el.outerHTML')
    expect(cards.nth(1)).to_contain_text('Pensávamos: Atravessa')
    expect(cards.nth(1)).to_contain_text('para antes de atravessar')
    page.screenshot(path=str(PROOF / f'{SLUG}-after-results.png'), full_page=True)
    page.locator('#next').click()
    expect(page.locator('#u3 h2')).to_be_focused()
    support(page, 3)
    assert errors == []


@pytest.mark.parametrize('level', ['support', 'intermediate', 'challenge'])
def test_wrong_complete_oral_and_optional_reflection(page, pontes_origin, level):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    page.locator(f'[data-level="{level}"]').click()
    trials(page)
    explain(page, oral=True)
    expect(page.locator('#u4')).to_be_visible()
    support(page, 4)
    for height in ['1', '2', '3']:
        choose(page, 'peerRightHeight', height)
        page.locator('#test-peer').click()
        expect(page.locator('#peer-test-status')).to_contain_text('atravessa.' if height == '2' else 'para antes')
    choose(page, 'peerConclusion', 'not-found')
    page.locator('#peer-oral').check()
    page.locator('#next').click()
    expect(page.locator('#local-reflection')).to_be_visible()
    page.locator('#finish-local').click()
    expect(page.locator('#finished')).to_contain_text('concluída')
    checkpoint = saved(page)
    assert checkpoint['readyForReflection'] is True
    assert checkpoint['state']['changedVariable'] == 'left'
    assert checkpoint['state']['reflectionChoices'] == ['', '', '']
    assert not page.get_by_text('nota', exact=True).count()


def test_revision_levels_and_reload_preserve_work(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    trials(page)
    explain(page)
    peer(page)
    before = saved(page)['state']
    guides = []
    for level in ['support', 'challenge', 'intermediate']:
        page.locator(f'[data-level="{level}"]').click()
        guides.append(page.locator('#level-guide').inner_text())
        current = saved(page)['state']
        assert {k:v for k,v in current.items() if k != 'level'} == {k:v for k,v in before.items() if k != 'level'}
    assert len(set(guides)) == 3
    page.locator('#revise-explanation').click()
    choose(page, 'currentHypothesis', 'side')
    page.locator('#explanation').fill('Revemos: a vista de cima omite a altura; A atravessa e B para.')
    page.locator('#next').click()
    expect(page.locator('#pair-explanation')).to_contain_text('a vista de cima omite a altura')
    expect(page.locator('#peerConclusion-found')).not_to_be_checked()
    after = saved(page)['state']
    assert after['savedA'] and after['savedB']
    assert after['peerComment'] == before['peerComment']
    assert after['predictionA'] == before['predictionA']
    assert after['predictionB'] == before['predictionB']
    assert after['peerConclusion'] == ''
    page.locator('[data-level="support"]').click()
    restored = saved(page)
    page.reload()
    assert saved(page) == restored
    expect(page.locator('#u4')).to_be_visible()
    expect(page.locator('[data-level="support"]')).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('#peer-comment')).to_have_value(before['peerComment'])


def wrong(page, value):
    choose(page, 'changedVariable', value)
    page.locator('#confirm-variable').click()


def test_automatic_modal_distinct_retries_focus_and_reset(page, pontes_origin):
    from playwright.sync_api import expect
    page.add_init_script("window.speechCalls=[]; speechSynthesis.speak=(u)=>speechCalls.push(u.text)")
    page.goto(pontes_origin + '/lesson')
    trials(page)
    wrong(page, 'left')
    page.locator('#confirm-variable').click()
    wrong(page, 'position')
    assert not page.locator('dialog[open]').count()
    wrong(page, 'deck')
    dialog = page.locator('dialog[open]')
    expect(dialog).to_be_visible()
    assert page.evaluate('document.activeElement.closest("dialog") !== null')
    assert page.evaluate('speechCalls') == []
    page.keyboard.press('Escape')
    expect(dialog).to_be_visible()
    dialog.locator('[data-action="listen"]').focus()
    page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.closest("dialog") !== null')
    dialog.locator('[data-action="next"]').click()
    expect(page.locator('dialog[open]')).to_be_visible()
    page.locator('dialog[open] [data-action="continue"]').click()
    expect(page.locator('dialog[open]')).to_have_count(0)
    wrong(page, 'right')
    wrong(page, 'left')
    wrong(page, 'position')
    assert not page.locator('dialog[open]').count()
    wrong(page, 'deck')
    page.locator('dialog[open] [data-action="teacher"]').click()
    expect(page.locator('dialog[open]')).to_have_count(0)
    expect(page.locator('[data-pagecraft-support="u3"] .pc-support-notice')).to_contain_text('professor')
    wrong(page, 'left')
    wrong(page, 'position')
    page.locator('[data-step="1"]').click()
    page.locator('[data-step="2"]').click()
    wrong(page, 'deck')
    expect(page.locator('dialog[open]')).to_have_count(0)
    page.screenshot(path=str(PROOF / f'{SLUG}-after-help.png'), full_page=True)


@pytest.mark.parametrize('width', [390, 768, 1280])
def test_layout_keyboard_font_offline_and_targets(page, pontes_origin, width):
    from playwright.sync_api import expect
    requests, errors = [], []
    page.on('request', lambda request: requests.append(request.url))
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.set_viewport_size({'width':width, 'height':900})
    page.goto(pontes_origin + '/lesson')
    page.evaluate('document.fonts.load(\'20px "Didact Gothic"\')')
    page.evaluate('document.fonts.ready')
    assert page.evaluate("document.fonts.check('20px \"Didact Gothic\"')")
    assert page.locator('body').evaluate('(el)=>getComputedStyle(el).fontSize') == '20px'
    page.keyboard.press('Tab')
    expect(page.get_by_text('Ir para a atividade', exact=True)).to_be_focused()
    assert page.locator(':focus').evaluate('(el)=>parseFloat(getComputedStyle(el).outlineWidth)') >= 3
    page.keyboard.press('Enter')
    page.locator('#initialHypothesis-top').focus()
    page.keyboard.press('Space')
    page.keyboard.press('ArrowDown')
    expect(page.locator('#initialHypothesis-side')).to_be_checked()
    choose(page, 'predictionA', 'stopped')
    choose(page, 'predictionB', 'crossed')
    page.locator('#save-predictions').focus()
    page.keyboard.press('Enter')
    page.locator('#next').focus()
    page.keyboard.press('Space')
    page.locator('#test-a').click()
    page.locator('#lower-right').click()
    page.locator('#test-b').click()
    page.locator('#next').click()
    explain(page)
    for step in ['0', '1', '2', '3']:
        page.locator(f'[data-step="{step}"]').click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        small = page.locator('button:visible, select:visible, summary:visible, label:visible').evaluate_all('(els)=>els.filter(el=>{const r=el.getBoundingClientRect();return r.width<48||r.height<48}).map(el=>({tag:el.tagName,text:el.textContent,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height}))')
        assert small == []
    page.screenshot(path=str(PROOF / f'{SLUG}-width-{width}.png'), full_page=True)
    page.context.set_offline(True)
    page.locator('[data-step="2"]').click()
    wrong(page, 'left')
    expect(page.locator('#variable-feedback')).to_contain_text('Comparem')
    assert all(url.startswith(pontes_origin) or url.startswith('data:') for url in requests)
    assert errors == []


def test_embedded_restore_byte_budget_and_stale_support_reply(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/host')
    frame = page.frame_locator('#lesson')
    expect(frame.locator('#storage-status')).to_contain_text('aguardar')
    page.evaluate('restore()')
    trials(frame)
    explain(frame)
    peer(frame)
    page.wait_for_function("events.some(e=>e.type==='activity_state'&&e.payload.readyForReflection)")
    before = page.evaluate('events')
    state_event = [event for event in before if event['type'] == 'activity_state'][-1]
    attempts = len([event for event in before if event['type'] in ['attempt', 'assessment_result']])
    page.evaluate('(event)=>{events=[]; restore([event])}', state_event)
    page.wait_for_timeout(100)
    assert not page.evaluate("events.filter(e=>['attempt','assessment_result'].includes(e.type))")
    assert attempts > 0
    expect(frame.locator('#peer-comment')).to_have_value(state_event['payload']['state']['peerComment'])
    # Exercise maximum code-point strings through a real host restore message.
    payload = state_event['payload']
    payload['state']['explanation'] = '🧱' * 240
    payload['state']['peerComment'] = '🧱' * 240
    payload['state']['reflection'] = '🧱' * 160
    payload['state']['level'] = 'challenge'
    page.evaluate('(payload)=>restore([{type:"activity_state",payload}])', payload)
    page.wait_for_timeout(100)
    envelopes = page.evaluate('events.filter(e=>e.type==="activity_state").map(e=>new TextEncoder().encode(JSON.stringify(e)).length)')
    assert max(envelopes) < 4096
    assert frame.locator('#explanation').input_value() == '🧱' * 240
    # JSON escapes ASCII controls to six bytes each, larger than a Unicode emoji.
    escaped = json.loads(json.dumps(payload))
    escaped['state']['explanation'] = '\x01' * 240
    escaped['state']['peerComment'] = '\x01' * 240
    escaped['state']['reflection'] = '\x01' * 160
    page.evaluate('(payload)=>restore([{type:"activity_state",payload}])', escaped)
    page.wait_for_timeout(100)
    assert frame.locator('#explanation').input_value() == '\x01' * 240
    assert frame.locator('#peer-comment').input_value() == '\x01' * 240
    envelopes = page.evaluate('events.filter(e=>e.type==="activity_state").map(e=>new TextEncoder().encode(JSON.stringify(e)).length)')
    assert max(envelopes) < 4096
    page.evaluate('(payload)=>restore([{type:"activity_state",payload}])', payload)
    page.wait_for_timeout(100)
    # Simulated delayed AI reply: no provider is contacted in this test host.
    panel = frame.locator('[data-pagecraft-support="u4"]')
    panel.locator('[data-support-action="hint"]').click()
    panel.locator('[data-support-action="ai"]').click()
    page.wait_for_function('events.some(e=>e.type==="feedback_request")')
    request = page.evaluate('events.filter(e=>e.type==="feedback_request").at(-1)')
    frame.locator('#peer-comment').fill('A minha procura mudou.')
    page.evaluate('(requestId)=>document.querySelector("iframe").contentWindow.postMessage({pagecraft:1,type:"ai_feedback",payload:{request_id:requestId,unit_id:"u4",text:"RESPOSTA ANTIGA TESTE",source:"ai"}},"*")', request['payload']['request_id'])
    page.wait_for_timeout(100)
    assert 'RESPOSTA ANTIGA TESTE' not in frame.locator('body').inner_text()
    frame.locator('#peer-comment').blur()
    panel.locator('[data-support-action="hint"]').click()
    panel.locator('[data-support-action="ai"]').click()
    request = page.evaluate('events.filter(e=>e.type==="feedback_request").at(-1)')
    frame.locator('[data-step="2"]').click()
    page.evaluate('(requestId)=>document.querySelector("iframe").contentWindow.postMessage({pagecraft:1,type:"ai_feedback",payload:{request_id:requestId,unit_id:"u4",text:"RESPOSTA ETAPA ANTIGA",source:"ai"}},"*")', request['payload']['request_id'])
    page.wait_for_timeout(100)
    assert 'RESPOSTA ETAPA ANTIGA' not in frame.locator('body').inner_text()
    (PROOF / f'{SLUG}-browser-metrics.json').write_text(json.dumps({'maximum_observed_checkpoint_envelope_bytes':max(envelopes),'limit_bytes':4096,'unicode_code_points':{'explanation':240,'peerComment':240,'reflection':160},'escaped_controls_tested':True,'optional_reflection_may_shrink_to_fit':True,'simulated_provider':True},ensure_ascii=False,indent=2)+'\n')


def test_presentation_suppresses_evidence_and_disables_support(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson?presentation=1')
    page.evaluate('window.evidence=[]; document.addEventListener("pagecraft:activity-event", e=>evidence.push(e.detail))')
    trials(page)
    explain(page, oral=True)
    peer(page, oral=True)
    assert page.evaluate('evidence') == []
    assert page.locator('[data-pagecraft-support="u4"]').evaluate('(el)=>el.inert')
    assert saved(page) is None


def test_real_private_studio_evidence_reflection_and_download(page, pontes_studio):
    from playwright.sync_api import expect
    spec = json.loads((ROOT / f'drafts/{SLUG}-docspec.json').read_text())
    assert page.request.get(pontes_studio + '/api/teacher-bootstrap').ok
    response = page.request.post(pontes_studio + '/api/learning/activities', data={'slug':SLUG,'title':'Duas pontes, duas vistas','year':3,'duration':15,'languages':['pt'],'criteria':spec['criteria'],'requires_completion':True})
    assert response.status == 201, response.text()
    draft = response.json()
    assert draft['published'] is False
    page.goto(pontes_studio + '/' + draft['code'])
    page.get_by_label('Como te chamas?').fill('Criança de ensaio Pontes')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    expect(lesson.locator('#u1')).to_be_visible()
    trials(lesson)
    explain(lesson)
    peer(lesson)
    page.wait_for_function('async()=>{const r=await fetch("/api/learning/me");const d=await r.json();return d.events.some(e=>e.type==="activity_state"&&e.payload.readyForReflection)}')
    before_reload = page.request.get(pontes_studio + '/api/learning/me').json()['events']
    page.reload()
    expect(lesson.locator('#u4')).to_be_visible()
    expect(lesson.locator('#peer-comment')).to_have_value('Com 1 bloco direito para, apesar de parecer igual de cima.')
    after_reload = page.request.get(pontes_studio + '/api/learning/me').json()['events']
    assert len([e for e in before_reload if e['type'] in ['attempt','assessment_result']]) == len([e for e in after_reload if e['type'] in ['attempt','assessment_result']])
    lesson.locator('#next').focus()
    lesson.locator('#next').press('Enter')
    # Host reflection is an optional individual voice with a visible name.
    expect(page.locator('#reflection')).to_be_visible()
    expect(page.locator('#reflection')).to_contain_text('Criança de ensaio Pontes')
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    data = page.request.get(pontes_studio + '/api/learning/me').json()
    assert data['completed_at']
    observed = [e for e in data['events'] if e['type'] == 'assessment_result']
    assert any(e['payload']['detail']['field'] == 'predictionA' for e in observed)
    assert any(e['payload']['detail']['field'] == 'savedB' for e in observed)
    assert any(e['payload']['detail']['field'] == 'explanation' for e in observed)
    assert data['assessment'] is not None
    assert page.request.get(pontes_studio + '/api/learning/reports').json() == []
    report = page.request.get(pontes_studio + f'/api/learning/reports/{data["id"]}/download')
    assert report.ok
    text = report.text()
    assert 'Criança de ensaio Pontes' in text
    assert 'De cima parecem iguais' in text
    assert '## Evidências no PageCraft' in text
    assert '## Autoavaliação' in text
    assert text.index('## Evidências no PageCraft') < text.index('## Autoavaliação')
    (PROOF / f'{SLUG}-private-report.txt').write_text(text)
    page.screenshot(path=str(PROOF / f'{SLUG}-after-studio.png'), full_page=True)


def test_automatic_modal_wraps_tab_inside(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    trials(page)
    for value in ['left', 'position', 'deck']:
        wrong(page, value)
    dialog = page.locator('dialog[open]')
    expect(dialog).to_be_visible()
    dialog.locator('[data-action="continue"]').focus()
    page.keyboard.press('Tab')
    focus = page.evaluate('({tag:document.activeElement.tagName,inside:!!document.activeElement.closest("dialog"),html:document.activeElement.outerHTML.slice(0,180)})')
    page.screenshot(path=str(PROOF / f'{SLUG}-modal-focus.png'), full_page=True)
    (PROOF / f'{SLUG}-modal-focus.json').write_text(json.dumps(focus, ensure_ascii=False, indent=2)+'\n')
    assert focus['inside'], f"Tab from last button escaped modal: {focus}"
    dialog.locator('[data-action="listen"]').focus()
    page.keyboard.press('Shift+Tab')
    assert page.evaluate('!!document.activeElement.closest("dialog")')


def test_navigation_warning_clears_when_missing_work_is_done(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    predict(page)
    page.locator('#test-b').focus()
    page.keyboard.press('Enter')
    expect(page.locator('#navigation-status')).to_contain_text('Guardem A')
    page.locator('#test-a').click()
    page.locator('#lower-right').click()
    page.locator('#test-b').click()
    expect(page.locator('#next')).to_have_attribute('aria-disabled','false')
    page.screenshot(path=str(PROOF / f'{SLUG}-stale-warning.png'), full_page=True)
    expect(page.locator('#navigation-status')).to_be_hidden()


@pytest.mark.parametrize('level', ['support', 'intermediate', 'challenge'])
def test_each_required_response_gates_future_steps(page, pontes_origin, level):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    page.locator(f'[data-level="{level}"]').click()

    def blocked(unit):
        expect(page.locator('#next')).to_have_attribute('aria-disabled','true')
        page.locator('#next').focus()
        page.keyboard.press('Enter')
        expect(page.locator(f'#u{unit}')).to_be_visible()
        expect(page.locator('#navigation-status')).to_be_visible()
        if unit < 4:
            page.locator('[data-step="3"]').focus()
            page.keyboard.press('Enter')
            expect(page.locator(f'#u{unit}')).to_be_visible()

    blocked(1)
    choose(page, 'initialHypothesis', 'unsure')
    blocked(1)
    choose(page, 'predictionA', 'unsure')
    blocked(1)
    choose(page, 'predictionB', 'unsure')
    blocked(1)
    page.locator('#save-predictions').click()
    page.locator('#next').click()
    blocked(2)
    page.locator('#test-a').click()
    blocked(2)
    page.locator('#lower-right').click()
    blocked(2)
    page.locator('#test-b').click()
    page.locator('#next').click()
    blocked(3)
    choose(page, 'changedVariable', 'left')
    blocked(3)
    page.locator('#confirm-variable').click()
    blocked(3)
    choose(page, 'currentHypothesis', 'top')
    blocked(3)
    page.locator('#explained-orally').check()
    page.locator('#next').click()
    blocked(4)
    page.locator('#test-peer').click()
    blocked(4)
    choose(page, 'peerConclusion', 'not-found')
    blocked(4)
    page.locator('#peer-oral').check()
    page.locator('#next').click()
    expect(page.locator('#local-reflection')).to_be_visible()


def test_support_first_click_after_editing_text(page, pontes_origin):
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/lesson')
    trials(page)
    explain(page)
    page.locator('#peer-comment').fill('Quero comparar a hipótese do par.')
    panel = page.locator('[data-pagecraft-support="u4"]')
    panel.locator('[data-support-action="hint"]').click()
    page.screenshot(path=str(PROOF / f'{SLUG}-support-first-click.png'), full_page=True)
    expect(panel.locator('.pc-support-action')).to_be_visible()


@pytest.mark.parametrize('host,frame_id', [('learning','lesson'), ('student','activity-frame')])
def test_canonical_modal_host_adapter_wraps_keyboard(page, pontes_origin, host, frame_id):
    """Real canonical modal in both iframe adapters; host shell/payload are simulated."""
    from playwright.sync_api import expect
    page.goto(pontes_origin + '/canonical-' + host)
    frame = page.frame_locator('#' + frame_id)
    expect(frame.locator('#u1')).to_be_visible()
    frame.locator('body').evaluate('''()=>parent.postMessage({pagecraft:1,type:'support_modal',payload:{action:'open',hint_id:'canonical-keyboard-proof',text:'Compara os apoios nas vistas de lado.',language:'pt',labels:{listen:'Ouvir',next:'Outra pista',stuck:'Ainda estou preso',teacher:'Pedir ajuda ao professor',continue:'Vou experimentar'}}},'*')''')
    dialog = page.locator('dialog[open]')
    expect(dialog).to_be_visible()
    assert dialog.evaluate('(el)=>Math.abs(el.getBoundingClientRect().width-innerWidth)<1')
    assert page.evaluate('!!document.activeElement.closest("dialog")')
    page.keyboard.press('Escape')
    expect(dialog).to_be_visible()
    dialog.locator('[data-action="continue"]').focus()
    page.keyboard.press('Tab')
    forward = page.evaluate('({tag:document.activeElement.tagName,inside:!!document.activeElement.closest("dialog")})')
    dialog.locator('[data-action="listen"]').focus()
    page.keyboard.press('Shift+Tab')
    backward = page.evaluate('({tag:document.activeElement.tagName,inside:!!document.activeElement.closest("dialog")})')
    (PROOF / f'{SLUG}-canonical-{host}-focus.json').write_text(json.dumps({'host_adapter':host,'frame_id':frame_id,'forward':forward,'backward':backward,'simulated_host_shell_and_payload':True},indent=2)+'\n')
    page.screenshot(path=str(PROOF / f'{SLUG}-canonical-{host}-focus.png'), full_page=True)
    assert forward['inside'] and backward['inside']


@pytest.mark.parametrize('host', ['learning', 'student'])
def test_real_studio_hosts_load_current_modal_and_resume_keyboard(page, pontes_studio, host):
    """Actual host/cookies/cache and child support pipeline; local guide, never AI."""
    import httpx
    from playwright.sync_api import expect
    responses = []
    errors = []
    page.on('response', lambda response: responses.append(response) if 'support-modal.js' in response.url else None)
    page.on('pageerror', lambda error: errors.append(str(error)))
    spec = json.loads((ROOT / f'drafts/{SLUG}-docspec.json').read_text())
    registration = {'slug':SLUG,'title':'Duas pontes, duas vistas','year':3,'duration':15,
                    'languages':['pt'],'criteria':spec['criteria'],'requires_completion':True}
    session_id = None
    with httpx.Client(base_url=pontes_studio) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        draft_response = teacher.post('/api/learning/activities', json=registration)
        draft_response.raise_for_status()
        draft = draft_response.json()
        assert draft['published'] is False
        assert teacher.get('/activities/' + SLUG + '/').status_code == 404
        try:
            if host == 'learning':
                assert page.request.get(pontes_studio + '/api/teacher-bootstrap').ok
                page.goto(pontes_studio + '/' + draft['code'])
                page.get_by_label('Como te chamas?').fill('Ensaio do foco Learning')
                page.get_by_role('button', name='Começar', exact=True).click()
                frame_id = 'lesson'
            else:
                classroom_response = teacher.post('/api/classes', json={'name':'Ensaio descartável do foco','year':3,'students':['Aluno de ensaio do foco']})
                classroom_response.raise_for_status()
                classroom = classroom_response.json()
                response = teacher.post('/api/sessions', json={'class_id':classroom['id'],'activity_slug':SLUG,'activity_title':registration['title']})
                response.raise_for_status()
                session = response.json()
                session_id = session['id']
                page.goto(pontes_studio + '/student/')
                page.locator('#code-input').fill(session['join_code'])
                page.get_by_role('button', name='Entrar', exact=True).click()
                page.get_by_role('button', name='Aluno de ensaio do foco', exact=True).click()
                page.get_by_role('button', name='Começar', exact=True).click()
                frame_id = 'activity-frame'
            frame = page.frame_locator('#' + frame_id)
            expect(frame.locator('#u1')).to_be_visible()
            assert responses, 'Real host did not request the canonical modal script'
            assert all(response.status == 200 and response.url.endswith('/student/support-modal.js?v=2') for response in responses)
            canonical = (ROOT / 'server/static/student/support-modal.js').read_text()
            assert responses[-1].text() == canonical
            assert page.locator('script[src="/student/support-modal.js?v=2"]').count() == 1
            frame.locator('#save-predictions').focus()
            expect(frame.locator('#save-predictions')).to_be_focused()
            hint_id = frame.locator('body').evaluate('''()=>{window.modalActions=[];addEventListener('message',e=>{if(e.source===parent&&e.data?.type==='support_modal_action')modalActions.push(e.data.payload)});PageCraftSupport.requestHint('u1',true);return PageCraftSupport.currentHintId()}''')
            assert hint_id
            dialog = page.locator('dialog[open]')
            expect(dialog).to_be_visible()
            assert dialog.evaluate('(el)=>Math.abs(el.getBoundingClientRect().width-innerWidth)<1')
            expect(dialog.locator('[data-action="continue"]')).to_be_focused()
            dialog.locator('[data-action="continue"]').focus()
            page.keyboard.press('Tab')
            expect(dialog.locator('[data-action="listen"]')).to_be_focused()
            page.keyboard.press('Shift+Tab')
            expect(dialog.locator('[data-action="continue"]')).to_be_focused()
            page.keyboard.press('Escape')
            expect(dialog).to_be_visible()
            page.screenshot(path=str(PROOF / f'{SLUG}-green-real-{host}-modal.png'), full_page=True)
            dialog.locator('[data-action="continue"]').press('Enter')
            expect(page.locator('dialog[open]')).to_have_count(0)
            resumed_focus = {
                'host':page.evaluate('({tag:document.activeElement.tagName,id:document.activeElement.id})'),
                'frame':frame.locator('body').evaluate('({tag:document.activeElement.tagName,id:document.activeElement.id})'),
            }
            (PROOF / f'{SLUG}-green-real-{host}-resume-focus.json').write_text(json.dumps(resumed_focus,indent=2)+'\n')
            page.screenshot(path=str(PROOF / f'{SLUG}-green-real-{host}-resumed.png'), full_page=True)
            expect(frame.locator('[data-pagecraft-support="u1"] .pc-support-action')).to_be_focused()
            actions = frame.locator('body').evaluate('modalActions')
            assert actions == [{'hint_id':hint_id,'action':'continue'}]
            frame.locator('#initialHypothesis-unsure').focus()
            frame.locator('#initialHypothesis-unsure').press('Space')
            expect(frame.locator('#initialHypothesis-unsure')).to_be_checked()
            assert errors == []
            page.screenshot(path=str(PROOF / f'{SLUG}-green-real-{host}-resumed.png'), full_page=True)
            evidence = {'host':host,'actual_host_page':True,'url_path':page.url.removeprefix(pontes_studio),
                        'frame_id':frame_id,'script_urls':[response.url for response in responses],
                        'script_matches_canonical':True,'script_version':2,'tab_last_to_first':True,
                        'shift_tab_first_to_last':True,'escape_keeps_modal_open':True,
                        'explicit_action':actions[0],'focus_restored_to':'.pc-support-action',
                        'keyboard_work_resumed':True,'simulated_modal_payload':False,'local_guide_pipeline':True,'real_ai_provider':False,
                        'production_written':False,'published':False,'page_errors':errors}
            (PROOF / f'{SLUG}-green-real-{host}-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
        finally:
            if session_id:
                teacher.post(f'/api/sessions/{session_id}/close').raise_for_status()
