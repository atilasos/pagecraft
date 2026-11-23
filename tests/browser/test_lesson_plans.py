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
    # Desmarcar o aluno não apaga a seleção; guardar com ela por atribuir é recusado.
    page.get_by_label('Marcar Carla', exact=True).uncheck()
    expect(page.locator('#picker')).to_be_visible()
    page.get_by_role('button', name='Guardar roteiro da aula', exact=True).click()
    expect(page.locator('#status')).to_contain_text('Há atividades selecionadas por atribuir.')
    # Trocar de roteiro com uma seleção pendente pede confirmação; recusar mantém tudo.
    asked = []
    def refuse(dialog):
        asked.append(dialog.message)
        dialog.dismiss()
    page.once('dialog', refuse)
    page.get_by_role('button', name='Preparar novo roteiro', exact=True).click()
    assert asked == ['Há alterações por guardar. Queres abrir outro roteiro?']
    page.get_by_label('Marcar Carla', exact=True).check()
    expect(page.get_by_role('checkbox', name='Selecionar Metades na aula', exact=True)).to_be_checked()
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
        expect(page.locator('#board-now')).to_have_text('O quadro não mostra nenhuma atividade deste roteiro.')
        expect(rows.get_by_role('row', name=re.compile('^Ana'))).to_contain_text('Ainda não entrou')
        expect(rows.get_by_role('row', name=re.compile('^Carla'))).to_contain_text('Caderno')
        # Primeiro um jogo das 28 palavras: arranca no quadro com uma realização vazia.
        page.get_by_label('Outra atividade do roteiro', exact=True).select_option(activities[0]['code'])
        page.get_by_role('button', name='Mostrar no quadro', exact=True).click()
        expect(screen.locator('#session-join-code')).to_have_text(lesson['code'], timeout=8000)
        expect(screen.locator('#session-title')).to_contain_text(activities[0]['title'])
        game = screen.frame_locator('#board')
        expect(game.locator('#initialization-status')).to_be_hidden(timeout=8000)
        expect(game.locator('#main')).to_be_visible()
        # Depois, a atividade em curso: um toque troca o quadro.
        page.get_by_role('button', name='Metades na aula · 1 aluno', exact=True).click()
        expect(page.locator('#board-now')).to_have_text('O quadro mostra: Metades na aula')
        expect(page.get_by_role('button', name='Metades na aula · 1 aluno', exact=True)).to_have_attribute('aria-pressed', 'true')
        expect(screen.locator('#session-title')).to_contain_text('Metades na aula', timeout=8000)
        page.get_by_label('Observação sobre Bruno', exact=True).fill('Precisou de apoio na segunda página.')
        page.get_by_label('Observação sobre Ana', exact=True).focus()
        expect(rows.get_by_role('row', name=re.compile('^Bruno'))).to_contain_text('Guardada.')
        # Uma observação ainda em edição entra no registo descarregado.
        page.get_by_label('Observação sobre Ana', exact=True).fill('Ainda não entrou: leu comigo.')
        with page.expect_download() as download:
            page.get_by_role('button', name='Descarregar registo (Markdown)', exact=True).click()
        record = open(download.value.path(), encoding='utf-8').read()
        assert 'Precisou de apoio na segunda página.' in record and 'Ainda não entrou: leu comigo.' in record
        assert 'Sem autoavaliação' in page.locator('#rows').inner_text() and 'Caderno' in record
        progress = page.request.get(origin + f"/api/learning/lessons/{lesson['code']}/progress").json()
        assert next(s for s in progress['students'] if s['id'] == bruno['id'])['note'] == 'Precisou de apoio na segunda página.'
        page.get_by_role('button', name='Tirar do quadro', exact=True).click()
        expect(page.locator('#board-now')).to_have_text('O quadro não mostra nenhuma atividade deste roteiro.')
        # O quadro volta à espera no próximo ciclo; consulta-se o mesmo pedido que o quadro faz.
        assert screen.request.get(origin + '/api/board/session').status == 204
        # O Bruno entrega a autoavaliação só com «Passar»: conta à parte, não como respondida.
        status = tab.evaluate('''async () => {
            const me = await (await fetch('/api/learning/me')).json();
            const answers = Object.fromEntries(me.criteria.map(c => [c.id, 'skip']));
            const response = await fetch('/api/learning/me/finish', {method: 'POST', headers: {
                'content-type': 'application/json', 'X-PageCraft-Realization': me.id},
                body: JSON.stringify({answers})});
            return response.status;
        }''')
        assert status == 200
        page.evaluate('refresh(); 0')
        bruno_row = rows.get_by_role('row', name=re.compile('^Bruno'))
        expect(bruno_row).to_contain_text('Entregue sem respostas em 1 atividade')
        expect(bruno_row).to_contain_text('autoavaliação entregue sem respostas')
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


