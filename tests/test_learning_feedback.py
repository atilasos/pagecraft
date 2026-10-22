import asyncio
from contextlib import asynccontextmanager

import pytest

from fakes import FakeProvider
from test_learning import learning_clients, register, start
from server.feedback_context import TIMEOUT_MESSAGE


@pytest.mark.parametrize('source, text', [
    ('ai', 'Compara a escrita com o exemplo.'),
    ('unavailable', ''),
])
async def test_feedback_completion_during_repeated_request_keeps_full_outcome(
    learning_clients, monkeypatch, source, text,
):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    service = app.state.learning_feedback
    learning = app.state.learning
    provider = FakeProvider(default={'feedback': text})
    service.provider = provider
    service.timeout_s = 10
    payload = {'request_id': 'same-request', 'answer': 'avó'}
    provider_started = asyncio.Event()
    finish_provider = asyncio.Event()
    snapshot_ready = asyncio.Event()
    resume_snapshot = asyncio.Event()
    second = None
    original_complete = provider._complete_once
    original_attempt = learning.attempt
    original_lock = learning.lock
    original_record = learning.record
    records = []

    async def controlled_complete(*args, **kwargs):
        response = await original_complete(*args, **kwargs)
        provider_started.set()
        await finish_provider.wait()
        return response

    async def paused_attempt(identifier):
        snapshot = await original_attempt(identifier)
        if asyncio.current_task() is second and not snapshot_ready.is_set():
            assert [e['type'] for e in snapshot['events']] == ['feedback_request']
            snapshot_ready.set()
            await resume_snapshot.wait()
        return snapshot

    @asynccontextmanager
    async def observed_lock(key):
        lock = original_lock(key)
        if key == 'feedback:' + attempt['id'] and lock.locked() and snapshot_ready.is_set():
            # No código corrigido, a conclusão espera pelo lock da segunda leitura.
            resume_snapshot.set()
        async with lock:
            yield

    async def observed_record(identifier, events, **kwargs):
        records.extend(e['type'] for e in events)
        return await original_record(identifier, events, **kwargs)

    monkeypatch.setattr(provider, '_complete_once', controlled_complete)
    monkeypatch.setattr(learning, 'attempt', paused_attempt)
    monkeypatch.setattr(learning, 'lock', observed_lock)
    monkeypatch.setattr(learning, 'record', observed_record)

    first = asyncio.create_task(service.request(attempt['id'], 'u1', payload))
    # No código antigo, liberta a leitura só depois de a tarefa terminar e sair de tasks.
    first.add_done_callback(lambda done: resume_snapshot.set())
    try:
        async with asyncio.timeout(5):
            await provider_started.wait()
            second = asyncio.create_task(service.request(attempt['id'], 'u1', payload))
            await snapshot_ready.wait()
            finish_provider.set()
            results = await asyncio.gather(first, second)
    finally:
        finish_provider.set()
        resume_snapshot.set()
        for task in (first, second):
            if task is not None and not task.done():
                task.cancel()
        await asyncio.gather(*(t for t in (first, second) if t is not None), return_exceptions=True)

    saved = await learning.attempt(attempt['id'])
    assert results[0]['source'] == source
    assert results[0] == results[1] == saved['events'][-1]['payload']
    assert len(provider.calls) == 1
    assert records == ['feedback_request', 'ai_feedback']
    assert [e['type'] for e in saved['events']] == ['feedback_request', 'ai_feedback']
    assert not service.tasks
    assert await service.request(attempt['id'], 'u1', payload) == results[0]
    assert len(provider.calls) == 1
    assert records == ['feedback_request', 'ai_feedback']


@pytest.mark.parametrize('answers', [('avó', 'avô'), ('Lisboa', 'lisboa')])
async def test_permanent_feedback_cache_keeps_spelling_distinctions(learning_clients, answers):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    await start(pupil, activity['code'])
    hints = ['Lê a palavra em voz alta.', 'Compara a escrita com o exemplo.']
    provider = FakeProvider([{'feedback': hint} for hint in hints])
    app.state.learning_feedback.provider = provider
    for number, answer in enumerate(answers):
        response = await pupil.post('/api/learning/me/feedback', json={
            'unit_id': 'u1', 'request_id': f'spelling-{number}',
            'context': {'question': 'Revê a palavra.', 'answer': answer},
        })
        assert response.status_code == 200
        assert response.json()['text'] == hints[number]
        assert response.json()['source'] == 'ai'
    repeated = await pupil.post('/api/learning/me/feedback', json={
        'unit_id': 'u1', 'request_id': 'spelling-repeat',
        'context': {'question': 'Revê a palavra.', 'answer': answers[-1]},
    })
    assert repeated.status_code == 200
    assert repeated.json()['text'] == hints[-1]
    assert repeated.json()['source'] == 'cache'
    assert repeated.json()['request_id'] == 'spelling-repeat'
    assert len(provider.calls) == 2


