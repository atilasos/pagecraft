"""Fluxos do professor num Studio descartável e browser aberto pelo Hub."""

def test_class_and_session_links_keep_the_explicit_context(page, studio_origin):
    from playwright.sync_api import expect

    page.goto(studio_origin + '/teacher/')
    classes = []
    for name in ['Turma A de ensaio', 'Turma B de ensaio']:
        response = page.request.post(studio_origin + '/api/classes', data={
            'name': name, 'year': 3, 'students': ['Exemplo'],
        })
        assert response.ok
        classes.append(response.json()['id'])
    sessions = []
    for index, class_id in enumerate([classes[0], classes[0], classes[1]]):
        response = page.request.post(studio_origin + '/api/sessions', data={
            'class_id': class_id, 'activity_slug': 'canva-4ano-estudio-de-slides',
            'activity_title': f'Trabalho de ensaio {index}',
        })
        assert response.ok
        sessions.append(response.json()['id'])
        if index < 2:
            assert page.request.post(studio_origin + f'/api/sessions/{sessions[-1]}/close').ok

    page.goto(studio_origin + f'/teacher/class.html?class={classes[0]}&activity=canva-4ano-estudio-de-slides')
    expect(page.locator('#launch-class')).to_have_value(classes[0])
    expect(page.locator('#report-class')).to_have_value(classes[0])
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#launch-btn')).to_have_text('Continuar trabalho')

    # O link escolhe uma sessão antiga, mesmo havendo outra mais recente do mesmo trabalho.
    page.goto(studio_origin + f'/teacher/class.html?session={sessions[0]}')
    page.get_by_role('button', name='Continuar trabalho', exact=True).click()
    expect(page.locator('#live-title')).to_contain_text('Trabalho de ensaio 0')
    assert page.request.get(studio_origin + f'/api/sessions/{sessions[1]}').json()['status'] == 'closed'

    page.goto(studio_origin + f'/teacher/class.html?session={sessions[2]}')
    expect(page.locator('#live-title')).to_contain_text('Trabalho de ensaio 2')
    page.goto(studio_origin + f'/teacher/class.html?class={classes[0]}&view=report')
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#report-class')).to_have_value(classes[0])
    expect(page.locator('#report-out')).to_contain_text('Exemplo')

    page.goto(studio_origin + '/teacher/class.html?session=inexistente')
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#launch-hint')).to_contain_text('não foi encontrada')
