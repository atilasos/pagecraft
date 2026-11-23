"""Roteiro da aula: palavras atuais do método, alunos fora do PageCraft,
acompanhamento por aluno e atividade de roteiro no Quadro."""
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from server.app import create_app


@pytest.fixture
async def clients(tmp_path, monkeypatch):
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setenv('PAGECRAFT_ACTIVITIES_DIR', str(tmp_path / 'activities'))
    (tmp_path / 'activities').mkdir()
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.8', 1234)),
                                         base_url='http://test') as pupil:
                yield app, teacher, pupil


async def publish(app, teacher, slug, title, *, order=None, status='published'):
    folder = app.state.config.activities_dir / slug
    folder.mkdir(parents=True)
    (folder / 'index.html').write_text(f'<html>{title}</html>')
    meta = {'slug': slug, 'title': title, 'status': status}
    if order is not None:
        meta['order'] = order
    (folder / 'meta.json').write_text(json.dumps(meta))
    response = await teacher.post('/api/learning/activities', json={
        'slug': slug, 'title': title, 'year': 1, 'duration': 5,
        'criteria': [{'id': 'read', 'pt': 'Leio a palavra.'}]})
    assert response.status_code == 201, response.text
    code = response.json()['code']
    assert (await teacher.post(f'/api/learning/activities/{code}/publish')).status_code == 200
    return code


async def setup(app, teacher):
    codes = {
        'old': await publish(app, teacher, 'm28p-v3-casa-match', 'Palavra igual · casa', order=8, status='archived'),
        'sentence': await publish(app, teacher, 'm28p-ciclo-casa-sentence', 'Montar frases · casa', order=8),
        'discover': await publish(app, teacher, 'm28p-ciclo-casa-discover', 'Descobrir palavras · casa', order=8),
        'uva': await publish(app, teacher, 'm28p-ciclo-uva-discover', 'Descobrir palavras · uva', order=3),
        'math': await publish(app, teacher, 'dobro-ate-10', 'Dobro até 10'),
    }
    cls = (await teacher.post('/api/classes', json={'name': '1A', 'year': 1,
                                                     'students': ['Ana', 'Bruno', 'Carla', 'Duarte']})).json()
    return codes, cls, [s['id'] for s in cls['students']]


async def test_word_metadata_marks_cycle_games_and_retired_collection(clients):
    app, teacher, _ = clients
    codes, _, _ = await setup(app, teacher)
    items = {a['code']: a for a in (await teacher.get('/api/learning/activities')).json()}
    assert items[codes['old']]['retired'] is True
    assert items[codes['sentence']]['retired'] is False
    assert items[codes['sentence']]['m28p'] == {'word': 'casa', 'label': 'casa', 'kind': 'sentence',
                                                'kind_order': 9, 'order': 8}
    assert items[codes['uva']]['m28p']['order'] == 3
    assert 'm28p' not in items[codes['math']]


async def test_offline_pupils_are_recorded_hidden_from_entry_and_never_assigned(clients):
    app, teacher, pupil = clients
    codes, cls, (ana, bruno, carla, duarte) = await setup(app, teacher)
    lesson = {'title': 'Terça', 'class_id': cls['id'], 'offline': {duarte: 'Caderno com a professora'},
              'assignments': [{'title': 'Palavra casa', 'word': 'casa', 'student_ids': [ana],
                               'activity_codes': [codes['discover'], codes['sentence']]}]}
    created = await teacher.post('/api/learning/lessons', json=lesson)
    assert created.status_code == 201, created.text
    code = created.json()['code']
    entry = (await pupil.get(f'/api/learning/lessons/{code}/entry')).json()
    assert duarte not in {s['id'] for s in entry['students']}
    work = (await pupil.get(f'/api/learning/lessons/{code}/students/{ana}')).json()
    # Os jogos de uma palavra chegam ao aluno pela ordem do ciclo.
    assert [a['code'] for a in work['activities']] == [codes['discover'], codes['sentence']]
    clash = dict(lesson, offline={ana: ''})
    assert (await teacher.post('/api/learning/lessons', json=clash)).status_code == 422
    stranger = dict(lesson, offline={'abcdef12': ''})
    assert (await teacher.post('/api/learning/lessons', json=stranger)).status_code == 422
    only_offline = {'title': 'Só caderno', 'class_id': cls['id'], 'assignments': [], 'offline': {bruno: ''}}
    assert (await teacher.post('/api/learning/lessons', json=only_offline)).status_code == 201
    empty = {'title': 'Vazio', 'class_id': cls['id'], 'assignments': []}
    assert (await teacher.post('/api/learning/lessons', json=empty)).status_code == 422


