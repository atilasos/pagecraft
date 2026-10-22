"""Refused work keeps its original authors while later groups can continue."""
from contextlib import contextmanager

import httpx
import pytest

expect = pytest.importorskip('playwright.sync_api').expect


@contextmanager
def classroom(page, origin, pair=True):
    with httpx.Client(base_url=origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        cls = teacher.post('/api/classes', json={
            'name': 'Recusas por composição', 'year': 4, 'students': ['Ana', 'Bruno', 'Carla']
        }).json()
        session = teacher.post('/api/sessions', json={
            'class_id': cls['id'], 'activity_slug': 'canva-animais-4ano'
        }).json()
        page.goto(origin + '/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        if pair:
            page.get_by_role('button', name='A pares', exact=True).click()
        for name in ['Ana', 'Bruno'] if pair else ['Ana']:
            page.get_by_role('button', name=name, exact=True).click()
        page.get_by_role('button', name='Começar', exact=True).click()
        expect(page.locator('#activity-frame')).to_be_visible()
        expect(page.locator('#save-work')).to_be_enabled()
        yield teacher, session, '/api/sessions/' + session['id']


def stored(page):
    return page.evaluate("""() => {
        const key = Object.keys(sessionStorage).find(key =>
            /pc-(group|student)-outbox:/.test(key) && !key.endsWith(':status'));
        return {key, events:JSON.parse(sessionStorage.getItem(key)),
            status:JSON.parse(sessionStorage.getItem(key + ':status'))};
    }""")


def overflow(page):
    expect(page.locator('#activity-frame')).to_be_visible()
    expect(page.locator('#save-work')).to_be_enabled()
    page.route('**/events', lambda route: route.fulfill(status=503, body='{}'))
    # Actual UI handlers create every event. No fabricated bridge messages.
    page.evaluate("() => { for (let i=0;i<205;i++) document.querySelector('#help-btn').click(); }")
    expect(page.locator('#queue-status')).to_contain_text('alterações ficaram de fora')
    assert len([event for event in stored(page)['events'] if not event.get('composition_conflict')]) == 200


def save(page, text):
    page.get_by_role('button', name='Guardar para continuar', exact=True).click()
    expect(page.locator('#save-work-status')).to_contain_text(text)


def answer(page, value):
    page.frame_locator('#activity-frame').locator('#animals').fill(value)
    page.frame_locator('#activity-frame').locator('#animals').press('Tab')


def refusal_items(page):
    return page.locator('#pending-group-list li').filter(has_text='alterações ficaram de fora')


def test_repeated_compositions_preserve_each_refusal_and_only_review_current(page, studio_origin):
    with classroom(page, studio_origin) as (teacher, session, path):
        ids = list(session['roster'])
        group = page.request.get(studio_origin + path + '/me').json()['work_group']
        overflow(page)
        first = stored(page)

        def change(participants, name):
            current = page.request.get(studio_origin + path + '/me').json()['work_group']
            teacher.patch(path + f"/groups/{current['id']}/participants", json={
                'participant_ids': participants, 'mode': 'pair'
            }).raise_for_status()
            expect(page.locator('#student-name')).to_have_text(name, timeout=10000)
            expect(page.locator('#queue-notice')).to_be_hidden()

        change([ids[0], ids[2]], 'Ana + Carla')
        expect(refusal_items(page)).to_have_count(1)
        page.reload()
        expect(refusal_items(page)).to_contain_text('Ana + Bruno')
        overflow(page)
        second = stored(page)
        assert len(second['status']['refusals']) == 2
        assert second['status']['refusals'][0]['participant_ids'] == [ids[0], ids[1]]
        assert second['status']['refusals'][1]['participant_ids'] == [ids[0], ids[2]]

        # Returning to the same names is a new composition, not permission to
        # replay or silently dismiss either earlier refusal.
        change([ids[0], ids[1]], 'Ana + Bruno')
        expect(refusal_items(page)).to_have_count(2)
        page.reload()
        overflow(page)
        page.unroute('**/events')
        save(page, 'não foi possível guardar tudo')
        expect(page.locator('#queue-status')).to_contain_text('alterações ficaram de fora')
        assert all(event.get('composition_conflict') for event in stored(page)['events'])
        answer(page, 'Recusada até à revisão explícita')
        save(page, 'não foi possível guardar tudo')
        history = teacher.get(path + f'/students/{ids[0]}/history').json()['events']
        assert not any(event.get('payload', {}).get('detail', {}).get('value') ==
                       'Recusada até à revisão explícita' for event in history)
        page.reload()
        expect(page.locator('#queue-status')).to_contain_text('alterações ficaram de fora')
        page.get_by_role('button', name='Voltar ao último trabalho aceite', exact=True).click()
        expect(page.locator('#save-work')).to_be_enabled()
        expect(page.locator('#queue-notice')).to_be_hidden()
        expect(refusal_items(page)).to_have_count(2)
        assert stored(page)['status']['refusals'] == second['status']['refusals']
        # All original accepted events remain byte-for-byte, only marked old.
        old_by_id = {event['event_id']: event for event in stored(page)['events']}
        for event in first['events']:
            assert old_by_id[event['event_id']] == {**event, 'composition_conflict': True}

        # Lose actual server responses until reconnection, so a timer cannot
        # acknowledge a retry before the explicit save observes the outage.
        def lose_response(route):
            route.fetch()
            route.abort()
        page.route('**/events', lose_response)
        answer(page, 'Novo trabalho com Bruno')
        save(page, 'não foi possível guardar tudo')
        page.reload()
        expect(page.frame_locator('#activity-frame').locator('#animals')).to_have_value('Novo trabalho com Bruno')
        page.unroute('**/events')
        save(page, 'Trabalho atual guardado')
        history = teacher.get(path + f'/students/{ids[1]}/history').json()['events']
        answers = [event for event in history if event.get('payload', {}).get('detail', {}).get('value') == 'Novo trabalho com Bruno']
        assert len(answers) == 1
        assert answers[0]['participant_ids'] == [ids[0], ids[1]]
        current = page.request.get(studio_origin + path + '/me').json()['work_group']
        assert current['composition_version'] > group['composition_version']
        assert answers[0]['work_group_id'] == current['id']
        carla = teacher.get(path + f'/students/{ids[2]}/history').json()['events']
        assert not any(event['type'] == 'assessment_result' for event in carla)
        expect(refusal_items(page)).to_have_count(2)
        page.screenshot(path='/tmp/pagecraft-fila-ronda2-composicoes.png', full_page=True)


def test_access_renewal_archives_refusal_even_after_accepted_queue_drains(page, studio_origin):
    with classroom(page, studio_origin) as (teacher, session, path):
        old = page.request.get(studio_origin + path + '/me').json()['work_group']
        overflow(page)
        page.unroute('**/events')
        save(page, 'não foi possível guardar tudo')
        assert stored(page)['events'] == []
        refusal = stored(page)['status']['refusals'][0]
        # A fresh access code revokes the old cookie; re-enter on the same tab.
        code = teacher.post(path + f"/groups/{old['id']}/access-code").json()['code']
        page.reload()
        expect(page.locator('#step-code')).to_be_visible()
        page.get_by_label('Código da aula').fill(code)
        page.get_by_role('button', name='Entrar', exact=True).click()
        expect(page.locator('#activity-frame')).to_be_visible()
        expect(page.locator('#save-work')).to_be_enabled()
        current = page.request.get(studio_origin + path + '/me').json()['work_group']
        assert current['composition_version'] == old['composition_version']
        assert current['access_version'] > old['access_version']
        expect(page.locator('#queue-notice')).to_be_hidden()
        expect(refusal_items(page)).to_contain_text('Ana + Bruno')
        expect(refusal_items(page)).not_to_contain_text('composição')
        expect(refusal_items(page)).not_to_contain_text('acesso')
        assert refusal['scope'] == {'device_id': old['device_id'],
                                   'composition_version': old['composition_version'],
                                   'access_version': old['access_version']}
        assert refusal['refused_at']
        page.reload()
        expect(refusal_items(page)).to_be_visible()
        answer(page, 'Resposta na entrada renovada')
        save(page, 'Trabalho atual guardado')
        assert stored(page)['status']['refusals'] == [refusal]
        history = page.request.get(studio_origin + path + '/groups/me/history').json()['events']
        answers = [event for event in history if event.get('payload', {}).get('detail', {}).get('value') == 'Resposta na entrada renovada']
        assert len(answers) == 1
        assert answers[0]['work_group_id'] == current['id']
        page.screenshot(path='/tmp/pagecraft-fila-ronda2-acesso.png', full_page=True)


def test_legacy_refusal_cannot_be_attributed_to_the_only_remaining_old_queue(page, studio_origin):
    with classroom(page, studio_origin) as (teacher, session, path):
        ids = list(session['roster'])
        group = page.request.get(studio_origin + path + '/me').json()['work_group']
        page.route('**/events', lambda route: route.fulfill(status=503, body='{}'))
        page.get_by_role('button', name='Preciso de ajuda', exact=False).click()
        accepted_a = stored(page)['events']
        assert accepted_a
        teacher.patch(path + f"/groups/{group['id']}/participants", json={
            'participant_ids': [ids[0], ids[2]], 'mode': 'pair'
        }).raise_for_status()
        expect(page.locator('#student-name')).to_have_text('Ana + Carla', timeout=10000)
        overflow(page)
        page.unroute('**/events')
        save(page, 'não foi possível guardar tudo')
        remaining = stored(page)
        assert {event['event_id'] for event in remaining['events']} == {event['event_id'] for event in accepted_a}
        assert all(event['composition_version'] == group['composition_version'] for event in remaining['events'])
        assert remaining['status']['refusals'][0]['work_group_name'] == 'Ana + Carla'

        # Old clients persisted only true, after B drained and only A remained.
        # The unanimous A queue is not evidence that A made the refused edits.
        page.goto(studio_origin + '/api/health')
        page.evaluate("key => sessionStorage.setItem(key + ':status', JSON.stringify({refusedWork:true}))", remaining['key'])
        page.goto(studio_origin + '/student/')
        expect(page.locator('#activity-frame')).to_be_visible()
        answer(page, 'Alteração de Carla ainda recusada')
        save(page, 'não foi possível guardar tudo')
        expect(page.locator('#queue-status')).to_contain_text('contexto')
        expect(refusal_items(page)).to_have_count(0)
        assert stored(page)['status']['refusals'] == [{'scope': None, 'context_unknown': True}]
        history = teacher.get(path + f'/students/{ids[2]}/history').json()['events']
        assert not any(event.get('payload', {}).get('detail', {}).get('value') ==
                       'Alteração de Carla ainda recusada' for event in history)
        page.reload()
        expect(page.locator('#queue-status')).to_contain_text('contexto')
        page.get_by_role('button', name='Voltar ao último trabalho aceite', exact=True).click()
        expect(page.locator('#activity-frame')).to_be_visible()
        expect(page.locator('#queue-notice')).to_be_hidden()
        assert [event for event in stored(page)['events'] if event.get('composition_conflict')] == remaining['events']
        answer(page, 'Carla depois da revisão')
        save(page, 'Guardado.')
        history = teacher.get(path + f'/students/{ids[2]}/history').json()['events']
        answers = [event for event in history if event.get('payload', {}).get('detail', {}).get('value') == 'Carla depois da revisão']
        assert len(answers) == 1 and answers[0]['participant_ids'] == [ids[0], ids[2]]


@pytest.mark.parametrize('pair,drain', [(True, False), (True, True), (False, True)],
                         ids=['unanimous-old-queue', 'empty-group-queue', 'individual'])
def test_legacy_refused_status_is_migrated_conservatively(page, studio_origin, pair, drain):
    with classroom(page, studio_origin, pair) as (teacher, session, path):
        overflow(page)
        if drain:
            page.unroute('**/events')
            save(page, 'não foi possível guardar tudo')
            assert not stored(page)['events']
        # Simulate only the persisted status format of the previous client.
        # All evidence still comes from actual controls and HTTP requests.
        page.goto(studio_origin + '/api/health')
        key = stored(page)['key']
        page.evaluate("key => sessionStorage.setItem(key + ':status', JSON.stringify({refusedWork:true}))", key)
        if pair:
            group = page.request.get(studio_origin + path + '/me').json()['work_group']
            ids = list(session['roster'])
            teacher.patch(path + f"/groups/{group['id']}/participants", json={
                'participant_ids': [ids[0], ids[2]], 'mode': 'pair'
            }).raise_for_status()
        page.goto(studio_origin + '/student/')
        expect(page.locator('#activity-frame')).to_be_visible()
        expect(page.locator('#save-work')).to_be_enabled()
        if not drain:
            page.unroute('**/events')
        expect(page.locator('#queue-status')).to_contain_text('alterações ficaram de fora')
        expect(page.locator('#queue-status')).to_contain_text('contexto')
        expect(refusal_items(page)).to_have_count(0)
        answer(page, 'Ainda recusada')
        save(page, 'não foi possível guardar tudo')
        assert stored(page)['status']['refusals'] == [{'scope': None, 'context_unknown': True}]
        page.reload()
        expect(page.locator('#queue-status')).to_contain_text('alterações ficaram de fora')
        page.get_by_role('button', name='Voltar ao último trabalho aceite', exact=True).click()
        expect(page.locator('#save-work')).to_be_enabled()
        expect(page.locator('#queue-notice')).to_be_hidden()
        save(page, 'Guardado.')
