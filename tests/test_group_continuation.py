"""A group resumes its saved work in a new school day and a different browser."""
from datetime import datetime, timezone

import httpx
import pytest

from server.app import create_app


@pytest.fixture
async def continuation(tmp_path, monkeypatch):
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    app = create_app()
    clock = {'now': datetime(2026, 10, 1, 10, tzinfo=timezone.utc)}
    async with app.router.lifespan_context(app):
        app.state.classroom._clock = lambda: clock['now'].isoformat()
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            cls = (await teacher.post('/api/classes', json={
                'name': 'Retoma', 'year': 4, 'students': ['Ana', 'Bruno', 'Carla', 'Duarte']
            })).json()
            session = (await teacher.post('/api/sessions', json={
                'class_id': cls['id'], 'activity_slug': 'canva-animais-4ano',
                'activity_title': 'Dois animais'
            })).json()
            yield app, transport, teacher, session, clock


async def test_resume_recovers_group_on_another_day_without_copying_evidence(continuation):
    app, transport, teacher, session, clock = continuation
    path = '/api/sessions/' + session['id']
    ids = list(session['roster'])
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as original:
        group = (await original.post(path + '/groups/claim', json={
            'participant_ids': ids[:2], 'mode': 'pair', 'level': 'challenge'
        })).json()['work_group']
        declaration = {'result': 'Declaração do grupo', 'detail': {
            'activity': 'canva-animais-4ano', 'field': 'layoutPlan',
            'value': 'Duas zonas, uma por animal.', 'confirmed': True
        }}
        checkpoint = {'activity': 'canva-animais-4ano', 'version': 1,
                      'readyForReflection': False, 'state': {'step': 2, 'level': 'challenge'}}
        result = await original.post(path + '/events', json={'events': [
            {'event_id': 'saved-plan', 'type': 'assessment_result', 'payload': declaration},
            {'event_id': 'saved-step', 'type': 'activity_state', 'payload': checkpoint},
            {'event_id': 'real-attempt', 'type': 'attempt', 'payload': {'correct': False}}
        ]})
        assert result.json()['accepted'] == ['saved-plan', 'saved-step', 'real-attempt']
        await teacher.post(path + '/close')
        clock['now'] = datetime(2026, 10, 8, 10, tzinfo=timezone.utc)
        resumed = await teacher.post(path + '/resume')
        assert resumed.status_code == 200, resumed.text
        data = resumed.json()
        assert data['id'] == session['id'] and data['status'] == 'live'
        assert data['started_at'] == session['started_at']
        row = next(row for row in data['group_codes'] if row['id'] == group['id'])
        assert len(row['code']) == 8 and row['display_name'] == 'Ana + Bruno'
        assert (await original.get(path + '/me')).status_code == 401
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as next_day:
            entered = await next_day.post('/api/groups/enter', json={'code': row['code']})
            assert entered.status_code == 200, entered.text
            assert 'HttpOnly' in entered.headers['set-cookie']
            assert entered.json()['work_group']['id'] == group['id']
            assert entered.json()['work_group']['level'] == 'challenge'
            history = (await next_day.get(path + '/groups/me/history')).json()['events']
            assert [e['event_id'] for e in history if e.get('event_id') in {
                'saved-plan', 'saved-step', 'real-attempt'
            }] == ['saved-plan', 'saved-step', 'real-attempt']
            assert history[0]['payload'] == declaration
            assert history[1]['payload'] == checkpoint
            current = (await teacher.get(path)).json()
            assert next(row for row in current['group_codes'] if row['id'] == group['id'])['code'] is None
            assert (await next_day.get(path + f'/students/{ids[0]}/history')).status_code == 403
        again = (await teacher.post(path + '/resume')).json()
        assert again['active_since'] == data['active_since']
        assert (await app.state.classroom.get_session(session['id']))['status'] == 'live'


