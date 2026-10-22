"""Disposable component pilot, compiled from canonical sources inside a host iframe.

PAGECRAFT_TEST_CDP must point to our own Agent Browser Hub session.
"""
import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from server.activity_support import embed_activity_support

ROOT = Path(__file__).resolve().parents[2]
SPEC = json.loads((ROOT / 'tests/fixtures/support-examples.json').read_text())[0]
FIRST = SPEC['units'][0]['support']['obstacles'][0]['hints'][0]['text']['pt']['individual']
SECOND = SPEC['units'][0]['support']['obstacles'][0]['hints'][1]['text']['pt']['individual']


@pytest.fixture(scope='module')
def support_origin():
    spec = copy.deepcopy(SPEC)
    spec['units'].append(copy.deepcopy(spec['units'][0]))
    spec['units'][1]['summary'] = 'Outra tarefa'
    lesson = embed_activity_support('''<!doctype html><html lang="pt-PT"><meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Piloto descartável de pistas</title>
      <style>body{font:20px/1.55 system-ui;background:#f5f3ea;color:#233c32;margin:12px}h1{overflow-wrap:anywhere}
      *{box-sizing:border-box}input{font:inherit;width:100%;min-height:56px}
      button{font:inherit;min-height:56px}body.zoom{zoom:2}</style><body>
      <h1>Comparar as barras</h1><section data-unit="u1">
      <label for="answer">A minha resposta</label><input id="answer">
      <aside data-pagecraft-support="u1"></aside></section>
      <button id="other" type="button">Ir para outra tarefa</button>
      <section data-unit="u2"><aside data-pagecraft-support="u2"></aside></section>
      <script>
      const answer=document.querySelector('#answer');
      answer.value=localStorage.getItem('answer')||'Uma tentativa';
      if(location.search.includes('zoom'))document.body.classList.add('zoom');
      const context=()=>PageCraftSupport.update({unit_id:'u1',task_id:'barras',question:'Qual barra?',answer:answer.value});
      document.addEventListener('pagecraft-support-ready',context);
      answer.addEventListener('input',()=>{localStorage.setItem('answer',answer.value);context()});
      document.querySelector('#other').onclick=()=>PageCraftSupport.update({unit_id:'u2',task_id:'outra',question:'Outra pergunta?'});
      window.readings=[];
      Object.defineProperty(window,'speechSynthesis',{configurable:true,writable:true,value:{cancel(){},speak(u){readings.push({text:u.text,lang:u.lang})}}});
      </script></body></html>''', spec)
    host = '''<!doctype html><html lang="pt-PT"><meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1"><title>Ensaio de consulta de pistas</title>
      <style>body{margin:0}iframe{display:block;border:0;width:100%;height:100vh}</style><body>
      <iframe title="Atividade descartável"></iframe><script>
      const frame=document.querySelector('iframe');
      window.events=JSON.parse(localStorage.getItem('events')||'[]');window.restored=false;
      window.addEventListener('message',e=>{
        if(e.source!==frame.contentWindow||e.data?.pagecraft!==1)return;
        events.push(e.data);localStorage.setItem('events',JSON.stringify(events));
      });
      frame.onload=()=>{
        const send=(type,payload)=>frame.contentWindow.postMessage({pagecraft:1,type,payload},location.origin);
        send('learning_preferences',{route:new URLSearchParams(location.search).get('route')||'permanent'});
        send('learning_restore',{events});
        // A task queued in the iframe after both host messages is the restore barrier.
        frame.contentWindow.setTimeout(()=>{window.restored=true},0);
      };
      frame.src='/lesson'+(location.search.includes('zoom')?'?zoom':'');
      </script></body></html>'''

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write((lesson if self.path.startswith('/lesson') else host).encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('route', ['permanent', 'studio'])
def test_edit_reload_and_reread_without_events_or_ai(page, support_origin, route, tmp_path):
    from playwright.sync_api import expect

    errors, requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests.append(request.url))
    page.goto(support_origin + '?route=' + route)
    page.wait_for_function('restored')
    lesson = page.frame_locator('iframe')
    panel = lesson.locator('[data-pagecraft-support="u1"]')
    expect(panel.locator('.pc-support-history')).to_have_count(0)
    panel.get_by_role('button', name='Preciso de uma pista', exact=True).click()
    panel.get_by_role('button', name='Outra pista', exact=True).click()
    expect(panel.locator('.pc-support-action')).to_have_text(SECOND)
    lesson.get_by_label('A minha resposta').fill('Resposta revista')
    expect(panel.locator('.pc-support-action')).to_have_count(0)
    page.wait_for_function('events.length === 2')
    saved = page.evaluate('JSON.stringify(events)')
    page.reload()
    page.wait_for_function('restored')
    expect(panel.locator('.pc-support-action')).to_have_count(0)
    history = panel.locator('.pc-support-history')
    outer = history.locator(':scope > summary')
    outer.focus()
    outer.press('Enter')
    expect(history).to_have_attribute('open', '')
    first = history.locator('li details').first
    first.locator('summary').focus()
    first.locator('summary').press('Space')
    expect(first).to_have_attribute('open', '')
    expect(first.locator('.pc-support-history-text')).to_have_text(FIRST)
    expect(first).to_contain_text('Pista anterior: o contexto mudou.')
    expect(first).to_contain_text('Uma tentativa')
    expect(first).to_contain_text(SPEC['support']['version'])
    expect(first).to_contain_text('Comparar as barras')
    assert lesson.locator('body').evaluate('readings.length') == 0
    reader = first.get_by_role('button', name='Ouvir · Pista 1', exact=True)
    reader.focus()
    reader.press('Enter')
    assert lesson.locator('body').evaluate('readings') == [{'text': FIRST, 'lang': 'pt-PT'}]
    assert page.evaluate('JSON.stringify(events)') == saved
    # The accessibility tree exposes the native disclosure and the named action.
    tree = first.aria_snapshot()
    assert 'button "Ouvir · Pista 1"' in tree
    assert 'Resposta nessa altura' in tree
    outer.scroll_into_view_if_needed()
    page.screenshot(path=str(tmp_path / f'historico-{route}.png'), full_page=True)
    lesson.get_by_role('button', name='Ir para outra tarefa', exact=True).click()
    other = lesson.locator('[data-pagecraft-support="u2"]')
    other.locator('.pc-support-history > summary').click()
    other.locator('.pc-support-history li summary').first.click()
    expect(other.locator('.pc-support-history li').first).to_contain_text('Pista anterior: o contexto mudou.')
    expect(other.locator('.pc-support-history li').first).to_contain_text('Comparar as barras')
    assert page.evaluate('JSON.stringify(events)') == saved
    assert not errors
    assert all(url.startswith(support_origin) for url in requests)


