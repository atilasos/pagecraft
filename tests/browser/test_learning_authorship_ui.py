"""Shared cookies must not transfer a permanent realization's authorship."""
import pytest

from test_learning_recovery import open_preview


def start_tab(page, origin, name):
    page.get_by_label('Como te chamas?').fill(name)
    page.get_by_role('button', name='Começar', exact=True).click()
    page.locator('#work').wait_for(state='visible')
    page.wait_for_load_state('networkidle')
    return page.request.get(origin + '/api/learning/me').json()


def two_realizations(page, origin):
    code = open_preview(page, origin)
    first = start_tab(page, origin, 'Aluno A')
    second_tab = page.context.new_page()
    second_tab.goto(origin + '/' + code)
    second_tab.get_by_role('button', name='Trocar de aluno', exact=True).click()
    second = start_tab(second_tab, origin, 'Aluno B')
    assert first['id'] != second['id']
    return first, second, second_tab


@pytest.mark.parametrize('action', ['events', 'feedback', 'finish', 'leave'])
def test_stale_actions_preserve_other_tab_and_pending_work(page, studio_origin, action):
    from playwright.sync_api import expect

    first, second, second_tab = two_realizations(page, studio_origin)
    before = page.request.get(studio_origin + '/api/learning/me').json()
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.locator('#strategy').fill('Reflexão A por guardar')
    if action == 'events':
        page.get_by_role('button', name='Voltar à atividade', exact=True).click()
        with page.expect_response(lambda r: r.url.endswith('/me/events')) as response:
            page.frame_locator('#lesson').locator('#animals').fill('Resposta antiga A')
            page.frame_locator('#lesson').locator('#animals').press('Tab')
    elif action == 'feedback':
        page.frame_locator('#lesson').locator('body').evaluate('''() => {
          window.receivedFeedback = [];
          window.addEventListener('message', event => {
            if (event.data?.type === 'ai_feedback') window.receivedFeedback.push(event.data);
          });
        }''')
        with page.expect_response(lambda r: r.url.endswith('/me/feedback')) as response:
            page.locator('#lesson').evaluate("""frame => window.dispatchEvent(new MessageEvent('message', {
              source: frame.contentWindow, data: {pagecraft: 1, type: 'feedback_request', unitId: 'u1',
              payload: {request_id: 'hint-A', answer: 'Resposta A'}}
            }))""")
    elif action == 'finish':
        with page.expect_response(lambda r: r.url.endswith('/me/finish')) as response:
            page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    else:
        with page.expect_response(lambda r: r.url.endswith('/me/leave')) as response:
            page.get_by_role('button', name='Trocar de aluno', exact=True).click()
    after = page.request.get(studio_origin + '/api/learning/me').json()
    assert after == before, f'{action}: A alterou ou apagou B (HTTP {response.value.status})'
    assert response.value.status == 409
    expect(page.locator('#status')).to_contain_text('outra realização')
    expect(page.locator('#done')).to_be_hidden()
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-reflection:" + id))', first['id'])['strategy'] == 'Reflexão A por guardar'
    if action == 'events':
        pending = page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id'])
        assert any(e['payload'].get('detail', {}).get('value') == 'Resposta antiga A' for e in pending)
        # Finishing/leaving with a pending queue retries that queue, and cannot
        # clear it or falsely report a completed realization.
        for button in ['Autoavaliar e terminar', 'Guardar e terminar', 'Trocar de aluno']:
            if button == 'Autoavaliar e terminar':
                page.get_by_role('button', name=button, exact=True).click()
                continue
            with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 409):
                page.get_by_role('button', name=button, exact=True).press('Enter')
            expect(page.locator('#status')).to_contain_text('outra realização')
            expect(page.locator('#done')).to_be_hidden()
            assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id']) == pending
    elif action == 'feedback':
        assert page.frame_locator('#lesson').locator('body').evaluate('() => window.receivedFeedback') == []
    # B is still authorized and can save its own response.
    with second_tab.expect_response(lambda r: r.url.endswith('/me/events') and r.ok):
        second_tab.frame_locator('#lesson').locator('#animals').fill('Resposta B')
        second_tab.frame_locator('#lesson').locator('#animals').press('Tab')
    assert page.request.get(studio_origin + '/api/learning/me').json()['id'] == second['id']


