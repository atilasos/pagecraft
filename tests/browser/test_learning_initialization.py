"""A visible lesson must consume its authorized restore before accepting input."""
import json
from pathlib import Path

import pytest

expect = pytest.importorskip('playwright.sync_api').expect

# Retain only delivery, leaving the real host, listeners, CSP and content intact.
# This schedules the same messages that can otherwise race native user input.
HOLD_INITIALIZATION = '''(() => {
  if (window === parent) return;
  window.heldInitialization = [];
  let released = false;
  addEventListener('message', event => {
    if (!released && event.source === parent &&
        ['learning_restore','learning_preferences'].includes(event.data?.type)) {
      event.stopImmediatePropagation();
      window.heldInitialization.push(event.data);
      if (event.data.type === 'learning_preferences')
        document.documentElement.dataset.initializationHeld = 'true';
    }
  }, true);
  window.releaseInitialization = () => {
    released = true;
    for (const data of window.heldInitialization)
      dispatchEvent(new MessageEvent('message', {data, source:parent}));
  };
})()'''


def register_fraction(page, origin):
    registration = json.loads((Path(__file__).resolve().parents[2] /
                              'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    page.request.get(origin + '/api/teacher-bootstrap')
    activity = page.request.post(origin + '/api/learning/activities', data=registration).json()
    page.goto(origin + '/' + activity['code'])
    page.get_by_label('Como te chamas?').fill('Ensaio de inicialização')


def wait_for_initialization(lesson):
    # The activity exposes its controls only after consuming both messages.
    expect(lesson.get_by_role('button', name='Cortar ao meio', exact=True)).to_be_visible()


@pytest.mark.parametrize('resume', [False, True], ids=['new', 'resume'])
def test_learning_restores_before_accepting_native_input(page, studio_origin, resume):
    register_fraction(page, studio_origin)
    if resume:
        with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok and any(
            e['type'] == 'activity_state' for e in r.request.post_data_json['events']
        )):
            page.get_by_role('button', name='Começar', exact=True).click()
    page.add_init_script(HOLD_INITIALIZATION)
    if resume:
        page.on('dialog', lambda dialog: dialog.accept())
        page.reload()
    else:
        # Init scripts apply only to subsequently created documents, including
        # this iframe. The host is still the real entry page.
        page.get_by_role('button', name='Começar', exact=True).click()
    lesson = page.frame_locator('#lesson')
    expect(lesson.locator('body')).to_be_visible()
    expect(lesson.locator('html')).to_have_attribute('data-initialization-held', 'true')
    messages = lesson.locator('body').evaluate('() => window.heldInitialization.map(d => d.type)')
    assert messages == ['learning_restore', 'learning_preferences']
    cut = lesson.locator('[data-cut="0.5"]')
    early_input_available = cut.is_visible()
    if not early_input_available:
        status = lesson.get_by_role('status').filter(has_text='A recuperar o teu trabalho…')
        expect(status).to_be_visible()
        # Inert descendants are absent from the browser accessibility tree.
        assert status.evaluate("el => el.closest('[inert]') === null")
    # A product may defer input or preserve it. It must never accept a cut and
    # then silently erase it when the authorized snapshot arrives.
    if early_input_available:
        cut.click()
    else:
        cut.focus()
        assert not cut.evaluate('el => el === document.activeElement')
        page.keyboard.press('Enter')
    expect(cut).to_have_attribute('aria-pressed', str(early_input_available).lower())
    lesson.locator('body').evaluate('() => window.releaseInitialization()')
    wait_for_initialization(lesson)
    if not early_input_available:
        cut.click()
    expect(lesson.get_by_role('button', name='Sim', exact=True)).to_be_enabled()
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok and any(
        e['type'] == 'attempt' for e in r.request.post_data_json['events']
    )):
        lesson.get_by_role('button', name='Sim', exact=True).click()
    events = page.request.get(studio_origin + '/api/learning/me').json()['events']
    assert len([e for e in events if e['type'] == 'attempt']) == 1
    assert [e for e in events if e['type'] == 'attempt'][0]['payload']['correct'] is True


