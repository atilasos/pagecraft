"""Fluxos do professor num Studio descartável e browser aberto pelo Hub."""
import re


def test_class_and_session_links_keep_the_explicit_context(page, studio_origin):
    from playwright.sync_api import expect

    page.goto(studio_origin + '/teacher/')
    classes = []
    for name in ['Turma A de ensaio', 'Turma B de ensaio']:
        response = page.request.post(studio_origin + '/api/classes', data={
            'name': name, 'year': 3, 'students': ['Exemplo'],
        })
        assert response.ok
        classes.append(response.json()['id'])
    sessions = []
    for index, class_id in enumerate([classes[0], classes[0], classes[1]]):
        response = page.request.post(studio_origin + '/api/sessions', data={
            'class_id': class_id, 'activity_slug': 'canva-4ano-estudio-de-slides',
            'activity_title': f'Trabalho de ensaio {index}',
        })
        assert response.ok
        sessions.append(response.json()['id'])
        if index < 2:
            assert page.request.post(studio_origin + f'/api/sessions/{sessions[-1]}/close').ok

    page.goto(studio_origin + f'/teacher/class.html?class={classes[0]}&activity=canva-4ano-estudio-de-slides')
    expect(page.locator('#launch-class')).to_have_value(classes[0])
    expect(page.locator('#report-class')).to_have_value(classes[0])
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#launch-btn')).to_have_text('Continuar trabalho')

    # O link escolhe uma sessão antiga, mesmo havendo outra mais recente do mesmo trabalho.
    page.goto(studio_origin + f'/teacher/class.html?session={sessions[0]}')
    page.get_by_role('button', name='Continuar trabalho', exact=True).click()
    expect(page.locator('#live-title')).to_contain_text('Trabalho de ensaio 0')
    assert page.request.get(studio_origin + f'/api/sessions/{sessions[1]}').json()['status'] == 'closed'

    page.goto(studio_origin + f'/teacher/class.html?session={sessions[2]}')
    expect(page.locator('#live-title')).to_contain_text('Trabalho de ensaio 2')
    page.goto(studio_origin + f'/teacher/class.html?class={classes[0]}&view=report')
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#report-class')).to_have_value(classes[0])
    expect(page.locator('#report-out')).to_contain_text('Exemplo')

    page.goto(studio_origin + '/teacher/class.html?session=inexistente')
    expect(page.locator('#live')).to_be_hidden()
    expect(page.locator('#launch-hint')).to_contain_text('não foi encontrada')


def library_examples():
    items = [{
        'code': f'TEST{chr(65 + index)}A',
        'title': 'Área e perímetro' if index == 7 else f'Atividade de ensaio {index}',
        'year': index % 4 + 1, 'duration': 20, 'languages': ['pt'],
        'published': index % 2 == 0, 'created_at': f'2026-10-{index + 1:02d}T12:00:00Z',
    } for index in range(20)]
    return items + [dict(items[0], code='OLDONE', title='Atividade retirada', archived_at='2026-10-24')]


def test_library_search_pages_keyboard_and_report_context(page, studio_origin):
    from playwright.sync_api import expect

    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/api/learning/activities?include_archived=true', lambda route: route.fulfill(json=library_examples()))
    page.goto(studio_origin + '/teacher/activities.html')
    expect(page.locator('.activity-row')).to_have_count(6)
    expect(page.locator('#library-total')).to_have_text('20 atividades · 10 por rever · 10 disponíveis')
    page.get_by_role('button', name='Seguinte', exact=True).click()
    expect(page.locator('#library-page')).to_have_text('Página 2 de 4')
    chosen = page.locator('.activity-row').first
    code = chosen.get_attribute('data-code')
    chosen.get_by_role('button', name='Ver registos', exact=True).focus()
    page.keyboard.press('Enter')
    expect(page.locator('#filter-activity')).to_have_value(code)
    expect(page.locator('#page-title')).to_be_focused()
    expect(page.locator('#activities-panel')).to_be_hidden()
    assert page.locator('#filter-name').bounding_box()['y'] < 900
    # Os registos retirados continuam disponíveis no filtro do relatório.
    expect(page.locator('#filter-activity option[value="OLDONE"]')).to_contain_text('retirada')
    page.locator('#nav-activities').click()
    expect(page.locator('#library-page')).to_have_text('Página 2 de 4')
    page.locator('#library-search').fill('area')
    expect(page.locator('.activity-row')).to_have_count(1)
    expect(page.locator('.activity-row h2')).to_have_text('Área e perímetro')
    page.locator('#library-search').fill('TESTBA')
    expect(page.locator('.activity-row')).to_have_count(1)
    page.locator('#library-clear').click()
    page.locator('#library-state').select_option('draft')
    page.locator('#library-year').select_option('2')
    expect(page.locator('.activity-row')).to_have_count(5)
    page.locator('#library-search').fill('inexistente')
    expect(page.locator('#activity-count')).to_contain_text('Sem atividades')
    page.locator('#library-clear').click()
    page.locator('#library-next').click()
    page.locator('#library-next').click()
    page.locator('#library-next').click()
    expect(page.locator('.activity-row')).to_have_count(2)
    expect(page.locator('#library-next')).to_be_disabled()
    for width in [1280, 768, 360]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert errors == []


