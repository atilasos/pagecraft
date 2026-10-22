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
    expect(lesson.locator('body')).to_have_js_property('inert', False)
    # A matching checkpoint is an observable reply to the preferences, rather
    # than a timeout or a network-idle assumption.
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
    expect(lesson.locator('body')).to_have_js_property('inert', True)
    lesson.locator('body').evaluate('''() => new Promise(resolve => {
      const check = () => window.heldInitialization.some(d => d.type === 'learning_preferences')
        ? resolve() : requestAnimationFrame(check);
      check();
    })''')
    messages = lesson.locator('body').evaluate('() => window.heldInitialization.map(d => d.type)')
    assert messages == ['learning_restore', 'learning_preferences']
    cut = lesson.get_by_role('button', name='Cortar ao meio', exact=True)
    box = cut.bounding_box()
    # Native input during the retained initialization must not create work
    # which the subsequent restore would silently overwrite.
    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    expect(cut).to_have_attribute('aria-pressed', 'false')
    lesson.locator('body').evaluate('() => window.releaseInitialization()')
    wait_for_initialization(lesson)
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
    page.evaluate("""() => new Promise(resolve => {
      const frame = document.getElementById('lesson');
      addEventListener('message', function finish(event) {
        if (event.source === frame.contentWindow && event.data?.probe === 1) {
          removeEventListener('message', finish); resolve();
        }
      });
      frame.contentWindow.postMessage({probe:1}, '*');
    })""")
    assert lesson.locator('body').evaluate('window.receivedPreferences') == []
    assert lesson.get_by_label('Nível de diferenciação').input_value() == 'intermediate'
    assert not any(e['type'] == 'activity_state' for e in page.evaluate('window.lessonMessages'))
    page.evaluate('window.releaseLessonLoad()')
    wait_for_initialization(lesson)
    expect(lesson.get_by_label('Nível de diferenciação')).to_have_value('challenge')
    lesson.get_by_role('button', name='Cortar ao meio', exact=True).click()
    expect(lesson.get_by_role('button', name='Sim', exact=True)).to_be_enabled()
