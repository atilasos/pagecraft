"""Percurso real de aprovação em lote e atribuições na mesma aula, via Hub."""
import re

import pytest

expect = pytest.importorskip('playwright.sync_api').expect


def seed(page, origin):
    page.request.get(origin + '/api/teacher-bootstrap')
    activities = []
    for index, kind in enumerate(['match', 'pairs', 'syllables', 'gap', 'recall', 'hunt'], 1):
        response = page.request.post(origin + '/api/learning/activities', data={
            'slug': 'm28p-v3-menina-' + kind, 'title': f'Jogo {index} · menina',
            'year': 1, 'duration': 10, 'group': 'm28p-v3', 'criteria': [{'id': 'read', 'pt': 'Leio a palavra.'}],
        })
        assert response.status == 201, response.text()
        activities.append(response.json())
    other = page.request.post(origin + '/api/learning/activities', data={
        'slug': 'fraction-test', 'title': 'Metades na aula', 'year': 2, 'duration': 20,
        'criteria': [{'id': 'half', 'pt': 'Reconheço uma metade.'}],
    }).json()
    cls = page.request.post(origin + '/api/classes', data={
        'name': '2A · roteiro', 'year': 2, 'students': ['Ana', 'Bruno', 'Carla'],
    }).json()
    return activities, other, cls


def approve_word(page, origin):
    page.goto(origin + '/teacher/activities.html')
    # Procurar só um jogo não limita a seleção de todos os jogos da palavra.
    page.locator('#library-search').fill('Jogo 1')
    page.get_by_role('checkbox', name='menina (6)', exact=True).check()
    expect(page.locator('#publish-selected')).to_have_text('Aprovar e publicar selecionadas (6)')
    dialogs = []
    def approve(dialog):
        dialogs.append(dialog.message)
        dialog.accept()
    page.once('dialog', approve)
    page.locator('#publish-selected').click()
    expect(page.locator('#library-load-status')).to_have_text('6 publicadas · 0 por resolver.')
    assert len(dialogs) == 1
    expect(page.locator('#publish-selected')).to_be_disabled()
    page.locator('#library-search').fill('Metades')
    page.get_by_role('checkbox', name='Selecionar Metades na aula', exact=True).check()
    page.once('dialog', lambda dialog: dialog.accept())
    page.locator('#publish-selected').click()
    expect(page.locator('#library-load-status')).to_have_text('1 publicadas · 0 por resolver.')


