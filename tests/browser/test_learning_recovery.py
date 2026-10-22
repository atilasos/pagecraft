"""Permanent entry must distinguish missing credentials from interrupted recovery."""
import pytest


def open_preview(page, origin):
    page.request.get(origin + '/api/teacher-bootstrap')
    response = page.request.post(origin + '/api/learning/activities', data={
        'slug': 'canva-animais-4ano', 'title': 'Ensaio de retoma', 'year': 4,
        'duration': 30, 'criteria': [{'id': 'compare', 'pt': 'Comparei dois animais.'}],
    })
    assert response.ok
    code = response.json()['code']
    page.goto(origin + '/' + code)
    return code


@pytest.mark.parametrize('failure', ['http', 'network'])
def test_interrupted_recovery_preserves_realization_pending_work_and_reflection(page, studio_origin, failure):
    from playwright.sync_api import expect

    open_preview(page, studio_origin)
    page.get_by_label('Como te chamas?').fill('Ensaio de ligação')
    page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok):
        lesson.locator('#animals').fill('Golfinho e tartaruga')
        lesson.locator('#animals').press('Tab')
    original = page.request.get(studio_origin + '/api/learning/me').json()
    assert any(e['payload'].get('detail', {}).get('value') == 'Golfinho e tartaruga'
               for e in original['events'])

    page.route('**/api/learning/me/events', lambda route: route.fulfill(status=503, json={}))
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 503):
        lesson.locator('#animals').fill('Golfinho e baleia')
        lesson.locator('#animals').press('Tab')
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.get_by_label('Consegui com ajuda', exact=True).check()
    page.locator('#strategy').fill('Comparei com o meu colega.')
    page.locator('#next-step').fill('Quero comparar os habitats.')

    def interrupt(route):
        if failure == 'http':
            route.fulfill(status=503, json={'detail': 'Ensaio de ligação'})
        else:
            route.abort('failed')

    page.route('**/api/learning/me', interrupt)
    page.on('dialog', lambda dialog: dialog.accept())
    page.reload()
    expect(page.locator('#status')).to_contain_text('Não foi possível recuperar o teu trabalho')
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#work')).to_be_hidden()
    expect(page.get_by_role('button', name='Tentar recuperar novamente', exact=True)).to_be_visible()
    assert page.request.get(studio_origin + '/api/learning/me').json()['id'] == original['id']

    page.unroute('**/api/learning/me')
    page.get_by_role('button', name='Tentar recuperar novamente', exact=True).click()
    expect(lesson.locator('#animals')).to_have_value('Golfinho e baleia')
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    expect(page.get_by_label('Consegui com ajuda', exact=True)).to_be_checked()
    expect(page.locator('#strategy')).to_have_value('Comparei com o meu colega.')
    expect(page.locator('#next-step')).to_have_value('Quero comparar os habitats.')

    page.unroute('**/api/learning/me/events')
    with page.expect_response(lambda r: r.url.endswith('/me/finish') and r.ok):
        page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
    restored = page.request.get(studio_origin + '/api/learning/me').json()
    assert restored['id'] == original['id']
    assert any(e['payload'].get('detail', {}).get('value') == 'Golfinho e baleia'
               for e in restored['events'])
    assert restored['assessment']['answers'] == {'compare': 'help'}
    assert restored['assessment']['strategy'] == 'Comparei com o meu colega.'
    assert restored['assessment']['next_step'] == 'Quero comparar os habitats.'


def test_entry_waits_until_the_server_confirms_no_realization(page, studio_origin):
    from playwright.sync_api import expect

    pending = []
    page.route('**/api/learning/me', lambda route: pending.append(route))
    with page.expect_request(lambda r: r.url.endswith('/api/learning/me')):
        open_preview(page, studio_origin)
    expect(page.locator('#start-form')).to_be_hidden()
    expect(page.locator('#status')).to_contain_text('A recuperar o teu trabalho')
    assert len(pending) == 1
    pending[0].fulfill(status=401, json={'detail': 'Volta a entrar na atividade.'})
    expect(page.locator('#start-form')).to_be_visible()
    expect(page.locator('#status')).to_be_empty()
