"""The final construction is declared; only the on-page answer is assessed."""
from playwright.sync_api import expect
from test_fraction_units import finish_representations


def finish_exploration(lesson, level='intermediate'):
    finish_representations(lesson, level)
    lesson.get_by_role('button', name='Confirmar composição').click()
    lesson.get_by_role('button', name='Não', exact=True).click()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    count = 3 if level == 'challenge' else 2
    for i in range(count):
        lesson.get_by_role('group', name=f'Comparação {i+1} de {count}', exact=True).get_by_role('button', name='Iguais', exact=True).click()
    lesson.get_by_role('button', name='9. Construir', exact=True).click()


def test_construction_requires_both_declaration_and_answer(page, lesson_origin):
    page.goto(lesson_origin)
    finish_exploration(page)
    expect(page.get_by_role('heading', name='Pinta 1/4 dos 20 blocos.')).to_be_visible()
    next_button = page.get_by_role('button', name='Seguinte', exact=True)
    assert next_button.is_disabled()
    page.get_by_role('button', name='2 blocos', exact=True).click()
    assert next_button.is_disabled()
    assert page.get_by_role('button', name='10. Refletir', exact=True).is_disabled()
    page.get_by_role('button', name='Já fizemos', exact=True).click()
    assert next_button.is_enabled()
    expect(page.get_by_text('Conta os blocos de cada grupo.', exact=True)).to_be_visible()
    page.get_by_role('button', name='Papel ou cubos', exact=True).click()
    assert next_button.is_disabled()
    expect(page.get_by_role('button', name='Já fizemos', exact=True)).to_have_attribute('aria-pressed','false')
    page.get_by_role('button', name='Já fizemos', exact=True).click()
    assert next_button.is_disabled()
    page.get_by_role('button', name='5 blocos', exact=True).click()
    expect(page.get_by_text('Um quarto são 5 blocos.', exact=True)).to_be_visible()
    next_button.click()
    expect(page.get_by_role('heading', name='Como foi o teu trabalho?')).to_be_visible()
    page.get_by_role('button', name='9. Construir', exact=True).click()
    expect(page.get_by_role('button', name='5 blocos', exact=True)).to_have_attribute('aria-pressed','true')


