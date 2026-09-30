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


async def test_only_the_authorized_device_gets_group_content_with_level_adapter(classroom):
    transport, teacher, cls, session=classroom
    ids=list(session['roster']);path=f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport,base_url='http://test') as pair, httpx.AsyncClient(transport=transport,base_url='http://test') as anonymous:
        await pair.post(path+'/groups/claim',json={'participant_ids':ids[:2],'mode':'pair'})
        response=await pair.get(path+'/content')
        assert response.status_code == 200
        assert 'work_group_preferences' in response.text
        assert "connect-src 'none'" in response.headers['content-security-policy']
        assert (await anonymous.get(path+'/content')).status_code == 401


@pytest.mark.parametrize('mode, indices, level, status', [
    ('pair', [0, 1, 2], 'support', 400),
    ('group', [0, 1], 'support', 400),
    ('group', [0, 1, 1], 'support', 400),
    ('pair', [0, None], 'support', 404),
    ('pair', [0, 1], 'unknown', 422),
    ('unknown', [0, 1], 'support', 422),
])
async def test_invalid_group_claim_does_not_reserve_any_names(classroom, mode, indices, level, status):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    response = await teacher.post(f"/api/sessions/{session['id']}/groups/claim", json={
        'participant_ids':[ids[i] if i is not None else 'outside-roster' for i in indices],
        'mode':mode, 'level':level,
    })
    assert response.status_code == status, response.text
    roster = (await teacher.get('/api/join/' + session['join_code'])).json()['roster']
    assert not any(student['taken'] for student in roster)


