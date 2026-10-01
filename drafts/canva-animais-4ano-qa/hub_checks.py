"""QA sobre a sessão temporary existente do Agent Browser Hub; só localhost."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path

from agent_browser_hub import browser_use_adapter as hub, sessions
from agent_browser_hub.audit import log_event

OUT = Path('/home/proteu/pagecraft/drafts/canva-animais-4ano-qa')
PREFIX = 'http://127.0.0.1:8788/canva-animais-4ano.html'

MEASURE = r"""(()=>{
const visible=e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden';
const controls=[...document.querySelectorAll('button,input,select,summary')].filter(visible).map(e=>({text:e.innerText.slice(0,50)||e.id,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}));
function rgb(c){const x=document.createElement('canvas');x.width=x.height=1;const k=x.getContext('2d');k.fillStyle=c;k.fillRect(0,0,1,1);return [...k.getImageData(0,0,1,1).data].slice(0,3)}
function lum(c){return rgb(c).map(v=>v/255).map(v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4)).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0)}
function contrast(a,b){const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
const c=getComputedStyle(document.body),r=getComputedStyle(document.documentElement);
return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,font:c.fontSize,fontFamily:c.fontFamily,controls,tooSmall:controls.filter(x=>x.w<47.5||x.h<47.5),inkContrast:contrast(c.color,c.backgroundColor),primaryContrast:contrast(r.getPropertyValue('--paper'),r.getPropertyValue('--primary')),images:[...document.images].map(i=>({loaded:i.complete&&i.naturalWidth>0,embedded:i.src.startsWith('data:')})),network:performance.getEntriesByType('resource').map(x=>x.name).filter(x=>!x.startsWith('data:')),stage:document.querySelector('.stage-meta').innerText};})()"""

JOURNEY = r"""(async()=>{
window.qaEvents=[];window.qaErrors=[];addEventListener('message',e=>{if(e.data?.pagecraft)qaEvents.push(e.data)});addEventListener('error',e=>qaErrors.push(e.message));
const levels=LEVEL_PLACEHOLDER;document.getElementById('tab-'+levels).click();const logs=[];
for(let i=0;i<7;i++){
 const before=document.getElementById('next').disabled;
 const future=[...document.querySelectorAll('#index button')].slice(i+1).every(b=>b.disabled);
 const choice=document.querySelector('[data-choice]:not([disabled])');if(choice)choice.click();
 for(const el of document.querySelectorAll('[data-field]')){
  el.value=el.tagName==='SELECT'?el.options[el.options.length-1].value:({animals:'Coruja e golfinho',choiceReason:'Os colegas podem comparar os animais.',layoutPlan:'Duas zonas com cinco factos cada.',taskTurns:'Trocamos após cada animal.',presentationOutline:'Produto: cartaz. Decisão: duas zonas. Melhoria: espaço. Cooperação: trocar teclado.'}[el.id]||'O grupo explica uma decisão e pede ajuda se necessário.');
  el.dispatchEvent(new Event(el.tagName==='SELECT'?'change':'input',{bubbles:true}));el.dispatchEvent(new Event('blur'));
 }
 logs.push({stage:i+1,initialBlocked:before,futuresBlocked:future,afterBlocked:document.getElementById('next').disabled,hint:document.getElementById('support-panel').innerText,feedback:document.querySelector('.feedback')?.innerText||'',visualHint:!!document.querySelector('.focus-zone,.highlighted')});
 document.getElementById('next').click();
}
await new Promise(r=>setTimeout(r,30));return {level:levels,logs,final:document.querySelector('.stage-meta').innerText,reflectionEnabled:!document.getElementById('reflection').disabled,errors:qaErrors,maxPayload:Math.max(...qaEvents.map(e=>new TextEncoder().encode(JSON.stringify(e.payload)).length)),attempts:qaEvents.filter(e=>e.type==='attempt').length,readyInitial:qaEvents.find(e=>e.type==='activity_state')?.payload.readyForReflection,readyFinal:qaEvents.filter(e=>e.type==='activity_state').at(-1)?.payload.readyForReflection};})()"""

async def main():
    meta = sessions.get_session('canva-qa')
    results = {'backend': 'Existing Agent Browser Hub temporary session via its adapter/CDP', 'responsive': [], 'journeys': []}
    async with hub.connect(meta) as bs:
        root = await bs.get_or_create_cdp_session()
        targets = (await root.cdp_client.send.Target.getTargets())['targetInfos']
        target = next(t for t in targets if t.get('type') == 'page' and t['url'] == PREFIX + '?qa=final')
        cdp = await bs.get_or_create_cdp_session(target_id=target['targetId'])

        async def evaluate(expression):
            res = await cdp.cdp_client.send.Runtime.evaluate(params={'expression': '(async()=>JSON.stringify(await (' + expression + ')))()', 'returnByValue': True, 'awaitPromise': True}, session_id=cdp.session_id)
            if res.get('exceptionDetails'):
                raise RuntimeError(res['exceptionDetails'])
            return json.loads(res['result']['value'])

        assert (await evaluate('location.href')).startswith(PREFIX)
        async def reload_clean():
            await evaluate("(()=>{window.removeEventListener('pagehide',flush);sessionStorage.removeItem('canva-animais-4ano');return true})()")
            await cdp.cdp_client.send.Page.reload(session_id=cdp.session_id)
            for _ in range(30):
                try:
                    if await evaluate("!!document.getElementById('product-poster')"):
                        return
                except Exception:
                    pass
                await asyncio.sleep(.05)
            raise RuntimeError('Local activity did not finish loading')

        async def screenshot(name):
            metrics = await cdp.cdp_client.send.Page.getLayoutMetrics(session_id=cdp.session_id)
            size = metrics.get('cssContentSize', metrics['contentSize'])
            r = await cdp.cdp_client.send.Page.captureScreenshot(params={'format': 'png', 'captureBeyondViewport': True, 'clip': {'x': 0, 'y': 0, 'width': size['width'], 'height': size['height'], 'scale': 1}}, session_id=cdp.session_id)
            (OUT / name).write_bytes(base64.b64decode(r['data']))

        await reload_clean()
        for width in [390, 768, 1280]:
            await cdp.cdp_client.send.Emulation.setDeviceMetricsOverride(params={'width': width, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False}, session_id=cdp.session_id)
            await asyncio.sleep(.1)
            results['responsive'].append(await evaluate(MEASURE))
            await screenshot(f'final-{width}.png')
        for level in ['support', 'intermediate', 'challenge']:
            await reload_clean()
            results['journeys'].append(await evaluate(JOURNEY.replace('LEVEL_PLACEHOLDER', json.dumps(level))))
        results['finalResponsive'] = await evaluate(MEASURE)
        results['allStageLayouts'] = []
        for width in [390, 768]:
            await cdp.cdp_client.send.Emulation.setDeviceMetricsOverride(params={'width': width, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False}, session_id=cdp.session_id)
            for stage in range(8):
                await evaluate(f"(()=>{{document.querySelector('[data-go=\"{stage}\"]').click();return true}})()")
                await asyncio.sleep(.08)
                row = await evaluate(MEASURE)
                results['allStageLayouts'].append({'width': width, 'stage': stage + 1, 'scrollWidth': row['scrollWidth'], 'tooSmall': row['tooSmall']})
                if stage == 2:
                    await screenshot(f'final-guide-{width}.png')
        await evaluate("(()=>{document.querySelector('[data-go=\"2\"]').click();document.querySelector('[data-zoom]').click();return true})()")
        results['zoomBeforeEscape'] = await evaluate("({expanded:document.querySelector('[data-zoom]').getAttribute('aria-expanded'),focused:document.activeElement.getAttribute('data-close-zoom'),pageWidth:innerWidth,pageScroll:document.documentElement.scrollWidth})")
        for kind in ['keyDown', 'keyUp']:
            await cdp.cdp_client.send.Input.dispatchKeyEvent(params={'type': kind, 'key': 'Escape', 'code': 'Escape', 'windowsVirtualKeyCode': 27}, session_id=cdp.session_id)
        results['zoomAfterEscape'] = await evaluate("({expanded:document.querySelector('[data-zoom]').getAttribute('aria-expanded'),focusReturned:document.activeElement.hasAttribute('data-zoom')})")
        await evaluate("(()=>{document.getElementById('tab-support').focus();return true})()")
        for kind in ['keyDown', 'keyUp']:
            await cdp.cdp_client.send.Input.dispatchKeyEvent(params={'type': kind, 'key': 'ArrowRight', 'code': 'ArrowRight', 'windowsVirtualKeyCode': 39}, session_id=cdp.session_id)
        results['keyboardSupport'] = await evaluate("({selected:document.querySelector('[aria-selected=true]').id,focus:document.activeElement.id,outline:getComputedStyle(document.activeElement).outlineWidth})")
        await cdp.cdp_client.send.Network.enable(session_id=cdp.session_id)
        await cdp.cdp_client.send.Network.emulateNetworkConditions(params={'offline': True, 'latency': 0, 'downloadThroughput': 0, 'uploadThroughput': 0}, session_id=cdp.session_id)
        results['offline'] = await evaluate("(async()=>{const stages=[];for(let i=0;i<8;i++){document.querySelector('[data-go=\"'+i+'\"]').click();await new Promise(r=>setTimeout(r,40));stages.push(document.querySelector('.stage-meta').innerText)}return{stages,errors:window.qaErrors||[],remoteResources:performance.getEntriesByType('resource').map(x=>x.name).filter(x=>!x.startsWith('data:')),canvaWasNotOpened:true}})()")
        await cdp.cdp_client.send.Network.emulateNetworkConditions(params={'offline': False, 'latency': 0, 'downloadThroughput': -1, 'uploadThroughput': -1}, session_id=cdp.session_id)
        frame_setup = """(async()=>{window.qaHostEvents=[];const f=document.createElement('iframe');f.id='qa-frame';f.setAttribute('sandbox','allow-scripts allow-same-origin');f.style='width:100%;height:900px';addEventListener('message',e=>{if(e.source===f.contentWindow&&e.data?.pagecraft)qaHostEvents.push(e.data)});const loaded=new Promise(r=>f.onload=r);document.body.replaceChildren(f);f.src=location.origin+location.pathname+'?qa=iframe';await loaded;await new Promise(r=>setTimeout(r,40));return {initialState:qaHostEvents.find(e=>e.type==='activity_state')?.payload.readyForReflection,loaded:qaHostEvents.some(e=>e.type==='activity_loaded'),storagePresentInSharedOrigin:f.contentWindow.sessionStorage.getItem('canva-animais-4ano')!==null}})()"""
        results['frameInitial'] = await evaluate(frame_setup)
        inner_journey = JOURNEY.replace('LEVEL_PLACEHOLDER', '"intermediate"').replace('document.', 'D.')
        inner_journey = inner_journey.replace('window.qaEvents=[];', 'const D=document.getElementById("qa-frame").contentDocument;window.qaEvents=[];')
        inner_journey = inner_journey.replace('const logs=[];', 'await new Promise(r=>setTimeout(r,40));const logs=[];')
        inner_journey = inner_journey.replace('if(choice)choice.click();', 'if(choice){choice.click();await new Promise(r=>setTimeout(r,40));}')
        inner_journey = inner_journey.replace(' logs.push(', ' await new Promise(r=>setTimeout(r,40));logs.push(')
        inner_journey = inner_journey.replace("D.getElementById('next').click();", "D.getElementById('next').click();await new Promise(r=>setTimeout(r,40));")
        results['frameJourney'] = await evaluate(inner_journey)
        results['bridgeRestore'] = await evaluate("""(async()=>{const f=document.getElementById('qa-frame');const original=qaHostEvents.slice();const before=qaHostEvents.length;await new Promise(r=>{f.onload=r;f.contentWindow.location.reload()});await new Promise(r=>setTimeout(r,30));f.contentWindow.postMessage({pagecraft:1,type:'learning_restore',payload:{events:original}},'*');await new Promise(r=>setTimeout(r,40));const added=qaHostEvents.slice(before);const d=f.contentDocument;d.getElementById('reflection').click();await new Promise(r=>setTimeout(r,20));return {restoredStage:d.querySelector('.stage-meta').innerText,restoredReady:qaHostEvents.filter(e=>e.type==='activity_state').at(-1)?.payload.readyForReflection,newAttempts:added.filter(e=>e.type==='attempt').length,openReflection:qaHostEvents.at(-1).type,maxPayload:Math.max(...qaHostEvents.map(e=>new TextEncoder().encode(JSON.stringify(e.payload)).length)),portugueseRows:original.filter(e=>e.type==='assessment_result').every(e=>e.payload.result==='Declaração do grupo'),fieldNotes:original.filter(e=>e.type==='assessment_result').every(e=>typeof e.payload.detail.note==='string')}})()""")
        results['sourceSha256'] = hashlib.sha256(Path('/home/proteu/pagecraft/drafts/canva-animais-4ano.html').read_bytes()).hexdigest()
        log_event('canva-qa', {'event': 'qa-cdp-diagnostics', 'scope': 'localhost activity only', 'viewports': [390, 768, 1280], 'supportJourneys': 3})
    (OUT / 'browser-checks.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'journeys': results['journeys'], 'layouts': results['allStageLayouts'], 'zoom': results['zoomAfterEscape'], 'keyboard': results['keyboardSupport'], 'offline': results['offline'], 'restore': results['bridgeRestore'], 'sha256': results['sourceSha256']}, ensure_ascii=False))

asyncio.run(main())