def test_library_failure_does_not_hide_reports_and_can_retry(page, studio_origin):
    from playwright.sync_api import expect

    calls = []
    def activities(route):
        calls.append(True)
        if len(calls) == 1:
            route.fulfill(status=503, json={'detail': 'Falha de ensaio'})
        else:
            route.fulfill(json=library_examples())
    page.route('**/api/learning/activities?include_archived=true', activities)
    page.goto(studio_origin + '/teacher/activities.html#registos')
    expect(page.locator('#summary')).to_contain_text('realizações')
    expect(page.locator('#filter-name')).to_be_visible()
    page.locator('#nav-activities').click()
    expect(page.locator('#library-total')).to_have_text('Biblioteca indisponível')
    page.locator('#library-search').fill('area')
    expect(page.locator('#library-total')).to_have_text('Biblioteca indisponível')
    page.locator('#library-retry').click()
    expect(page.locator('.activity-row')).to_have_count(1)
    expect(page.locator('#library-retry')).to_be_hidden()


def test_old_review_survives_catalog_error_and_failed_approval(page, studio_origin):
    from playwright.sync_api import expect

    jobs = [dict(id=f'done-{index}', topic=f'Publicado {index}', status='done',
                 subject='Matemática', year=3, duration=30, slug='exemplo',
                 created_at=f'2026-10-{index + 1:02d}T12:00:00Z') for index in range(12)]
    jobs.append(dict(id='old-review', topic='Revisão antiga', status='awaiting_review',
                     subject='Matemática', year=3, duration=30, created_at='2026-09-01',
                     artifact_version=1, review={'id': 'a' * 64}, preview_url='/api/jobs/old-review/preview'))
    page.route('**/api/meta', lambda route: route.fulfill(status=503, json={}))
    page.route('**/api/jobs', lambda route: route.fulfill(json=jobs))
    page.route('**/api/jobs/old-review/approve', lambda route: route.fulfill(status=503, body='offline'))
    page.goto(studio_origin + '/teacher/')
    expect(page.locator('#catalog-status')).to_contain_text('Não foi possível')
    review = page.locator('#job-old-review')
    expect(review).to_be_visible()
    expect(page.locator('#jobs-summary')).to_contain_text('1 por rever')
    expect(page.locator('#published-jobs .card')).to_have_count(12)
    expect(page.locator('#job-history')).not_to_have_attribute('open', '')
    approve = review.get_by_role('button', name='Aprovar e publicar')
    approve.click()
    expect(review.locator('[aria-live]')).to_contain_text('Não foi possível publicar')
    expect(approve).to_be_enabled()
    expect(page.locator('#submit-btn')).to_be_disabled()


def test_home_recovers_without_confusing_failure_with_empty_classes(page, studio_origin):
    from playwright.sync_api import expect

    calls = []
    def sessions(route):
        calls.append(True)
        route.fulfill(status=503, json={}) if len(calls) == 1 else route.fulfill(json=[])
    page.route('**/api/classes', lambda route: route.fulfill(json=[]))
    page.route('**/api/sessions', sessions)
    page.goto(studio_origin + '/teacher/')
    expect(page.locator('#overview-status')).to_contain_text('Não foi possível')
    expect(page.get_by_role('link', name='Criar a primeira turma')).to_have_count(0)
    page.locator('#overview-retry').click()
    expect(page.get_by_role('link', name='Criar a primeira turma')).to_be_visible()
    expect(page.locator('#overview-retry')).to_be_hidden()


