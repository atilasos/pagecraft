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


def test_bridge_reports_answers_but_presentation_does_not(page, lesson_origin):
    page.set_content('<iframe title="Atividade"></iframe><pre id="events"></pre>')
    page.evaluate('''url => {
        window.received = [];
        addEventListener('message', event => {
            if (event.source === document.querySelector('iframe').contentWindow && event.data?.pagecraft === 1) {
                received.push(event.data);
                document.querySelector('#events').textContent = JSON.stringify(received);
            }
        });
        document.querySelector('iframe').src = url;
    }''', lesson_origin)
    lesson = page.frame_locator('iframe')
    lesson.get_by_role('button', name='Cortar à esquerda', exact=True).click()
    lesson.get_by_role('button', name='Sim', exact=True).click()
    page.wait_for_function("received.some(e => e.type === 'attempt')")
    attempts = page.evaluate("received.filter(e => e.type === 'attempt')")
    assert [(e['unitId'], e['payload']['correct']) for e in attempts] == [('u1', False)]
    lesson.get_by_role('button', name='Não', exact=True).click()
    page.wait_for_function("received.filter(e => e.type === 'attempt').length === 2")
    assert page.evaluate("received.filter(e => e.type === 'attempt')[1].payload.correct") is True
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    lesson.get_by_role('button', name='1. Partilhar', exact=True).click()
    assert page.evaluate("received.filter(e => e.type === 'attempt').length") == 2
    # Existing host preference contract; a profile changes the lesson level.
    page.evaluate("document.querySelector('iframe').contentWindow.postMessage({pagecraft:1,type:'learning_preferences',payload:{level:'challenge'}}, '*')")
    from playwright.sync_api import expect
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    page.evaluate("url => document.querySelector('iframe').src = url", lesson_origin + '?presentation=1')
    expect(lesson.get_by_text('Demonstração · As respostas não ficam registadas.')).to_be_visible()
    page.evaluate('received.length = 0')
    lesson.get_by_role('button', name='2. Comparar', exact=True).click()
    lesson.get_by_role('button', name='Partilha B', exact=True).click()
    lesson.get_by_role('button', name='3. Rever', exact=True).click()
    assert page.evaluate('received.length') == 0


def test_responsive_keyboard_and_level_change_keeps_independent_answers(page, lesson_origin):
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    for width in [390, 768, 1280]:
        page.set_viewport_size({'width':width, 'height':900})
        page.goto(lesson_origin)
        for level in ['support', 'intermediate', 'challenge']:
            page.get_by_label('Nível de diferenciação').select_option(level)
            page.get_by_role('button', name='1. Partilhar', exact=True).click()
            button = page.get_by_role('button', name='Cortar ao meio', exact=True)
            button.focus()
            page.keyboard.press('Enter')
            assert button.evaluate('(el) => el === document.activeElement')
            page.get_by_role('button', name='Sim', exact=True).click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.get_by_role('button', name='Seguinte', exact=True).click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button', name='Cortar ao meio', exact=True).click()
        page.get_by_role('button', name='As partes têm tamanhos diferentes.', exact=True).click()
        page.get_by_role('button', name='Seguinte', exact=True).click()
        page.get_by_label('Nível de diferenciação').select_option('intermediate')
        assert page.get_by_role('button', name='Seguinte', exact=True).is_disabled()
        page.get_by_role('button', name='1. Partilhar', exact=True).click()
        assert page.get_by_role('button', name='Sim', exact=True).get_attribute('aria-pressed') == 'true'
    assert errors == []
