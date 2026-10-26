"""Preparação privada do roteiro e entrada pública pelo código da aula."""

from typing import Annotated

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from ..access import RoutePolicy, access_policy
from .learning import Code, LessonCode, Short

router = APIRouter()
StudentId = Annotated[str, Field(pattern=r'^[a-f0-9]{8}$')]


class Assignment(BaseModel):
    title: Short
    student_ids: list[StudentId] = Field(min_length=1, max_length=40)
    activity_codes: list[Code] = Field(min_length=1, max_length=300)

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Dá um nome ao conjunto.')
        return value.strip()


class LessonContent(BaseModel):
    title: Short
    assignments: list[Assignment] = Field(min_length=1, max_length=40)

    @field_validator('title')
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Dá um nome ao roteiro.')
        return value.strip()


class CreateLesson(LessonContent):
    class_id: Annotated[str, Field(pattern=r'^[a-f0-9]{10}$')]


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
                    {key: activity[key] for key in ('code', 'title', 'year', 'duration')}
                    for activity in activities])


@router.get('/aula/{code}')
@access_policy(RoutePolicy.PUBLIC)
async def lesson_page(code: LessonCode, request: Request):
    return FileResponse(request.app.state.config.repo_root / 'server' / 'static' / 'learning' / 'lesson.html')
