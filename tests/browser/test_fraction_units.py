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
