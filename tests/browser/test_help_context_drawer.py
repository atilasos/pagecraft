"""The real teacher drawer keeps help context tied to its recorded authors and IDs."""
from contextlib import contextmanager

import httpx


@contextmanager
def classroom(origin):
    with httpx.Client(base_url=origin) as teacher, httpx.Client(base_url=origin) as pair, httpx.Client(base_url=origin) as other:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        cls = teacher.post('/api/classes', json={
            'name': 'Contexto de ajuda', 'year': 4,
            'students': ['Ana', 'Bruno', 'Carla', 'Duarte', 'Eva'],
        }).json()
        session = teacher.post('/api/sessions', json={
            'class_id': cls['id'], 'activity_slug': 'fraction-test', 'activity_title': 'Contexto de ajuda',
        }).json()
        path = '/api/sessions/' + session['id']
        ids = list(session['roster'])
        for client, members in [(pair, ids[:2]), (other, ids[2:4])]:
            client.post(path + '/groups/claim', json={'participant_ids': members, 'mode': 'pair'}).raise_for_status()
        yield teacher, pair, other, session, path, ids
        teacher.post(path + '/close').raise_for_status()


def post(client, path, *events):
    response = client.post(path + '/events', json={'events': [
        {'event_id': f'{path}-{event[0]}', 'type': event[1], 'unit_id': event[2], 'payload': event[3]}
        for event in events
    ]})
    response.raise_for_status()
    assert len(response.json()['accepted']) == len(events)


def open_teacher(page, origin):
    page.goto(origin + '/teacher/class.html')
    page.request.get(origin + '/api/teacher-bootstrap')
    page.reload()


def open_drawer(page, name):
    page.locator('#work-groups').get_by_role('button', name=f'Ver percurso de {name}', exact=True).first.click()


def test_pending_request_shows_own_context_and_correlated_hint_without_resolving(page, studio_origin):
    from playwright.sync_api import expect
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    with classroom(studio_origin) as (teacher, pair, other, session, path, ids):
        post(pair, path,
             ('old-hint', 'hint_presented', 'u1', {'hint_id': 'old', 'text': 'Pista antiga de outra etapa'}),
             ('hint', 'hint_presented', 'u2', {'hint_id': 'ours', 'text': 'Compare as duas zonas.'}),
             ('feedback', 'hint_feedback', 'u2', {'hint_id': 'ours', 'usefulness': 'not_helped'}),
             ('resolved', 'help_needed', 'u1', {'help_request_id': 'done', 'note': 'Pedido já resolvido'}),
             ('resolve', 'help_resolved', 'u1', {'help_request_id': 'done'}),
             ('help', 'help_needed', 'u2', {
                 'help_request_id': 'pending', 'hint_id': 'ours',
                 'note': 'Não sabemos <img src=x onerror="window.drawerXss=1"> organizar',
                 'context': {'stage': 'Planear', 'question': 'Como distribuir os animais?',
                             'answer': 'Um animal por zona', 'product': 'Cartaz', 'criteria': ['Duas zonas legíveis']},
             }),
             ('unrelated', 'attempt', 'u3', {'detail': 'Resposta de outra tarefa'}))
        post(other, path,
             ('other-hint', 'hint_presented', 'u2', {'hint_id': 'ours', 'text': 'Pista do outro grupo'}),
             ('other-feedback', 'hint_feedback', 'u2', {'hint_id': 'ours', 'usefulness': 'helped'}),
             ('other-help', 'help_needed', 'u3', {'note': 'Pedido de Carla e Duarte'}))
        history_url = path + f'/students/{ids[0]}/history'
        before = teacher.get(history_url).json()
        open_teacher(page, studio_origin)
        open_drawer(page, 'Ana')
        context = page.locator('#drawer-help')
        expect(context).to_contain_text('Não sabemos <img src=x onerror="window.drawerXss=1"> organizar')
        for text in ['Planear', 'Como distribuir os animais?', 'Um animal por zona', 'Cartaz',
                     'Duas zonas legíveis', 'Compare as duas zonas.', 'Não ajudou, segundo o grupo',
                     'Trabalho conjunto · Ana + Bruno', 'pedido pending', 'pista ours', 'registo #']:
            expect(context).to_contain_text(text)
        for text in ['Pista antiga', 'Pedido já resolvido', 'Resposta de outra tarefa', 'outro grupo', 'Carla']:
            expect(context).not_to_contain_text(text)
        assert context.locator('img').count() == 0
        assert page.evaluate('window.drawerXss') is None
        expect(page.locator('#drawer-events')).to_contain_text('pediu ajuda')
        page.locator('#drawer-close').click()
        open_drawer(page, 'Carla')
        expect(context).to_contain_text('Pedido de Carla e Duarte')
        expect(context).to_contain_text('não registado')
        expect(context).not_to_contain_text('Compare as duas zonas.')
        page.locator('#drawer-close').click()
        open_drawer(page, 'Ana')
        expect(context).to_contain_text('pedido pending')
        assert teacher.get(history_url).json() == before
        assert not errors