def test_teacher_distributes_word_and_other_activity_and_pupil_returns_to_own_list(page, studio_origin):
    origin = studio_origin
    activities, other, cls = seed(page, origin)
    approve_word(page, origin)
    page.get_by_role('link', name='Distribuir atividades por alunos', exact=True).click()
    expect(page.locator('#lesson-form'), page.locator('#status').text_content()).not_to_have_attribute('inert', '')
    page.get_by_label('Nome do roteiro', exact=True).fill('Leitura e matemática')
    page.get_by_label('Turma', exact=True).select_option(cls['id'])
    # Dois alunos na mesma palavra com uma só ação; a Carla com outra atividade.
    page.get_by_label('Marcar Ana', exact=True).check()
    page.get_by_label('Marcar Bruno', exact=True).check()
    expect(page.locator('#marked-count')).to_have_text('2 alunos marcados')
    page.get_by_label('Palavra para os marcados', exact=True).select_option('menina')
    page.get_by_role('button', name='Dar esta palavra', exact=True).click()
    expect(page.get_by_label('Palavra de Bruno', exact=True)).to_have_value('menina')
    expect(page.locator('#plan-summary')).to_contain_text('Sem nada atribuído: Carla')
    page.get_by_role('button', name='Desmarcar', exact=True).click()
    page.get_by_label('Marcar Carla', exact=True).check()
    page.get_by_role('button', name='Escolher outras atividades…', exact=True).click()
    page.get_by_role('checkbox', name='Selecionar Metades na aula', exact=True).check()
    page.get_by_role('button', name='Atribuir ao aluno marcado', exact=True).click()
    expect(page.locator('#plan-rows')).to_contain_text('Metades na aula')
    expect(page.locator('#plan-summary')).to_contain_text('Todos os alunos têm um plano')
    page.get_by_role('button', name='Guardar roteiro da aula', exact=True).click()
    expect(page.locator('#save-status')).to_have_text('Roteiro guardado.')
    lesson = next(l for l in page.request.get(origin + '/api/learning/lessons').json() if l['title'] == 'Leitura e matemática')
    assert len(lesson['assignments']) == 2
    # A entrada comum do aluno reconhece o código do roteiro.
    pupil = page.context.browser.new_context()
    try:
        tab = pupil.new_page()
        tab.goto(origin + '/student/')
        tab.locator('#code-input').fill(lesson['code'])
        tab.locator('#code-form button').click()
        tab.get_by_role('link', name='Ana', exact=True).click()
        expect(tab.locator('#activities article')).to_have_count(6)
        expect(tab.locator('#activities')).not_to_contain_text('Metades')
        tab.get_by_role('link', name='Escolher outro nome', exact=True).click()
        tab.get_by_role('link', name='Carla', exact=True).click()
        expect(tab.locator('#activities article')).to_have_count(1)
        expect(tab.locator('#activities')).to_contain_text('Metades')
        tab.get_by_role('link', name='Começar', exact=True).click()
        expect(tab.get_by_label('Como te chamas?', exact=True)).to_have_value('Carla')
        expect(tab.get_by_label('Como te chamas?', exact=True)).to_have_attribute('readonly', '')
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        tab.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
        tab.get_by_role('button', name='Guardar e terminar', exact=True).click()
        expect(tab.locator('#done')).to_be_visible()
        tab.get_by_role('link', name='Escolher outra atividade do roteiro', exact=True).click()
        expect(tab.locator('#greeting')).to_have_text('Olá, Carla!')
        expect(tab.locator('#activities article')).to_have_count(1)
        reports = page.request.get(origin + '/api/learning/reports').json()
        report = next(r for r in reports if r.get('lesson_code') == lesson['code'])
        assert report['name'] == 'Carla' and report['group'] == cls['name']
        assert report['student_id'] == cls['students'][2]['id']
        assert report['completed_at']
    finally:
        pupil.close()
    # O professor acrescenta a palavra à Carla e encerra a entrada.
    page.get_by_label('Palavra de Carla', exact=True).select_option('menina')
    page.get_by_label('Disponível aos alunos', exact=True).uncheck()
    page.get_by_role('button', name='Guardar roteiro da aula', exact=True).click()
    expect(page.locator('#save-status')).to_have_text('Roteiro guardado.')
    updated = next(l for l in page.request.get(origin + '/api/learning/lessons').json() if l['code'] == lesson['code'])
    assert not updated['active']
    carla = next(a for a in updated['assignments'] if cls['students'][2]['id'] in a['student_ids'])
    assert carla['word'] == 'menina' and other['code'] in carla['activity_codes']
    assert len(carla['activity_codes']) == 7
    page.get_by_role('link', name='Ver registos deste roteiro', exact=True).click()
    expect(page.locator('#filter-lesson')).to_have_value(lesson['code'])
    expect(page.locator('#reports-panel')).to_be_visible()
    expect(page.locator('#reports')).to_contain_text('Carla')
    expect(page.locator('#reports')).to_contain_text('Leitura e matemática')


