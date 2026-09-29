"""HTTP boundary for permanent activities and private reports."""
from __future__ import annotations

import json
import re
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from ..access import (RateLimitOperation, Role, RoutePolicy, TrustChannel, access_policy,
                      rate_limited)
from ..learning import LEARNING_COOKIE

ACTIVITY_CONTENT_HEADERS = {
        'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; media-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'",
        'Cache-Control': 'no-store',
    }

router = APIRouter()
Slug = Annotated[str, Field(pattern=r'^[a-z0-9][a-z0-9-]{0,100}$')]
Code = Annotated[str, Field(pattern=r'^[A-Za-z2-9]{6}$')]
Identifier = Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
Short = Annotated[str, Field(min_length=1, max_length=120)]
Level = Literal['support', 'intermediate', 'challenge']
Language = Literal['pt', 'en']


class Criterion(BaseModel):
    id: Annotated[str, Field(pattern=r'^[a-z0-9_-]{1,40}$')]
    pt: Annotated[str, Field(min_length=1, max_length=300)]
    en: Annotated[str, Field(max_length=300)] = ''


class ActivityInput(BaseModel):
    slug: Slug
    title: Short
    title_en: str = Field(default="", max_length=120)
    year: int = Field(ge=1, le=4)
    duration: int = Field(ge=5, le=180)
    group: str = Field(default='', max_length=80)
    languages: list[Language] = Field(default=['pt'], min_length=1, max_length=2)
    criteria: list[Criterion] = Field(min_length=1, max_length=8)

    @field_validator('criteria')
    @classmethod
    def unique_criteria(cls, criteria):
        if len({c.id for c in criteria}) != len(criteria):
            raise ValueError('Os critérios precisam de identificadores distintos.')
        return criteria


class StartInput(BaseModel):
    name: Short
    group: str = Field(default='', max_length=80)
    mode: Literal['classroom', 'home'] = 'classroom'
    language: Language = 'pt'
    level: Level = 'intermediate'

    @field_validator('name')
    @classmethod
    def name_not_blank(cls, value):
        if not value.strip():
            raise ValueError('Escreve o teu nome.')
        return value


class Event(BaseModel):
    id: Annotated[str, Field(min_length=1, max_length=80)]
    type: Literal['activity_loaded', 'unit_started', 'attempt', 'discovery',
                  'assessment_result', 'help_needed', 'share_requested', 'language_changed', 'level_changed',
                  'activity_state']
    unitId: str = Field(default='', max_length=80)
    payload: dict = Field(default_factory=dict)

    @field_validator('payload')
    @classmethod
    def small_payload(cls, value):
        if len(json.dumps(value)) > 4096:
            raise ValueError('Registo demasiado longo.')
        return value


class EventBatch(BaseModel):
    events: list[Event] = Field(max_length=100)


class Assessment(BaseModel):
    answers: dict[str, Literal['alone', 'help', 'practising', 'skip']] = Field(default_factory=dict)
    strategy: str = Field(default='', max_length=1500)
    next_step: str = Field(default='', max_length=1500)
    language: Language = 'pt'
    level: Level = 'intermediate'


class Annotation(BaseModel):
    name: Short
    group: str = Field(default='', max_length=80)
    teacher_note: str = Field(default='', max_length=5000)


async def visible_activity(request, code):
    activity = await request.app.state.learning.activity(code)
    if not activity['published'] and request.state.access.role is not Role.TEACHER:
        raise HTTPException(404, 'Atividade não encontrada.')
    return activity


@router.get('/api/learning/activities')
@access_policy(RoutePolicy.TEACHER)
async def activities(request: Request):
    return list((await request.app.state.learning.activities()).values())


@router.post('/api/learning/activities', status_code=201)
@access_policy(RoutePolicy.TEACHER)
async def register(data: ActivityInput, request: Request):
    if 'en' in data.languages and any(not c.en for c in data.criteria):
        raise HTTPException(422, 'Traduz todos os critérios para inglês.')
    return await request.app.state.learning.register(data.model_dump())


@router.post('/api/learning/activities/{code}/publish')
@access_policy(RoutePolicy.TEACHER)
async def publish(code: Code, request: Request):
    return await request.app.state.learning.publish(code)


@router.get('/api/learning/activities/{code}')
@access_policy(RoutePolicy.PUBLIC)
async def activity(code: Code, request: Request):
    return await visible_activity(request, code)


@router.get('/api/learning/activities/{code}/content')
@access_policy(RoutePolicy.PUBLIC)
async def content(code: Code, request: Request):
    activity = await visible_activity(request, code)
    return FileResponse(request.app.state.learning.content_path(activity), headers=ACTIVITY_CONTENT_HEADERS)


@router.post('/api/learning/activities/{code}/start', status_code=201)
@access_policy(RoutePolicy.PUBLIC)
@rate_limited(RateLimitOperation.ACTIVITY_START)
async def start(code: Code, data: StartInput, request: Request, response: Response):
    svc = request.app.state.learning
    activity = await visible_activity(request, code)
    if data.language not in activity['languages']:
        raise HTTPException(422, 'Língua indisponível nesta atividade.')
    attempt, cookie = await svc.start(activity, data.model_dump(), preview=not activity['published'])
    response.set_cookie(LEARNING_COOKIE, cookie, httponly=True, samesite='strict',
                        secure=request.state.access.channel is TrustChannel.CLOUDFLARE,
                        max_age=86400, path='/')
    return svc.public_attempt(attempt)


