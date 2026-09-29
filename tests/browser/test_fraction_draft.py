"""Public lesson behaviour; no inspection of private activity state."""

def test_all_responses_unlock_next_even_when_wrong(page, lesson_origin):
    page.goto(lesson_origin)
    next_button = page.get_by_role('button', name='Seguinte', exact=True)
    assert next_button.is_disabled()
    page.get_by_role('button', name='Cortar à esquerda', exact=True).click()
    assert next_button.is_disabled()
    page.get_by_role('button', name='Sim', exact=True).click()
    assert page.get_by_text('Compara os tamanhos.', exact=True).is_visible()
    assert next_button.is_enabled()
    next_button.click()
    assert page.get_by_role('heading', name='Qual partilha mostra metades?').is_visible()