@pytest.mark.parametrize('zoom', [False, True])
def test_narrow_keyboard_voice_unavailable_and_focus(page, support_origin, zoom, tmp_path):
    from playwright.sync_api import expect

    page.set_viewport_size({'width': 320, 'height': 800})
    page.goto(support_origin + ('?zoom' if zoom else ''))
    page.wait_for_function('restored')
    lesson = page.frame_locator('iframe')
    panel = lesson.locator('[data-pagecraft-support="u1"]')
    panel.get_by_role('button', name='Preciso de uma pista', exact=True).click()
    lesson.get_by_label('A minha resposta').fill('Outra resposta')
    summary = panel.locator('.pc-support-history > summary')
    summary.focus()
    summary.press('Enter')
    # Tab reaches the first hint; Enter expands it and Tab reaches its reader.
    summary.press('Tab')
    first = panel.locator('.pc-support-history li details').first
    expect(first.locator('summary')).to_be_focused()
    first.locator('summary').press('Enter')
    first.locator('summary').press('Tab')
    reader = first.get_by_role('button', name='Ouvir · Pista 1', exact=True)
    expect(reader).to_be_focused()
    assert reader.evaluate('el => getComputedStyle(el).outlineStyle') == 'solid'
    assert reader.bounding_box()['height'] >= 56
    lesson.locator('body').evaluate('window.speechSynthesis=null')
    saved = page.evaluate('JSON.stringify(events)')
    reader.press('Enter')
    expect(panel.get_by_role('status')).to_have_text('A leitura em voz alta não está disponível neste dispositivo.')
    expect(first).to_have_attribute('open', '')
    expect(reader).to_be_focused()
    assert page.evaluate('JSON.stringify(events)') == saved
    page.screenshot(path=str(tmp_path / f'historico-320-zoom-{zoom}.png'), full_page=True)
    assert lesson.locator('html').evaluate('el => el.scrollWidth <= el.clientWidth'), json.dumps(lesson.locator('body').evaluate('''() => ({
      innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,x:scrollX,
      overflow:[...document.querySelectorAll('*')].filter(el => el.scrollWidth > el.clientWidth)
        .map(el => ({tag:el.tagName,cls:el.className,text:el.textContent.slice(0,60),width:el.clientWidth,scroll:el.scrollWidth}))})'''), ensure_ascii=False)