def test_task_ids_bound_answers_and_only_the_matching_request_is_resolved(page, studio_origin):
    from playwright.sync_api import expect
    with classroom(studio_origin) as (teacher, pair, other, session, path, ids):
        post(pair, path,
             ('right-answer', 'attempt', 'u2', {'task_id': 'layout', 'detail': {'value': 'Duas colunas', 'note': 'Esboço registado'}}),
             ('wrong-task', 'attempt', 'u2', {'task_id': 'colour', 'detail': 'Outra tarefa na mesma etapa'}),
             ('wrong-unit', 'attempt', 'u3', {'task_id': 'layout', 'detail': 'Outra etapa com o mesmo ID de tarefa'}),
             ('legacy-hint', 'hint_presented', 'u2', {'hint_id': 'old', 'text': 'Pista sem ligação ao pedido'}),
             ('help-layout', 'help_needed', 'u2', {'help_request_id': 'layout-help', 'task_id': 'layout', 'note': 'Organização do cartaz'}),
             ('help-colour', 'help_needed', 'u2', {'help_request_id': 'colour-help', 'task_id': 'colour', 'note': 'Pedido que vamos resolver'}),
             ('resolve-colour', 'help_resolved', 'u2', {'help_request_id': 'colour-help'}))
        open_teacher(page, studio_origin)
        open_drawer(page, 'Ana')
        context = page.locator('#drawer-help')
        expect(context).to_contain_text('Duas colunas')
        expect(context).to_contain_text('Esboço registado')
        for text in ['Outra tarefa', 'Outra etapa', 'Pista sem ligação', 'Pedido que vamos resolver']:
            expect(context).not_to_contain_text(text)
        expect(context.locator('article')).to_have_count(1)
        expect(context).to_contain_text('não registado')
        # A new response or usefulness declaration does not resolve help.
        post(pair, path, ('later-answer', 'attempt', 'u2', {'task_id': 'layout', 'detail': 'Depois do pedido'}),
             ('later-feedback', 'hint_feedback', 'u2', {'hint_id': 'old', 'usefulness': 'helped'}))
        expect(page.locator('#drawer-events')).to_contain_text('Depois do pedido')
        expect(context).to_contain_text('pedido layout-help')
        expect(context).not_to_contain_text('Depois do pedido')
        post(pair, path, ('resolved-layout', 'help_resolved', 'u2', {'help_request_id': 'layout-help'}))
        expect(context).to_have_text('Sem pedidos de ajuda pendentes neste percurso.')
        expect(page.locator('#drawer-events')).to_contain_text('declarou que já consegue continuar')
        # Legacy requests without task/hint IDs keep explicit missing fields.
        post(pair, path, ('legacy-help', 'help_needed', 'u2', {'note': 'Pedido antigo sem identificadores'}))
        expect(context).to_contain_text('Pedido antigo sem identificadores')
        for text in ['Duas colunas', 'Depois do pedido', 'Pista sem ligação']:
            expect(context).not_to_contain_text(text)
        post(pair, path, ('legacy-resolved', 'help_resolved', None, {}))
        expect(context).to_have_text('Sem pedidos de ajuda pendentes neste percurso.')


def test_group_composition_and_individual_voice_never_supply_another_requests_context(page, studio_origin):
    from playwright.sync_api import expect
    with classroom(studio_origin) as (teacher, pair, other, session, path, ids):
        post(pair, path,
             ('old-hint', 'hint_presented', 'u2', {'hint_id': 'reused', 'text': 'Pista de Ana e Bruno'}),
             ('old-feedback', 'hint_feedback', 'u2', {'hint_id': 'reused', 'usefulness': 'helped'}))
        group = pair.get(path + '/me').json()['work_group']
        changed = teacher.patch(path + f'/groups/{group["id"]}/participants', json={
            'participant_ids': [ids[0], ids[4]], 'mode': 'pair',
        })
        changed.raise_for_status()
        group = changed.json()['work_group']
        response = pair.post(path + '/events', json={'events': [{
            'event_id': 'changed-help', 'type': 'help_needed', 'unit_id': 'u2',
            'composition_version': group['composition_version'], 'access_version': group['access_version'],
            'payload': {'help_request_id': 'new-group', 'hint_id': 'reused', 'note': 'Ajuda de Ana e Eva'},
        }]})
        response.raise_for_status()
        assert response.json()['accepted'] == ['changed-help']
        reflection = pair.post(path + '/groups/me/reflections', json={
            'student_id': ids[0], 'event_id': 'ana-voice', 'composition_version': group['composition_version'],
            'access_version': group['access_version'], 'expected_revision': 0, 'answers': {},
            'strategy': 'Eu comparei os desenhos.', 'next_step': 'Quero experimentar outra vez.', 'skipped': False,
        })
        reflection.raise_for_status()
        # Student access still cannot read a member's complete teacher history.
        assert pair.get(path + f'/students/{ids[0]}/history').status_code == 403
        open_teacher(page, studio_origin)
        open_drawer(page, 'Ana')
        context = page.locator('#drawer-help')
        expect(context).to_contain_text('Trabalho conjunto · Ana + Eva')
        expect(context).to_contain_text('Ajuda de Ana e Eva')
        expect(context).not_to_contain_text('Pista de Ana e Bruno')
        expect(context).not_to_contain_text('Ajudou, segundo o grupo')
        expect(context).not_to_contain_text('Eu comparei os desenhos.')
        history = page.locator('#drawer-events')
        expect(history).to_contain_text('Trabalho conjunto · Ana + Bruno')
        voice = history.locator('li').filter(has_text='Reflexão individual')
        expect(voice).to_contain_text('Trabalho individual · Ana')
        expect(voice).to_contain_text('Eu comparei os desenhos.')
        expect(voice).not_to_contain_text('Trabalho conjunto')
        page.locator('#drawer-close').click()
        open_drawer(page, 'Eva')
        expect(page.locator('#drawer-events')).not_to_contain_text('Eu comparei os desenhos.')
        expect(page.locator('#drawer-events')).not_to_contain_text('Pista de Ana e Bruno')