def test_catalog_keeps_class_while_overview_refreshes_or_fails(page, studio_origin):
    from playwright.sync_api import expect

    classes = [dict(id=key, name=key, year=3, students=[]) for key in ['Turma A', 'Turma B']]
    page.route('**/api/classes', lambda route: route.fulfill(json=classes))
    page.route('**/api/sessions', lambda route: route.fulfill(json=[]))
    page.goto(studio_origin + '/teacher/')
    page.locator('#dashboard-class').select_option('Turma B')
    links = page.locator('#catalog a.button-link')
    expect(links.first).to_have_attribute('href', re.compile(r'class=Turma\+B'))
    pending = []
    page.route('**/api/sessions', lambda route: pending.append(route))
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
    expect(page.locator('#dashboard-class')).to_be_disabled()
    page.locator('#catalog-search').fill('canva')
    expect(links.first).to_have_attribute('href', re.compile(r'class=Turma\+B'))
    assert len(pending) == 1
    pending[0].fulfill(status=503, json={})
    expect(page.locator('#overview-status')).to_contain_text('Não foi possível')
    page.locator('#catalog-search').fill('')
    expect(links.first).to_have_attribute('href', re.compile(r'class=Turma\+B'))


def mock_job_events(page):
    """Controla a entrega e o replay do SSE, mantendo reais o fetch e a interface."""
    page.add_init_script("""
      window.jobStreams = {};
      window.EventSource = class extends EventTarget {
        constructor(url) { super(); this.closed = false; window.jobStreams[url] = this; }
        close() { this.closed = true; }
        emit(type) {
          if (!this.closed) this.dispatchEvent(new MessageEvent(type, {data: '{"payload":{}}'}));
        }
      };
    """)


def test_historical_review_event_does_not_stop_publication_updates(page, studio_origin):
    from playwright.sync_api import expect

    mock_job_events(page)
    job = dict(id='publishing', topic='A publicar', status='publishing',
               subject='Matemática', year=3, duration=30, slug='exemplo')
    page.route('**/api/jobs', lambda route: route.fulfill(json=[job]))
    page.route('**/api/jobs/publishing', lambda route: route.fulfill(json=job))
    page.goto(studio_origin + '/teacher/')
    expect(page.locator('#job-publishing progress')).to_be_visible()
    with page.expect_response('**/api/jobs/publishing'):
        page.evaluate("jobStreams['/api/jobs/publishing/stream'].emit('awaiting_review')")
    expect(page.locator('#job-publishing-log')).not_to_be_empty()
    assert page.evaluate("!jobStreams['/api/jobs/publishing/stream'].closed")
    job['status'] = 'done'
    page.evaluate("jobStreams['/api/jobs/publishing/stream'].emit('done')")
    expect(page.locator('#published-jobs #job-publishing')).to_have_count(1)
    expect(page.locator('#job-history-label')).to_contain_text('(1)')
    assert page.evaluate("jobStreams['/api/jobs/publishing/stream'].closed")


def test_unrelated_job_events_keep_keyboard_focus_on_review(page, studio_origin):
    from playwright.sync_api import expect

    mock_job_events(page)
    review = dict(id='review', topic='Rever', status='awaiting_review',
                  subject='Matemática', year=3, duration=30, artifact_version=1,
                  review={'id': 'a' * 64}, preview_url='/api/jobs/review/preview')
    running = dict(review, id='running', topic='Em preparação', status='queued')
    page.route('**/api/jobs', lambda route: route.fulfill(json=[review, running]))
    page.route('**/api/jobs/running', lambda route: route.fulfill(json=running))
    page.goto(studio_origin + '/teacher/')
    expect(page.locator('#job-running')).to_be_visible()
    approve = page.locator('#job-review button[data-approve]')
    approve.focus()
    page.evaluate("jobStreams['/api/jobs/running/stream'].emit('phase_started')")
    expect(page.locator('#job-running-log')).not_to_be_empty()
    expect(approve).to_be_focused()
    # Uma nova revisão pode mudar a ordem sem tirar o foco da revisão já aberta.
    running.update(status='awaiting_review', created_at='2026-10-24')
    page.evaluate("jobStreams['/api/jobs/running/stream'].emit('awaiting_review')")
    expect(page.locator('#jobs > .card').first).to_have_attribute('id', 'job-running')
    expect(approve).to_be_focused()
