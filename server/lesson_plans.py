"""Roteiros de aula: várias atividades atribuídas a conjuntos de alunos."""

from __future__ import annotations

import secrets
from collections import Counter
from datetime import datetime, timezone

from fastapi import HTTPException

from .activity_collections import describe, sort_key
from .events import utcnow
from .learning import ALPHABET

# «Sem atividade recente no PageCraft»: três minutos sem trabalho reconhecido.
IDLE_SECONDS = 180


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return instant if instant.tzinfo else instant.replace(tzinfo=timezone.utc)


def summarize_realization(attempt: dict) -> dict:
    """Factos observados numa realização, sem juízos automáticos."""
    events = attempt.get("events") or []
    attempts = [e for e in events if e.get("type") == "attempt" and isinstance(e.get("payload"), dict)]
    # Só `correct` explícito conta; descobertas e respostas abertas não têm correção automática.
    correct = sum(1 for e in attempts if e["payload"].get("correct") is True)
    different = sum(1 for e in attempts if e["payload"].get("correct") is False)
    help_events = [e for e in events if e.get("type") in {"help_needed", "help_resolved"}]
    completed_at = attempt.get("completed_at")
    states = [e for e in events if e.get("type") == "activity_state" and isinstance(e.get("payload"), dict)]
    # O jogo declara quando chegou ao fim; a autoavaliação pode ficar por fazer.
    reached_end = bool(states) and states[-1]["payload"].get("readyForReflection") is True
    finished = bool(completed_at) or reached_end
    help_pending = not finished and bool(help_events) and help_events[-1]["type"] == "help_needed"
    seen = [e.get("received_at") for e in events if e.get("received_at")]
    assessment = attempt.get("assessment")
    answers = None
    if assessment:
        counts = Counter(assessment.get("answers", {}).values())
        answers = {key: counts.get(key, 0) for key in ("alone", "help", "practising", "skip")}
    return {
        "id": attempt["id"],
        "code": attempt["code"],
        "title": attempt["title"],
        "level": attempt.get("level"),
        "started_at": attempt["started_at"],
        "completed_at": completed_at,
        "finished": finished,
        "last_at": max(seen + [attempt["started_at"]] + ([completed_at] if completed_at else [])),
        "correct": correct,
        "different": different,
        "unscored": len(attempts) - correct - different,
        "help": sum(1 for e in events if e.get("type") == "help_needed"),
        "help_pending": help_pending,
        "assessment": answers,
        "strategy": (assessment or {}).get("strategy", ""),
        "next_step": (assessment or {}).get("next_step", ""),
    }


