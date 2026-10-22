"""Studio outbox: real activity, dropped event requests and disposable identities."""
from contextlib import contextmanager

import httpx
import pytest
from playwright.sync_api import expect


@contextmanager
def classroom(origin):
    with httpx.Client(base_url=origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        group = teacher.post('/api/classes', json={
            'name': 'Fila individual', 'year': 4, 'students': ['Ana', 'Bruno']
        }).json()
        session = teacher.post('/api/sessions', json={
            'class_id': group['id'], 'activity_slug': 'canva-animais-4ano'
        }).json()
        yield teacher, session, '/api/sessions/' + session['id']


def enter(page, origin, session, pair=False):
    page.goto(origin + '/student/')
    page.get_by_label('Código da aula ou do grupo').fill(session['join_code'])
    page.get_by_role('button', name='Entrar', exact=True).click()
    if pair:
        page.get_by_role('button', name='A pares', exact=True).click()
    page.get_by_role('button', name='Ana', exact=True).click()
    if pair:
        page.get_by_role('button', name='Bruno', exact=True).click()
    page.get_by_role('button', name='Começar', exact=True).click()
    expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)


def queue_data(page):
    return page.evaluate("""() => Object.entries(sessionStorage)
        .filter(([key]) => /pc-(student|group)-outbox:/.test(key) && !key.endsWith(':status'))
        .map(([key, value]) => [key, JSON.parse(value)])""")


def test_individual_reload_retries_same_evidence_once(page, studio_origin):
    with classroom(studio_origin) as (teacher, session, path):
        enter(page, studio_origin, session)
        identity = page.request.get(studio_origin + path + '/me').json()
        page.route('**/events', lambda route: route.abort('internetdisconnected'))
        lesson = page.frame_locator('#activity-frame')
        lesson.locator('#animals').fill('Golfinho e tartaruga, sem rede')
        lesson.locator('#animals').press('Tab')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('não foi possível guardar tudo')
        queues = queue_data(page)
        assert len(queues) == 1, 'Individual work needs a persistent outbox'
        accepted = queues[0][1]
        # Same pending event twice in storage and server history must still restore/send once.
        event = next(e for e in accepted if e.get('payload', {}).get('detail', {}).get('field') == 'animals')
        result = page.request.post(studio_origin + path + '/events', data={'events': [event]})
        assert result.ok
        page.evaluate('([key, events]) => sessionStorage.setItem(key, JSON.stringify(events))',
                      [queues[0][0], accepted + [event]])
        page.reload()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(lesson.locator('#animals')).to_have_value('Golfinho e tartaruga, sem rede')
        restored = queue_data(page)[0][1]
        assert len({e['event_id'] for e in restored}) == len(restored)
        page.unroute('**/events')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('Guardado.')
        history = teacher.get(path + '/students/' + identity['student_id'] + '/history').json()['events']
        matching = [e for e in history if e.get('event_id') == event['event_id']]
        assert len(matching) == 1
        assert matching[0]['student_id'] == identity['student_id']
        assert not queue_data(page)[0][1]