def test_reload_conflict_preserves_tab_identity_and_drafts(page, studio_origin):
    from playwright.sync_api import expect

    first, second, _ = two_realizations(page, studio_origin)
    before = page.request.get(studio_origin + '/api/learning/me').json()
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 409):
        page.frame_locator('#lesson').locator('#animals').fill('Resposta pendente A')
        page.frame_locator('#lesson').locator('#animals').press('Tab')
    pending = page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id'])
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.locator('#strategy').fill('Reflexão A por guardar')
    # Queue survives reload, even though the shared cookie now belongs to B.
    page.on('dialog', lambda dialog: dialog.accept())
    page.reload()
    expect(page.locator('#status')).to_contain_text('outra realização')
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#work')).to_be_hidden()
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id']) == pending
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-reflection:" + id))', first['id'])['strategy'] == 'Reflexão A por guardar'
    assert page.request.get(studio_origin + '/api/learning/me').json() == before


def test_known_tab_without_cookie_keeps_pending_drafts_and_does_not_offer_new_entry(page, studio_origin):
    from playwright.sync_api import expect

    open_preview(page, studio_origin)
    first = start_tab(page, studio_origin, 'Aluno A')
    page.route('**/api/learning/me/events', lambda route: route.fulfill(status=503, json={}))
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 503):
        page.frame_locator('#lesson').locator('#animals').fill('Resposta pendente A')
        page.frame_locator('#lesson').locator('#animals').press('Tab')
    pending = page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id'])
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.locator('#strategy').fill('Reflexão A por guardar')
    page.context.clear_cookies(name='pagecraft_realization')
    page.on('dialog', lambda dialog: dialog.accept())
    page.reload()
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#status')).to_contain_text('Não foi possível recuperar o teu trabalho')
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id']) == pending
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-reflection:" + id))', first['id'])['strategy'] == 'Reflexão A por guardar'


@pytest.mark.parametrize('reload', [True, False], ids=['after-reload', 'without-reload'])
def test_completed_realization_with_expired_cookie_can_explicitly_start_new_work(page, studio_origin, reload):
    from playwright.sync_api import expect

    code = open_preview(page, studio_origin)
    first = start_tab(page, studio_origin, 'Aluno A')
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.locator('#strategy').fill('Reflexão concluída A')
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    before = page.request.get(studio_origin + '/api/learning/me').json()
    assert before['completed_at']
    assert page.evaluate('(code) => sessionStorage.getItem("pc-realization:" + code)', code) == first['id']
    assert page.evaluate('(id) => [sessionStorage.getItem("pc-queue:" + id), sessionStorage.getItem("pc-reflection:" + id)]', first['id']) == [None, None]
    # Expire the browser credential; the server must now reject recovery/leave.
    cookie = next(c for c in page.context.cookies() if c['name'] == 'pagecraft_realization')
    page.context.add_cookies([dict(cookie, expires=1)])
    assert page.request.get(studio_origin + '/api/learning/me').status == 401
    if reload:
        page.reload()
        expect(page.locator('#start-form')).to_be_hidden()
        expect(page.get_by_role('button', name='Começar uma nova realização', exact=True)).to_be_visible()
    page.get_by_role('button', name='Começar uma nova realização', exact=True).click()
    expect(page.locator('#start-form')).to_be_visible()
    assert page.evaluate('(code) => sessionStorage.getItem("pc-realization:" + code)', code) is None
    second = start_tab(page, studio_origin, 'Aluno B')
    assert second['id'] != first['id']
    saved = page.request.get(studio_origin + '/api/learning/reports/' + first['id'] + '/download').text()
    assert 'Reflexão concluída A' in saved
    assert before['completed_at'] in saved
