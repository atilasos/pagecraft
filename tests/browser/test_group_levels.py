"""The common level changes real controls in existing published activities."""
import re

import httpx
import pytest


@pytest.mark.parametrize('slug, intermediate, count', [
    ('bota', 'standard', 8),
    ('arvore', 'standard', 1),
    ('canva-4ano-estudio-de-slides', 'standard', 2),
    ('classificar-objetos-1ano', 'intermedio', 3),
    ('2026-03-17-dobro-ate-10', 'medio', 3),
    ('dedo', 'middle', 7),
])
def test_common_level_changes_every_activity_unit(page, studio_origin, slug, intermediate, count):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        classroom = teacher.post('/api/classes', json={
            'name':'Nível conjunto', 'year':2, 'students':['Ana','Bruno']
        }).json()
        session = teacher.post('/api/sessions', json={
            'class_id':classroom['id'], 'activity_slug':slug
        }).json()
        page.goto(studio_origin + '/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_role('button', name='A pares', exact=True).click()
        page.get_by_role('button', name='Ana', exact=True).click()
        page.get_by_role('button', name='Bruno', exact=True).click()
        page.get_by_role('button', name='Começar', exact=True).click()
        page.get_by_label('Nível do grupo', exact=True).select_option('challenge')
        lesson = page.frame_locator('#activity-frame')
        chosen = lesson.locator('button[data-level].active, button[data-level][aria-selected=true], .diff-tabs button[data-show][aria-selected=true]')
        expect(chosen).to_have_count(count)
        attribute = 'data-show' if slug.startswith('canva') else 'data-level'
        challenge = re.compile('.*challenge$') if attribute == 'data-show' else (
            'desafio' if intermediate in ['intermedio','medio'] else 'challenge'
        )
        for i in range(count):
            expect(chosen.nth(i)).to_have_attribute(attribute, challenge)
        page.get_by_label('Nível do grupo', exact=True).select_option('intermediate')
        for i in range(count):
            expected = re.compile('.*standard$') if attribute == 'data-show' else intermediate
            expect(chosen.nth(i)).to_have_attribute(attribute, expected)
