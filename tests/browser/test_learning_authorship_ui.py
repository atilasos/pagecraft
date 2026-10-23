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


@pytest.mark.parametrize('stored_queue,stored_reflection,read_failure', [
    ('[]', '{"answers":{},"strategy":"","next_step":""}', None),
    ('[{"id":"pending-A","type":"attempt","payload":{"answer":"A"}}]', None, None),
    ('[]', '{"answers":{},"strategy":"Reflexão pendente A","next_step":""}', None),
    ('[]', '{"answers":{"compare":"skip"},"strategy":"","next_step":""}', None),
    ('broken', None, None),
    ('{}', None, None),
    ('null', None, None),
    ('[]', 'broken', None),
    ('[]', '{}', None),
    ('[]', 'null', None),
    ('[]', None, 'pc-queue:'),
    ('[]', None, 'pc-reflection:'),
], ids=['empty', 'queued-answer', 'reflection', 'reflection-choice', 'invalid-queue',
        'object-queue', 'null-queue', 'invalid-reflection', 'object-reflection',
        'null-reflection', 'queue-read-error', 'reflection-read-error'])
def test_expired_recovery_only_offers_local_exit_when_storage_proves_no_pending_work(
    page, studio_origin, stored_queue, stored_reflection, read_failure,
):
    from playwright.sync_api import expect

    code = open_preview(page, studio_origin)
    first = start_tab(page, studio_origin, 'Aluno A')
    page.evaluate('''({id, queued, reflection}) => {
      sessionStorage.setItem('pc-queue:' + id, queued);
      if (reflection === null) sessionStorage.removeItem('pc-reflection:' + id);
      else sessionStorage.setItem('pc-reflection:' + id, reflection);
    }''', {'id': first['id'], 'queued': stored_queue, 'reflection': stored_reflection})
    if read_failure:
        page.add_init_script("""(() => {
          const getItem = Storage.prototype.getItem;
          Storage.prototype.getItem = function(key) {
            if (key.startsWith(%r)) throw new Error('Storage unavailable');
            return getItem.call(this, key);
          };
        })()""" % read_failure)
    page.context.clear_cookies(name='pagecraft_realization')
    page.reload()
    expect(page.get_by_role('button', name='Tentar recuperar novamente', exact=True)).to_be_visible()
    expect(page.locator('#start-form')).to_be_hidden()
    safe = stored_queue == '[]' and stored_reflection == '{"answers":{},"strategy":"","next_step":""}' and not read_failure
    if safe:
        expect(page.locator('#recovery-new')).to_be_visible()
        expect(page.locator('#status')).to_contain_text('Não há trabalho pendente')
    else:
        expect(page.locator('#recovery-new')).to_be_hidden()
        expect(page.locator('#status')).to_contain_text('Não foi possível recuperar o teu trabalho')
    # Inspect the actual storage without getItem so read-error cases are checked too.
    state = page.evaluate('(id) => ({...sessionStorage})', first['id'])
    assert state['pc-realization:' + code] == first['id']
    assert state['pc-queue:' + first['id']] == stored_queue
    assert state.get('pc-reflection:' + first['id']) == stored_reflection


@pytest.mark.parametrize('reload', [True, False], ids=['after-reload', 'without-reload'])
def test_completed_tab_with_other_cookie_cannot_offer_or_start_replacement(page, studio_origin, reload):
    from playwright.sync_api import expect

    code = open_preview(page, studio_origin)
    first = start_tab(page, studio_origin, 'Aluno A')
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    second_tab = page.context.new_page()
    second_tab.goto(studio_origin + '/' + code)
    second_tab.get_by_role('button', name='Começar uma nova realização', exact=True).click()
    second = start_tab(second_tab, studio_origin, 'Aluno B')
    before = page.request.get(studio_origin + '/api/learning/me').json()
    if reload:
        page.reload()
    else:
        page.get_by_role('button', name='Começar uma nova realização', exact=True).click()
    expect(page.locator('#status')).to_contain_text('outra realização')
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#recovery-new')).to_be_hidden()
    assert page.evaluate('(code) => sessionStorage.getItem("pc-realization:" + code)', code) == first['id']
    assert page.request.get(studio_origin + '/api/learning/me').json() == before
    with second_tab.expect_response(lambda r: r.url.endswith('/me/events') and r.ok):
        second_tab.frame_locator('#lesson').locator('#animals').fill('Resposta B')
        second_tab.frame_locator('#lesson').locator('#animals').press('Tab')
    assert page.request.get(studio_origin + '/api/learning/me').json()['id'] == second['id']


@pytest.mark.parametrize('pending', ['reflection', 'corruption', 'read-error'])
def test_completed_expired_tab_cannot_leave_when_local_work_is_pending_or_uncertain(page, studio_origin, pending):
    from playwright.sync_api import expect

    code = open_preview(page, studio_origin)
    first = start_tab(page, studio_origin, 'Aluno A')
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    reflection = '{"answers":{},"strategy":"Reflexão pendente A","next_step":""}' if pending == 'reflection' else 'broken'
    page.evaluate('([id, draft]) => sessionStorage.setItem("pc-reflection:" + id, draft)', [first['id'], reflection])
    if pending == 'read-error':
        page.evaluate("""() => {
          const getItem = Storage.prototype.getItem;
          Storage.prototype.getItem = function(key) {
            if (key.startsWith('pc-reflection:')) throw new Error('Storage unavailable');
            return getItem.call(this, key);
          };
        }""")
    page.context.clear_cookies(name='pagecraft_realization')
    with page.expect_response(lambda r: r.url.endswith('/me/leave') and r.status == 401):
        page.get_by_role('button', name='Começar uma nova realização', exact=True).click()
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#status')).to_contain_text('Tens trabalho por guardar')
    state = page.evaluate('() => ({...sessionStorage})')
    assert state['pc-realization:' + code] == first['id']
    assert state['pc-reflection:' + first['id']] == reflection
