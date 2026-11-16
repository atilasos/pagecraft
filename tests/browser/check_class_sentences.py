"""QA: uv run --no-project --with playwright python tests/browser/check_class_sentences.py."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
    try:
        for restore_first in (True, False):
            page = browser.new_page(viewport={'width': 1366, 'height': 768})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto((ROOT/'drafts/m28p-v3/menina/m28p-ciclo-menina-sentence.html').as_uri())
            page.evaluate('''restoreFirst => {
              const send=(type,payload)=>window.postMessage({pagecraft:1,type,payload},'*');
              const state={version:3,page:0,level:'support',answers:{'c-turma':['p0']},confirmed:{},aids:{'c-turma':{demo_shown:true}},counts:{},last:{}};
              if(restoreFirst)send('state_restore',{state});
              send('class_sentences',{sentences:[{id:'turma',text:'A menina.',tokens:['A','menina']}]});
              if(!restoreFirst)send('state_restore',{state});
            }''', restore_first)
            page.get_by_text('Frase da turma', exact=True).wait_for()
            assert page.locator('.tray button').count() == 1
            assert 'A · menina.' in page.locator('.model').text_content()
            # Sem voz local, não pode existir leitura remota nem botão enganador.
            if not page.evaluate("!!window.speechSynthesis?.getVoices().some(v=>v.localService===true&&/^pt[-_]PT$/i.test(v.lang))"):
                assert page.locator('.model').get_by_role('button', name='Ouvir a frase').count() == 0
            # A voz remota aparece primeiro: só a voz local pode receber o texto.
            page.evaluate("""() => {
              window.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};
              speechSynthesis.getVoices=()=>[{lang:'pt-PT',localService:false},{lang:'pt-PT',localService:true}];
              speechSynthesis.speak=u=>{window.spoken={text:u.text,local:u.voice.localService};};
              speechSynthesis.dispatchEvent(new Event('voiceschanged'));
            }""")
            page.locator('.model').get_by_role('button', name='Ouvir a frase').click()
            assert page.evaluate('window.spoken') == {'text': 'A menina.', 'local': True}
            page.locator('[data-piece="p1"]').click()
            page.locator('#confirm').click()
            assert 'Encontraste' in page.locator('#feedback').text_content()
            page.locator('.support-details summary').click()
            page.locator('[data-level=intermediate]').click()
            assert 'A · menina' not in page.locator('.model').text_content()
            assert not errors, errors
            print(f'Frase da turma: restauro {"antes" if restore_first else "depois"}, montagem e apoios OK')
            page.close()
    finally:
        browser.close()