async def test_codes_are_scoped_consumed_rotated_and_available_only_to_teacher_and_board(continuation):
    app, transport, teacher, session, clock = continuation
    path = '/api/sessions/' + session['id']
    ids = list(session['roster'])
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as first, httpx.AsyncClient(transport=transport, base_url='http://test') as second:
        ours = (await first.post(path + '/groups/claim', json={'participant_ids': ids[:2], 'mode': 'pair'})).json()['work_group']
        theirs = (await second.post(path + '/groups/claim', json={'participant_ids': ids[2:], 'mode': 'pair'})).json()['work_group']
        await first.post(path + '/events', json={'events': [{'event_id': 'only-ours', 'type': 'attempt', 'payload': {'correct': True}}]})
        await second.post(path + '/events', json={'events': [{'event_id': 'only-theirs', 'type': 'attempt', 'payload': {'correct': False}}]})
        await teacher.post(path + '/close')
        rows = (await teacher.post(path + '/resume')).json()['group_codes']
        code = next(row['code'] for row in rows if row['id'] == ours['id'])
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as device:
            assert (await device.post(path + '/resume')).status_code == 401
            assert (await device.post('/api/groups/enter', json={'code': 'XXXXXXXX'})).status_code == 404
            assert (await device.post('/api/groups/enter', json={'code': code})).status_code == 200
            assert 'group_codes' not in (await device.get(path + '/me')).json()['session']
            events = (await device.get(path + '/groups/me/history')).json()['events']
            assert 'only-theirs' not in [e.get('event_id') for e in events]
            refreshed = (await teacher.post(path + f'/groups/{ours["id"]}/access-code')).json()
            assert refreshed['code'] != code
            assert (await device.get(path + '/me')).status_code == 401
            assert (await device.post('/api/groups/enter', json={'code': code})).status_code == 404
            assert (await device.post('/api/groups/enter', json={'code': refreshed['code']})).status_code == 200
        # Stored work survives a service reload; session expiry still closes the new window.
        from server.classroom.service import ClassroomService
        from server.events import EventHub
        restarted = ClassroomService(app.state.classroom.config, app.state.storage,
                                     EventHub(app.state.storage), clock=app.state.classroom._clock)
        assert (await restarted.get_session(session['id']))['active_since'] == (await teacher.get(path)).json()['active_since']
        assert len(await restarted.events_log(session['id']).replay()) == len(await app.state.classroom.events_log(session['id']).replay())
        clock['now'] = datetime(2026, 10, 1, 19, tzinfo=timezone.utc)
        assert (await teacher.get(path)).json()['status'] == 'closed'
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as stranger:
            remaining = next(row['code'] for row in rows if row['id'] == theirs['id'])
            assert (await stranger.post('/api/groups/enter', json={'code': remaining})).status_code == 404


async def test_projected_codes_follow_group_changes_and_release(continuation):
    app, transport, teacher, session, clock = continuation
    path = '/api/sessions/' + session['id']
    ids = list(session['roster'])
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as student:
        group = (await student.post(path + '/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair'})).json()['work_group']
        await teacher.post(path + '/close')
        resumed = (await teacher.post(path + '/resume')).json()
        code = resumed['group_codes'][0]['code']
        # The teacher can correct an absent participant before anybody enters.
        changed = await teacher.patch(path + '/groups/' + group['id'] + '/participants',
                                      json={'participant_ids':[ids[0],ids[2]], 'mode':'pair'})
        assert changed.status_code == 200
        current = changed.json()['work_group']
        from server.classroom.live_state import session_state_snapshot
        records = await app.state.classroom.events_log(session['id']).replay()
        board = session_state_snapshot(records, await app.state.classroom.get_session(session['id']),
                                       now=clock['now'], role='board')
        assert board['session']['group_codes'] == [{'id':current['id'], 'display_name':'Ana + Carla', 'code':code}]
        assert 'group_codes' not in session_state_snapshot(records, session, now=clock['now'],
                                                          role='student', work_group_id=current['id'])['session']
        assert (await teacher.post(path + '/release/' + ids[0], json={})).status_code == 200
        records = await app.state.classroom.events_log(session['id']).replay()
        assert records[-1]['payload']['groups'] == []
        assert (await student.post('/api/groups/enter', json={'code':code})).status_code == 404