@pytest.mark.parametrize('pair', [False, True], ids=['individual', 'group'])
def test_overflow_preserves_accepted_work_and_never_claims_everything_saved(page, studio_origin, pair):
    with classroom(studio_origin) as (_, session, path):
        enter(page, studio_origin, session, pair)
        page.route('**/events', lambda route: route.abort('internetdisconnected'))
        page.frame_locator('#activity-frame').locator('#animals').fill('Primeiro trabalho aceite')
        page.frame_locator('#activity-frame').locator('#animals').press('Tab')
        # Exercise the real iframe bridge, beyond the 200-event boundary.
        lesson = page.frames[1]
        lesson.evaluate("""() => {
          for (let i = 0; i < 205; i++) parent.postMessage({pagecraft:1, type:'attempt',
            unitId:'overflow-' + i, payload:{correct:false}}, '*');
        }""")
        expect(page.locator('#queue-status')).to_contain_text('fila está cheia')
        accepted = queue_data(page)[0][1]
        assert len(accepted) == 200
        assert any(e.get('payload', {}).get('detail', {}).get('value') == 'Primeiro trabalho aceite' for e in accepted)
        page.reload()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(page.locator('#queue-status')).to_contain_text('ficaram de fora')
        expect(page.frame_locator('#activity-frame').locator('#animals')).to_have_value('Primeiro trabalho aceite')
        page.unroute('**/events')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('não foi possível guardar tudo')
        assert not queue_data(page)[0][1]
        expect(page.locator('#queue-status')).to_contain_text('ficaram de fora')
        page.get_by_role('button', name='Voltar ao último trabalho aceite', exact=True).click()
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(page.locator('#queue-status')).to_be_hidden()
        expect(page.frame_locator('#activity-frame').locator('#animals')).to_have_value('Primeiro trabalho aceite')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('Guardado.')


@pytest.mark.parametrize('same_child', [False, True], ids=['other-child', 'new-claim-same-child'])
def test_reload_never_restores_another_identity_version(page, studio_origin, same_child):
    with classroom(studio_origin) as (teacher, session, path):
        enter(page, studio_origin, session)
        before = page.request.get(studio_origin + path + '/me').json()
        page.route('**/events', lambda route: route.abort('internetdisconnected'))
        lesson = page.frame_locator('#activity-frame')
        lesson.locator('#animals').fill('Só pertence à entrada antiga')
        lesson.locator('#animals').press('Tab')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('não foi possível guardar tudo')
        old_key, old_events = queue_data(page)[0]
        # Leave the activity before the teacher releases it, as with a closed
        # tab being reopened. Its SSE must not clear the remembered session.
        page.goto(studio_origin + '/api/health')
        teacher.post(path + '/release/' + before['student_id']).raise_for_status()
        # Release revokes the previous cookie before any new identity is chosen.
        assert page.request.get(studio_origin + path + '/me').status == 401
        sid = before['student_id'] if same_child else next(sid for sid in session['roster'] if sid != before['student_id'])
        claim = page.request.post(studio_origin + path + '/claim', data={'student_id': sid})
        assert claim.ok
        assert claim.json()['identity_version'] != before['identity_version']
        page.unroute('**/events')
        page.goto(studio_origin + '/student/')
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        expect(lesson.locator('#animals')).to_have_value('')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('Guardado.')
        assert dict(queue_data(page))[old_key] == old_events
        assert len(queue_data(page)) == 2
        for student_id in session['roster']:
            events = teacher.get(path + '/students/' + student_id + '/history').json()['events']
            assert not any(e.get('payload', {}).get('detail', {}).get('value') == 'Só pertence à entrada antiga' for e in events)


def test_live_cookie_change_keeps_old_queue_without_sending_as_new_child(page, studio_origin):
    with classroom(studio_origin) as (teacher, session, path):
        enter(page, studio_origin, session)
        original = page.request.get(studio_origin + path + '/me').json()
        page.route('**/events', lambda route: route.abort('internetdisconnected'))
        lesson = page.frame_locator('#activity-frame')
        lesson.locator('#animals').fill('Trabalho de Ana por enviar')
        lesson.locator('#animals').press('Tab')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_contain_text('não foi possível guardar tudo')
        old_key, old_events = queue_data(page)[0]
        bruno = next(sid for sid in session['roster'] if sid != original['student_id'])
        assert page.request.post(studio_origin + path + '/claim', data={'student_id': bruno}).ok
        page.unroute('**/events')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#step-code')).to_be_visible()
        assert dict(queue_data(page))[old_key] == old_events
        events = teacher.get(path + '/students/' + bruno + '/history').json()['events']
        assert not any(e.get('payload', {}).get('detail', {}).get('value') == 'Trabalho de Ana por enviar' for e in events)