async def test_permanent_code_feedback_is_contextual_private_and_idempotent(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    provider = FakeProvider(default={'feedback': 'Afasta-te do ecrã e lê o título.'})
    app.state.learning_feedback.provider = provider
    body = {'unit_id': 'u2', 'request_id': 'revision-2', 'context': {
        'age_range': '8-9 anos', 'trigger': 'consecutive_incorrect_attempts',
        'observed_difficulties': [{'answer': n, 'result': 'incorrect'} for n in ['1', '2', '3']],
        'activity_version': 'v1', 'objective': 'Comunicar aos colegas', 'product': 'poster',
        'previous_hints': [{'text': 'Rever o contraste', 'usefulness': 'not_helped'}],
    }}
    responses = await asyncio.gather(*(pupil.post('/api/learning/me/feedback', json=body) for _ in range(3)))
    assert all(r.status_code == 200 for r in responses)
    assert len(provider.calls) == 1
    assert responses[0].json()['request_id'] == 'revision-2'
    assert 'not_helped' in provider.calls[0]['prompt']
    assert '8-9 anos' in provider.calls[0]['prompt']
    assert 'consecutive_incorrect_attempts' in provider.calls[0]['prompt']
    saved = await app.state.learning.attempt(attempt['id'])
    assert [e['type'] for e in saved['events']] == ['feedback_request', 'ai_feedback']
    assert (await pupil.get('/api/learning/reports')).status_code in {401, 403}
    conflict = await pupil.post('/api/learning/me/feedback', json=body | {'context': {'product': 'book'}})
    assert conflict.status_code == 409
    # A nova instância recupera o resultado persistido, sem voltar ao modelo.
    from server.learning_feedback import LearningFeedback
    app.state.learning_feedback = LearningFeedback(app.state.learning, provider, 1)
    assert (await pupil.post('/api/learning/me/feedback', json=body)).json() == responses[0].json()
    assert len(provider.calls) == 1


async def test_permanent_feedback_failure_and_event_boundary(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    await start(pupil, activity['code'])
    app.state.learning_feedback.provider = FakeProvider([RuntimeError('offline')])
    body = {'unit_id': 'u1', 'request_id': 'offline', 'context': {'answer': 'Preciso de ajuda'}}
    response = await pupil.post('/api/learning/me/feedback', json=body)
    assert response.json()['text'] == TIMEOUT_MESSAGE
    assert response.json()['source'] == 'unavailable'
    for type_ in ['hint_presented', 'hint_feedback', 'hint_acknowledged', 'hint_listened', 'work_location', 'help_resolved']:
        result = await pupil.post('/api/learning/me/events', json={'events': [{'id': type_, 'type': type_, 'payload': {}}]})
        assert result.status_code == 200
    forged = await pupil.post('/api/learning/me/events', json={'events': [{'id': 'forged', 'type': 'ai_feedback', 'payload': {}}]})
    assert forged.status_code == 422
    await pupil.post('/api/learning/me/leave')
    assert (await pupil.post('/api/learning/me/feedback', json=body)).status_code in {401, 403}


async def test_feedback_queue_wait_has_a_deadline_and_no_read_claim(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    await start(pupil, activity['code'])
    service = app.state.learning_feedback
    service.timeout_s = .02
    service.slots = asyncio.Semaphore(0)
    response = await pupil.post('/api/learning/me/feedback', json={'unit_id': 'u1', 'request_id': 'timeout', 'context': {}})
    assert response.json()['source'] == 'unavailable'
    assert 'já viu' not in response.json()['text']


async def test_teacher_summary_filters_realizations_and_protects_sources(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    for name in ['Ana e Bruno', 'Carla e Diogo']:
        await start(pupil, activity['code'], name)
        await pupil.post('/api/learning/me/events', json={'events': [
            {'id':'hint', 'type':'hint_presented', 'unitId':'u2', 'payload':{'hint_id':'h','text':'Apontem uma zona.'}},
            {'id':'stuck', 'type':'hint_feedback', 'unitId':'u2', 'payload':{'hint_id':'h','usefulness':'not_helped'}},
            {'id':'help', 'type':'help_needed', 'unitId':'u2', 'payload':{'note':'Não encontramos o comando'}},
        ]})
        await pupil.post('/api/learning/me/leave')
    path='/api/learning/support-summary?code='+activity['code']
    summary=(await teacher.get(path)).json()
    assert summary['counts']['presented'] == 2
    assert summary['counts']['unresolved'] == 2
    assert summary['recurring'][0]['count'] == 2
    assert (await teacher.get(path+'&name=Ana')).json()['counts']['presented'] == 1
    assert (await teacher.get(path+'&date_from=2099-01-01')).json()['counts']['presented'] == 0
    assert (await pupil.get(path)).status_code in {401,403}


async def test_pupil_cannot_forge_an_assistant_record_identifier(learning_clients):
    app, teacher, pupil = learning_clients
    activity,_=await register(teacher)
    await start(pupil,activity['code'])
    for prefix in ['request:', 'feedback:']:
        response=await pupil.post('/api/learning/me/events',json={'events':[{
            'id':prefix+'fake','type':'hint_presented','payload':{'text':'Inventada'},
        }]})
        assert response.status_code==422
