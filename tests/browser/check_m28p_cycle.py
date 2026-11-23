"""QA local: uv run --no-project --with playwright python tests/browser/check_m28p_cycle.py [pasta-de-capturas]."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
pages = sorted((ROOT/'drafts/m28p-v3').glob('*/m28p-ciclo-*.html'))
pages = [p for p in pages if not p.name.endswith('-guia-docente.md')]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
    try:
        for width in (1366, 920, 390):
            for path in pages:
                page = browser.new_page(viewport={'width': width, 'height': 800})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(path.as_uri())
                data = json.loads(page.locator('#m28p-content').text_content())
                game, r = data['game'], data['rounds'][0]
                def key(selector):
                    page.locator(selector).first.focus()
                    page.keyboard.press('Enter')
                def piece(label):
                    page.locator('.pieces').get_by_role('button', name=label, exact=True, disabled=False).first.focus()
                    page.keyboard.press('Enter')
                    # Depois de usar uma peça, o foco nunca cai no corpo da página.
                    assert page.evaluate('document.activeElement && document.activeElement !== document.body'), 'foco perdido'
                key('#start')
                # A demonstração usa a palavra-chave e não mostra nenhuma resposta das rondas.
                stage = page.locator('#demo-stage').inner_text()
                answers = [w['label'] for x in data['rounds'] for w in x.get('lexicon', [])] or \
                          [x['target'].get('label') or x['target'].get('text') for x in data['rounds']]
                assert data['word']['syllables'][0] in stage, stage
                assert not any(a and a in stage for a in answers), stage
                if SHOTS and width == 1366:
                    page.wait_for_timeout(2600)
                    page.screenshot(path=str(SHOTS/f"{data['slug']}-demo.png"))
                key('#demo-close')
                state = json.loads(page.evaluate(f"sessionStorage.getItem('pagecraft:m28p-tic-v3:{data['slug']}')"))
                assert state['introDemo'] is True and not state['aids'].get(r['id'], {}).get('demo_shown')
                if game == 'discover':
                    assert f"Encontradas: 0 de {len(r['lexicon'])}" in page.locator('.hidden-count').text_content()
                    used = {s for w in r['lexicon'] for s in w['syllables']}
                    extra = [x['label'] for x in r['pieces'] if x['label'] not in used]
                    if extra:
                        for label in [extra[0], r['lexicon'][0]['syllables'][0]]:
                            piece(label)
                        key('#confirm')
                        assert 'não está escondida' in page.locator('#feedback').text_content()
                        assert page.locator('.tray.visual-cue').count() == 1
                        key('#undo'); key('#undo')
                    for w in r['lexicon']:
                        assert not page.locator('#next').is_visible()
                        for label in w['syllables']:
                            piece(label)
                        key('#confirm')
                    assert 'Encontraste todas' in page.locator('#feedback').text_content()
                    assert page.locator('.hidden-word.found').count() == len(r['lexicon'])
                    # Concluída, a ronda não reabre: desfazer fica indisponível.
                    assert page.locator('#undo').is_disabled()
                else:
                    if game == 'read-choose':
                        labels = [b.get_attribute('aria-label') for b in page.locator('.choices button').all()]
                        assert labels == ['Imagem 1', 'Imagem 2', 'Imagem 3'], labels
                        assert page.locator('.choices title').count() == 0
                    wrong = [next(o['id'] for o in r['options'] if o['id'] not in r['answer'])] if game == 'read-choose' else r['answer'][::-1]
                    for id_ in wrong:
                        key(f'[data-{"option" if game == "read-choose" else "piece"}="{id_}"]')
                    key('#confirm'); assert page.locator('#next').is_visible()
                    assert 'Experimenta outra vez' in page.locator('#feedback').text_content()
                    if game != 'read-choose':
                        assert page.locator('.visual-cue').count() > 0
                        for _ in wrong:
                            key('#undo')
                    answer = r['answer']
                    if r.get('alternatives'):
                        # A ordem equivalente também conta como certa.
                        used = []
                        answer = []
                        for label in r['alternatives'][0]:
                            pid = next(x['id'] for x in r['pieces'] if x['label'] == label and x['id'] not in used)
                            used.append(pid); answer.append(pid)
                    for id_ in answer:
                        key(f'[data-{"option" if game == "read-choose" else "piece"}="{id_}"]')
                    key('#confirm'); assert 'Está certo' in page.locator('#feedback').text_content()
                for level in ('support', 'intermediate', 'challenge'):
                    page.locator('.support-details summary').click()
                    page.locator(f'[data-level="{level}"]').click()
                    assert page.locator('#next').is_visible(), 'mudar de ajuda conserva a resposta'
                    page.locator('.support-details summary').click()
                if len(data['rounds']) > 1:
                    key('#next')
                    assert 'Ronda 2' in page.locator('#progress').get_attribute('aria-label')
                assert page.locator('svg title').count() == 0
                assert not errors, errors
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'scroll horizontal'
                print(f"{width} {data['slug']}: demonstração, teclado, tentativa, correção, níveis e avanço OK")
                page.close()
    finally:
        browser.close()
