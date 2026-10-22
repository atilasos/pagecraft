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


async def test_resume_reserves_individual_names_until_teacher_authorizes_reentry(continuation):
    app, transport, teacher, session, clock = continuation
    path = '/api/sessions/' + session['id']
    ids = list(session['roster'])
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as original:
        assert (await original.post(path + '/claim', json={'student_id': ids[0]})).status_code == 200
        assert (await original.post(path + '/events', json={'events': [
            {'event_id': 'private-answer', 'type': 'attempt', 'payload': {'text': 'Só da Ana'}}
        ]})).status_code == 200
        await teacher.post(path + '/close')
        clock['now'] = datetime(2026, 10, 8, 10, tzinfo=timezone.utc)
        resumed = (await teacher.post(path + '/resume')).json()
        assert resumed['roster'][ids[0]]['taken']
        assert (await original.get(path + '/me')).status_code == 401
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as stranger:
            roster = (await stranger.get('/api/join/' + resumed['join_code'])).json()['roster']
            assert next(child for child in roster if child['student_id'] == ids[0])['taken']
            assert (await stranger.post(path + '/claim', json={'student_id': ids[0]})).status_code == 409
            assert (await stranger.get(path + f'/students/{ids[0]}/history')).status_code == 401
            assert (await stranger.post(path + '/groups/claim', json={
                'participant_ids': ids[:2], 'mode': 'pair'
            })).status_code == 409
            # Only the teacher can authorize another device for an individual child.
            assert (await teacher.post(path + '/release/' + ids[0], json={})).status_code == 200
            assert (await stranger.post(path + '/claim', json={'student_id': ids[0]})).status_code == 200
        assert any(event.get('event_id') == 'private-answer' for event in
                   (await teacher.get(path + f'/students/{ids[0]}/history')).json()['events'])


async def test_resumed_window_and_unused_codes_expire_at_school_midnight(continuation):
    app, transport, teacher, session, clock = continuation
    from zoneinfo import ZoneInfo
    app.state.classroom._school_timezone = ZoneInfo('Atlantic/Madeira')
    path = '/api/sessions/' + session['id']
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as student:
        await student.post(path + '/groups/claim', json={
            'participant_ids': list(session['roster'])[:2], 'mode': 'pair'
        })
        await teacher.post(path + '/close')
        clock['now'] = datetime(2026, 10, 1, 22, tzinfo=timezone.utc)
        first_code = (await teacher.post(path + '/resume')).json()['group_codes'][0]['code']
        # Madeira is UTC+1 here: the school day ends before UTC midnight.
        clock['now'] = datetime(2026, 10, 1, 23, 10, tzinfo=timezone.utc)
        assert (await student.post('/api/groups/enter', json={'code': first_code})).status_code == 404
        assert (await teacher.get(path)).json()['status'] == 'closed'
        resumed = (await teacher.post(path + '/resume')).json()
        assert resumed['status'] == 'live'
        assert resumed['group_codes'][0]['code'] != first_code
        assert (await student.post('/api/groups/enter', json={
            'code': resumed['group_codes'][0]['code']
        })).status_code == 200


@pytest.mark.parametrize('new_window', [False, True])
async def test_old_pending_work_cannot_overwrite_work_after_a_new_entry(continuation, new_window):
    app, transport, teacher, session, clock = continuation
    path = '/api/sessions/' + session['id']
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as device:
        group = (await device.post(path + '/groups/claim', json={
            'participant_ids': list(session['roster'])[:2], 'mode': 'pair'
        })).json()['work_group']
        old_pending = {'event_id': 'old-offline', 'type': 'activity_state',
                       'composition_version': group['composition_version'],
                       'access_version': group['access_version'],
                       'payload': {'state': {'step': 1}}}
        if new_window:
            await teacher.post(path + '/close')
            clock['now'] = datetime(2026, 10, 8, 10, tzinfo=timezone.utc)
            code = (await teacher.post(path + '/resume')).json()['group_codes'][0]['code']
        else:
            code = (await teacher.post(path + f'/groups/{group["id"]}/access-code')).json()['code']
        current = (await device.post('/api/groups/enter', json={'code': code})).json()['work_group']
        assert current['device_id'] == group['device_id']
        assert current['composition_version'] == group['composition_version']
        assert current['access_version'] > group['access_version']
        new_work = {**old_pending, 'event_id': 'new-work', 'access_version': current['access_version'],
                    'payload': {'state': {'step': 3}}}
        assert (await device.post(path + '/events', json={'events': [new_work]})).json()['accepted'] == ['new-work']
        rejected = await device.post(path + '/events', json={'events': [old_pending]})
        assert rejected.status_code == 409
        assert rejected.json()['detail']['event_ids'] == ['old-offline']
        # A request from an older host that lacks the generation is stale too.
        old_pending.pop('access_version')
        assert (await device.post(path + '/events', json={'events': [old_pending]})).status_code == 409
        history = (await device.get(path + '/groups/me/history')).json()['events']
        assert [e['payload']['state']['step'] for e in history if e['type'] == 'activity_state'] == [3]
