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


def test_levels_correction_and_all_navigation_paths(page, lesson_origin):
    page.goto(lesson_origin)
    level = page.get_by_label('Nível de diferenciação')
    assert level.input_value() == 'intermediate'
    for choice in ['support', 'intermediate', 'challenge']:
        page.goto(lesson_origin)
        level.select_option(choice)
        assert page.get_by_role('button', name='3. Rever', exact=True).is_disabled()
        assert page.get_by_role('button', name='2. Inventar' if choice == 'challenge' else '2. Comparar', exact=True).is_disabled()
        page.get_by_role('button', name='Cortar ao meio', exact=True).click()
        page.get_by_role('button', name='Sim', exact=True).click()
        page.get_by_role('button', name='Seguinte', exact=True).click()
        if choice == 'challenge':
            page.get_by_role('button', name='Cortar à direita', exact=True).click()
            page.get_by_role('button', name='O pão tem outra cor.', exact=True).click()
        else:
            page.get_by_role('button', name='Partilha B', exact=True).click()
        page.get_by_role('button', name='Seguinte', exact=True).click()
        assert page.get_by_role('heading', name='Respondeste à unidade do pão.').is_visible()
        page.get_by_role('button', name='1. Partilhar', exact=True).click()
        assert page.get_by_role('button', name='Sim', exact=True).get_attribute('aria-pressed') == 'true'
        page.get_by_role('button', name='Cortar à esquerda', exact=True).click()
        assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
        assert page.get_by_role('button', name='3. Rever', exact=True).is_disabled()
        page.get_by_role('button', name='Não', exact=True).click()
        assert page.get_by_role('button', name='3. Rever', exact=True).is_enabled()