def test_note_that_fails_to_save_blocks_the_lesson_record_download(page, studio_origin):
    origin = studio_origin
    page.request.get(origin + '/api/teacher-bootstrap')
    _, other, cls = seed(page, origin)
    page.request.post(origin + '/api/learning/activities/publish', data={'codes': [other['code']]})
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Notas que falham', 'class_id': cls['id'], 'assignments': [
            {'title': 'Metades', 'student_ids': [cls['students'][0]['id']], 'activity_codes': [other['code']]}]}).json()
    attempts, held = [], []

    def hold_first(route):
        # O primeiro pedido fica retido até depois do clique: a falha chega com a exportação à espera.
        attempts.append(route.request.post_data)
        if len(attempts) == 1:
            held.append(route)
        else:
            route.continue_()

    page.route('**/notes/**', hold_first)
    downloads = []
    page.on('download', lambda item: downloads.append(item))
    page.goto(origin + f"/teacher/lesson-live.html?aula={lesson['code']}")
    note = page.get_by_label('Observação sobre Ana', exact=True)
    note.fill('Leu as metades sozinha.')
    with page.expect_request('**/notes/**'):
        page.get_by_role('button', name='Descarregar registo (Markdown)', exact=True).click()
    for _ in range(50):
        if held:
            break
        page.wait_for_timeout(20)
    assert len(held) == 1
    held.pop().fulfill(status=500, content_type='application/json', body='{"detail": "falha simulada"}')
    expect(page.locator('#status')).to_have_text('Há uma observação por guardar. Tenta novamente antes de descarregar ou imprimir.')
    page.wait_for_timeout(500)
    assert downloads == []
    with page.expect_download() as download:
        page.get_by_role('button', name='Descarregar registo (Markdown)', exact=True).click()
    assert 'Leu as metades sozinha.' in open(download.value.path(), encoding='utf-8').read()


def test_progress_answer_started_before_a_save_does_not_restore_the_old_note(page, studio_origin):
    origin = studio_origin
    page.request.get(origin + '/api/teacher-bootstrap')
    _, other, cls = seed(page, origin)
    page.request.post(origin + '/api/learning/activities/publish', data={'codes': [other['code']]})
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Consulta atrasada', 'class_id': cls['id'], 'assignments': [
            {'title': 'Metades', 'student_ids': [cls['students'][0]['id']], 'activity_codes': [other['code']]}]}).json()
    page.goto(origin + f"/teacher/lesson-live.html?aula={lesson['code']}")
    note = page.get_by_label('Observação sobre Ana', exact=True)
    expect(note).to_be_visible()
    held = []

    def hold(route):
        # A resposta fica com o estado anterior à gravação e só chega depois dela.
        held.append((route, route.fetch()))

    page.route('**/progress', hold)
    page.evaluate('refresh(); 0')
    for _ in range(100):
        if held:
            break
        page.wait_for_timeout(20)
    assert held
    note.fill('Nota nova confirmada.')
    page.get_by_label('Observação sobre Bruno', exact=True).focus()
    expect(page.locator('#rows').get_by_role('row', name=re.compile('^Ana'))).to_contain_text('Guardada.')
    route, stale = held.pop()
    route.fulfill(response=stale)
    page.unroute('**/progress')
    page.wait_for_timeout(500)
    expect(note).to_have_value('Nota nova confirmada.')
    with page.expect_download() as download:
        page.get_by_role('button', name='Descarregar registo (Markdown)', exact=True).click()
    assert 'Nota nova confirmada.' in open(download.value.path(), encoding='utf-8').read()
