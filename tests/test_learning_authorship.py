"""An expected realization is a precondition, never an access credential."""
import pytest

from test_learning import learning_clients, register, start


HEADER = 'X-PageCraft-Realization'
ACTIONS = [
    ('GET', '/me', None),
    ('POST', '/me/events', {'events': [
        {'id': 'from-tab-A', 'type': 'attempt', 'payload': {'answer': 'Resposta A'}},
    ]}),
    ('POST', '/me/feedback', {'unit_id': 'u1', 'request_id': 'hint-A', 'context': {'answer': 'A'}}),
    ('POST', '/me/finish', {'strategy': 'Reflexão A'}),
    ('POST', '/me/leave', None),
]


@pytest.mark.parametrize('as_teacher', [False, True])
@pytest.mark.parametrize('method,path,body', ACTIONS)
async def test_stale_tab_cannot_read_mutate_or_clear_other_realization(
    learning_clients, as_teacher, method, path, body, monkeypatch,
):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher, published=not as_teacher)
    client = teacher if as_teacher else pupil
    first = await start(client, activity['code'], 'Aluno A')
    first_before = await app.state.learning.attempt(first['id'])
    second = await start(client, activity['code'], 'Aluno B')
    before = await app.state.learning.attempt(second['id'])
    cookies_before = dict(client.cookies)

    async def unexpected_feedback(*args, **kwargs):
        pytest.fail('Stale feedback reached the service')

    if path == '/me/feedback':
        monkeypatch.setattr(app.state.learning_feedback, 'request', unexpected_feedback)
    response = await client.request(method, '/api/learning' + path, json=body,
                                    headers={HEADER: first['id']})
    after = await app.state.learning.attempt(second['id'])
    assert after == before, f'{path}: a ação de A alterou B (HTTP {response.status_code})'
    assert dict(client.cookies) == cookies_before, f'{path}: a ação de A apagou a credencial de B'
    assert response.status_code == 409, response.text
    assert response.json()['detail']['code'] == 'realization_conflict'
    assert second['id'] not in response.text
    assert await app.state.learning.attempt(first['id']) == first_before


@pytest.mark.parametrize('method,path,body', ACTIONS[1:])
async def test_old_mutation_clients_must_declare_the_expected_realization(learning_clients, method, path, body):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    before = await app.state.learning.attempt(attempt['id'])
    cookies_before = dict(pupil.cookies)
    response = await pupil.request(method, '/api/learning' + path, json=body)
    assert response.status_code == 428
    assert await app.state.learning.attempt(attempt['id']) == before
    assert dict(pupil.cookies) == cookies_before


@pytest.mark.parametrize('method,path,body', ACTIONS)
async def test_identifier_alone_never_authenticates(learning_clients, method, path, body):
    app, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    pupil.cookies.clear()
    response = await pupil.request(method, '/api/learning' + path, json=body,
                                   headers={HEADER: attempt['id']})
    assert response.status_code == 401


async def test_expected_identity_allows_discovery_retry_finish_and_leave(learning_clients):
    _, teacher, pupil = learning_clients
    activity, _ = await register(teacher)
    attempt = await start(pupil, activity['code'])
    # Only initial discovery may read without the precondition.
    assert (await pupil.get('/api/learning/me')).json()['id'] == attempt['id']
    headers = {HEADER: attempt['id']}
    assert (await pupil.get('/api/learning/me', headers=headers)).json()['id'] == attempt['id']
    for expected_count in [1, 0]:
        response = await pupil.post('/api/learning/me/events', headers=headers, json=ACTIONS[1][2])
        assert response.json() == {'accepted': expected_count}
    for _ in range(2):
        response = await pupil.post('/api/learning/me/finish', headers=headers, json=ACTIONS[3][2])
        assert response.status_code == 200
        assert response.json()['id'] == attempt['id']
    assert (await pupil.post('/api/learning/me/leave', headers=headers)).status_code == 204
    assert (await pupil.get('/api/learning/me', headers=headers)).status_code == 401
