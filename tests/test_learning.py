import asyncio
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from server.app import create_app
from server.access import TEACHER_COOKIE_NAME


@pytest.fixture
async def learning_clients(tmp_path, monkeypatch):
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setenv('PAGECRAFT_ACTIVITIES_DIR', str(tmp_path / 'activities'))
    (tmp_path / 'activities' / 'test-lesson').mkdir(parents=True)
    (tmp_path / 'activities' / 'test-lesson' / 'index.html').write_text('<html>Lesson</html>')
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.8', 1234)), base_url='http://test') as pupil:
                yield app, teacher, pupil


async def register(teacher, published=True):
    data = {'slug': 'test-lesson', 'title': 'Teste', 'year': 4, 'duration': 45,
            'languages': ['pt', 'en'], 'criteria': [{'id': 'readable', 'pt': 'Consigo ler', 'en': 'I can read'}]}
    response = await teacher.post('/api/learning/activities', json=data)
    assert response.status_code == 201, response.text
    activity = response.json()
    if published:
        response = await teacher.post(f"/api/learning/activities/{activity['code']}/publish")
        assert response.status_code == 200, response.text
    return activity, data


async def start(pupil, code, name='Ana'):
    response = await pupil.post(f'/api/learning/activities/{code}/start', json={'name': name, 'language': 'en'})
    assert response.status_code == 201, response.text
    attempt = response.json()
    # This client now represents the tab that started this realization.
    pupil.headers['X-PageCraft-Realization'] = attempt['id']
    return attempt


async def test_draft_is_private_registration_idempotent_and_code_survives_restart(learning_clients):
    app, teacher, pupil = learning_clients
    activity, data = await register(teacher, published=False)
    code = activity['code']
    assert len(code) == 6
    assert (await teacher.post('/api/learning/activities', json=data)).json()['code'] == code
    for path in [f'/{code}', f'/api/learning/activities/{code}', f'/api/learning/activities/{code}/content']:
        assert (await pupil.get(path)).status_code == 404
    assert (await pupil.post(f'/api/learning/activities/{code}/start', json={'name': 'Ana'})).status_code == 404
    from server.learning import Learning
    reloaded = Learning(app.state.storage, app.state.config)
    assert (await reloaded.activity(code))['slug'] == 'test-lesson'


async def test_retired_draft_preserves_realizations_and_cannot_be_published(learning_clients):
    app, teacher, pupil = learning_clients
    activity, data = await register(teacher, published=False)
    code = activity['code']
    started = await teacher.post(f'/api/learning/activities/{code}/start', json={'name': 'Revisão'})
    assert started.status_code == 201
    assert (await pupil.post(f'/api/learning/activities/{code}/archive')).status_code in (401, 403)
    first = await teacher.post(f'/api/learning/activities/{code}/archive')
    assert first.status_code == 200
    again = await teacher.post(f'/api/learning/activities/{code}/archive')
    assert again.json()['archived_at'] == first.json()['archived_at']
    assert (await teacher.get('/api/learning/activities')).json() == []
    assert (await teacher.get('/api/learning/activities?include_archived=true')).json()[0]['code'] == code
    assert (await teacher.post(f'/api/learning/activities/{code}/publish')).status_code == 409
    assert (await teacher.post(f'/api/learning/activities/{code}/start', json={'name': 'Novo ensaio'})).status_code == 409
    # Reexecutar o registo não reativa inadvertidamente o rascunho antigo.
    assert (await teacher.post('/api/learning/activities', json=data)).json()['archived_at']
    preserved = await app.state.learning.attempt(started.json()['id'])
    assert preserved['name'] == 'Revisão'
    assert preserved['code'] == code
    assert app.state.learning.content_path(await app.state.learning.activity(code)).is_file()


async def test_retirement_does_not_unpublish_existing_lessons(learning_clients):
    _, teacher, _ = learning_clients
    activity, _ = await register(teacher)
    assert (await teacher.post(f"/api/learning/activities/{activity['code']}/archive")).status_code == 409
    assert len((await teacher.get('/api/learning/activities')).json()) == 1