def test_preferences_wait_for_real_frame_load_and_keep_latest_choice(page, studio_origin):
    register_fraction(page, studio_origin)
    # Retain the host's load callback. The browser still parses the real frame.
    page.evaluate('''() => {
      const frame = document.getElementById('lesson');
      const loaded = frame.onload;
      window.releaseLessonLoad = () => loaded();
      frame.onload = () => { window.lessonLoadHeld = true; };
      window.lessonMessages = [];
      addEventListener('message', event => {
        if (event.source === frame.contentWindow && event.data?.pagecraft === 1)
          window.lessonMessages.push(event.data);
      });
    }''')
    page.get_by_role('button', name='Começar', exact=True).click()
    page.wait_for_function('window.lessonLoadHeld === true')
    lesson = page.frame_locator('#lesson')
    lesson.locator('body').evaluate("""() => {
      window.receivedPreferences = [];
      addEventListener('message', event => {
        if (event.source !== parent) return;
        if (event.data?.type === 'learning_preferences') window.receivedPreferences.push(event.data);
        if (event.data?.probe === 1) parent.postMessage({probe:1}, '*');
      });
    }""")
    page.locator('#level').select_option('challenge')
    # A round-trip queued after the preferences proves delivery order without
    # relying on time or the network becoming idle.
    page.evaluate("""() => {
      const frame = document.getElementById('lesson');
      addEventListener('message', function finish(event) {
        if (event.source === frame.contentWindow && event.data?.probe === 1) {
          removeEventListener('message', finish); window.initializationProbeReceived = true;
        }
      });
      frame.contentWindow.postMessage({probe:1}, '*');
    }""")
    page.wait_for_function('window.initializationProbeReceived === true')
    assert lesson.locator('body').evaluate('window.receivedPreferences') == []
    assert lesson.get_by_label('Nível de diferenciação').input_value() == 'intermediate'
    assert not any(e['type'] == 'activity_state' for e in page.evaluate('window.lessonMessages'))
    page.evaluate('window.releaseLessonLoad()')
    wait_for_initialization(lesson)
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    lesson.get_by_role('button', name='Cortar ao meio', exact=True).click()
    expect(lesson.get_by_role('button', name='Sim', exact=True)).to_be_enabled()


def test_pending_preferences_and_checkpoint_survive_initialization(page, studio_origin):
    register_fraction(page, studio_origin)
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok and any(
        e['type'] == 'activity_state' for e in r.request.post_data_json['events']
    )):
        page.get_by_role('button', name='Começar', exact=True).click()
    original = page.request.get(studio_origin + '/api/learning/me').json()
    owner = original['id']
    page.route('**/api/learning/me/events', lambda route: route.fulfill(status=503, json={}))
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 503):
        page.locator('#level').select_option('challenge')
    lesson = page.frame_locator('#lesson')
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 503):
        lesson.get_by_role('button', name='Cortar à esquerda', exact=True).click()
    pending = page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', owner)
    assert any(e['type'] == 'level_changed' and e['payload']['level'] == 'challenge' for e in pending)
    assert any(e['type'] == 'activity_state' and e['payload']['state']['cut'] == .25 for e in pending)
    page.add_init_script(HOLD_INITIALIZATION)
    page.on('dialog', lambda dialog: dialog.accept())
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.status == 503):
        page.reload()
    expect(page.locator('#level')).to_have_value('challenge')
    expect(lesson.locator('html')).to_have_attribute('data-initialization-held', 'true')
    held = lesson.locator('body').evaluate('window.heldInitialization')
    assert held[-1]['payload']['level'] == 'challenge'
    checkpoint = [e for e in held[0]['payload']['events'] if e['type'] == 'activity_state'][-1]
    assert checkpoint['payload']['state']['cut'] == .25
    lesson.locator('body').evaluate('window.releaseInitialization()')
    wait_for_initialization(lesson)
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    expect(lesson.get_by_role('button', name='Cortar à esquerda', exact=True)).to_have_attribute('aria-pressed', 'true')
    assert page.evaluate('(id) => JSON.parse(sessionStorage.getItem("pc-queue:" + id))', owner)[:len(pending)] == pending
    page.unroute('**/api/learning/me/events')
    with page.expect_response(lambda r: r.url.endswith('/me/events') and r.ok) as response:
        lesson.get_by_role('button', name='Não', exact=True).click()
    assert response.value.request.headers['x-pagecraft-realization'] == owner
    saved = page.request.get(studio_origin + '/api/learning/me').json()
    assert saved['id'] == owner
    assert saved['level'] == 'challenge'
    assert len([e for e in saved['events'] if e['type'] == 'attempt']) == 1
