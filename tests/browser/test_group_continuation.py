"""Real Canva draft: two lessons, another device, teacher choice and board codes."""
import httpx


def test_group_continues_real_saved_work_in_another_browser(page, studio_origin):
    from playwright.sync_api import expect
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    browser = page.context.browser
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        classroom = teacher.post('/api/classes', json={
            'name': '4.º A · Continuação', 'year': 4, 'students': ['Ana', 'Bruno']
        }).json()
        session = teacher.post('/api/sessions', json={
            'class_id': classroom['id'], 'activity_slug': 'canva-animais-4ano',
            'activity_title': 'Dois animais, três formas de comunicar'
        }).json()
        path = '/api/sessions/' + session['id']
        page.goto(studio_origin + '/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_role('button', name='A pares', exact=True).click()
        for name in ['Ana', 'Bruno']:
            page.get_by_role('button', name=name, exact=True).click()
        page.get_by_role('button', name='Começar', exact=True).click()
        lesson = page.frame_locator('#activity-frame')
        expect(page.locator('#activity-frame')).to_be_visible(timeout=15000)
        lesson.locator('#animals').fill('Golfinho e tartaruga')
        lesson.locator('#product-poster').click()
        lesson.locator('#choiceReason').fill('Os colegas podem comparar os animais.')
        expect(lesson.locator('#animals')).to_have_value('Golfinho e tartaruga')
        expect(lesson.locator('#next')).to_be_enabled()
        lesson.locator('#choiceReason').press('Tab')
        lesson.locator('#next').click()
        expect(lesson.locator('.stage-meta')).to_contain_text('Etapa 2 de 8')
        lesson.locator('#layoutPlan').fill('Duas zonas, uma por animal.')
        page.get_by_role('button', name='Guardar para continuar', exact=True).click()
        expect(page.locator('#save-work-status')).to_have_text('Guardado. Podem continuar na próxima aula.')
        # Poll the real server; do not treat an unresolved browser Promise as an acknowledgement.
        saved = False
        for _ in range(100):
            history = page.request.get(studio_origin + path + '/groups/me/history').json()['events']
            saved = any(e.get('payload', {}).get('detail', {}).get('field') == 'layoutPlan' for e in history)
            if saved: break
            page.wait_for_timeout(100)
        assert saved
        teacher.post(path + '/close').raise_for_status()

        teacher_context = browser.new_context()
        board_context = browser.new_context()
        next_context = browser.new_context()
        try:
            panel = teacher_context.new_page()
            panel.request.get(studio_origin + '/api/teacher-bootstrap')
            panel.goto(studio_origin + '/teacher/class.html')
            panel.get_by_label('Turma', exact=True).select_option(classroom['id'])
            panel.get_by_role('button', name='Dois animais, três formas de comunicar').click()
            expect(panel.get_by_role('button', name='Continuar trabalho', exact=True)).to_be_visible()
            expect(panel.get_by_role('button', name='Começar novo trabalho', exact=True)).to_be_visible()
            panel.get_by_role('button', name='Continuar trabalho', exact=True).click()
            expect(panel.locator('#work-groups')).to_contain_text('Ana + Bruno', timeout=10000)
            resumed = teacher.get(path).json()
            assert resumed['status'] == 'live'
            assert len(teacher.get('/api/sessions').json()) == 1
            code = resumed['group_codes'][0]['code']

            board = board_context.new_page()
            challenge = board.request.post(studio_origin + '/api/board/pairings').json()
            teacher.post('/api/board/pairings/confirm', json={'code': challenge['code']}).raise_for_status()
            assert board.request.post(studio_origin + '/api/board/pairings/complete',
                                      data={'pairing_id': challenge['pairing_id']}).ok
            board.goto(studio_origin + '/board/')
            expect(board.locator('#group-codes-grid')).to_contain_text(code)
            expect(board.locator('#board')).to_be_hidden()
            board.screenshot(path='/tmp/pagecraft-retoma-quadro.png', full_page=True)

            next_day = next_context.new_page()
            next_day.route('**/groups/me/history', lambda route: route.fulfill(status=503, body='{}'))
            next_day.goto(studio_origin + '/student/')
            next_day.get_by_label('Código da aula ou do grupo').fill(code)
            next_day.get_by_role('button', name='Entrar', exact=True).click()
            expect(next_day.locator('#restore-status')).to_contain_text('Não foi possível recuperar')
            expect(next_day.locator('#activity-frame')).to_be_hidden()
            next_day.unroute('**/groups/me/history')
            next_day.get_by_role('button', name='Tentar recuperar novamente', exact=True).click()
            restored = next_day.frame_locator('#activity-frame')
            expect(next_day.locator('#activity-frame')).to_be_visible(timeout=15000)
            expect(restored.locator('#layoutPlan')).to_have_value('Duas zonas, uma por animal.', timeout=15000)
            expect(restored.locator('.stage-meta')).to_contain_text('Etapa 2 de 8')
            expect(restored.locator('.stage-meta')).to_contain_text('Cartaz')
            expect(board.locator('#group-codes-grid')).to_contain_text('Grupo já entrou')
            expect(panel.locator('#work-groups')).to_contain_text('Grupo já entrou')
            restored.locator('#previous').click()
            expect(restored.locator('#animals')).to_have_value('Golfinho e tartaruga')
            expect(restored.locator('#choiceReason')).to_have_value('Os colegas podem comparar os animais.')
            panel.get_by_role('button', name='Mostrar atividade no quadro', exact=True).click()
            expect(board.locator('#group-codes-panel')).to_be_hidden()
            expect(board.locator('#board')).to_be_visible()
            panel.get_by_role('button', name='Novo código para Ana + Bruno', exact=True).click()
            expect(panel.locator('.group-access-code')).not_to_have_text('Grupo já entrou')
            assert page.request.get(studio_origin + path + '/me').status == 401
            teacher.post(path + '/close').raise_for_status()
            panel.reload()
            panel.get_by_label('Turma', exact=True).select_option(classroom['id'])
            panel.get_by_role('button', name='Dois animais, três formas de comunicar').click()
            panel.get_by_role('button', name='Começar novo trabalho', exact=True).click()
            expect(panel.locator('#live')).to_be_visible()
            assert len(teacher.get('/api/sessions').json()) == 2
            assert teacher.get(path).json()['status'] == 'closed'
            assert not errors
        finally:
            teacher_context.close()
            board_context.close()
            next_context.close()