async def test_bulk_publication_is_teacher_only_retryable_and_reports_each_failure(learning_clients):
    app, teacher, pupil = learning_clients
    activity, data = await register(teacher, published=False)
    retired_dir = app.state.config.activities_dir / 'retired-lesson'
    retired_dir.mkdir()
    (retired_dir / 'index.html').write_text('<html>Retired</html>')
    retired = (await teacher.post('/api/learning/activities', json={**data, 'slug': 'retired-lesson'})).json()
    await teacher.post(f"/api/learning/activities/{retired['code']}/archive")
    batch = {'codes': [activity['code'].lower(), retired['code'], activity['code'], 'ZZZZZZ']}
    assert (await pupil.post('/api/learning/activities/publish', json=batch)).status_code in (401, 403)
    assert (await teacher.post('/api/learning/activities/publish', json={'codes': []})).status_code == 422
    result = await teacher.post('/api/learning/activities/publish', json=batch)
    assert result.status_code == 200
    assert [a['code'] for a in result.json()['published']] == [activity['code']]
    assert {e['code'] for e in result.json()['errors']} == {retired['code'], 'ZZZZZZ'}
    repeated = (await teacher.post('/api/learning/activities/publish', json=batch)).json()
    assert repeated['published'][0]['published_at'] == result.json()['published'][0]['published_at']
    assert (await pupil.get('/' + activity['code'])).status_code == 200
    assert not (await app.state.learning.activity(retired['code']))['published']


async def lesson_setup(app, teacher):
    first, data = await register(teacher)
    directory = app.state.config.activities_dir / 'other-lesson'
    directory.mkdir()
    (directory / 'index.html').write_text('<html>Other lesson</html>')
    second = (await teacher.post('/api/learning/activities', json={**data, 'slug': 'other-lesson'})).json()
    await teacher.post(f"/api/learning/activities/{second['code']}/publish")
    cls = (await teacher.post('/api/classes', json={'name': '2A', 'year': 2, 'students': ['Ana', 'Bruno', 'Carla']})).json()
    ana, bruno, carla = [s['id'] for s in cls['students']]
    data = dict(title='A nossa aula', class_id=cls['id'], assignments=[
        dict(title='Leitura', student_ids=[ana, bruno], activity_codes=[first['code'], second['code']]),
        dict(title='Outro trabalho', student_ids=[carla, bruno], activity_codes=[second['code']]),
    ])
    response = await teacher.post('/api/learning/lessons', json=data)
    assert response.status_code == 201, response.text
    return response.json(), first, second


async def test_lesson_assigns_several_activities_to_different_students_without_duplicates(learning_clients):
    app, teacher, pupil = learning_clients
    lesson, first, second = await lesson_setup(app, teacher)
    code = lesson['code']
    assert len(code) == 7
    entry = (await pupil.get(f'/api/learning/lessons/{code}/entry')).json()
    assert 'assignments' not in entry
    assert 'revision' not in entry
    assert entry['class_name'] == '2A'
    for student, expected in zip(lesson['students'], [[first['code'], second['code']], [first['code'], second['code']], [second['code']]]):
        result = await pupil.get(f"/api/learning/lessons/{code}/students/{student['id']}")
        assert result.status_code == 200
        assert [a['code'] for a in result.json()['activities']] == expected
        assert 'students' not in result.json()
    assert (await pupil.get('/api/learning/lessons')).status_code in (401, 403)
    assert (await pupil.put(f'/api/learning/lessons/{code}', json=lesson)).status_code in (401, 403)
    from server.lesson_plans import LessonPlans
    reloaded = LessonPlans(app.state.storage, app.state.learning, app.state.classroom)
    assert (await reloaded.get(code.lower()))['assignments'] == lesson['assignments']


async def test_assigned_realization_uses_roster_and_denies_unassigned_activity(learning_clients):
    app, teacher, pupil = learning_clients
    lesson, first, second = await lesson_setup(app, teacher)
    carla = lesson['students'][2]
    values = dict(name='Nome enviado pelo browser', group='Outra turma', mode='home', assignment={
        'lesson_code': lesson['code'], 'student_id': carla['id']})
    assert (await pupil.post(f"/api/learning/activities/{first['code']}/start", json=values)).status_code == 403
    response = await pupil.post(f"/api/learning/activities/{second['code']}/start", json=values)
    assert response.status_code == 201
    attempt = response.json()
    assert attempt['name'] == 'Carla' and attempt['group'] == '2A' and attempt['mode'] == 'classroom'
    assert attempt['lesson_code'] == lesson['code'] and attempt['student_id'] == carla['id']
    assert attempt['class_id'] == lesson['class_id']
    pupil.headers['X-PageCraft-Realization'] = attempt['id']
    # Escolher o mesmo nome noutro browser não oferece a credencial desta realização.
    pupil.cookies.clear()
    await pupil.get(f"/api/learning/lessons/{lesson['code']}/students/{carla['id']}")
    assert (await pupil.get('/api/learning/me')).status_code == 401
    assert (await teacher.get('/api/learning/reports')).json()[0]['id'] == attempt['id']


