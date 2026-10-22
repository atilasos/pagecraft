"""A saved intention is an optional, read-only reminder with explicit authorship."""
import os
from pathlib import Path

import httpx


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


def test_saved_intentions_are_read_only_and_separate_from_new_step(page, studio_origin):
    from playwright.sync_api import expect
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
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.locator('#reflection-previous-step')).to_have_text('Comparar terços.')
        history = teacher.get(path + '/students/' + list(session['roster'])[0] + '/history').json()['events']
        assert [event['payload']['next_step'] for event in history if event['type'] == 'individual_reflection'] == [
            'Comparar as metades.', 'Comparar terços.'
        ]


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
            teacher.patch(path + f"/groups/{group['id']}/participants", json={
                'participant_ids': [ids[0], ids[2]], 'mode': 'pair'
            }).raise_for_status()
            expect(next_day.locator('#student-name')).to_have_text('Ana + Carla', timeout=10000)
            expect(ticket).to_be_hidden()
            expect(next_day.locator('#return-ticket-text')).to_have_text('')
            next_day.get_by_role('button', name='O meu próximo passo', exact=True).click()
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