async def current_id(request):
    # Teachers exercise drafts with the separate realization cookie too.
    identifier = await request.app.state.learning.resolve(request.cookies.get(LEARNING_COOKIE, ''))
    if identifier is None:
        raise HTTPException(401, 'Volta a entrar na atividade.')
    return identifier


@router.get('/api/learning/me')
@access_policy(RoutePolicy.LEARNER, RoutePolicy.TEACHER)
async def me(request: Request):
    return request.app.state.learning.public_attempt(await request.app.state.learning.attempt(await current_id(request)))


@router.post('/api/learning/me/events')
@access_policy(RoutePolicy.LEARNER, RoutePolicy.TEACHER)
async def events(data: EventBatch, request: Request):
    count = await request.app.state.learning.record(await current_id(request), [e.model_dump() for e in data.events])
    return {'accepted': count}


@router.post('/api/learning/me/finish')
@access_policy(RoutePolicy.LEARNER, RoutePolicy.TEACHER)
async def finish(data: Assessment, request: Request):
    result = await request.app.state.learning.finish(await current_id(request), data.model_dump())
    return request.app.state.learning.public_attempt(result)


@router.post('/api/learning/me/leave', status_code=204)
@access_policy(RoutePolicy.PUBLIC)
async def leave(response: Response):
    response.delete_cookie(LEARNING_COOKIE, path='/')


@router.get('/api/learning/reports')
@access_policy(RoutePolicy.TEACHER)
async def reports(request: Request):
    return await request.app.state.learning.reports()


@router.patch('/api/learning/reports/{identifier}')
@access_policy(RoutePolicy.TEACHER)
async def annotate(identifier: Identifier, data: Annotation, request: Request):
    result = await request.app.state.learning.annotate(identifier, data.model_dump())
    return request.app.state.learning.public_attempt(result, teacher=True)


def report_markdown(attempt):
    def safe(value):
        return re.sub(r'([\\`*_{}\[\]()!#|])', r'\\\1', str(value)).replace('<', '&lt;').replace('>', '&gt;').replace('\r', '').replace('\n', '\n    ')
    lines = [f"# Registo de trabalho — {safe(attempt['title'])}",
             f"Aluno: {safe(attempt['name'])}", f"Turma: {safe(attempt['group'])}",
             f"Início: {attempt['started_at']}", f"Contexto: {attempt['mode']}",
             f"Fim: {attempt['completed_at'] or 'em curso'}", '', '## Evidências no PageCraft']
    from ..learning_reports import describe_evidence
    for event in attempt['events']:
        for description in describe_evidence(event):
            lines.append(f"- {event['received_at']} · {safe(description)}")
    lines += ['', '## Autoavaliação do aluno']
    assessment = attempt['assessment']
    if assessment:
        labels = {'alone': 'Consegui com autonomia', 'help': 'Consegui com ajuda',
                  'practising': 'Quero continuar a praticar', 'skip': 'Sem resposta'}
        for criterion in attempt['criteria']:
            lines.append(f"- {safe(criterion['pt'])}: {labels.get(assessment['answers'].get(criterion['id']), 'Sem resposta')}")
        lines += [f"Estratégia: {safe(assessment['strategy'])}", f"Próximo passo proposto pelo aluno: {safe(assessment['next_step'])}"]
    else:
        lines.append('Ainda não submetida.')
    lines += ['', '## Observação e próximo passo do professor', safe(attempt['teacher_note']) or 'Por registar.',
              '', 'O trabalho realizado em aplicações externas não é observado automaticamente pelo PageCraft.']
    return '\n\n'.join(lines) + '\n'


@router.get('/api/learning/reports/{identifier}/download')
@access_policy(RoutePolicy.TEACHER)
async def download(identifier: Identifier, request: Request):
    attempt = await request.app.state.learning.attempt(identifier)
    return PlainTextResponse(report_markdown(attempt), media_type='text/markdown',
                             headers={'Content-Disposition': f'attachment; filename="pagecraft-{identifier}.md"'})


@router.post('/api/teacher-pairing')
@access_policy(RoutePolicy.TEACHER)
async def pairing():
    raise HTTPException(410, 'O acesso remoto passou a usar código por e-mail no Cloudflare Access.')


@router.post('/api/teacher-login')
@access_policy(RoutePolicy.PUBLIC)
async def teacher_login():
    raise HTTPException(410, 'Entra pela área do professor com o teu e-mail.')


@router.post('/api/teacher-logout', status_code=204)
@access_policy(RoutePolicy.PUBLIC)
async def teacher_logout(response: Response):
    from ..access import TEACHER_COOKIE_NAME
    response.delete_cookie(TEACHER_COOKIE_NAME, path='/')
