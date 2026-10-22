"""A saved intention is an optional, read-only reminder with explicit authorship."""
import os
from pathlib import Path

import httpx
import pytest


def enter_pair(page, origin, code):
    page.goto(origin + '/student/')
    page.get_by_label('Código da aula ou do grupo').fill(code)
    page.get_by_role('button', name='Entrar', exact=True).click()
    page.get_by_role('button', name='A pares', exact=True).click()
    for name in ['Ana', 'Bruno']:
        page.get_by_role('button', name=name, exact=True).click()
    page.get_by_role('button', name='Começar', exact=True).click()


def create_session(teacher):
    teacher.get('/api/teacher-bootstrap').raise_for_status()
    classroom = teacher.post('/api/classes', json={
        'name': 'Bilhete de regresso', 'year': 2, 'students': ['Ana', 'Bruno', 'Carla']
    }).json()
    return teacher.post('/api/sessions', json={
        'class_id': classroom['id'], 'activity_slug': 'fraction-test'
    }).json()


def save_intentions(page):
    from playwright.sync_api import expect
    page.get_by_role('button', name='A minha reflexão', exact=True).click()
    for name, text in [('Ana', 'Comparar as metades.'), ('Bruno', 'Experimentar quartos.')]:
        page.get_by_role('button', name=name + ' · Por responder', exact=True).click()
        page.get_by_label('O que queres experimentar a seguir?').fill(text)
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
    page.get_by_role('button', name='Voltar à atividade', exact=True).click()


def screenshot(page, name):
    if directory := os.environ.get('PAGECRAFT_TICKET_PROOF'):
        page.screenshot(path=str(Path(directory) / name), full_page=True)


@pytest.mark.parametrize('change', ['strategy', 'criterion'])
def test_revising_reflection_preserves_the_saved_step(page, studio_origin, change):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        teacher.post('/api/learning/activities', json={
            'slug': 'fraction-test', 'title': 'Frações', 'year': 2, 'duration': 45,
            'criteria': [{'id': 'iguais', 'pt': 'Reconheço partes iguais.'}]
        }).raise_for_status()
        session = create_session(teacher)
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('')
        if change == 'strategy':
            page.get_by_label('O que te ajudou?').fill('Comparei os blocos.')
        else:
            page.get_by_label('Consegui com ajuda', exact=True).check()
        with page.expect_request(lambda request: request.method == 'POST' and request.url.endswith('/groups/me/reflections')) as sent:
            page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        assert sent.value.post_data_json['expected_revision'] == 1
        assert sent.value.post_data_json['next_step'] == 'Comparar as metades.'
        records = page.request.get(studio_origin + '/api/sessions/' + session['id'] + '/groups/me/reflections').json()
        voice = records['reflections'][list(session['roster'])[0]]['payload']
        assert voice['next_step'] == 'Comparar as metades.'
        assert voice['revision'] == 2
        if change == 'strategy':
            assert voice['strategy'] == 'Comparei os blocos.'
        else:
            assert voice['answers'] == {'iguais': 'help'}


