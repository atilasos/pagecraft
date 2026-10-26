"""Percurso real de aprovação em lote e atribuições na mesma aula, via Hub."""
import re

import pytest

expect = pytest.importorskip('playwright.sync_api').expect


def seed(page, origin):
    page.request.get(origin + '/api/teacher-bootstrap')
    activities = []
    for index, kind in enumerate(['match', 'pairs', 'syllables', 'gap', 'recall', 'hunt'], 1):
        response = page.request.post(origin + '/api/learning/activities', data={
            'slug': 'm28p-v3-menina-' + kind, 'title': f'Jogo {index} · menina',
            'year': 1, 'duration': 10, 'group': 'm28p-v3', 'criteria': [{'id': 'read', 'pt': 'Leio a palavra.'}],
        })
        assert response.status == 201, response.text()
        activities.append(response.json())
    other = page.request.post(origin + '/api/learning/activities', data={
        'slug': 'fraction-test', 'title': 'Metades na aula', 'year': 2, 'duration': 20,
        'criteria': [{'id': 'half', 'pt': 'Reconheço uma metade.'}],
    }).json()
    cls = page.request.post(origin + '/api/classes', data={
        'name': '2A · roteiro', 'year': 2, 'students': ['Ana', 'Bruno', 'Carla'],
    }).json()
    return activities, other, cls


def approve_word(page, origin):
    page.goto(origin + '/teacher/activities.html')
    # Procurar só um jogo não limita a seleção de todos os jogos da palavra.
    page.locator('#activities').get_by_label('Procurar atividades').fill('Jogo 1')
    page.get_by_role('checkbox', name='menina (6)', exact=True).check()
    expect(page.locator('#publish-selected')).to_have_text('Aprovar e publicar selecionadas (6)')
    dialogs = []
    def approve(dialog):
        dialogs.append(dialog.message)
        dialog.accept()
    page.once('dialog', approve)
    page.locator('#publish-selected').click()
    expect(page.locator('#status')).to_have_text('6 publicadas · 0 por resolver.')
    assert len(dialogs) == 1
    expect(page.locator('#publish-selected')).to_be_disabled()
    page.locator('#activities').get_by_label('Procurar atividades').fill('Metades')
    page.get_by_role('checkbox', name='Selecionar Metades na aula', exact=True).check()
    page.once('dialog', lambda dialog: dialog.accept())
    page.locator('#publish-selected').click()
    expect(page.locator('#status')).to_have_text('1 publicadas · 0 por resolver.')


def test_teacher_distributes_word_and_other_activity_and_pupil_returns_to_own_list(page, studio_origin):
    origin = studio_origin
    activities, other, cls = seed(page, origin)
    approve_word(page, origin)
    page.get_by_role('link', name='Distribuir atividades por alunos', exact=True).click()
    expect(page.locator('#lesson-form'), page.locator('#status').text_content()).not_to_have_attribute('inert', '')
    page.get_by_label('Nome do roteiro', exact=True).fill('Leitura e matemática')
    page.get_by_label('Turma', exact=True).select_option(cls['id'])
    page.get_by_label('Nome do conjunto', exact=True).fill('Leitores')
    page.locator('#students').get_by_role('checkbox', name='Ana', exact=True).check()
    page.locator('#students').get_by_role('checkbox', name='Bruno', exact=True).check()
    page.get_by_role('checkbox', name='menina (6)', exact=True).check()
    page.get_by_role('button', name='Acrescentar conjunto ao roteiro', exact=True).click()
    expect(page.locator('#assignments')).to_contain_text('6 atividades')
    expect(page.locator('#unassigned')).to_contain_text('Carla')
    page.get_by_label('Nome do conjunto', exact=True).fill('Matemática')
    page.locator('#students').get_by_role('checkbox', name='Carla', exact=True).check()
    page.get_by_role('checkbox', name='Selecionar Metades na aula', exact=True).check()
    page.get_by_role('button', name='Acrescentar conjunto ao roteiro', exact=True).click()
    expect(page.locator('#unassigned')).to_have_text('Todos os alunos têm atividades atribuídas.')
    page.get_by_role('button', name='Guardar roteiro da aula', exact=True).click()
    expect(page.locator('#save-status')).to_have_text('Roteiro guardado.')
    lesson = next(l for l in page.request.get(origin + '/api/learning/lessons').json() if l['title'] == 'Leitura e matemática')
    assert len(lesson['assignments']) == 2
    # A entrada comum do aluno reconhece o código do roteiro.
    pupil = page.context.browser.new_context()
    try:
        tab = pupil.new_page()
        tab.goto(origin + '/student/')
        tab.locator('#code-input').fill(lesson['code'])
        tab.locator('#code-form button').click()
        tab.get_by_role('link', name='Ana', exact=True).click()
        expect(tab.locator('#activities article')).to_have_count(6)
        expect(tab.locator('#activities')).not_to_contain_text('Metades')
        tab.get_by_role('link', name='Escolher outro nome', exact=True).click()
        tab.get_by_role('link', name='Carla', exact=True).click()
        expect(tab.locator('#activities article')).to_have_count(1)
        expect(tab.locator('#activities')).to_contain_text('Metades')
        tab.get_by_role('link', name='Começar', exact=True).click()
        expect(tab.get_by_label('Como te chamas?', exact=True)).to_have_value('Carla')
        expect(tab.get_by_label('Como te chamas?', exact=True)).to_have_attribute('readonly', '')
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        tab.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
        tab.get_by_role('button', name='Guardar e terminar', exact=True).click()
        expect(tab.locator('#done')).to_be_visible()
        tab.get_by_role('link', name='Escolher outra atividade do roteiro', exact=True).click()
        expect(tab.locator('#greeting')).to_have_text('Olá, Carla!')
        expect(tab.locator('#activities article')).to_have_count(1)
        reports = page.request.get(origin + '/api/learning/reports').json()
        report = next(r for r in reports if r.get('lesson_code') == lesson['code'])
        assert report['name'] == 'Carla' and report['group'] == cls['name']
        assert report['student_id'] == cls['students'][2]['id']
        assert report['completed_at']
    finally:
        pupil.close()
    # O professor consegue alterar um conjunto existente e encerrar a entrada.
    page.locator('#assignments').get_by_role('button', name='Alterar conjunto', exact=True).first.click()
    page.locator('#students').get_by_role('checkbox', name='Carla', exact=True).check()
    page.get_by_role('button', name='Guardar alteração do conjunto', exact=True).click()
    page.get_by_label('Disponível aos alunos', exact=True).uncheck()
    page.get_by_role('button', name='Guardar roteiro da aula', exact=True).click()
    expect(page.locator('#save-status')).to_have_text('Roteiro guardado.')
    updated = next(l for l in page.request.get(origin + '/api/learning/lessons').json() if l['code'] == lesson['code'])
    assert not updated['active']
    assert cls['students'][2]['id'] in updated['assignments'][0]['student_ids']
    page.get_by_role('link', name='Ver registos deste roteiro', exact=True).click()
    expect(page.locator('#filter-lesson')).to_have_value(lesson['code'])
    expect(page.locator('#reports')).to_contain_text('Carla')
    expect(page.locator('#reports')).to_contain_text('Leitura e matemática')


