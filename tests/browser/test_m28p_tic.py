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
    page.add_init_script("window.observed=[];addEventListener('message',e=>{if(e.data?.pagecraft===1)window.observed.push(e.data)});")
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