def test_standalone_reflection_is_optional_and_does_not_claim_sending(page, lesson_origin):
    page.goto(lesson_origin)
    finish_exploration(page)
    page.get_by_role('button', name='Já fizemos', exact=True).click()
    page.get_by_role('button', name='2 blocos', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    page.get_by_role('button', name='Refletir sobre o meu trabalho').click()
    group = page.get_by_role('group', name='Represento uma fração numa unidade de 20 blocos.', exact=True)
    group.get_by_role('button', name='Com ajuda', exact=True).click()
    page.get_by_label('O que te ajudou?').fill('Contar os grupos')
    page.get_by_role('button', name='Terminar a reflexão', exact=True).click()
    expect(page.get_by_role('heading', name='Terminaste a reflexão.')).to_be_visible()
    assert page.get_by_role('heading', name='Terminaste a reflexão.').evaluate('(el) => el === document.activeElement')
    expect(page.get_by_text('As respostas ficam apenas nesta página.', exact=True)).to_be_visible()
    assert page.get_by_role('button', name='Terminar a reflexão', exact=True).count() == 0


def start_preview(page, studio_origin, *, requires_completion=True):
    import json
    from pathlib import Path
    registration = json.loads((Path(__file__).resolve().parents[2] / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    if not requires_completion:
        registration.pop('requires_completion',None)
    page.request.get(studio_origin + '/api/teacher-bootstrap')
    page.request.post(studio_origin + '/api/learning/me/leave')
    draft = page.request.post(studio_origin + '/api/learning/activities', data=registration).json()
    page.goto(studio_origin + '/' + draft['code'])
    page.get_by_label('Como te chamas?').fill('Revisão completa')
    page.get_by_role('button', name='Começar', exact=True).click()
    return page.frame_locator('#lesson')


def test_studio_reflection_waits_for_complete_work_and_finishes_once(page, studio_origin):
    lesson = start_preview(page, studio_origin)
    expect(lesson.get_by_role('button', name='Cortar ao meio', exact=True)).to_be_visible()
    expect(page.get_by_role('button', name='Autoavaliar e terminar', exact=True)).to_be_disabled()
    finish_exploration(lesson)
    lesson.get_by_role('button', name='Já fizemos', exact=True).click()
    assert page.get_by_role('button', name='Autoavaliar e terminar', exact=True).is_disabled()
    lesson.get_by_role('button', name='2 blocos', exact=True).click()
    expect(page.get_by_role('button', name='Autoavaliar e terminar', exact=True)).to_be_enabled()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    lesson.get_by_role('button', name='Refletir sobre o meu trabalho').click()
    expect(page.locator('#reflection')).to_be_visible()
    assert page.locator('#reflection h1').evaluate('(el) => el === document.activeElement')
    page.get_by_role('group', name='Represento uma fração numa unidade de 20 blocos.', exact=True).get_by_role('radio', name='Consegui com ajuda', exact=True).check()
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    result = page.request.get(studio_origin + '/api/learning/me').json()
    assert result['completed_at']
    assert result['assessment']['answers']['construir'] == 'help'
    assert [e['payload']['correct'] for e in result['events'] if e['type'] == 'attempt' and e['unitId'] == 'u6'] == [False]
    assert not [e for e in result['events'] if e['type'] == 'assessment_result']
    repeated = page.request.post(studio_origin + '/api/learning/me/finish', data=result['assessment']).json()
    assert repeated['completed_at'] == result['completed_at']
    assert page.request.get(studio_origin + '/api/learning/reports').json() == []


def test_long_drawing_does_not_prevent_later_work_from_being_saved(page, studio_origin):
    import time
    lesson = start_preview(page, studio_origin)
    finish_exploration(lesson)
    lesson.get_by_role('button', name='5. Grelha', exact=True).click()
    lesson.get_by_text('Desenho livre (opcional)', exact=True).click()
    sketch = lesson.get_by_role('img', name='Desenho livre, sem avaliação')
    sketch.scroll_into_view_if_needed()
    box = sketch.bounding_box()
    page.mouse.move(box['x']+10,box['y']+30)
    page.mouse.down()
    page.mouse.move(box['x']+box['width']-10,box['y']+box['height']-30,steps=250)
    page.mouse.up()
    lesson.get_by_role('button', name='9. Construir', exact=True).click()
    lesson.get_by_role('button', name='Já fizemos', exact=True).click()
    lesson.get_by_role('button', name='5 blocos', exact=True).click()
    # Wait for the real queue to save the final construction checkpoint.
    for _ in range(40):
        data = page.request.get(studio_origin + '/api/learning/me').json()
        snapshots = [e for e in data['events'] if e['type'] == 'activity_state']
        if snapshots and snapshots[-1]['payload']['state'].get('maker',{}).get('answer') == 5:
            break
        time.sleep(.1)
    else:
        raise AssertionError('A drawing prevented the construction checkpoint from being saved')
    page.reload()
    expect(lesson.get_by_role('button', name='5 blocos', exact=True)).to_have_attribute('aria-pressed','true')
    expect(page.get_by_role('button', name='Autoavaliar e terminar', exact=True)).to_be_enabled()
    lesson.get_by_role('button', name='5. Grelha', exact=True).click()
    lesson.get_by_text('Desenho livre (opcional)', exact=True).click()
    assert sketch.locator('path').get_attribute('d').count('L') >= 200


import pytest


@pytest.mark.parametrize('level', ['support','intermediate','challenge'])
@pytest.mark.parametrize('width', [390,768,1280])
def test_final_pages_on_touch_layouts_and_twenty_block_geometry(page, lesson_origin, level, width):
    page.set_viewport_size({'width':width,'height':900})
    page.goto(lesson_origin + '?presentation=1')
    page.get_by_label('Nível de diferenciação').select_option(level)
    page.get_by_role('button', name='9. Construir', exact=True).click()
    target = {'support':'1/2','intermediate':'1/4','challenge':'1/4'}[level]
    if level == 'challenge':
        page.get_by_role('group', name='Fração para construir').get_by_role('button', name=target, exact=True).click()
    expected = 10 if level == 'support' else 5
    picture = page.get_by_role('img', name=f'{expected} de 20 blocos pintados, {2 if level == "support" else 4} grupos iguais').first
    blocks = picture.locator('[data-block]')
    assert blocks.count() == 20
    assert blocks.evaluate_all('(items) => items.filter(r => r.getAttribute("fill") === "#315e4d").length') == expected
    assert blocks.evaluate_all('(items) => items.every(r => r.getAttribute("width") === "60" && r.getAttribute("height") === "60")')
    page.get_by_role('button', name='Já fizemos', exact=True).click()
    page.get_by_role('button', name=f'{expected} blocos', exact=True).click()
    assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
    assert page.locator('.scene button,.panel .choices button').evaluate_all('(buttons) => buttons.every(b => b.getBoundingClientRect().width >= 56 && b.getBoundingClientRect().height >= 56)')
    page.get_by_role('button', name='10. Refletir', exact=True).click()
    page.get_by_role('button', name='Refletir sobre o meu trabalho').click()
    assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
    button = page.get_by_role('group', name='Represento uma fração numa unidade de 20 blocos.', exact=True).get_by_role('button', name='Com ajuda', exact=True)
    button.focus()
    page.keyboard.press('Enter')
    assert button.evaluate('(el) => el === document.activeElement')
    page.get_by_role('button', name='Terminar a reflexão').click()
    expect(page.get_by_role('heading', name='Terminaste a reflexão.')).to_be_visible()


def test_changing_fraction_invalidates_construction_and_all_examples_are_exact(page, lesson_origin):
    page.goto(lesson_origin)
    finish_exploration(page,'challenge')
    for target, painted, groups in [('1/2',10,2),('1/4',5,4),('2/5',8,5),('1/10',2,10)]:
        page.get_by_role('group', name='Fração para construir').get_by_role('button', name=target, exact=True).click()
        assert page.get_by_role('button', name='10. Refletir', exact=True).is_disabled()
        picture = page.get_by_role('img', name=f'{painted} de 20 blocos pintados, {groups} grupos iguais').first
        assert picture.locator('g').count() == groups
        assert picture.locator('[data-block]').evaluate_all('(items) => items.filter(r => r.getAttribute("fill") === "#315e4d").length') == painted
        assert all(picture.locator('g').nth(i).locator('[data-block]').count() == 20//groups for i in range(groups))
        page.get_by_role('button', name='Já fizemos', exact=True).click()
        page.get_by_role('button', name=f'{painted} blocos', exact=True).click()
        assert page.get_by_role('button', name='10. Refletir', exact=True).is_enabled()
    page.get_by_role('button', name='1. Partilhar', exact=True).click()
    expect(page.get_by_role('button', name='Sim', exact=True)).to_have_attribute('aria-pressed','true')


def test_reflection_is_locked_while_the_lesson_is_loading(page, studio_origin):
    pending = []
    page.route('**/api/learning/activities/*/content', lambda route: pending.append(route))
    lesson = start_preview(page, studio_origin)
    expect(page.locator('#work')).to_be_visible()
    expect(page.get_by_role('button', name='Autoavaliar e terminar', exact=True)).to_be_disabled()
    assert pending
    pending[0].continue_()
    expect(lesson.get_by_role('button', name='Cortar ao meio', exact=True)).to_be_visible()
    assert page.get_by_role('button', name='Autoavaliar e terminar', exact=True).is_disabled()


def test_legacy_activities_keep_the_existing_reflection_flow(page, studio_origin):
    start_preview(page, studio_origin, requires_completion=False)
    button = page.get_by_role('button', name='Autoavaliar e terminar', exact=True)
    expect(button).to_be_enabled()
    button.click()
    expect(page.locator('#reflection')).to_be_visible()


def test_demonstration_can_complete_construction_and_reflection_without_events(page, lesson_origin):
    page.set_content('<iframe title="Demonstração"></iframe>')
    page.evaluate('''url => {
        window.received = [];
        addEventListener('message', e => { if (e.data?.pagecraft === 1) received.push(e.data); });
        document.querySelector('iframe').src = url;
    }''',lesson_origin + '?presentation=1')
    lesson = page.frame_locator('iframe')
    lesson.get_by_role('button', name='9. Construir', exact=True).click()
    lesson.get_by_role('button', name='Já fizemos', exact=True).click()
    lesson.get_by_role('button', name='2 blocos', exact=True).click()
    lesson.get_by_role('button', name='10. Refletir', exact=True).click()
    lesson.get_by_role('button', name='Refletir sobre o meu trabalho').click()
    lesson.get_by_role('button', name='Terminar a reflexão').click()
    expect(lesson.get_by_role('heading', name='Terminaste a reflexão.')).to_be_visible()
    assert page.evaluate('received') == []
