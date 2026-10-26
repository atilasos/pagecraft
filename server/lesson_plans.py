"""Roteiros de aula: várias atividades atribuídas a conjuntos de alunos."""

from __future__ import annotations

import secrets

from fastapi import HTTPException

from .events import utcnow
from .learning import ALPHABET


class LessonPlans:
    def __init__(self, storage, learning, classroom):
        self.storage = storage
        self.learning = learning
        self.classroom = classroom

    def path(self, code):
        return self.storage.path("learning", "lessons", f"{code.upper()}.json")

    async def get(self, code, *, active=False):
        lesson = await self.storage.read_json(self.path(code))
        if lesson is None:
            raise HTTPException(404, "Roteiro da aula não encontrado.")
        if active and not lesson['active']:
            raise HTTPException(409, "Este roteiro está encerrado. Pede ajuda ao professor.")
        return lesson

    async def list(self):
        directory = self.storage.root / "learning" / "lessons"
        lessons = [await self.storage.read_json(path) for path in directory.glob('*.json')]
        return sorted(lessons, key=lambda lesson: lesson['updated_at'], reverse=True)

    async def validate_assignments(self, students, assignments):
        roster = {student['id'] for student in students}
        activities = await self.learning.activities()
        for assignment in assignments:
            if set(assignment['student_ids']) - roster:
                raise HTTPException(422, "Seleciona apenas alunos desta turma.")
            assignment['student_ids'] = list(dict.fromkeys(assignment['student_ids']))
            assignment['activity_codes'] = list(dict.fromkeys(code.upper() for code in assignment['activity_codes']))
            for code in assignment['activity_codes']:
                activity = activities.get(code)
                if not activity or not activity['published'] or activity.get('archived_at'):
                    raise HTTPException(422, f"A atividade {code} precisa de estar aprovada e disponível.")

    async def create(self, data):
        cls = await self.classroom.get_class(data['class_id'])
        if not cls:
            raise HTTPException(404, "Turma não encontrada.")
        await self.validate_assignments(cls['students'], data['assignments'])
        # Sete caracteres distinguem roteiros das sessões (6) e dos grupos (8).
        async with self.learning.lock('lesson-codes'):
            code = ''.join(secrets.choice(ALPHABET) for _ in range(7))
            while self.path(code).exists():
                code = ''.join(secrets.choice(ALPHABET) for _ in range(7))
            lesson = dict(data, code=code, class_name=cls['name'], year=cls['year'],
                          students=cls['students'], active=data.get('active', True), revision=1,
                          created_at=utcnow(), updated_at=utcnow())
            await self.storage.write_json(self.path(code), lesson)
        return lesson

    async def update(self, code, data):
        async with self.learning.lock('lesson:' + code.upper()):
            lesson = await self.get(code)
            if data.pop('revision') != lesson['revision']:
                raise HTTPException(409, "O roteiro foi alterado noutro separador. Volta a abri-lo antes de guardar.")
            await self.validate_assignments(lesson['students'], data['assignments'])
            lesson.update(data, revision=lesson['revision'] + 1, updated_at=utcnow())
            await self.storage.write_json(self.path(code), lesson)
        return lesson

    async def entry(self, code):
        lesson = await self.get(code, active=True)
        # O código permite escolher o nome, nunca consultar realizações anteriores.
        return {key: lesson[key] for key in ('code', 'title', 'class_name', 'year', 'students')}

    async def student_work(self, code, student_id):
        lesson = await self.get(code, active=True)
        student = next((s for s in lesson['students'] if s['id'] == student_id), None)
        if student is None:
            raise HTTPException(404, "Aluno não encontrado neste roteiro.")
        codes = dict.fromkeys(code for assignment in lesson['assignments']
                              if student_id in assignment['student_ids']
                              for code in assignment['activity_codes'])
        activities = await self.learning.activities()
        selected = [activities[code] for code in codes if code in activities
                    and activities[code]['published'] and not activities[code].get('archived_at')]
        return lesson, student, selected

    async def start_context(self, code, student_id, activity_code):
        lesson, student, activities = await self.student_work(code, student_id)
        if activity_code.upper() not in {activity['code'] for activity in activities}:
            raise HTTPException(403, "Esta atividade não está atribuída a este aluno no roteiro.")
        return dict(name=student['display_name'], group=lesson['class_name'], mode='classroom',
                    lesson_code=lesson['code'], class_id=lesson['class_id'], student_id=student_id)
