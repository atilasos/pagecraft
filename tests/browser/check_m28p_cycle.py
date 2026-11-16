"""QA local: uv run --no-project --with playwright python tests/browser/check_m28p_cycle.py."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
    try:
        for width in (1366,920):
            for game in ('listen-build','read-choose','sentence','discover'):
                page=browser.new_page(viewport={'width':width,'height':768})
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto((ROOT/f'drafts/m28p-v3/uva/m28p-ciclo-uva-{game}.html').as_uri())
                data=json.loads(page.locator('#m28p-content').text_content())
                r=data['rounds'][0]
                def key(selector):
                    page.locator(selector).first.focus()
                    page.keyboard.press('Enter')
                key('#start');key('#demo-close')
                if game=='discover':
                    # Duas vogais isoladas não são palavras da lista.
                    for label in ('a','a'):
                        page.get_by_role('button',name=label,exact=True).last.focus();page.keyboard.press('Enter')
                    key('#confirm')
                    assert 'Essa não está na nossa lista' in page.locator('#feedback').text_content()
                    key('#undo');key('#undo')
                    w=next(w for w in r['lexicon'] if len(w['syllables'])==2)
                    for label in w['syllables']:
                        page.get_by_role('button',name=label,exact=True).last.focus();page.keyboard.press('Enter')
                    key('#confirm')
                    assert w['label'] in page.locator('#round-content').text_content()
                else:
                    wrong=r['answer'][::-1] if game!='read-choose' else [next(o['id'] for o in r['options'] if o['id'] not in r['answer'])]
                    for id_ in wrong:
                        key(f'[data-{"option" if game=="read-choose" else "piece"}="{id_}"]')
                    key('#confirm');assert page.locator('#next').is_visible()
                    assert 'Podes experimentar' in page.locator('#feedback').text_content()
                    if game!='read-choose':
                        assert page.locator('.visual-cue').count()>0
                        for _ in wrong:key('#undo')
                    for id_ in r['answer']:
                        key(f'[data-{"option" if game=="read-choose" else "piece"}="{id_}"]')
                    key('#confirm');assert 'Encontraste' in page.locator('#feedback').text_content()
                key('#next')
                assert 'Ronda 2' in page.locator('#progress').get_attribute('aria-label')
                assert not errors,errors
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                print(f'{width} {game}: teclado, tentativa, correção e avanço OK')
                page.close()
    finally:
        browser.close()