@pytest.mark.parametrize('choice', ['keep', 'replace', 'remove'])
def test_step_choice_survives_draft_reload_and_lost_save_response(page, studio_origin, choice):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        path = '/api/sessions/' + session['id']
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        page.get_by_label('O que te ajudou?').fill('Comparei com o meu colega.')
        new_text = 'Comparar terços.' if choice == 'replace' else ''
        expected_step = {'keep': 'Comparar as metades.', 'replace': new_text, 'remove': ''}[choice]
        next_step = page.get_by_label('O que queres experimentar a seguir?')
        withdrawal = page.get_by_label('Quero retirar o passo guardado', exact=True)
        if choice == 'remove':
            next_step.fill('Texto ainda por decidir.')
            withdrawal.check()
            expect(next_step).to_be_disabled()
            withdrawal.uncheck()
            expect(next_step).to_be_enabled()
            expect(next_step).to_have_value('Texto ainda por decidir.')
        next_step.fill(new_text)
        if choice == 'remove':
            withdrawal.check()
        page.get_by_role('button', name='Bruno · Guardada', exact=True).click()
        expect(withdrawal).not_to_be_checked()
        expect(next_step).to_have_value('')
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        expect(withdrawal).to_be_checked(checked=choice == 'remove')
        page.reload()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        expect(next_step).to_have_value(new_text)
        expect(withdrawal).to_be_checked(checked=choice == 'remove')
        expect(page.locator('#reflection-previous-step')).to_have_text('Comparar as metades.')
        lost = []

        def lose_response(route):
            lost.append(route.request.post_data_json)
            route.fetch()
            route.abort()

        page.route('**/groups/me/reflections', lose_response, times=1)
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Não foi possível guardar')
        assert lost[0]['next_step'] == expected_step
        assert lost[0]['expected_revision'] == 1
        page.reload()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        expect(next_step).to_have_value(new_text)
        expect(next_step).to_be_disabled()
        with page.expect_request(lambda request: request.method == 'POST' and request.url.endswith('/groups/me/reflections')) as retried:
            page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        assert retried.value.post_data_json == lost[0]
        history = teacher.get(path + '/students/' + list(session['roster'])[0] + '/history').json()['events']
        voices = [event['payload'] for event in history if event['type'] == 'individual_reflection']
        assert [(voice['revision'], voice['next_step']) for voice in voices] == [
            (1, 'Comparar as metades.'), (2, expected_step)
        ]
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        ticket = page.locator('#return-ticket')
        if choice == 'remove':
            expect(ticket.get_by_role('button', name='Ana', exact=True)).to_have_count(0)
        else:
            ticket.get_by_role('button', name='Ana', exact=True).click()
            expect(page.locator('#return-ticket-text')).to_have_text(expected_step)