async def test_lesson_updates_keep_roster_detect_conflicts_and_close_only_new_entry(learning_clients):
    app, teacher, pupil = learning_clients
    lesson, first, second = await lesson_setup(app, teacher)
    ana = lesson['students'][0]
    values = dict(name='Ana', assignment={'lesson_code': lesson['code'], 'student_id': ana['id']})
    started = await pupil.post(f"/api/learning/activities/{first['code']}/start", json=values)
    pupil.headers['X-PageCraft-Realization'] = started.json()['id']
    # Alterar a turma não reatribui trabalho guardado a outros alunos.
    await app.state.classroom.update_class_students(lesson['class_id'], ['Outro nome'])
    update = {k: lesson[k] for k in ('title', 'assignments', 'revision')}
    update['active'] = False
    closed = await teacher.put(f"/api/learning/lessons/{lesson['code']}", json=update)
    assert closed.status_code == 200
    assert closed.json()['students'] == lesson['students']
    assert (await teacher.put(f"/api/learning/lessons/{lesson['code']}", json=update)).status_code == 409
    assert (await pupil.get(f"/api/learning/lessons/{lesson['code']}/entry")).status_code == 409
    assert (await pupil.post(f"/api/learning/activities/{first['code']}/start", json=values)).status_code == 409
    assert (await pupil.post('/api/learning/me/events', json={'events': [{'id': 'saved', 'type': 'discovery'}]})).status_code == 200
    assert (await pupil.post('/api/learning/me/finish', json={'answers': {}})).status_code == 200
    update.update(active=True, revision=closed.json()['revision'])
    assert (await teacher.put(f"/api/learning/lessons/{lesson['code']}", json=update)).status_code == 200
    assert (await pupil.get(f"/api/learning/lessons/{lesson['code']}/entry")).status_code == 200


async def test_lesson_rejects_drafts_unknown_students_and_empty_assignments(learning_clients):
    app, teacher, _ = learning_clients
    activity, _ = await register(teacher, published=False)
    cls = (await teacher.post('/api/classes', json={'name': '2A', 'year': 2, 'students': ['Ana']})).json()
    data = dict(title='Aula', class_id=cls['id'], assignments=[dict(title='Leitura', student_ids=[cls['students'][0]['id']], activity_codes=[activity['code']])])
    assert (await teacher.post('/api/learning/lessons', json=data)).status_code == 422
    await teacher.post(f"/api/learning/activities/{activity['code']}/publish")
    data['assignments'][0]['student_ids'] = ['ffffffff']
    assert (await teacher.post('/api/learning/lessons', json=data)).status_code == 422
    data['assignments'][0]['student_ids'] = []
    assert (await teacher.post('/api/learning/lessons', json=data)).status_code == 422
    data['assignments'] = []
    assert (await teacher.post('/api/learning/lessons', json=data)).status_code == 422


