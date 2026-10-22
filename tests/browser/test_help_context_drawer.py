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
    page.locator('#work-groups').get_by_role('button', name=f'Ver percurso de {name}', exact=True).click()


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
