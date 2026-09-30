"""Work groups are observed through the classroom's public HTTP interface."""
import asyncio

import httpx
import pytest

from server.app import create_app


@pytest.fixture
async def classroom(tmp_path, monkeypatch):
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            cls = (await teacher.post('/api/classes', json={'name':'Grupos', 'year':2, 'students':['Ana','Bruno','Carla','Duarte']})).json()
            session = (await teacher.post('/api/sessions', json={'class_id':cls['id'], 'activity_slug':'fracoes-2-minecraft', 'activity_title':'Frações'})).json()
            yield transport, teacher, cls, session


async def test_pair_reserves_every_member_and_resumes_as_the_group(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair:
        response = await pair.post(path+'/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair', 'level':'support'})
        assert response.status_code == 200, response.text
        group = response.json()['work_group']
        assert group['participant_ids'] == ids[:2]
        assert [m['display_name'] for m in group['members']] == ['Ana','Bruno']
        assert group['level'] == 'support'
        assert 'token' not in response.text
        assert 'HttpOnly' in response.headers['set-cookie']
        me = (await pair.get(path+'/me')).json()
        assert me['work_group'] == group
        assert me['student_id'] is None
        joined = (await teacher.get('/api/join/'+session['join_code'])).json()
        assert [entry['taken'] for entry in joined['roster']] == [True,True,False,False]
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as other:
            conflict = await other.post(path+'/claim', json={'student_id':ids[1]})
            assert conflict.status_code == 409
        projected = (await teacher.get(path)).json()
        assert projected['work_groups'][group['id']]['members'] == group['members']
        assert 'token' not in str(projected['work_groups'])
