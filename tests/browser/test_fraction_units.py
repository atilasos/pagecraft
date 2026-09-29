"""The child answers each request; correctness never gates navigation."""
from playwright.sync_api import expect


def finish_bread(page, level='intermediate'):
    page.get_by_label('Nível de diferenciação').select_option(level)
    page.get_by_role('button', name='Cortar ao meio', exact=True).click()
    page.get_by_role('button', name='Sim', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    if level == 'challenge':
        page.get_by_role('button', name='Cortar à esquerda', exact=True).click()
        page.get_by_role('button', name='As partes têm tamanhos diferentes.', exact=True).click()
    else:
        page.get_by_role('button', name='Partilha A', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()


def test_fraction_representation_needs_confirmation_and_allows_correction(page, lesson_origin):
    page.goto(lesson_origin)
    finish_bread(page)
    expect(page.get_by_role('heading', name='Pinta 1/4.')).to_be_visible()
    next_button = page.get_by_role('button', name='Seguinte', exact=True)
    assert next_button.is_disabled()
    # A displayed empty grid becomes an answer only when confirmed.
    page.get_by_role('button', name='Confirmar representação').click()
    expect(page.get_by_text('Compara com a fração pedida.', exact=True)).to_be_visible()
    assert next_button.is_enabled()
    page.get_by_role('button', name='Parte 1', exact=True).click()
    assert next_button.is_disabled()
    page.get_by_role('button', name='Confirmar representação').click()
    expect(page.get_by_text('Representaste 1/4.', exact=True)).to_be_visible()
    assert next_button.is_enabled()
    page.get_by_role('button', name='1. Partilhar', exact=True).click()
    page.get_by_role('button', name='3. Pintar', exact=True).click()
    assert page.get_by_role('button', name='Parte 1', exact=True).get_attribute('aria-pressed') == 'true'
    assert next_button.is_enabled()


def test_associations_keep_wrong_answers_and_grid_requires_confirmation(page, lesson_origin):
    page.goto(lesson_origin)
    finish_bread(page)
    page.get_by_role('button', name='Confirmar representação').click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    first = page.get_by_role('group', name='Associação 1 de 2', exact=True)
    second = page.get_by_role('group', name='Associação 2 de 2', exact=True)
    first.get_by_role('button', name='1/4', exact=True).click()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
    second.get_by_role('button', name='1/4', exact=True).click()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_enabled()
    expect(first.get_by_text('Olha para as partes pintadas.', exact=True)).to_be_visible()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    expect(page.get_by_role('heading', name='Mostra 3/4 na grelha.')).to_be_visible()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
    page.get_by_role('button', name='Parte 1', exact=True).click()
    page.get_by_role('button', name='Confirmar grelha', exact=True).click()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_enabled()
    page.get_by_role('button', name='4. Associar', exact=True).click()
    assert first.get_by_role('button', name='1/4', exact=True).get_attribute('aria-pressed') == 'true'
    first.get_by_role('button', name='1/2', exact=True).click()
    expect(first.get_by_text('Ligaste as representações.', exact=True)).to_be_visible()
    page.get_by_role('button', name='5. Grelha', exact=True).click()
    assert page.get_by_role('button', name='Parte 1', exact=True).get_attribute('aria-pressed') == 'true'
    page.get_by_role('button', name='Parte 2', exact=True).click()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()


def finish_representations(page, level='intermediate'):
    finish_bread(page, level)
    page.get_by_role('button', name='Confirmar representação').click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    count = 3 if level == 'challenge' else 2
    for i in range(count):
        page.get_by_role('group', name=f'Associação {i+1} de {count}', exact=True).get_by_role('button', name='1/4', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    page.get_by_role('button', name='Confirmar grelha', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()


def test_whole_requires_composition_and_answer_and_comparisons_accept_errors(page, lesson_origin):
    page.goto(lesson_origin)
    finish_representations(page)
    expect(page.get_by_role('heading', name='Completa a unidade.')).to_be_visible()
    next_button = page.get_by_role('button', name='Seguinte', exact=True)
    assert page.get_by_role('button', name='Sim', exact=True).is_disabled()
    page.get_by_role('button', name='Confirmar composição').click()
    assert next_button.is_disabled()
    page.get_by_role('button', name='Sim', exact=True).click()
    assert next_button.is_enabled()
    expect(page.get_by_text('Olha para os espaços livres.', exact=True)).to_be_visible()
    page.get_by_role('button', name='Parte 1', exact=True).click()
    assert next_button.is_disabled()
    assert page.get_by_role('button', name='Sim', exact=True).is_disabled()
    page.get_by_role('button', name='Confirmar composição').click()
    page.get_by_role('button', name='Não', exact=True).click()
    next_button.click()
    expect(page.get_by_role('heading', name='Qual tem mais pintado?')).to_be_visible()
    first = page.get_by_role('group', name='Comparação 1 de 2', exact=True)
    second = page.get_by_role('group', name='Comparação 2 de 2', exact=True)
    first.get_by_role('button', name='A', exact=True).click()
    assert next_button.is_disabled()
    second.get_by_role('button', name='B', exact=True).click()
    assert next_button.is_enabled()
    expect(first.get_by_text('Alinha as partes pintadas.', exact=True)).to_be_visible()
    next_button.click()
    expect(page.get_by_role('heading', name='Exploraste as cinco unidades.')).to_be_visible()
    page.get_by_role('button', name='6. Completar', exact=True).click()
    page.get_by_role('button', name='Parte 2', exact=True).click()
    assert page.get_by_role('button', name='8. Rever', exact=True).is_disabled()
    assert page.get_by_role('button', name='7. Comparar', exact=True).is_disabled()


import pytest


@pytest.mark.parametrize('level', ['support', 'intermediate', 'challenge'])
@pytest.mark.parametrize('width', [390, 768, 900, 1280])
def test_five_units_at_each_level_and_width(page, lesson_origin, level, width):
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.set_viewport_size({'width':width, 'height':900})
    page.goto(lesson_origin)
    finish_representations(page, level)
    page.get_by_role('button', name='Confirmar composição').click()
    page.get_by_role('button', name='Sim', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    count = 3 if level == 'challenge' else 2
    for i in range(count):
        group = page.get_by_role('group', name=f'Comparação {i+1} de {count}', exact=True)
        group.get_by_role('button', name='A', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    expect(page.get_by_role('heading', name='Exploraste as cinco unidades.')).to_be_visible()
    for label in ['1. Partilhar', '3. Pintar', '4. Associar', '5. Grelha', '6. Completar', '7. Comparar']:
        page.get_by_role('button', name=label, exact=True).click()
        assert page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth')
        dimensions = page.locator('.scene button').evaluate_all('(buttons) => buttons.map(b => ({w:b.getBoundingClientRect().width,h:b.getBoundingClientRect().height}))')
        assert all(d['w'] >= 56 and d['h'] >= 56 for d in dimensions)
        panels = page.locator('.panel').evaluate_all('(panels) => panels.map(p => ({x:p.getBoundingClientRect().x,y:p.getBoundingClientRect().y}))')
        assert panels[0]['y'] < panels[1]['y'] < panels[2]['y'] if width <= 960 else panels[0]['x'] < panels[1]['x'] < panels[2]['x']
    # Known equality 1/2 = 1/2 or 2/4 = 1/2, with identical whole widths.
    group = page.get_by_role('group', name=f'Comparação {count} de {count}', exact=True)
    group.get_by_role('button', name='Iguais', exact=True).click()
    expect(group.get_by_text('Comparaste a parte pintada.', exact=True)).to_be_visible()
    bars = group.locator('.equal-units').first.locator('svg')
    assert bars.nth(0).bounding_box()['width'] == bars.nth(1).bounding_box()['width']
    # Use the keyboard to paint, invalidate confirmation, and regain it.
    page.get_by_role('button', name='5. Grelha', exact=True).click()
    cell = page.get_by_role('button', name='Parte 1', exact=True)
    cell.focus()
    page.keyboard.press('Space')
    assert cell.evaluate('(el) => el === document.activeElement')
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
    page.get_by_role('button', name='Confirmar grelha').click()
    page.get_by_role('button', name='1. Partilhar', exact=True).click()
    assert page.get_by_role('button', name='Sim', exact=True).get_attribute('aria-pressed') == 'true'
    assert errors == []


def test_level_change_preserves_unchanged_requests(page, lesson_origin):
    page.goto(lesson_origin)
    finish_representations(page)
    page.get_by_role('button', name='5. Grelha', exact=True).click()
    page.get_by_role('button', name='Parte 1', exact=True).click()
    page.get_by_role('button', name='Confirmar grelha', exact=True).click()
    page.get_by_label('Nível de diferenciação').select_option('challenge')
    # Bread question, symbol and associations changed; same 3/4 grid survives.
    expect(page.get_by_role('heading', name='Porque não são metades?')).to_be_visible()
    page.get_by_role('button', name='Cortar à esquerda', exact=True).click()
    page.get_by_role('button', name='As partes têm tamanhos diferentes.', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
    page.get_by_role('button', name='Confirmar representação').click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    for i in range(3):
        page.get_by_role('group', name=f'Associação {i+1} de 3').get_by_role('button', name='1/4', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    expect(page.get_by_role('button', name='Parte 1', exact=True)).to_have_attribute('aria-pressed', 'true')
    assert page.get_by_role('button', name='Seguinte', exact=True).is_enabled()


def test_unchanged_association_survives_switching_support(page, lesson_origin):
    page.goto(lesson_origin)
    finish_representations(page, 'support')
    page.get_by_label('Nível de diferenciação').select_option('intermediate')
    page.get_by_role('button', name='Confirmar representação').click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    first = page.get_by_role('group', name='Associação 1 de 2', exact=True)
    expect(first.get_by_role('button', name='1/4', exact=True)).to_have_attribute('aria-pressed', 'true')
    second = page.get_by_role('group', name='Associação 2 de 2', exact=True)
    assert second.get_by_role('button', name='1/4', exact=True).get_attribute('aria-pressed') == 'false'
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()


def test_realization_restores_all_units_and_drawing_without_duplicate_attempts(page, studio_origin):
    import json
    import time
    from pathlib import Path
    registration = json.loads((Path(__file__).resolve().parents[2] / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    page.request.get(studio_origin + '/api/teacher-bootstrap')
    page.request.post(studio_origin + '/api/learning/me/leave')
    draft = page.request.post(studio_origin + '/api/learning/activities', data=registration).json()
    page.goto(studio_origin + '/' + draft['code'])
    page.get_by_label('Como te chamas?').fill('Ensaio cinco unidades')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    finish_representations(lesson)
    lesson.get_by_role('button', name='Confirmar composição').click()
    lesson.get_by_role('button', name='Não', exact=True).click()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    for i in range(2):
        lesson.get_by_role('group', name=f'Comparação {i+1} de 2', exact=True).get_by_role('button', name='Iguais', exact=True).click()
    lesson.get_by_role('button', name='5. Grelha', exact=True).click()
    lesson.get_by_text('Desenho livre (opcional)', exact=True).click()
    sketch = lesson.get_by_role('img', name='Desenho livre, sem avaliação')
    sketch.focus()
    page.keyboard.press('ArrowRight')
    page.keyboard.press('Space')
    path = sketch.locator('path').get_attribute('d')
    assert path
    lesson.get_by_role('button', name='8. Rever', exact=True).click()
    for _ in range(50):
        data = page.request.get(studio_origin + '/api/learning/me').json()
        snapshots = [e for e in data['events'] if e['type'] == 'activity_state']
        if snapshots and snapshots[-1]['payload']['state']['page'] == 7:
            break
        time.sleep(.1)
    else:
        raise AssertionError('The last page was not saved')
    attempts = [e for e in data['events'] if e['type'] == 'attempt']
    assert set(e['unitId'] for e in attempts) == {'u1','u2','u3','u4','u5'}
    assert len(attempts) == 10
    assert [e['payload']['correct'] for e in attempts if e['unitId'] == 'u5'] == [False, True]
    page.reload()
    expect(lesson.get_by_role('heading', name='Exploraste as cinco unidades.')).to_be_visible()
    lesson.get_by_role('button', name='5. Grelha', exact=True).click()
    lesson.get_by_text('Desenho livre (opcional)', exact=True).click()
    assert sketch.locator('path').get_attribute('d') == path
    assert lesson.get_by_role('button', name='Seguinte', exact=True).is_enabled()
    lesson.get_by_role('button', name='4. Associar', exact=True).click()
    expect(lesson.get_by_role('group', name='Associação 2 de 2').get_by_role('button', name='1/4', exact=True)).to_have_attribute('aria-pressed', 'true')
    after = page.request.get(studio_origin + '/api/learning/me').json()['events']
    assert len([e for e in after if e['type'] == 'attempt']) == len(attempts)
    assert page.request.get(studio_origin + '/api/learning/reports').json() == []


def test_touch_controls_and_known_fraction_geometry(page, lesson_origin):
    context = page.context.browser.new_context(has_touch=True, viewport={'width':390,'height':900})
    touch = context.new_page()
    try:
        touch.goto(lesson_origin + '?presentation=1')
        touch.get_by_label('Nível de diferenciação').select_option('challenge')
        touch.get_by_role('button', name='3. Pintar', exact=True).tap()
        touch.get_by_role('button', name='Parte 1', exact=True).tap()
        touch.get_by_role('button', name='Parte 2', exact=True).tap()
        touch.get_by_role('button', name='Confirmar representação').tap()
        expect(touch.get_by_text('Representaste 2/5.', exact=True)).to_be_visible()
        # 2/5 of the full 300-unit SVG is 120, made of two equal 60-unit parts.
        drawing = touch.get_by_role('img', name='2 de 5 partes iguais pintadas').last
        rects = drawing.locator('rect').evaluate_all('(items) => items.map(r => ({x:+r.getAttribute("x"),width:+r.getAttribute("width"),fill:r.getAttribute("fill")}))')
        assert [r['x'] for r in rects] == [0,60,120,180,240]
        assert [r['width'] for r in rects] == [60,60,60,60,60]
        assert rects[0]['fill'] == rects[1]['fill'] != rects[2]['fill']
        touch.get_by_role('button', name='5. Grelha', exact=True).tap()
        touch.get_by_text('Desenho livre (opcional)', exact=True).tap()
        sketch = touch.get_by_role('img', name='Desenho livre, sem avaliação')
        sketch.tap()
        assert sketch.locator('path').get_attribute('d')
        touch.get_by_role('button', name='Limpar desenho').tap()
        expect(sketch).to_be_visible()
        assert sketch.locator('path').get_attribute('d') == ''
        assert touch.get_by_role('button', name='Limpar desenho').evaluate('(el) => el === document.activeElement')
    finally:
        context.close()


def test_same_comparison_survives_a_different_position_in_next_level(page, lesson_origin):
    page.goto(lesson_origin)
    finish_representations(page)
    page.get_by_role('button', name='Confirmar composição').click()
    page.get_by_role('button', name='Não', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    page.get_by_role('group', name='Comparação 2 de 2', exact=True).get_by_role('button', name='Iguais', exact=True).click()
    page.get_by_role('button', name='1. Partilhar', exact=True).click()
    finish_representations(page, 'challenge')
    page.get_by_role('button', name='Confirmar composição').click()
    page.get_by_role('button', name='Não', exact=True).click()
    page.get_by_role('button', name='Seguinte', exact=True).click()
    expect(page.get_by_role('group', name='Comparação 3 de 3', exact=True).get_by_role('button', name='Iguais', exact=True)).to_have_attribute('aria-pressed','true')
    assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