class LessonPlans:
    def __init__(self, storage, learning, classroom):
        self.storage = storage
        self.learning = learning
        self.classroom = classroom

    def path(self, code):
        return self.storage.path("learning", "lessons", f"{code.upper()}.json")

    def board_path(self):
        return self.storage.path("learning", "board-focus.json")

    @property
    def activities_dir(self):
        return self.learning.config.activities_dir

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

    async def validate_assignments(self, students, data):
        roster = {student['id'] for student in students}
        activities = await self.learning.activities()
        assignments = data['assignments']
        offline = data.setdefault('offline', {})
        if set(offline) - roster:
            raise HTTPException(422, "Seleciona apenas alunos desta turma.")
        for assignment in assignments:
            if set(assignment['student_ids']) - roster:
                raise HTTPException(422, "Seleciona apenas alunos desta turma.")
            if set(assignment['student_ids']) & set(offline):
                raise HTTPException(422, "Um aluno fora do PageCraft não recebe atividades nesta aula.")
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
        await self.validate_assignments(cls['students'], data)
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
            await self.validate_assignments(lesson['students'], data)
            lesson.update(data, revision=lesson['revision'] + 1, updated_at=utcnow())
            await self.storage.write_json(self.path(code), lesson)
        return lesson

    async def set_note(self, code, student_id, text):
        """A observação do professor não muda a distribuição nem a revisão."""
        async with self.learning.lock('lesson:' + code.upper()):
            lesson = await self.get(code)
            if student_id not in {s['id'] for s in lesson['students']}:
                raise HTTPException(404, "Aluno não encontrado neste roteiro.")
            notes = lesson.setdefault('notes', {})
            if text.strip():
                notes[student_id] = text.strip()
            else:
                notes.pop(student_id, None)
            await self.storage.write_json(self.path(code), lesson)
        return lesson

    async def entry(self, code):
        lesson = await self.get(code, active=True)
        offline = lesson.get('offline') or {}
        # O código permite escolher o nome, nunca consultar realizações anteriores.
        result = {key: lesson[key] for key in ('code', 'title', 'class_name', 'year')}
        result['students'] = [s for s in lesson['students'] if s['id'] not in offline]
        return result

    def assigned_codes(self, lesson, student_id):
        return list(dict.fromkeys(code for assignment in lesson['assignments']
                                  if student_id in assignment['student_ids']
                                  for code in assignment['activity_codes']))

    async def student_work(self, code, student_id):
        lesson = await self.get(code, active=True)
        student = next((s for s in lesson['students'] if s['id'] == student_id), None)
        if student is None:
            raise HTTPException(404, "Aluno não encontrado neste roteiro.")
        codes = self.assigned_codes(lesson, student_id)
        activities = await self.learning.activities()
        selected = [describe(activities[code], self.activities_dir) for code in codes if code in activities
                    and activities[code]['published'] and not activities[code].get('archived_at')]
        return lesson, student, sorted(selected, key=sort_key)

    async def start_context(self, code, student_id, activity_code):
        lesson, student, activities = await self.student_work(code, student_id)
        if activity_code.upper() not in {activity['code'] for activity in activities}:
            raise HTTPException(403, "Esta atividade não está atribuída a este aluno no roteiro.")
        return dict(name=student['display_name'], group=lesson['class_name'], mode='classroom',
                    lesson_code=lesson['code'], class_id=lesson['class_id'], student_id=student_id)

    async def progress(self, code, *, now: datetime | None = None):
        """Vista do professor: o que cada aluno tem, fez e disse, nesta aula."""
        lesson = await self.get(code)
        now = now or datetime.now(timezone.utc)
        catalog = await self.learning.activities()
        attempts = await self.learning.lesson_attempts(lesson['code'])
        by_student: dict[str, list[dict]] = {}
        for attempt in sorted(attempts, key=lambda a: a['started_at']):
            by_student.setdefault(attempt.get('student_id'), []).append(summarize_realization(attempt))
        offline = lesson.get('offline') or {}
        notes = lesson.get('notes') or {}
        words = {}
        for assignment in lesson['assignments']:
            for student_id in assignment['student_ids']:
                if assignment.get('word'):
                    words.setdefault(student_id, []).append(assignment['word'])
        used = {code for assignment in lesson['assignments'] for code in assignment['activity_codes']}
        activities = {}
        for activity_code in used:
            if activity_code in catalog:
                described = describe(catalog[activity_code], self.activities_dir)
                activities[activity_code] = {key: described.get(key) for key in ('code', 'title', 'm28p')}
        students = []
        for student in lesson['students']:
            sid = student['id']
            realizations = by_student.get(sid, [])
            assigned = self.assigned_codes(lesson, sid)
            # O estado segue a última ação em qualquer realização, não a última começada.
            latest = max(realizations, key=lambda r: r['last_at'], default=None)
            current = latest if latest and not latest['finished'] else None
            if sid in offline:
                state, current = 'offline', None
            elif current:
                idle = (now - _instant(current['last_at'])).total_seconds() >= IDLE_SECONDS
                state = 'idle' if idle else 'working'
            elif realizations:
                state = 'finished'
            elif assigned:
                state = 'not_started'
            else:
                state = 'unassigned'
            students.append({
                'id': sid, 'display_name': student['display_name'], 'state': state,
                'offline': offline.get(sid), 'note': notes.get(sid, ''), 'words': words.get(sid, []),
                'assigned': assigned, 'current': current['code'] if current else None,
                'current_title': current['title'] if current else None,
                # Só o pedido da atividade atual fica pendente; os anteriores ficam no histórico.
                'help_pending': bool(current and current['help_pending']),
                'realizations': realizations,
            })
        return {
            'code': lesson['code'], 'title': lesson['title'], 'class_name': lesson['class_name'],
            'active': lesson['active'], 'now': now.isoformat(), 'idle_seconds': IDLE_SECONDS,
            'activities': activities, 'students': students,
        }

    async def set_board(self, code, activity_code):
        """Escolhe a atividade do roteiro que o Quadro mostra; None tira-a do quadro."""
        lesson = await self.get(code)
        async with self.learning.lock('board-focus'):
            if activity_code is None:
                current = await self.storage.read_json(self.board_path())
                if current and current.get('lesson_code') == lesson['code']:
                    self.board_path().unlink(missing_ok=True)
                return None
            activity_code = activity_code.upper()
            used = {c for assignment in lesson['assignments'] for c in assignment['activity_codes']}
            activity = (await self.learning.activities()).get(activity_code)
            if activity_code not in used or not activity or not activity['published']:
                raise HTTPException(422, "Escolhe uma atividade deste roteiro.")
            if not lesson['active']:
                raise HTTPException(409, "Volta a disponibilizar o roteiro antes de o mostrar no quadro.")
            focus = dict(lesson_code=lesson['code'], activity_code=activity_code, set_at=utcnow())
            await self.storage.write_json(self.board_path(), focus)
        # Acorda os streams vivos: o do Quadro deixa de ser atual e fecha, e o
        # Quadro redescobre o que mostrar sem consultas periódicas.
        for session_id in self.classroom.live_session_ids():
            self.classroom.tick_session(session_id)
        return await self.board_focus(lesson)

    async def board_focus(self, lesson=None):
        """Projeção coletiva: título, turma e código de entrada; nunca trabalho individual."""
        focus = await self.storage.read_json(self.board_path())
        if not focus:
            return None
        # Como as sessões ao vivo, a escolha vale só no dia letivo em que foi feita.
        if self.classroom.school_date(_instant(focus['set_at'])) != self.classroom.school_date():
            return None
        if lesson is None:
            lesson = await self.storage.read_json(self.path(focus['lesson_code']))
        if not lesson or lesson['code'] != focus['lesson_code'] or not lesson['active']:
            return None
        used = {c for assignment in lesson['assignments'] for c in assignment['activity_codes']}
        activity = (await self.learning.activities()).get(focus['activity_code'])
        if focus['activity_code'] not in used or not activity or not activity['published']:
            return None
        return {
            'kind': 'lesson', 'id': f"lesson-{lesson['code']}-{activity['code']}-{focus['set_at']}",
            'lesson_code': lesson['code'], 'lesson_title': lesson['title'],
            'class_name': lesson['class_name'], 'activity_code': activity['code'],
            'activity_title': activity['title'], 'set_at': focus['set_at'],
        }
