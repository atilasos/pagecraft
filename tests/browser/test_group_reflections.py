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
        teacher_page.locator('#work-groups').get_by_role('button', name='Ver percurso de Ana', exact=True).click()
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


def test_late_response_cannot_close_another_groups_reflection(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap')
        cls = teacher.post('/api/classes', json={'name':'Troca', 'year':2, 'students':['Iris','João','Lara','Mário']}).json()
        session = teacher.post('/api/sessions', json={'class_id':cls['id'], 'activity_slug':'fraction-test'}).json()
        ids = list(session['roster']); path = '/api/sessions/'+session['id']
        page.goto(studio_origin+'/student/')
        def enter(names):
            page.get_by_label('Código da aula').fill(session['join_code'])
            page.get_by_role('button', name='Entrar', exact=True).click()
            page.get_by_role('button', name='A pares', exact=True).click()
            for name in names:
                page.get_by_role('button', name=name, exact=True).click()
            page.get_by_role('button', name='Começar', exact=True).click()
            page.get_by_role('button', name='A minha reflexão', exact=True).click()
            page.get_by_role('button', name=names[0]+' · Por responder', exact=True).click()
        enter(['Iris','João'])
        page.get_by_label('O que te ajudou?').fill('Reflexão anterior.')
        # Delay consumption of a real HTTP response, after the server saves it.
        page.evaluate('''() => {
          const fetchActual = window.fetch.bind(window);
          const bodyGate = new Promise(resolve => window.releaseReflectionBody = resolve);
          window.fetch = async (...args) => {
            const response = await fetchActual(...args);
            if (String(args[0]).endsWith('/groups/me/reflections') && args[1]?.method === 'POST') {
              const jsonActual = response.json.bind(response);
              response.json = async () => { const data = await jsonActual(); window.reflectionBodyWaiting = true; await bodyGate; return data; };
            }
            return response;
          };
        }''')
        page.get_by_role('button', name='Guardar a minha reflexão', exact=True).click()
        page.wait_for_function('window.reflectionBodyWaiting === true')
        teacher.post(path+'/release/'+ids[0], json={}).raise_for_status()
        expect(page.get_by_label('Código da aula')).to_be_visible(timeout=10000)
        enter(['Lara','Mário'])
        page.get_by_label('O que te ajudou?').fill('O meu novo rascunho.')
        page.evaluate('window.releaseReflectionBody()')
        expect(page.get_by_role('heading', name='A reflexão de Lara', exact=True)).to_be_visible()
        expect(page.get_by_label('O que te ajudou?')).to_have_value('O meu novo rascunho.')
        assert page.request.get(studio_origin+path+'/groups/me/reflections').json()['reflections'] == {}


def test_teacher_change_keeps_pending_answer_with_old_authors(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap')
        cls=teacher.post('/api/classes',json={'name':'Composição','year':2,'students':['Ana','Bruno','Carla']}).json()
        session=teacher.post('/api/sessions',json={'class_id':cls['id'],'activity_slug':'fraction-test'}).json()
        ids=list(session['roster']);path='/api/sessions/'+session['id']
        page.goto(studio_origin+'/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.get_by_role('button',name='A pares',exact=True).click()
        for name in ['Ana','Bruno']:page.get_by_role('button',name=name,exact=True).click()
        page.get_by_role('button',name='Começar',exact=True).click()
        page.route('**/events',lambda route:route.fulfill(status=503,body='{}'))
        lesson=page.frame_locator('#activity-frame')
        lesson.get_by_role('button',name='Cortar à esquerda',exact=True).click()
        lesson.get_by_role('button',name='Sim',exact=True).click()
        page.locator('#group-level').select_option('challenge')
        expect(lesson.locator('#level')).to_have_value('challenge')
        # Fill the old composition's queue through actual controls, never fake events.
        page.evaluate("() => { for(let i=0;i<200;i++) document.querySelector('#help-btn').click(); }")
        group=page.request.get(studio_origin+path+'/me').json()['work_group']
        teacher.patch(path+f"/groups/{group['id']}/participants",json={'participant_ids':[ids[0],ids[2]],'mode':'pair'}).raise_for_status()
        expect(page.locator('#student-name')).to_have_text('Ana + Carla',timeout=10000)
        expect(lesson.locator('#level')).to_have_value('intermediate')
        expect(page.locator('#pending-group-work')).to_contain_text('Ana + Bruno')
        page.unroute('**/events')
        page.reload()
        expect(page.locator('#student-name')).to_have_text('Ana + Carla')
        expect(page.locator('#pending-group-work')).to_contain_text('Ana + Bruno')
        lesson.get_by_role('button',name='Cortar ao meio',exact=True).click()
        lesson.get_by_role('button',name='Sim',exact=True).click()
        import time
        for _ in range(30):
            history=teacher.get(path+f'/students/{ids[2]}/history').json()['events']
            attempts=[e for e in history if e['type']=='attempt']
            if attempts:break
            time.sleep(.2)
        assert len(attempts)==1 and attempts[0]['payload']['correct'] is True
        assert attempts[0]['participant_ids']==[ids[0],ids[2]]
        old_history=teacher.get(path+f'/students/{ids[1]}/history').json()['events']
        assert not any(e['type']=='attempt' for e in old_history)


def test_reviewing_old_draft_preserves_it_after_new_reflection(page, studio_origin):
    from playwright.sync_api import expect
    with httpx.Client(base_url=studio_origin) as teacher:
        teacher.get('/api/teacher-bootstrap')
        cls=teacher.post('/api/classes',json={'name':'Rascunhos','year':2,'students':['Ana','Bruno','Carla']}).json()
        session=teacher.post('/api/sessions',json={'class_id':cls['id'],'activity_slug':'fraction-test'}).json()
        ids=list(session['roster']);path='/api/sessions/'+session['id']
        page.goto(studio_origin+'/student/')
        page.get_by_label('Código da aula').fill(session['join_code'])
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.get_by_role('button',name='A pares',exact=True).click()
        for name in ['Ana','Bruno']:page.get_by_role('button',name=name,exact=True).click()
        page.get_by_role('button',name='Começar',exact=True).click()
        page.get_by_role('button',name='A minha reflexão',exact=True).click()
        page.get_by_role('button',name='Ana · Por responder',exact=True).click()
        page.get_by_label('O que te ajudou?').fill('O corte feito com Bruno.')
        group=page.request.get(studio_origin+path+'/me').json()['work_group']
        teacher.patch(path+f"/groups/{group['id']}/participants",json={'participant_ids':[ids[0],ids[2]],'mode':'pair'}).raise_for_status()
        expect(page.locator('#student-name')).to_have_text('Ana + Carla',timeout=10000)
        page.get_by_role('button',name='A minha reflexão',exact=True).click()
        page.get_by_role('button',name='Ana · Por guardar',exact=True).click()
        expect(page.get_by_label('O que te ajudou?')).to_have_value('O corte feito com Bruno.')
        page.get_by_role('button',name='Rever versão guardada',exact=True).click()
        page.get_by_label('O que te ajudou?').fill('Comparei com Carla.')
        page.get_by_role('button',name='Guardar a minha reflexão',exact=True).click()
        expect(page.locator('#reflection-status')).to_contain_text('Reflexão guardada')
        page.reload()
        page.locator('#pending-reflection-list summary').click()
        expect(page.locator('#pending-reflection-list')).to_contain_text('Ana + Bruno')
        expect(page.locator('#pending-reflection-list')).to_contain_text('O corte feito com Bruno.')
        voices=[e for e in teacher.get(path+f'/students/{ids[0]}/history').json()['events'] if e['type']=='individual_reflection']
        assert len(voices)==1 and voices[0]['payload']['strategy']=='Comparei com Carla.'
