"""Exercita os 168 artefactos reais no browser aberto pelo Agent Browser Hub."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

import pytest

ROOT=Path(__file__).resolve().parents[2]
PATHS=sorted((ROOT/'drafts/m28p-v3').glob('*/*.html'))


@pytest.fixture(scope='module')
def tic_origin():
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,*args):
            pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()
    thread.join()


def choose(page,item,wrong=False):
    kind=item['kind']
    if kind in {'syllables','recall'}:
        answer=item['answer'][::-1] if wrong else item['answer']
        for value in answer:
            page.locator(f'[data-piece="{value}"]').click()
    elif kind=='pairs':
        ids=[o['id'] for o in item['options']]
        targets=ids[1:]+ids[:1] if wrong and len(ids)>1 else ids
        for left,right in zip(ids,targets):
            page.locator(f'[data-left="{left}"]').click()
            page.locator(f'[data-right="{right}"]').click()
    else:
        wrong_ids=[o['id'] for o in item['options'] if o['id'] not in item['answer']]
        answer=wrong_ids[:1] if wrong and wrong_ids else item['answer']
        for value in answer:
            page.locator(f'[data-option="{value}"]').click()


@pytest.mark.parametrize('path',PATHS,ids=lambda p:p.stem)
def test_every_game_all_rounds_keyboard_restore_and_no_network(page,tic_origin,path):
    page.set_viewport_size({'width':390 if 'gap' in path.stem or 'hunt' in path.stem else 1280,'height':900})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    requests=[]
    page.on('request',lambda request:requests.append(request.url))
    page.add_init_script("window.observed=[];document.addEventListener('pagecraft:activity-event',e=>window.observed.push(e.detail));")
    page.goto(tic_origin+'/'+str(path.relative_to(ROOT)))
    data=page.locator('#m28p-content').text_content()
    data=json.loads(data)
    assert page.locator('#start').is_visible()
    page.locator('#start').focus()
    page.keyboard.press('Enter')
    assert page.locator('#demonstration').is_visible()
    page.locator('#demo-close').click()
    for index,item in enumerate(data['rounds']):
        assert page.locator('#confirm').is_disabled()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        choose(page,item,wrong=index==0)
        page.locator('#confirm').click()
        assert page.locator('#next').is_enabled()
        if index==0:
            page.locator('.support-details').evaluate('(element)=>element.open=true')
            for level in ['support','challenge','intermediate']:
                page.locator(f'[data-level="{level}"]').click()
                assert page.locator('#next').is_enabled()
            count=page.evaluate("observed.filter(e=>e.type==='attempt').length")
            assert count==1
            page.locator('#demo-open').click()
            page.locator('#demo-close').click()
            assert page.locator('#next').is_enabled()
            assert page.evaluate("observed.filter(e=>e.type==='attempt').length")==count
            page.reload()
            assert page.locator('#next').is_enabled()
            assert page.evaluate("observed.filter(e=>e.type==='attempt').length")==0
        page.locator('#next').click()
    assert page.locator('#finish').is_visible()
    assert not errors
    assert all(url.startswith(tic_origin) or url.startswith('data:') for url in requests)


@pytest.mark.parametrize('word',['menina','cigarra','passarinho','flor'])
def test_embedded_mp3_decodes_without_browser_voice(page,tic_origin,word):
    page.goto(f'{tic_origin}/drafts/m28p-v3/{word}/m28p-v3-{word}-recall.html')
    result=page.evaluate('''async()=>{const data=JSON.parse(document.getElementById('m28p-content').textContent); const a=new Audio(data.audio.word);return await new Promise(resolve=>{a.onloadedmetadata=()=>resolve({duration:a.duration,error:null});a.onerror=()=>resolve({error:a.error?.code});setTimeout(()=>resolve({error:'timeout'}),3000);});}''')
    assert result['error'] is None
    assert result['duration']>0


def test_real_host_saves_help_and_restores_completed_draft_without_duplicate_attempts(page,studio_origin):
    metadata=json.loads((ROOT/'drafts/m28p-v3-menina-match-activity.json').read_text())
    page.request.get(studio_origin+'/api/teacher-bootstrap')
    response=page.request.post(studio_origin+'/api/learning/activities',data=metadata)
    assert response.status==201
    code=response.json()['code']
    visitor=page.context.browser.new_context()
    try:
        assert visitor.request.get(studio_origin+'/api/learning/activities/'+code+'/content').status==404
    finally:
        visitor.close()
    page.goto(studio_origin+'/'+code)
    page.get_by_label('Como te chamas?').fill('Ensaio TIC descartável')
    page.get_by_role('button',name='Começar',exact=True).click()
    frame=page.frame_locator('#lesson')
    frame.locator('#start').click()
    frame.locator('#demo-close').click()
    frame.get_by_role('button',name='Ouvir a palavra',exact=True).click()
    data=json.loads(frame.locator('#m28p-content').text_content())
    for item in data['rounds']:
        for value in item['answer']:
            frame.locator(f'[data-option="{value}"]').click()
        frame.locator('#confirm').click()
        frame.locator('#next').click()
    from playwright.sync_api import expect
    expect(page.locator('#reflect')).to_be_enabled()
    # O host confirma a gravação por GET, sem presumir que postMessage persistiu.
    page.wait_for_function("async()=>{const r=await fetch('/api/learning/me');const d=await r.json();return d.events.filter(e=>e.type==='attempt').length===4;}")
    before=page.request.get(studio_origin+'/api/learning/me').json()
    attempts=[e for e in before['events'] if e['type']=='attempt']
    assert attempts[0]['payload']['detail']['aids']['audio_word_requested'] is True
    page.reload()
    frame=page.frame_locator('#lesson')
    expect(frame.locator('#finish')).to_be_visible()
    expect(page.locator('#reflect')).to_be_enabled()
    after=page.request.get(studio_origin+'/api/learning/me').json()
    assert len([e for e in after['events'] if e['type']=='attempt'])==4
    assert after['preview'] is True