async def test_three_members_enter_as_a_group_and_closed_session_rejects_new_work(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as device:
        response = await device.post(path + '/groups/claim', json={
            'participant_ids':ids[:3], 'mode':'group', 'level':'challenge'
        })
        assert response.status_code == 200
        assert response.json()['work_group']['display_name'] == 'Ana + Bruno + Carla'
        roster = (await teacher.get('/api/join/' + session['join_code'])).json()['roster']
        assert [student['taken'] for student in roster] == [True, True, True, False]
        await teacher.post(path + '/close')
        response = await device.post(path + '/events', json={'events':[
            {'event_id':'too-late','type':'attempt','payload':{'correct':True}}
        ]})
        assert response.status_code == 409
        history = (await device.get(path + '/groups/me/history')).json()['events']
        assert not any(event['type'] == 'attempt' for event in history)


async def test_group_member_reflection_has_individual_authorship(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster'])
    path = f"/api/sessions/{session['id']}"
    registered = await teacher.post('/api/learning/activities', json={
        'slug': 'fracoes-2-minecraft', 'title': 'Frações', 'year': 2, 'duration': 45,
        'criteria': [{'id': 'iguais', 'pt': 'Reconheço partes iguais.'}],
    })
    assert registered.status_code == 201
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair:
        group = (await pair.post(path+'/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair'})).json()['work_group']
        available = await pair.get(path+'/groups/me/reflections')
        assert available.status_code == 200, available.text
        assert available.json()['criteria'] == [{'id':'iguais', 'pt':'Reconheço partes iguais.', 'en':''}]
        response = await pair.post(path+'/groups/me/reflections', json={
            'student_id':ids[0], 'event_id':'ana-reflection', 'expected_revision':0,
            'answers':{'iguais':'help'}, 'strategy':'Comparei os blocos.',
        })
        assert response.status_code == 200, response.text
        saved = (await pair.get(path+'/groups/me/reflections')).json()['reflections'][ids[0]]
        assert saved['student_id'] == ids[0]
        assert saved['payload']['answers'] == {'iguais':'help'}
        assert saved['payload']['source_work_group_id'] == group['id']
        history = (await teacher.get(path+f'/students/{ids[0]}/history')).json()['events']
        voice = [e for e in history if e['type']=='individual_reflection']
        assert len(voice) == 1
        assert not voice[0].get('work_group_id')
        peer = (await teacher.get(path+f'/students/{ids[1]}/history')).json()['events']
        assert not any(e['type']=='individual_reflection' for e in peer)


async def test_reflection_revision_retry_and_omission_preserve_each_child(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster']); path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as group:
        await group.post(path+'/groups/claim', json={'participant_ids':ids[:3], 'mode':'group'})
        first = {'student_id':ids[0], 'event_id':'ana-1', 'expected_revision':0, 'strategy':'Usei blocos.'}
        for data in [first, {'student_id':ids[1], 'event_id':'bruno-1', 'expected_revision':0, 'strategy':'Pedi ajuda.'},
                     {'student_id':ids[2], 'event_id':'carla-1', 'expected_revision':0, 'skipped':True}]:
            assert (await group.post(path+'/groups/me/reflections', json=data)).status_code == 200
        revised = {**first, 'event_id':'ana-2', 'expected_revision':1, 'strategy':'Comparei partes iguais.'}
        assert (await group.post(path+'/groups/me/reflections', json=revised)).status_code == 200
        assert (await group.post(path+'/groups/me/reflections', json=first)).status_code == 200
        assert (await group.post(path+'/groups/me/reflections', json=revised)).status_code == 200
        stale = {**first, 'event_id':'ana-stale', 'strategy':'Resposta antiga.'}
        assert (await group.post(path+'/groups/me/reflections', json=stale)).status_code == 409
        collision = {**first, 'strategy':'Outra resposta com o mesmo envio.'}
        assert (await group.post(path+'/groups/me/reflections', json=collision)).status_code == 409
        latest = (await group.get(path+'/groups/me/reflections')).json()['reflections']
        assert latest[ids[0]]['payload']['strategy'] == 'Comparei partes iguais.'
        assert latest[ids[1]]['payload']['strategy'] == 'Pedi ajuda.'
        assert latest[ids[2]]['payload']['skipped'] is True
        for sid, revisions in [(ids[0],2), (ids[1],1), (ids[2],1)]:
            history = (await teacher.get(path+f'/students/{sid}/history')).json()['events']
            assert len([e for e in history if e['type']=='individual_reflection']) == revisions
        report = (await teacher.get(f"/api/classes/{cls['id']}/report")).json()
        assert len(report['reflections']) == 3
        assert [r['payload']['strategy'] for r in report['reflections']] == ['Comparei partes iguais.', 'Pedi ajuda.', '']
        assert all(row['correct'] == 0 and row['assessment_result'] == 0 for row in report['students'])
        md = (await teacher.get(f"/api/classes/{cls['id']}/report?format=md")).text
        assert 'Reflexões individuais' in md
        assert 'Ana' in md and 'Comparei partes iguais.' in md
        assert 'Carla' in md and 'Preferiu não responder' in md


async def test_reflections_reject_foreign_members_and_legacy_joint_attribution(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster']); path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair, httpx.AsyncClient(transport=transport, base_url='http://test') as other:
        await pair.post(path+'/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair'})
        await other.post(path+'/groups/claim', json={'participant_ids':ids[2:], 'mode':'pair'})
        foreign = {'student_id':ids[2], 'event_id':'foreign', 'expected_revision':0, 'strategy':'Não sou deste grupo.'}
        assert (await pair.post(path+'/groups/me/reflections', json=foreign)).status_code == 404
        own = {**foreign, 'student_id':ids[0], 'event_id':'own'}
        assert (await pair.post(path+'/groups/me/reflections', json={**own, 'answers':{'invented':'alone'}})).status_code == 400
        assert (await pair.post(path+'/groups/me/reflections', json={**own, 'answers':{'invented':'excellent'}})).status_code == 422
        assert (await pair.post(path+'/groups/me/reflections', json=own)).status_code == 200
        assert (await other.get(path+'/groups/me/reflections')).json()['reflections'] == {}
        legacy = await pair.post(path+'/events', json={'events':[
            {'event_id':'old-reflection', 'type':'assessment_result', 'payload':{'result':'Todos conseguem sozinhos'}},
            {'event_id':'forged-voice', 'type':'individual_reflection', 'student_id':ids[2], 'payload':{}},
        ]})
        assert legacy.json()['accepted'] == []
        await teacher.post(path+'/close')
        assert (await pair.post(path+'/groups/me/reflections', json={**own, 'event_id':'closed', 'expected_revision':1})).status_code == 409
        assert len((await pair.get(path+'/groups/me/reflections')).json()['reflections']) == 1
        # Closed-session stream remains private; the other pair's child voice is absent.
        stream = (await other.get(path+'/stream')).text
        assert 'Não sou deste grupo.' not in stream
        assert ids[0] not in stream


async def test_published_activity_uses_its_declared_reflection_criteria(classroom):
    transport, teacher, cls, initial = classroom
    slug = 'leitura-al-el-il-ol-ul-minecraft-2ano-45min'
    session = (await teacher.post('/api/sessions', json={'class_id':cls['id'], 'activity_slug':slug})).json()
    ids = list(session['roster']); path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair:
        await pair.post(path+'/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair'})
        response = await pair.get(path+'/groups/me/reflections')
        assert response.status_code == 200
        assert response.json()['criteria'][0] == {'id':'localizar','pt':'Encontro al, el, il, ol ou ul nas palavras.','en':''}
        saved = await pair.post(path+'/groups/me/reflections', json={
            'student_id':ids[0], 'event_id':'reading-reflection', 'expected_revision':0,
            'answers':{'localizar':'practising'},
        })
        assert saved.status_code == 200
        assert saved.json()['payload']['criteria'] == response.json()['criteria']


async def test_teacher_changes_group_without_reattributing_previous_work(classroom):
    transport, teacher, cls, session = classroom
    ids = list(session['roster']); path = f"/api/sessions/{session['id']}"
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as pair:
        old = (await pair.post(path+'/groups/claim', json={'participant_ids':ids[:2], 'mode':'pair'})).json()['work_group']
        await pair.post(path+'/events',json={'events':[{'event_id':'before-change','type':'attempt','payload':{'correct':True}}]})
        await pair.post(path+'/groups/me/reflections',json={'student_id':ids[1],'event_id':'bruno-voice','expected_revision':0,'strategy':'Trabalhei com a Ana.'})
        response = await teacher.patch(path+f"/groups/{old['id']}/participants",json={'participant_ids':[ids[0],ids[2]],'mode':'pair'})
        assert response.status_code == 200, response.text
        new = response.json()['work_group']
        assert new['id'] != old['id']
        assert new['device_id'] == old['device_id']
        assert new['composition_version'] == 2
        assert (await pair.get(path+'/me')).json()['work_group'] == new
        await pair.post(path+'/events',json={'events':[{'event_id':'after-change','type':'attempt','composition_version':2,'payload':{'correct':False}}]})
        bruno = (await teacher.get(path+f'/students/{ids[1]}/history')).json()['events']
        carla = (await teacher.get(path+f'/students/{ids[2]}/history')).json()['events']
        assert [e['event_id'] for e in bruno if e['type']=='attempt'] == ['before-change']
        assert [e['event_id'] for e in carla if e['type']=='attempt'] == ['after-change']
        assert any(e['type']=='individual_reflection' and e['payload']['source_work_group_id']==old['id'] for e in bruno)
        assert not any(e['type']=='individual_reflection' for e in carla)
        available = (await teacher.get('/api/join/'+session['join_code'])).json()['roster']
        assert [r['taken'] for r in available] == [True,False,True,False]
        report = (await teacher.get(f"/api/classes/{cls['id']}/report")).json()
        assert sorted((g['display_name'],g['attempt']) for g in report['groups']) == [('Ana + Bruno',1),('Ana + Carla',1)]
        assert all(r['correct']==0 for r in report['students'])
