"""The shared computer switches child voice without copying a peer's answers."""
import httpx


def test_children_take_turns_and_teacher_reads_individual_reflections(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap').raise_for_status()
        cls = teacher.post('/api/classes', json={'name':'Reflexão', 'year':2, 'students':['Ana','Bruno','Carla']}).json()
        registration = {'slug':'fraction-test', 'title':'Frações', 'year':2, 'duration':45,
                        'criteria':[{'id':'iguais', 'pt':'Reconheço partes iguais.'}]}
        teacher.post('/api/learning/activities', json=registration).raise_for_status()
        session = teacher.post('/api/sessions', json={'class_id':cls['id'], 'activity_slug':'fraction-test', 'activity_title':'Frações'}).json()
        ids = list(session['roster']); path = '/api/sessions/'+session['id']
        page.goto(studio_origin+'/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_role('button', name='Em grupo', exact=True).click()
        for name in ['Ana','Bruno','Carla']:
            page.get_by_role('button', name=name, exact=True).click()
        page.get_by_role('button', name='Começar', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por responder', exact=True).click()
        expect(page.get_by_role('heading', name='A reflexão de Ana', exact=True)).to_be_visible()
        page.get_by_label('Consegui com ajuda', exact=True).check()
        page.get_by_label('O que te ajudou?').fill('Comparei os blocos.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        page.get_by_role('button', name='Bruno · Por responder', exact=True).click()
        expect(page.get_by_label('Consegui com ajuda', exact=True)).not_to_be_checked()
        expect(page.get_by_label('O que te ajudou?')).to_have_value('')
        page.get_by_label('Quero praticar mais', exact=True).check()
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        page.get_by_role('button', name='Carla · Por responder', exact=True).click()
        page.get_by_role('button', name='Prefiro não responder agora', exact=True).click()
        page.reload()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Guardada', exact=True).click()
        expect(page.get_by_label('Consegui com ajuda', exact=True)).to_be_checked()
        expect(page.get_by_label('O que te ajudou?')).to_have_value('Comparei os blocos.')
        page.get_by_label('Consegui com autonomia', exact=True).check()
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        for sid, count in [(ids[0],2), (ids[1],1), (ids[2],1)]:
            history = teacher.get(path+f'/students/{sid}/history').json()['events']
            assert len([e for e in history if e['type']=='individual_reflection']) == count
        # Teacher uses the same actual drawer and report as for individual work.
        teacher_page = page.context.new_page()
        teacher_page.goto(studio_origin+'/teacher/class.html')
        teacher_page.request.get(studio_origin+'/api/teacher-bootstrap')
        teacher_page.reload()
        teacher_page.get_by_role('button', name='Retomar', exact=True).first.click()
        teacher_page.locator('#work-groups').get_by_role('button', name='Ana', exact=True).click()
        expect(teacher_page.locator('#drawer-events')).to_contain_text('Reflexão individual')
        expect(teacher_page.locator('#drawer-events')).to_contain_text('Consegui com autonomia')
        expect(teacher_page.locator('#drawer-events')).to_contain_text('Comparei os blocos.')
        teacher_page.close()


def test_lost_save_response_retries_once_without_duplicating_reflection(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap')
        cls = teacher.post('/api/classes', json={'name':'Retoma', 'year':2, 'students':['Ana','Bruno']}).json()
        session = teacher.post('/api/sessions', json={'class_id':cls['id'], 'activity_slug':'fraction-test'}).json()
        ids = list(session['roster']); path = '/api/sessions/'+session['id']
        page.goto(studio_origin+'/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_role('button', name='A pares', exact=True).click()
        for name in ['Ana','Bruno']:
            page.get_by_role('button', name=name, exact=True).click()
        page.get_by_role('button', name='Começar', exact=True).click()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por responder', exact=True).click()
        page.get_by_label('O que te ajudou?').fill('Experimentei com blocos.')
        # The server saves normally; only its response is lost at the network boundary.
        def lose_response(route):
            route.fetch()
            route.abort()
        page.route('**/groups/me/reflections', lose_response, times=1)
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Não foi possível guardar')
        page.reload()
        page.get_by_role('button', name='A minha reflexão', exact=True).click()
        page.get_by_role('button', name='Ana · Por guardar', exact=True).click()
        expect(page.get_by_label('O que te ajudou?')).to_have_value('Experimentei com blocos.')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        expect(page.get_by_role('button', name='Ana · Guardada', exact=True)).to_be_visible()
        history = teacher.get(path+f'/students/{ids[0]}/history').json()['events']
        assert len([e for e in history if e['type']=='individual_reflection']) == 1
