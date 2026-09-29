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