def test_other_roster_choice_never_renders_previous_pupils_realization(page, studio_origin):
    origin = studio_origin
    page.request.get(origin + '/api/teacher-bootstrap')
    activities, other, cls = seed(page, origin)
    page.request.post(origin + f"/api/learning/activities/{other['code']}/publish")
    ana, bruno, _ = cls['students']
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Trocar nome', 'class_id': cls['id'], 'assignments': [
            {'title': 'Todos', 'student_ids': [ana['id'], bruno['id']], 'activity_codes': [other['code']]},
        ],
    }).json()
    tab = page.context.new_page()
    try:
        tab.goto(origin + f"/{other['code']}?aula={lesson['code']}&aluno={ana['id']}")
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        first = page.request.get(origin + '/api/learning/me').json()
        tab.goto(origin + f"/{other['code']}?aula={lesson['code']}&aluno={bruno['id']}")
        expect(tab.locator('#status')).to_contain_text('outra realização desta atividade')
        expect(tab.locator('#work')).to_be_hidden()
        expect(tab.locator('#done')).to_be_hidden()
        expect(tab.locator('#start-form')).to_be_hidden()
        assert page.request.get(origin + '/api/learning/me').json()['id'] == first['id']
        tab.get_by_role('button', name='Trocar de aluno', exact=True).click()
        expect(tab).to_have_url(re.compile('/aula/' + lesson['code'] + '$'))
        tab.get_by_role('link', name='Bruno', exact=True).click()
        tab.get_by_role('link', name='Começar', exact=True).click()
        tab.get_by_role('button', name='Começar', exact=True).click()
        expect(tab.locator('#work')).to_be_visible()
        second = page.request.get(origin + '/api/learning/me').json()
        assert second['id'] != first['id'] and second['name'] == 'Bruno'
    finally:
        tab.close()


def test_closing_roster_keeps_existing_realization_recoverable(page, studio_origin):
    origin = studio_origin
    _, activity, cls = seed(page, origin)
    page.request.post(origin + f"/api/learning/activities/{activity['code']}/publish")
    ana = cls['students'][0]
    lesson = page.request.post(origin + '/api/learning/lessons', data={
        'title': 'Recuperar depois de encerrar', 'class_id': cls['id'], 'assignments': [
            {'title': 'Leitura', 'student_ids': [ana['id']], 'activity_codes': [activity['code']]},
        ],
    }).json()
    page.goto(origin + f"/{activity['code']}?aula={lesson['code']}&aluno={ana['id']}")
    page.get_by_role('button', name='Começar', exact=True).click()
    expect(page.locator('#work')).to_be_visible()
    first = page.request.get(origin + '/api/learning/me').json()
    response = page.request.put(origin + f"/api/learning/lessons/{lesson['code']}", data={
        'title': lesson['title'], 'assignments': lesson['assignments'], 'revision': lesson['revision'], 'active': False,
    })
    assert response.status == 200
    page.reload()
    expect(page.locator('#work')).to_be_visible()
    assert page.request.get(origin + '/api/learning/me').json()['id'] == first['id']
    page.get_by_role('button', name='Autoavaliar e terminar', exact=True).click()
    page.get_by_role('button', name='Guardar e terminar', exact=True).click()
    expect(page.locator('#done')).to_be_visible()