@pytest.mark.parametrize('choice', ['keep', 'replace', 'remove'])
def test_step_choice_conflict_requires_review_of_the_saved_revision(page, studio_origin, choice):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        endpoint = studio_origin + '/api/sessions/' + session['id'] + '/groups/me/reflections'
        student_id = list(session['roster'])[0]
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        page.get_by_label('O que te ajudou?').fill('A minha revisão local.')
        if choice == 'replace':
            page.get_by_label('O que queres experimentar a seguir?').fill('O meu novo passo local.')
        elif choice == 'remove':
            page.get_by_label('Quero retirar o passo guardado', exact=True).check()
        # A concurrent, authorized save makes the local draft's revision stale.
        response = page.request.post(endpoint, data={
            'student_id': student_id, 'event_id': 'concurrent-step', 'expected_revision': 1,
            'answers': {}, 'strategy': 'Outra revisão guardada.', 'next_step': 'Experimentar quartos.'
        })
        assert response.ok
        page.reload()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        with page.expect_request(lambda request: request.method == 'POST' and request.url.endswith('/groups/me/reflections')) as sent:
            page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.get_by_role('button', name='Rever versão guardada', exact=True)).to_be_visible()
        expect(page.locator('#reflection-status')).not_to_contain_text('A guardar')
        assert sent.value.post_data_json['expected_revision'] == 1
        assert sent.value.post_data_json['next_step'] == {
            'keep': 'Comparar as metades.', 'replace': 'O meu novo passo local.', 'remove': ''
        }[choice]
        assert page.request.get(endpoint).json()['reflections'][student_id]['payload']['revision'] == 2
        page.get_by_role('button', name='Rever versão guardada', exact=True).click()
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('')
        expect(page.get_by_label('Quero retirar o passo guardado', exact=True)).not_to_be_checked()
        expect(page.locator('#reflection-previous-step')).to_have_text('Experimentar quartos.')
        page.get_by_label('O que te ajudou?').fill('Revi a versão guardada.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        voice = page.request.get(endpoint).json()['reflections'][student_id]['payload']
        assert (voice['revision'], voice['next_step'], voice['strategy']) == (
            3, 'Experimentar quartos.', 'Revi a versão guardada.'
        )


def test_saved_intentions_are_read_only_and_separate_from_new_step(page, studio_origin):
    from playwright.sync_api import expect
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        path = '/api/sessions/' + session['id']
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        page.reload()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        screenshot(page, 'atividade.png')
        expect(page.get_by_role('button', name='O meu próximo passo', exact=True)).to_be_visible()
        expect(page.locator('#return-ticket')).to_be_hidden()
        before = page.request.get(studio_origin + path + '/groups/me/history').json()['events']
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_be_hidden()
        ticket = page.locator('#return-ticket')
        ticket.get_by_role('button', name='Ana', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_have_text('Comparar as metades.')
        expect(page.locator('#return-ticket-child')).to_have_text('O próximo passo de Ana')
        ticket.get_by_role('button', name='Bruno', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_have_text('Experimentar quartos.')
        expect(ticket).not_to_contain_text('Comparar as metades.')
        screenshot(page, 'bilhete-bruno.png')
        page.get_by_role('button', name='Voltar ao trabalho', exact=True).click()
        expect(ticket).to_be_hidden()
        expect(page.get_by_role('button', name='O meu próximo passo', exact=True)).to_be_focused()
        after = page.request.get(studio_origin + path + '/groups/me/history').json()['events']
        assert after == before

        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Comparar as metades.')
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('')
        screenshot(page, 'reflexao.png')
        page.get_by_label('O que queres experimentar a seguir?').fill('Comparar terços.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        # The previous intention stays fixed for this opening, including child switches.
        page.get_by_role('button', name='Bruno · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Experimentar quartos.')
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('')
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Comparar as metades.')
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('')
        # A second edit in this opening keeps the CURRENT intention, not the frozen reference.
        page.get_by_label('O que te ajudou?').fill('Revimos as partes iguais.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Comparar terços.')
        history = teacher.get(path + '/students/' + list(session['roster'])[0] + '/history').json()['events']
        assert [event['payload']['next_step'] for event in history if event['type'] == 'individual_reflection'] == [
            'Comparar as metades.', 'Comparar terços.', 'Comparar terços.'
        ]
        assert not errors


def test_resume_and_composition_change_require_a_fresh_name_choice(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        path = '/api/sessions/' + session['id']
        ids = list(session['roster'])
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        teacher.post(path + '/close').raise_for_status()
        resumed = teacher.post(path + '/resume').json()
        other = page.context.browser.new_context()
        try:
            next_day = other.new_page()
            next_day.goto(studio_origin + '/student/')
            next_day.get_by_label('Código da aula ou do grupo').fill(resumed['group_codes'][0]['code'])
            next_day.get_by_role('button', name='Entrar', exact=True).click()
            expect(next_day.locator('#activity-frame')).to_be_visible(timeout=15000)
            next_day.get_by_role('button', name='O meu próximo passo', exact=True).click()
            ticket = next_day.locator('#return-ticket')
            ticket.get_by_role('button', name='Bruno', exact=True).click()
            expect(next_day.locator('#return-ticket-text')).to_have_text('Experimentar quartos.')
            group = next_day.request.get(studio_origin + path + '/me').json()['work_group']
            next_day.evaluate('''() => {
              const fetchActual = window.fetch.bind(window);
              let first = true;
              const gate = new Promise(resolve => window.releaseOldComposition = resolve);
              window.fetch = async (...args) => {
                const response = await fetchActual(...args);
                if (first && String(args[0]).endsWith('/groups/me/reflections')) {
                  first = false;
                  const jsonActual = response.json.bind(response);
                  response.json = async () => {
                    const data = await jsonActual(); window.oldCompositionWaiting = true;
                    await gate; window.oldCompositionReleased = true; return data;
                  };
                }
                return response;
              };
            }''')
            next_day.get_by_role('button', name='A minha reflexão', exact=True).click()
            next_day.wait_for_function('window.oldCompositionWaiting === true')
            teacher.patch(path + f"/groups/{group['id']}/participants", json={
                'participant_ids': [ids[0], ids[2]], 'mode': 'pair'
            }).raise_for_status()
            expect(next_day.locator('#student-name')).to_have_text('Ana + Carla', timeout=10000)
            expect(ticket).to_be_hidden()
            expect(next_day.locator('#return-ticket-text')).to_have_text('')
            next_day.get_by_role('button', name='O meu próximo passo', exact=True).click()
            next_day.evaluate('window.releaseOldComposition()')
            next_day.wait_for_function('window.oldCompositionReleased === true')
            expect(ticket).to_be_visible()
            expect(ticket.get_by_role('button', name='Bruno', exact=True)).to_have_count(0)
            expect(ticket.get_by_role('button', name='Carla', exact=True)).to_have_count(0)
            expect(next_day.locator('#return-ticket-text')).to_be_hidden()
            ticket.get_by_role('button', name='Ana', exact=True).click()
            expect(next_day.locator('#return-ticket-text')).to_have_text('Comparar as metades.')
            # Revoking access invalidates even an already open ticket.
            teacher.post(path + '/release/' + ids[0], json={}).raise_for_status()
            expect(next_day.locator('#step-code')).to_be_visible(timeout=10000)
            expect(ticket).to_be_hidden()
            expect(next_day.locator('#return-ticket-text')).to_have_text('')
        finally:
            other.close()


def test_missing_intention_and_read_failure_leave_the_activity_available(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        enter_pair(page, studio_origin, session['join_code'])
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(page.get_by_role('button', name='O meu próximo passo', exact=True)).to_be_hidden()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por responder', exact=True).click()
        expect(page.locator('#reflection-previous')).to_be_hidden()
        page.get_by_label('O que queres experimentar a seguir?').fill('   ')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        page.get_by_role('button', name='Bruno · Por responder', exact=True).click()
        page.get_by_role('button', name='Prefiro não responder agora', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.reload()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(page.get_by_role('button', name='O meu próximo passo', exact=True)).to_be_hidden()
        page.route('**/groups/me/reflections', lambda route: route.abort())
        page.reload()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(page.get_by_role('button', name='O meu próximo passo', exact=True)).to_be_hidden()
        # A failed optional read must not stop actual activity controls.
        page.frame_locator('#activity-frame').get_by_role('button', name='Cortar ao meio', exact=True).click()
        page.frame_locator('#activity-frame').get_by_role('button', name='Sim', exact=True).click()


def test_late_read_and_local_draft_cannot_replace_a_saved_intention(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        session = create_session(teacher)
        enter_pair(page, studio_origin, session['join_code'])
        save_intentions(page)
        # Hold the first real server response after reload. Newer reads and saves proceed normally.
        page.add_init_script('''(() => {
          const fetchActual = window.fetch.bind(window);
          let first = true;
          const bodyGate = new Promise(resolve => window.releaseTicketRead = resolve);
          window.fetch = async (...args) => {
            const response = await fetchActual(...args);
            if (first && String(args[0]).endsWith('/groups/me/reflections') && !args[1]?.method) {
              first = false;
              const jsonActual = response.json.bind(response);
              response.json = async () => {
                const data = await jsonActual(); window.ticketReadWaiting = true;
                await bodyGate; window.ticketReadReleased = true; return data;
              };
            }
            return response;
          };
        })();''')
        page.reload()
        page.wait_for_function('window.ticketReadWaiting === true')
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        page.get_by_label('O que queres experimentar a seguir?').fill('Testar oitavos.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada.')
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        ticket = page.locator('#return-ticket')
        ticket.get_by_role('button', name='Ana', exact=True).click()
        page.evaluate('window.releaseTicketRead()')
        page.wait_for_function('window.ticketReadReleased === true')
        expect(ticket).to_be_visible()
        expect(page.locator('#return-ticket-text')).to_have_text('Testar oitavos.')
        page.get_by_role('button', name='Voltar ao trabalho', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Testar oitavos.')
        page.get_by_label('O que queres experimentar a seguir?').fill('Ainda só um rascunho.')
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        ticket.get_by_role('button', name='Ana', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_have_text('Testar oitavos.')
        # Reload keeps the local draft editable, but references only the saved server value.
        page.reload()
        page.wait_for_function('window.ticketReadWaiting === true')
        page.evaluate('window.releaseTicketRead()')
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        ticket.get_by_role('button', name='Ana', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_have_text('Testar oitavos.')
        page.get_by_role('button', name='Voltar ao trabalho', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Testar oitavos.')
        expect(page.get_by_label('O que queres experimentar a seguir?')).to_have_value('Ainda só um rascunho.')
        # Reading an intention cannot bypass the separate gate for restoring actual work.
        page.route('**/groups/me/history', lambda route: route.fulfill(status=503, body='{}'))
        page.reload()
        page.wait_for_function('window.ticketReadWaiting === true')
        page.evaluate('window.releaseTicketRead()')
        expect(page.locator('#restore-status')).to_contain_text('Não foi possível recuperar')
        page.get_by_role('button', name='O meu próximo passo', exact=True).click()
        ticket.get_by_role('button', name='Ana', exact=True).click()
        expect(page.locator('#return-ticket-text')).to_have_text('Testar oitavos.')
        expect(page.locator('#activity-frame')).to_be_hidden()
        page.unroute('**/groups/me/history')
        page.get_by_role('button', name='Tentar recuperar novamente', exact=True).click()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