def test_other_roster_choice_never_renders_previous_pupils_realization(page, studio_origin):
    origin = studio_origin
    page.request.get(origin + '/api/teacher-bootstrap')
    activities, other, cls = seed(page, origin)
    page.request.post(origin + f"/api/learning/activities/{other['code']}/publish")
    ana, bruno, _ = cls['students']
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Trocar nome', 'class_id': cls['id'], 'assignments': [
            {'title': 'Todos', 'student_ids': [ana['id'], bruno['id']], 'activity_codes': [other['code']]},
        ],
    }).json()
    tab = page.context.new_page()
    try:
        tab.goto(origin + f"/{other['code']}?aula={lesson['code']}&aluno={ana['id']}")
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        first = page.request.get(origin + '/api/learning/me').json()
        tab.goto(origin + f"/{other['code']}?aula={lesson['code']}&aluno={bruno['id']}")
        expect(tab.locator('#status')).to_contain_text('outra realização desta atividade')
        expect(tab.locator('#work')).to_be_hidden()
        expect(tab.locator('#done')).to_be_hidden()
        expect(tab.locator('#start-form')).to_be_hidden()
        assert page.request.get(origin + '/api/learning/me').json()['id'] == first['id']
        tab.get_by_role('button', name='Trocar de aluno', exact=True).click()
        expect(tab).to_have_url(re.compile('/aula/' + lesson['code'] + '$'))
        tab.get_by_role('link', name='Bruno', exact=True).click()
        tab.get_by_role('link', name='Começar', exact=True).click()
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        second = page.request.get(origin + '/api/learning/me').json()
        assert second['id'] != first['id'] and second['name'] == 'Bruno'
    finally:
        tab.close()


def test_closing_roster_keeps_existing_realization_recoverable(page, studio_origin):
    origin = studio_origin
    _, activity, cls = seed(page, origin)
    page.request.post(origin + f"/api/learning/activities/{activity['code']}/publish")
    ana = cls['students'][0]
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Recuperar depois de encerrar', 'class_id': cls['id'], 'assignments': [
            {'title': 'Leitura', 'student_ids': [ana['id']], 'activity_codes': [activity['code']]},
        ],
    }).json()
    page.goto(origin + f"/{activity['code']}?aula={lesson['code']}&aluno={ana['id']}")
    page.get_by_role('button', name='Começar', exact=True).click()
    expect(page.locator('#work')).to_be_visible()
    first = page.request.get(origin + '/api/learning/me').json()
    response = page.request.put(origin + f"/api/learning/lessons/{lesson['code']}", data={
        'title': lesson['title'], 'assignments': lesson['assignments'], 'revision': lesson['revision'], 'active': False,
    })
    assert response.status == 200
    page.reload()
    expect(page.locator('#work')).to_be_visible()
    assert page.request.get(origin + '/api/learning/me').json()['id'] == first['id']
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()


