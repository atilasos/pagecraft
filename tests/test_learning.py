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
    return response.json()


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
    assert report['evidence'][1]['text'] == ['Apoio: Árvore robusta']
