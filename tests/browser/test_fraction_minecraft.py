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
