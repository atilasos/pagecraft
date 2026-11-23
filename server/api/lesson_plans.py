"""Preparação privada do roteiro e entrada pública pelo código da aula."""

from typing import Annotated

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from ..access import RoutePolicy, access_policy
from .learning import Code, LessonCode, Short

router = APIRouter()
StudentId = Annotated[str, Field(pattern=r'^[a-f0-9]{8}$')]


class Assignment(BaseModel):
    title: Short
    student_ids: list[StudentId] = Field(min_length=1, max_length=40)
    activity_codes: list[Code] = Field(min_length=1, max_length=300)
    # Palavra do método das 28 palavras escolhida para este conjunto, quando existe.
    word: Annotated[str, Field(pattern=r'^[a-z]{2,30}$')] | None = None

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Dá um nome ao conjunto.')
        return value.strip()


class LessonContent(BaseModel):
    title: Short
    assignments: list[Assignment] = Field(max_length=40)
    # Alunos que trabalham fora do PageCraft nesta aula, com uma nota curta do professor.
    offline: dict[StudentId, Annotated[str, Field(max_length=120)]] = Field(default_factory=dict, max_length=40)

    @model_validator(mode='after')
    def something_planned(self):
        if not self.assignments and not self.offline:
            raise ValueError('Atribui atividades a pelo menos um aluno.')
        return self

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Dá um nome ao roteiro.')
        return value.strip()


class CreateLesson(LessonContent):
    class_id: Annotated[str, Field(pattern=r'^[a-f0-9]{10}$')]
    active: bool = True


class UpdateLesson(LessonContent):
    active: bool
    revision: int = Field(ge=1)


@router.get('/api/learning/lessons')
@access_policy(RoutePolicy.TEACHER)
async def lessons(request: Request):
    return await request.app.state.lesson_plans.list()


@router.post('/api/learning/lessons', status_code=201)
@access_policy(RoutePolicy.TEACHER)
async def create_lesson(data: CreateLesson, request: Request):
    return await request.app.state.lesson_plans.create(data.model_dump())


@router.put('/api/learning/lessons/{code}')
@access_policy(RoutePolicy.TEACHER)
async def update_lesson(code: LessonCode, data: UpdateLesson, request: Request):
    return await request.app.state.lesson_plans.update(code, data.model_dump())


class Note(BaseModel):
    text: str = Field(default='', max_length=2000)


class BoardChoice(BaseModel):
    activity_code: Code | None = None


@router.get('/api/learning/lessons/{code}/progress')
@access_policy(RoutePolicy.TEACHER)
async def progress(code: LessonCode, request: Request):
    return await request.app.state.lesson_plans.progress(code)


@router.put('/api/learning/lessons/{code}/notes/{student_id}', status_code=204)
@access_policy(RoutePolicy.TEACHER)
async def note(code: LessonCode, student_id: StudentId, data: Note, request: Request):
    await request.app.state.lesson_plans.set_note(code, student_id, data.text)


@router.put('/api/learning/lessons/{code}/board')
@access_policy(RoutePolicy.TEACHER)
async def board(code: LessonCode, data: BoardChoice, request: Request):
    return await request.app.state.lesson_plans.set_board(code, data.activity_code)


@router.get('/api/learning/lessons/{code}/entry')
@access_policy(RoutePolicy.PUBLIC)
async def entry(code: LessonCode, request: Request):
    return await request.app.state.lesson_plans.entry(code)


@router.get('/api/learning/lessons/{code}/students/{student_id}')
@access_policy(RoutePolicy.PUBLIC)
async def student_work(code: LessonCode, student_id: StudentId, request: Request):
    lesson, student, activities = await request.app.state.lesson_plans.student_work(code, student_id)
    return dict(code=lesson['code'], title=lesson['title'], class_name=lesson['class_name'],
                student=student, year=lesson['year'], activities=[
                    {key: activity.get(key) for key in ('code', 'title', 'year', 'duration', 'm28p')}
                    for activity in activities])


@router.get('/aula/{code}')
@access_policy(RoutePolicy.PUBLIC)
async def lesson_page(code: LessonCode, request: Request):
    return FileResponse(request.app.state.config.repo_root / 'server' / 'static' / 'learning' / 'lesson.html')
