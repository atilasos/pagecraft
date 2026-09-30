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


async def test_overlapping_claims_are_atomic_and_leave_the_other_member_free(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as first, httpx.AsyncClient(transport=transport, base_url='http://test') as second:
        results = await asyncio.gather(
            first.post(path+'/groups/claim', json={'participant_ids':ids[:2],'mode':'pair'}),
            second.post(path+'/groups/claim', json={'participant_ids':ids[1:3],'mode':'pair'}),
        )
        assert sorted(r.status_code for r in results) == [200,409]
        roster = (await teacher.get('/api/join/'+session['join_code'])).json()['roster']
        assert sum(entry['taken'] for entry in roster) == 2
        free_id = next(entry['student_id'] for entry in roster if not entry['taken'])
        assert (await teacher.post(path+'/claim', json={'student_id':free_id})).status_code == 200


async def test_group_work_is_once_in_history_and_distinct_from_individual_results(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair:
        group = (await pair.post(path+'/groups/claim',json={'participant_ids':ids[:2],'mode':'pair'})).json()['work_group']
        event = {'event_id':'shared-answer','type':'attempt','unit_id':'u1','student_id':ids[2],'participant_ids':[ids[2]],'payload':{'correct':True,'detail':'Resposta conjunta'}}
        assert (await pair.post(path+'/events',json={'events':[event]})).json()['accepted'] == ['shared-answer']
        assert (await pair.post(path+'/events',json={'events':[event]})).json()['accepted'] == []
        for sid in ids[:2]:
            history = (await teacher.get(path+f'/students/{sid}/history')).json()['events']
            answers = [e for e in history if e['type'] == 'attempt']
            assert len(answers) == 1
            assert answers[0]['work_group_id'] == group['id']
            assert answers[0]['participant_ids'] == ids[:2]
            assert answers[0].get('student_id') is None
        assert (await teacher.get(path+f'/students/{ids[2]}/history')).json()['events'] == []
        # A shared credential sees only its joint work, not a member's private history.
        assert (await pair.get(path+f'/students/{ids[0]}/history')).status_code == 403
        own = await pair.get(path+'/groups/me/history')
        assert own.status_code == 200
        assert len([e for e in own.json()['events'] if e['type']=='attempt']) == 1
        report = (await teacher.get(f"/api/classes/{cls['id']}/report")).json()
        assert report['sessions'][0]['attempts'] == 1
        assert report['sessions'][0]['participants'] == 2
        assert [r['correct'] for r in report['students']] == [0,0,0,0]
        assert report['groups'][0]['attempt'] == 1
        assert report['groups'][0]['members'] == ['Ana','Bruno']


async def test_group_level_and_release_do_not_change_individual_profiles(classroom):
    transport, teacher, cls, session = classroom
    ids=list(session['roster'])
    path=f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport,base_url='http://test') as pair:
        group=(await pair.post(path+'/groups/claim',json={'participant_ids':ids[:2],'mode':'pair'})).json()['work_group']
        await pair.post(path+'/events',json={'events':[{'event_id':'level','type':'level_changed','payload':{'level':'challenge'}},{'event_id':'help','type':'help_needed','payload':{}}]})
        assert (await pair.get(path+'/me')).json()['work_group']['level'] == 'challenge'
        assert (await teacher.get('/api/classes')).json()[0]['students'] == cls['students']
        assert (await pair.post(path+'/pit',json={'text':'Plano em nome de ninguém'})).status_code == 403
        assert (await pair.post(path+f'/release/{ids[0]}',json={})).status_code == 403
        assert (await teacher.post(path+f'/release/{ids[0]}',json={})).status_code == 200
        assert (await pair.get(path+'/me')).status_code == 401
        roster=(await teacher.get('/api/join/'+session['join_code'])).json()['roster']
        assert not any(entry['taken'] for entry in roster)
        history=(await teacher.get(path+f'/students/{ids[1]}/history')).json()['events']
        assert len([e for e in history if e['type']=='help_needed']) == 1


async def test_group_stream_contains_its_work_without_other_groups(classroom):
    import json
    transport, teacher, cls, session=classroom
    ids=list(session['roster']); path=f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport,base_url='http://test') as pair, httpx.AsyncClient(transport=transport,base_url='http://test') as other:
        ours=(await pair.post(path+'/groups/claim',json={'participant_ids':ids[:2],'mode':'pair'})).json()['work_group']
        theirs=(await other.post(path+'/groups/claim',json={'participant_ids':ids[2:],'mode':'pair'})).json()['work_group']
        await pair.post(path+'/events',json={'events':[{'event_id':'our-help','type':'help_needed','payload':{}}]})
        await other.post(path+'/events',json={'events':[{'event_id':'their-answer','type':'attempt','payload':{'correct':True}}]})
        await teacher.post(path+'/close')
        response=await pair.get(path+'/stream')
        assert response.status_code == 200, response.text
        data=json.loads(next(line[6:] for line in response.text.splitlines() if line.startswith('data: ')))
        assert data['students'] == {}
        assert list(data['groups']) == [ours['id']]
        assert data['groups'][ours['id']]['triage']['explicit_help'] is True
        assert theirs['id'] not in response.text
        assert ids[2] not in response.text
        teacher_response=await teacher.get(path+'/stream')
        teacher_data=json.loads(next(line[6:] for line in teacher_response.text.splitlines() if line.startswith('data: ')))
        assert len(teacher_data['groups']) == 2
        assert teacher_data['numbers']['evidence']['attempt'] == 1
