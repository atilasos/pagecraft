"""The paired board leaves A and discovers B using a real Hub browser."""
import time

import httpx
import pytest


@pytest.mark.parametrize('wake', ['event', 'heartbeat'])
def test_board_discovers_current_session_without_retaining_old_codes(page, studio_origin, wake):
    from playwright.sync_api import expect

    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.add_init_script("""
        window.boardSources = [];
        const NativeEventSource = window.EventSource;
        window.EventSource = class extends NativeEventSource {
            constructor(...args) {
                super(...args);
                window.boardSources.push(this);
                this.addEventListener('error', () => { window.streamEndedAt = Date.now(); });
            }
        };
    """)
    discoveries = []
    held = []

    def discover(route):
        discoveries.append(time.monotonic())
        if len(discoveries) == 2:
            held.append(route)
        else:
            route.continue_()

    page.route('**/api/board/session', discover)
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        classroom = teacher.post('/api/classes', json={
            'name': 'Quadro descartável', 'year': 2, 'students': ['Ana', 'Bruno'],
        }).json()
        first = teacher.post('/api/sessions', json={
            'class_id': classroom['id'], 'activity_slug': 'fraction-test',
            'activity_title': 'Sessão A',
        }).json()
        path = '/api/sessions/' + first['id']
        group = teacher.post(path + '/groups/claim', json={
            'participant_ids': list(first['roster']), 'mode': 'pair',
        }).json()['work_group']
        code = teacher.post(path + '/groups/' + group['id'] + '/access-code').json()['code']
        teacher.post(path + '/group-codes', json={'visible': True}).raise_for_status()
        challenge = page.request.post(studio_origin + '/api/board/pairings').json()
        teacher.post('/api/board/pairings/confirm', json={'code': challenge['code']}).raise_for_status()
        assert page.request.post(studio_origin + '/api/board/pairings/complete',
                                 data={'pairing_id': challenge['pairing_id']}).ok
        page.goto(studio_origin + '/board/')
        expect(page.locator('#group-codes-grid')).to_contain_text(code)
        expect(page.locator('#session-title')).to_contain_text('Sessão A')
        page.screenshot(path=f'/tmp/pagecraft-quadro-{wake}-a.png', full_page=True)
        second = teacher.post('/api/sessions', json={
            'class_id': classroom['id'], 'activity_slug': 'fraction-test',
            'activity_title': 'Sessão B',
        }).json()
        assert second['started_at'] > first['started_at']
        assert teacher.get('/api/board/session').status_code == 401
        if wake == 'event':
            teacher.post(path + '/control', json={'action': 'freeze'}).raise_for_status()
        # Heartbeat case leaves A entirely silent. The real 30-second clock
        # must close its stream without a control action or synthetic tick.
        expect(page.locator('#waiting')).to_be_visible(timeout=40000)
        expect(page.locator('#board')).not_to_have_attribute('src')
        expect(page.locator('#group-codes-grid')).to_be_empty()
        expect(page.locator('#session-join-code')).to_be_empty()
        expect(page.locator('#session-title')).to_be_empty()
        page.screenshot(path=f'/tmp/pagecraft-quadro-{wake}-espera.png', full_page=True)
        page.wait_for_function('window.streamEndedAt && Date.now() - window.streamEndedAt >= 1600')
        assert len(held) == 1
        assert len(discoveries) == 2
        held.pop().continue_()
        expect(page.locator('#session-title')).to_contain_text('Sessão B')
        expect(page.locator('#board')).to_have_attribute(
            'src', f"/api/board/sessions/{second['id']}/content?presentation=1")
        expect(page.locator('#session-join-code')).to_have_text(second['join_code'])
        expect(page.locator('#group-codes-grid')).to_be_empty()
        # Queued callbacks from A cannot rewrite B or trigger another discovery.
        page.evaluate("""() => {
            const old = window.boardSources[0];
            old.dispatchEvent(new MessageEvent('session_state_changed', {data: JSON.stringify({
                session: {closed: true, group_codes_visible: true,
                    group_codes: [{display_name: 'ANTIGO', code: 'ANTIGO'}]}
            })}));
            old.dispatchEvent(new MessageEvent('session_closed', {data: '{}'}));
            old.dispatchEvent(new Event('error'));
        }""")
        page.wait_for_timeout(1800)
        expect(page.locator('#session-title')).to_contain_text('Sessão B')
        expect(page.locator('#group-codes-grid')).to_be_empty()
        assert len(discoveries) == 2
        assert page.evaluate('window.boardSources.length') == 2
        assert teacher.get(path).json()['status'] == 'live'
        assert errors == []
        page.screenshot(path=f'/tmp/pagecraft-quadro-{wake}-b.png', full_page=True)
