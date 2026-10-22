import json
from pathlib import Path

from fakes import FakeProvider
from test_learning import learning_clients
from test_feedback import _wait_event


async def test_studio_code_pair_help_model_and_teacher_summary(learning_clients):
    app, teacher, pupil = learning_clients
    registration = json.loads((Path(__file__).resolve().parents[1] / 'drafts/canva-animais-autonomia-piloto-registration.json').read_text())
    draft = await teacher.post('/api/learning/activities', json=registration)
    assert draft.status_code == 201
    classroom = (await teacher.post('/api/classes', json={'name':'Canva teste','year':4,'students':['Ana','Bruno']})).json()
    session = (await teacher.post('/api/sessions', json={'class_id':classroom['id'],'activity_slug':registration['slug'],'activity_title':registration['title']})).json()
    found = await pupil.get('/api/join/'+session['join_code'])
    assert found.status_code == 200
    ids = list(session['roster'])
    response = await pupil.post(f"/api/sessions/{session['id']}/groups/claim", json={'participant_ids':ids,'mode':'pair'})
    assert response.status_code == 200, response.text
    group = response.json().get('work_group', response.json())
    provider=FakeProvider(default={'feedback':'Apontem no esboço a zona de cada animal.'})
    app.state.feedback.provider=provider
    context={'request_id':'studio-pair-1','activity':registration['slug'],'activity_version':'v1',
             'stage':'Planear','objective':'Comunicar aos colegas','participant_count':2,'product':'poster',
             'answer':'Não sabemos organizar','previous_hints':[{'text':'Duas zonas','usefulness':'not_helped'}]}
    payloads=[('hint_presented',{'hint_id':'h1','text':'Duas zonas','activity':registration['slug']}),
              ('hint_feedback',{'hint_id':'h1','usefulness':'not_helped'}),
              ('help_needed',{'note':'Não conseguimos organizar','help_request_id':'teacher-1'}),
              ('work_location',{'location':'canva'}),('feedback_request',context)]
    events=[{'event_id':str(i),'type':type_,'unit_id':'u2','payload':payload,
             'composition_version':group.get('composition_version',1),'access_version':group.get('access_version',1)}
            for i,(type_,payload) in enumerate(payloads)]
    posted = await pupil.post(f"/api/sessions/{session['id']}/events", json={'events':events})
    assert posted.status_code == 200, posted.text
    assert len(posted.json()['accepted']) == 5
    result=await _wait_event(app.state.storage,session['id'],'ai_feedback')
    assert result['payload']['request_id']=='studio-pair-1'
    assert result['work_group_id']==group['id']
    assert result['participant_ids']==ids
    assert result.get('student_id') is None
    assert 'not_helped' in provider.calls[0]['prompt']
    path=f"/api/sessions/{session['id']}/support-summary"
    summary=(await teacher.get(path)).json()
    assert summary['counts']['unresolved']==1
    assert summary['counts']['not_helped']==1
    assert (await pupil.get(path)).status_code in {401,403}
    await teacher.post(f"/api/sessions/{session['id']}/close")
    assert (await teacher.get(path)).json()['counts']['unresolved']==1


async def test_contextual_support_fits_the_bounded_event_contracts(learning_clients):
    app, teacher, pupil = learning_clients
    from server.api.learning import Event
    from server.api.classroom import EventsRequest
    context={'activity_version':'v1','answer':'é'*650,'previous_hints':[{'text':'á'*200},{'text':'ç'*200}]}
    payload={'hint_id':'hint','text':'Uma ação','context':context}
    # O limite antigo contava escapes ASCII e recusava contexto português legítimo.
    assert len(json.dumps(payload)) > 4096
    assert Event(id='hint',type='hint_presented',payload=payload).payload==payload
    assert EventsRequest(events=[{'type':'hint_presented','payload':payload}]).events