async def test_identity_is_scoped_to_realization_not_typed_name(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    first = await start(pupil, activity['code'])
    assert 'credential_hash' not in first
    assert (await pupil.get('/api/learning/me')).json()['id'] == first['id']
    for path in ['/api/learning/reports', '/api/learning/activities', '/api/meta', f"/api/learning/reports/{first['id']}/download"]:
        assert (await pupil.get(path)).status_code in (401, 403)
    await pupil.post('/api/learning/me/leave')
    assert (await pupil.get('/api/learning/me')).status_code == 401
    second = await start(pupil, activity['code'])
    assert second['id'] != first['id']
    assert (await pupil.get('/api/learning/me')).json()['id'] == second['id']
    reports = (await teacher.get('/api/learning/reports')).json()
    assert len(reports) == 2
    assert all(r['name'] == 'Ana' for r in reports)


async def test_events_retry_finish_and_teacher_interpretation_remain_distinct(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    event = {'id': 'a1', 'type': 'attempt', 'unitId': 'u1', 'payload': {'correct': False}}
    replies = await asyncio.gather(*[pupil.post('/api/learning/me/events', json={'events': [event]}) for _ in range(3)])
    assert sum(r.json()['accepted'] for r in replies) == 1
    assert (await pupil.post('/api/learning/me/events', json={'events': [dict(event, type='teacher_highlight')]})).status_code == 422
    assert (await pupil.post('/api/learning/me/finish', json={'answers': {'unknown': 'alone'}})).status_code == 422
    assessment = {'answers': {'readable': 'alone'}, 'strategy': 'Li em voz alta', 'next_step': 'Rever com colega', 'language': 'en'}
    result = (await pupil.post('/api/learning/me/finish', json=assessment)).json()
    repeated = (await pupil.post('/api/learning/me/finish', json=assessment)).json()
    assert result['completed_at'] == repeated['completed_at']
    assert result['events'][0]['payload']['correct'] is False
    assert result['assessment']['answers']['readable'] == 'alone'
    assert (await pupil.post('/api/learning/me/events', json={'events': [dict(event, id='a2')]})).status_code == 409
    await teacher.patch(f"/api/learning/reports/{attempt['id']}", json={'name': 'Ana Silva', 'group': '4A', 'teacher_note': 'Trabalhar contraste.'})
    report = await teacher.get(f"/api/learning/reports/{attempt['id']}/download")
    assert 'Ana Silva' in report.text and 'Li em voz alta' in report.text and 'Trabalhar contraste.' in report.text
    assert 'credential_hash' not in report.text


async def test_old_teacher_pairing_is_retired(learning_clients):
    app, teacher, pupil = learning_clients
    assert (await teacher.post('/api/teacher-pairing')).status_code == 410
    assert (await pupil.post('/api/teacher-login', json={'code': 'OLD-CODE'})).status_code == 410
    assert (await pupil.get('/api/learning/reports')).status_code == 401


async def test_validation_preview_exclusion_expired_cookie(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher, published=False)
    attempt = await start(teacher, activity['code'])
    assert attempt['preview'] is True
    assert (await teacher.get('/api/learning/reports')).json() == []
    assert (await teacher.post('/api/learning/activities', json={'slug': '../x'})).status_code == 422
    assert (await teacher.post(f"/api/learning/activities/{activity['code']}/start", json={'name': '  '})).status_code == 422
    path = app.state.storage.path('learning', 'realizations', f"{attempt['id']}.json")
    stored = await app.state.storage.read_json(path)
    stored['expires_at'] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await app.state.storage.write_json(path, stored)
    assert (await teacher.get('/api/learning/me')).status_code == 401


async def test_whole_class_can_enter_from_same_school_ip_and_cross_origin_is_rejected(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    for n in range(30):
        await start(pupil, activity['code'], name=f'Aluno {n}')
    response = await teacher.post('/api/teacher-pairing', headers={'Origin': 'https://unrelated.example'})
    assert response.status_code == 403


async def test_teacher_notes_are_private_and_preferences_survive_reload(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    await pupil.post('/api/learning/me/events', json={'events': [
        {'id': 'lang', 'type': 'language_changed', 'payload': {'language': 'en'}},
        {'id': 'level', 'type': 'level_changed', 'payload': {'level': 'challenge'}},
    ]})
    await teacher.patch(f"/api/learning/reports/{attempt['id']}", json={
        'name': 'Ana', 'teacher_note': 'Observação privada', 'group': '4A'})
    current = (await pupil.get('/api/learning/me')).json()
    assert current['language'] == 'en' and current['level'] == 'challenge'
    assert 'teacher_note' not in current
    report = (await teacher.get('/api/learning/reports')).json()[0]
    assert report['teacher_note'] == 'Observação privada'
    assert report['evidence'][1]['text'] == ['Apoio: Mais desafios']


async def test_saved_activity_state_restores_without_becoming_evidence(learning_clients):
    _, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    await start(pupil, activity['code'])
    checkpoint = {'id':'state-1', 'type':'activity_state', 'unitId':'u1',
                  'payload':{'activity':'fraction-test', 'version':1, 'state':{'answer':None}}}
    attempt = {'id':'answer-1', 'type':'attempt', 'unitId':'u1', 'payload':{'correct':False}}
    response = await pupil.post('/api/learning/me/events', json={'events':[checkpoint, attempt]})
    assert response.status_code == 200
    assert response.json()['accepted'] == 2
    restored = (await pupil.get('/api/learning/me')).json()['events']
    assert [event['type'] for event in restored] == ['activity_state', 'attempt']
    report = (await teacher.get('/api/learning/reports')).json()[0]
    assert [event['type'] for event in report['events']] == ['attempt']
    assert [event['type'] for event in report['evidence']] == ['attempt']


@pytest.mark.parametrize('with_attempt', [False, True])
async def test_download_keeps_checkpoints_out_of_evidence(learning_clients, with_attempt):
    _, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    realization = await start(pupil, activity['code'])
    checkpoint = {'id': 'state-1', 'type': 'activity_state', 'unitId': 'u1',
                  'payload': {'activity': 'restore-only-marker', 'version': 1,
                              'state': {'answer': 'draft-answer-marker'}}}
    events = [checkpoint]
    if with_attempt:
        events.append({'id': 'answer-1', 'type': 'attempt', 'unitId': 'u1',
                       'payload': {'correct': False, 'reason': 'Comparei as partes.'}})
    events.append({**checkpoint, 'id': 'state-2'})
    saved = await pupil.post('/api/learning/me/events', json={'events': events})
    assert saved.status_code == 200
    assert saved.json()['accepted'] == len(events)
    finished = await pupil.post('/api/learning/me/finish', json={
        'answers': {'readable': 'help'}, 'strategy': 'Li com o meu colega.',
        'next_step': 'Voltar a comparar.'})
    assert finished.status_code == 200
    annotated = await teacher.patch(f"/api/learning/reports/{realization['id']}", json={
        'name': 'Ana', 'group': '4A', 'teacher_note': 'Retomar a comparação com material.'})
    assert annotated.status_code == 200

    report = (await teacher.get('/api/learning/reports')).json()[0]
    download = await teacher.get(f"/api/learning/reports/{realization['id']}/download")
    assert download.status_code == 200
    evidence = download.text.split('## Evidências no PageCraft', 1)[1].split('## Autoavaliação do aluno', 1)[0]
    assert 'restore-only-marker' not in download.text
    assert 'draft-answer-marker' not in download.text
    if with_attempt:
        assert [event['type'] for event in report['evidence']] == ['attempt']
        assert 'Resposta esperada: Não' in evidence
        assert 'Justificação: Comparei as partes.' in evidence
    else:
        assert report['evidence'] == []
        assert evidence.strip() == ''
    assert 'Consigo ler: Consegui com ajuda' in download.text
    assert 'Estratégia: Li com o meu colega.' in download.text
    assert 'Próximo passo proposto pelo aluno: Voltar a comparar.' in download.text
    assert 'Retomar a comparação com material.' in download.text
    restored = (await pupil.get('/api/learning/me')).json()['events']
    assert [event['type'] for event in restored] == [event['type'] for event in events]


async def test_support_summary_can_be_limited_to_one_lesson(learning_clients):
    app, teacher, pupil = learning_clients
    lesson, first, second = await lesson_setup(app, teacher)
    carla = lesson['students'][2]
    hint = {'events': [{'id': 'hint', 'type': 'hint_presented', 'unitId': 'u1',
                        'payload': {'hint_id': 'h', 'text': 'Conta a partir da porta.'}}]}
    assigned = await pupil.post(f"/api/learning/activities/{second['code']}/start", json=dict(
        name='Carla', assignment={'lesson_code': lesson['code'], 'student_id': carla['id']}))
    assert assigned.status_code == 201, assigned.text
    pupil.headers['X-PageCraft-Realization'] = assigned.json()['id']
    assert (await pupil.post('/api/learning/me/events', json=hint)).status_code == 200
    pupil.cookies.clear()
    await start(pupil, second['code'], 'Outra criança')
    assert (await pupil.post('/api/learning/me/events', json=hint)).status_code == 200
    path = f"/api/learning/support-summary?code={second['code']}"
    assert (await teacher.get(path)).json()['counts']['presented'] == 2
    only_lesson = await teacher.get(path + f"&lesson={lesson['code']}")
    assert only_lesson.status_code == 200, only_lesson.text
    assert only_lesson.json()['counts']['presented'] == 1
    assert (await teacher.get(path + '&lesson=<x>')).status_code == 422