def test_teacher_follows_lesson_records_missing_self_assessment_and_switches_board(page, studio_origin):
    origin = studio_origin
    activities, other, cls = seed(page, origin)
    codes = [a['code'] for a in activities] + [other['code']]
    assert page.request.post(origin + '/api/learning/activities/publish', data={'codes': codes}).status == 200
    ana, bruno, carla = cls['students']
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Acompanhar', 'class_id': cls['id'], 'offline': {carla['id']: 'Caderno'},
        'assignments': [
            {'title': 'Palavra menina', 'word': 'menina', 'student_ids': [ana['id']],
             'activity_codes': [a['code'] for a in activities]},
            {'title': 'Metades', 'student_ids': [bruno['id']], 'activity_codes': [other['code']]},
        ]}).json()
    pupil = page.context.browser.new_context()
    board = page.context.browser.new_context()
    try:
        tab = pupil.new_page()
        tab.goto(origin + f"/{other['code']}?aula={lesson['code']}&aluno={bruno['id']}")
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        screen = board.new_page()
        screen.goto(origin + '/board/')
        expect(screen.locator('#pairing-code span')).to_have_count(6)
        pairing = ''.join(screen.locator('#pairing-code span').all_inner_texts())
        assert page.request.post(origin + '/api/board/pairings/confirm', data={'code': pairing}).status == 200
        expect(screen.locator('#waiting')).to_be_visible(timeout=8000)

        page.goto(origin + f"/teacher/lesson-live.html?aula={lesson['code']}")
        rows = page.locator('#rows')
        expect(rows.get_by_role('row', name=re.compile('^Bruno'))).to_contain_text('A trabalhar')
        expect(rows.get_by_role('row', name=re.compile('^Bruno'))).to_contain_text('Sem autoavaliação em 1 atividade')
        expect(rows.get_by_role('row', name=re.compile('^Ana'))).to_contain_text('Ainda não entrou')
        expect(rows.get_by_role('row', name=re.compile('^Carla'))).to_contain_text('Caderno')
        page.get_by_role('button', name='Metades na aula · 1 aluno', exact=True).click()
        expect(page.locator('#board-now')).to_have_text('O quadro mostra: Metades na aula')
        expect(screen.locator('#session-join-code')).to_have_text(lesson['code'], timeout=8000)
        expect(screen.locator('#session-title')).to_contain_text('Metades na aula')
        page.get_by_label('Outra atividade do roteiro', exact=True).select_option(activities[0]['code'])
        page.get_by_role('button', name='Mostrar no quadro', exact=True).click()
        expect(screen.locator('#session-title')).to_contain_text(activities[0]['title'], timeout=8000)
        page.get_by_label('Observação sobre Bruno', exact=True).fill('Precisou de apoio na segunda página.')
        page.get_by_label('Observação sobre Ana', exact=True).focus()
        expect(rows.get_by_role('row', name=re.compile('^Bruno'))).to_contain_text('Guardada.')
        progress = page.request.get(origin + f"/api/learning/lessons/{lesson['code']}/progress").json()
        assert next(s for s in progress['students'] if s['id'] == bruno['id'])['note'] == 'Precisou de apoio na segunda página.'
        page.get_by_role('button', name='Tirar do quadro', exact=True).click()
        expect(page.locator('#board-now')).to_have_text('O quadro não mostra nenhuma atividade deste roteiro.')
        # O quadro volta à espera no próximo ciclo; consulta-se o mesmo pedido que o quadro faz.
        assert screen.request.get(origin + '/api/board/session').status == 204
    finally:
        pupil.close()
        board.close()


def test_board_leaves_live_session_when_teacher_shows_a_lesson_activity(page, studio_origin):
    """Sem consultas periódicas: o stream da sessão fecha e o quadro redescobre."""
    from playwright.sync_api import expect as expect_
    origin = studio_origin
    page.request.get(origin + '/api/teacher-bootstrap')
    _, other, cls = seed(page, origin)
    page.request.post(origin + '/api/learning/activities/publish', data={'codes': [other['code']]})
    live = page.request.post(origin + '/api/sessions', data={
        'class_id': cls['id'], 'activity_slug': 'fraction-test', 'activity_title': 'Sessão ao vivo'}).json()
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Roteiro e sessão', 'class_id': cls['id'], 'assignments': [
            {'title': 'Metades', 'student_ids': [cls['students'][0]['id']], 'activity_codes': [other['code']]}]}).json()
    board = page.context.browser.new_context()
    try:
        screen = board.new_page()
        challenge = screen.request.post(origin + '/api/board/pairings').json()
        assert page.request.post(origin + '/api/board/pairings/confirm', data={'code': challenge['code']}).ok
        assert screen.request.post(origin + '/api/board/pairings/complete', data={'pairing_id': challenge['pairing_id']}).ok
        screen.goto(origin + '/board/')
        expect_(screen.locator('#session-title')).to_contain_text('Sessão ao vivo')
        assert page.request.put(origin + f"/api/learning/lessons/{lesson['code']}/board",
                                data={'activity_code': other['code']}).ok
        expect_(screen.locator('#session-join-code')).to_have_text(lesson['code'], timeout=8000)
        expect_(screen.locator('#session-code-label')).to_have_text('Código do roteiro')
    finally:
        board.close()
        page.request.post(origin + f"/api/sessions/{live['id']}/close")
