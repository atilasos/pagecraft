import httpx


def test_teacher_receives_attempt_and_board_is_only_demonstration(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        classroom = teacher.post('/api/classes', json={'name':'Ensaio Frações', 'year':2, 'students':['Aluno de teste']}).json()
        response = teacher.post('/api/sessions', json={'class_id':classroom['id'], 'activity_slug':'fraction-test', 'activity_title':'Frações em revisão'})
        response.raise_for_status()
        session = response.json()
        student_id = next(iter(session['roster']))
        page.goto(studio_origin + '/student/')
        page.locator('#code-input').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_role('button', name='Aluno de teste', exact=True).click()
        lesson = page.frame_locator('#activity-frame')
        lesson.get_by_role('button', name='Cortar à esquerda', exact=True).click()
        with page.expect_response(lambda r: r.url.endswith('/events') and r.request.method == 'POST') as saved:
            lesson.get_by_role('button', name='Sim', exact=True).click()
        assert saved.value.ok
        # Poll the teacher's public API; transport flushes the queue periodically.
        import time
        for _ in range(30):
            history = teacher.get(f"/api/sessions/{session['id']}/students/{student_id}/history").json()['events']
            attempts = [e for e in history if e['type'] == 'attempt']
            if attempts:
                break
            time.sleep(.2)
        assert len(attempts) == 1
        assert attempts[0]['payload']['correct'] is False
        assert attempts[0]['unit_id'] == 'u1'
        with page.expect_response(lambda r: r.url.endswith('/events') and r.request.method == 'POST', timeout=6000):
            lesson.get_by_label('Nível de diferenciação').select_option('challenge')
        history = teacher.get(f"/api/sessions/{session['id']}/students/{student_id}/history").json()['events']
        changes = [e for e in history if e['type'] == 'level_changed']
        assert [e['payload']['level'] for e in changes] == ['challenge']
        # Switch to the actual registered draft, which has no public activity file.
        import json
        from pathlib import Path
        registration = json.loads((Path(__file__).resolve().parents[2] / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
        draft = teacher.post('/api/learning/activities', json=registration)
        draft.raise_for_status()
        teacher.post(f"/api/sessions/{session['id']}/close").raise_for_status()
        draft_session = teacher.post('/api/sessions', json={'class_id':classroom['id'], 'activity_slug':registration['slug'], 'activity_title':registration['title']})
        draft_session.raise_for_status()
        assert teacher.get('/activities/' + registration['slug'] + '/').status_code == 404
        # Pair this browser to the same isolated class and exercise the real board host.
        challenge = page.request.post(studio_origin + '/api/board/pairings').json()
        teacher.post('/api/board/pairings/confirm', json={'code':challenge['code']}).raise_for_status()
        completed = page.request.post(studio_origin + '/api/board/pairings/complete', data={'pairing_id':challenge['pairing_id']})
        assert completed.ok
        page.goto(studio_origin + '/board/')
        board = page.frame_locator('#board')
        expect(board.get_by_text('Demonstração · As respostas não ficam registadas.')).to_be_visible()
        board.get_by_role('button', name='2. Comparar', exact=True).click()
        board.get_by_role('button', name='Partilha B', exact=True).click()
        board.get_by_role('button', name='3. Rever', exact=True).click()
        history = teacher.get(f"/api/sessions/{session['id']}/students/{student_id}/history").json()['events']
        assert len([e for e in history if e['type'] == 'attempt']) == 1
        teacher.post(f"/api/sessions/{draft_session.json()['id']}/close").raise_for_status()


def test_reopening_realization_restores_work_without_inventing_attempts(page, studio_origin):
    import json
    from pathlib import Path
    from playwright.sync_api import expect
    registration = json.loads((Path(__file__).resolve().parents[2] / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    page.request.get(studio_origin + '/api/teacher-bootstrap')
    draft = page.request.post(studio_origin + '/api/learning/activities', data=registration).json()
    page.goto(studio_origin + '/' + draft['code'])
    page.get_by_label('Como te chamas?').fill('Revisão de retoma')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    lesson.get_by_role('button', name='Cortar ao meio', exact=True).click()
    lesson.get_by_role('button', name='Sim', exact=True).click()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    lesson.get_by_role('button', name='Partilha B', exact=True).click()
    lesson.get_by_role('button', name='1. Partilhar', exact=True).click()
    lesson.get_by_role('button', name='Cortar à direita', exact=True).click()
    import time
    for _ in range(30):
        events = page.request.get(studio_origin + '/api/learning/me').json()['events']
        snapshots = [event for event in events if event['type'] == 'activity_state']
        if snapshots and snapshots[-1]['payload']['state']['cut'] == .75 and snapshots[-1]['payload']['state']['answer'] is None:
            break
        time.sleep(.1)
    else:
        raise AssertionError('The last unanswered cut was not saved')
    assert len([event for event in events if event['type'] == 'attempt']) == 2
    page.reload()
    expect(lesson.get_by_role('button', name='Cortar à direita', exact=True)).to_have_attribute('aria-pressed','true')
    assert lesson.get_by_role('button', name='Seguinte', exact=True).is_disabled()
    lesson.get_by_role('button', name='Não', exact=True).click()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    expect(lesson.get_by_role('button', name='Partilha B', exact=True)).to_have_attribute('aria-pressed','true')
    assert page.request.get(studio_origin + '/api/learning/reports').json() == []


def test_pending_level_change_survives_reload_before_sync(page, studio_origin):
    import json
    from pathlib import Path
    from playwright.sync_api import expect
    registration = json.loads((Path(__file__).resolve().parents[2] / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    page.request.get(studio_origin + '/api/teacher-bootstrap')
    draft = page.request.post(studio_origin + '/api/learning/activities', data=registration).json()
    # Each check owns a fresh realization, even when another preview exists.
    page.request.post(studio_origin + '/api/learning/me/leave')
    page.goto(studio_origin + '/' + draft['code'])
    page.get_by_label('Como te chamas?').fill('Retoma com rede em falta')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    page.route('**/api/learning/me/events', lambda route: route.fulfill(status=503, json={'detail':'Ensaio: gravação temporariamente indisponível'}))
    lesson.get_by_role('button', name='Cortar ao meio', exact=True).click()
    lesson.get_by_role('button', name='Sim', exact=True).click()
    lesson.get_by_role('button', name='Seguinte', exact=True).click()
    lesson.get_by_label('Nível de diferenciação').select_option('challenge')
    lesson.get_by_role('button', name='Cortar à direita', exact=True).click()
    with page.expect_response(lambda r: r.url.endswith('/api/learning/me/events') and r.status == 503):
        lesson.get_by_role('button', name='As partes têm tamanhos diferentes.', exact=True).click()
    page.on('dialog', lambda dialog: dialog.accept())
    page.reload()
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    expect(lesson.get_by_role('button', name='As partes têm tamanhos diferentes.', exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(lesson.get_by_role('button', name='Seguinte', exact=True)).to_be_enabled()
    page.unroute('**/api/learning/me/events')
    page.evaluate("dispatchEvent(new Event('online'))")
