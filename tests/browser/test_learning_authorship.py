"""Shared cookies must not transfer a permanent realization's authorship."""
import pytest

from test_learning_recovery import open_preview


def start_tab(page, name):
    page.get_by_label('Como te chamas?').fill(name)
    page.get_by_role('button', name='Começar', exact=True).click()
    page.locator('#work').wait_for(state='visible')
    page.wait_for_load_state('networkidle')
    return page.request.get(page.url.split('/')[0] + '//' + page.url.split('/')[2] + '/api/learning/me').json()


def two_realizations(page, origin):
    code = open_preview(page, origin)
    first = start_tab(page, 'Aluno A')
    second_tab = page.context.new_page()
    second_tab.goto(origin + '/' + code)
    second_tab.get_by_role('button', name='Trocar de aluno', exact=True).click()
    second = start_tab(second_tab, 'Aluno B')
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
    # B is still authorized and can save its own response.
    with second_tab.expect_response(lambda r: r.url.endswith('/me/events') and r.ok):
        second_tab.frame_locator('#lesson').locator('#animals').fill('Resposta B')
        second_tab.frame_locator('#lesson').locator('#animals').press('Tab')
    assert page.request.get(studio_origin + '/api/learning/me').json()['id'] == second['id']


def test_reload_conflict_preserves_tab_identity_and_drafts(page, studio_origin):
    from playwright.sync_api import expect

    first, second, _ = two_realizations(page, studio_origin)
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.locator('#strategy').fill('Reflexão A por guardar')
    # Queue survives reload, even though the shared cookie now belongs to B.
    page.evaluate('''id => sessionStorage.setItem("pc-queue:" + id, JSON.stringify([
      {id: "pending-A", type: "attempt", payload: {answer: "A"}}
    ]))''', first['id'])
    page.reload()
    expect(page.locator('#status')).to_contain_text('outra realização')
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#work')).to_be_hidden()
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', first['id'])[0]['id'] == 'pending-A'
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-reflection:" + id))', first['id'])['strategy'] == 'Reflexão A por guardar'
    assert page.request.get(studio_origin + '/api/learning/me').json()['id'] == second['id']
