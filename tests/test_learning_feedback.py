import asyncio

import pytest

from fakes import FakeProvider
from test_learning import learning_clients, register, start
from server.feedback_context import TIMEOUT_MESSAGE


async def test_permanent_code_feedback_is_contextual_private_and_idempotent(learning_clients):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    provider = FakeProvider(default={'feedback': 'Afasta-te do ecrã e lê o título.'})
    app.state.learning_feedback.provider = provider
    body = {'unit_id': 'u2', 'request_id': 'revision-2', 'context': {
        'activity_version': 'v1', 'objective': 'Comunicar aos colegas', 'product': 'poster',
        'previous_hints': [{'text': 'Rever o contraste', 'usefulness': 'not_helped'}],
    }}
    responses = await asyncio.gather(*(pupil.post('/api/learning/me/feedback', json=body) for _ in range(3)))
    assert all(r.status_code == 200 for r in responses)
    assert len(provider.calls) == 1
    assert responses[0].json()['request_id'] == 'revision-2'
    assert 'not_helped' in provider.calls[0]['prompt']
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
    for type_ in ['hint_presented', 'hint_feedback', 'hint_listened', 'work_location', 'help_resolved']:
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