async def test_progress_reports_each_pupil_including_missing_self_assessment(clients):
    app, teacher, pupil = clients
    codes, cls, (ana, bruno, carla, duarte) = await setup(app, teacher)
    lesson = (await teacher.post('/api/learning/lessons', json={
        'title': 'Terça', 'class_id': cls['id'], 'offline': {duarte: 'Leitura com a professora'},
        'assignments': [
            {'title': 'Palavra casa', 'word': 'casa', 'student_ids': [ana, bruno],
             'activity_codes': [codes['discover'], codes['sentence']]},
        ]})).json()
    code = lesson['code']
    # Ana termina com autoavaliação; Bruno começa e fica sem a preencher.
    started = await pupil.post(f"/api/learning/activities/{codes['discover']}/start", json={
        'name': 'x', 'assignment': {'lesson_code': code, 'student_id': ana}})
    assert started.status_code == 201, started.text
    pupil.headers['X-PageCraft-Realization'] = started.json()['id']
    events = [{'id': 'a1', 'type': 'attempt', 'unitId': 'u1', 'payload': {'correct': False}},
              {'id': 'a2', 'type': 'attempt', 'unitId': 'u1', 'payload': {'correct': True}},
              {'id': 'h1', 'type': 'help_needed', 'unitId': 'u1', 'payload': {}}]
    assert (await pupil.post('/api/learning/me/events', json={'events': events})).status_code == 200
    finished = await pupil.post('/api/learning/me/finish', json={'answers': {'read': 'help'}, 'strategy': 'Li devagar'})
    assert finished.status_code == 200, finished.text
    pupil.cookies.clear()
    started = await pupil.post(f"/api/learning/activities/{codes['sentence']}/start", json={
        'name': 'x', 'assignment': {'lesson_code': code, 'student_id': bruno}})
    assert started.status_code == 201

    assert (await pupil.get(f'/api/learning/lessons/{code}/progress')).status_code in (401, 403)
    progress = (await teacher.get(f'/api/learning/lessons/{code}/progress')).json()
    rows = {s['display_name']: s for s in progress['students']}
    assert rows['Ana']['state'] == 'finished'
    [done] = rows['Ana']['realizations']
    assert (done['correct'], done['incorrect'], done['help'], done['help_pending']) == (1, 1, 1, True)
    assert done['assessment'] == {'alone': 0, 'help': 1, 'practising': 0, 'skip': 0}
    assert rows['Ana']['words'] == ['casa']
    assert rows['Bruno']['state'] == 'working'
    assert rows['Bruno']['current'] == codes['sentence']
    assert rows['Bruno']['realizations'][0]['assessment'] is None
    assert rows['Carla']['state'] == 'unassigned'
    assert rows['Duarte']['state'] == 'offline'
    assert rows['Duarte']['offline'] == 'Leitura com a professora'

    later = datetime.now(timezone.utc) + timedelta(minutes=4)
    idle = await app.state.lesson_plans.progress(code, now=later)
    assert {s['display_name']: s['state'] for s in idle['students']}['Bruno'] == 'idle'

    assert (await teacher.put(f'/api/learning/lessons/{code}/notes/{bruno}', json={'text': 'Leu a frase comigo.'})).status_code == 204
    again = (await teacher.get(f'/api/learning/lessons/{code}/progress')).json()
    assert {s['display_name']: s['note'] for s in again['students']}['Bruno'] == 'Leu a frase comigo.'
    # A nota não altera a revisão usada para detetar edições concorrentes.
    assert (await app.state.lesson_plans.get(code))['revision'] == lesson['revision']


async def test_board_shows_chosen_lesson_activity_until_a_newer_live_session(clients):
    app, teacher, _ = clients
    codes, cls, (ana, *_rest) = await setup(app, teacher)
    lesson = (await teacher.post('/api/learning/lessons', json={
        'title': 'Terça', 'class_id': cls['id'], 'assignments': [
            {'title': 'Matemática', 'student_ids': [ana], 'activity_codes': [codes['math']]}]})).json()
    code = lesson['code']
    board = app.state.board_pairings
    challenge = await board.create_challenge()
    assert (await teacher.post('/api/board/pairings/confirm', json={'code': challenge['code']})).status_code == 200
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.50', 1)),
                                 base_url='http://test') as screen:
        paired = await screen.post('/api/board/pairings/complete', json={'pairing_id': challenge['pairing_id']})
        assert paired.status_code == 200, paired.text
        assert (await screen.get('/api/board/session')).status_code == 204
        assert (await teacher.put(f'/api/learning/lessons/{code}/board', json={'activity_code': codes['uva']})).status_code == 422
        chosen = await teacher.put(f'/api/learning/lessons/{code}/board', json={'activity_code': codes['math']})
        assert chosen.status_code == 200, chosen.text
        shown = (await screen.get('/api/board/session')).json()
        assert shown['kind'] == 'lesson'
        assert (shown['lesson_code'], shown['activity_title']) == (code, 'Dobro até 10')
        assert 'students' not in shown
        content = await screen.get('/api/board/lesson-content')
        assert content.status_code == 200 and 'Dobro até 10' in content.text
        live = await teacher.post('/api/sessions', json={'class_id': cls['id'], 'activity_slug': 'dobro-ate-10'})
        assert live.status_code in (200, 201), live.text
        assert (await screen.get('/api/board/session')).json().get('kind') != 'lesson'
        await teacher.post(f"/api/sessions/{live.json()['id']}/close")
        await teacher.put(f'/api/learning/lessons/{code}/board', json={'activity_code': codes['math']})
        assert (await screen.get('/api/board/session')).json()['kind'] == 'lesson'
        assert (await teacher.put(f'/api/learning/lessons/{code}/board', json={'activity_code': None})).status_code == 200
        assert (await screen.get('/api/board/session')).status_code == 204
        assert (await screen.get('/api/board/lesson-content')).status_code == 404
