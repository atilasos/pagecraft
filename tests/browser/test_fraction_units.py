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
