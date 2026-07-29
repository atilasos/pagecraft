"""Endpoints de turmas, sessões de aula, eventos e PIT."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..classroom.errors import (
    ClassroomError,
    InvalidPitItemError,
    InvalidSessionEventError,
    SessionClosedError,
    SessionNotFoundError,
    StudentNotInRosterError,
)
from ..classroom.event_types import SESSION_EVENT_TYPES
from ..security import require_teacher

router = APIRouter(prefix="/api", tags=["classroom"])
teacher_only = Depends(require_teacher)


class ClassRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1, le=4)
    students: list[str] = Field(default_factory=list, max_length=40)


class SessionRequest(BaseModel):
    class_id: str
    activity_slug: str
    activity_title: str = ""


class ClaimRequest(BaseModel):
    student_id: str


class EventsRequest(BaseModel):
    student_token: str
    events: list[dict] = Field(max_length=20)


class PitRequest(BaseModel):
    student_token: str
    text: str = Field(min_length=1, max_length=280)
    status: str = "planned"
    item_id: str | None = None


class TeacherMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=400)
    student_id: str | None = None


class ControlRequest(BaseModel):
    action: str = Field(pattern="^(highlight|freeze|unfreeze)$")
    unit_id: str | None = Field(default=None, max_length=40)
    unit_label: str | None = Field(default=None, max_length=200)
    student_id: str | None = None


def _svc(request: Request):
    return request.app.state.classroom


async def _domain(command):
    try:
        return await command
    except (SessionNotFoundError, StudentNotInRosterError) as error:
        raise HTTPException(404, str(error)) from error
    except SessionClosedError as error:
        raise HTTPException(409, str(error)) from error
    except (InvalidPitItemError, InvalidSessionEventError) as error:
        raise HTTPException(400, str(error)) from error
    except ClassroomError as error:
        raise HTTPException(409, str(error)) from error


# ---- turmas ----


@router.post("/classes", dependencies=[teacher_only])
async def create_class(body: ClassRequest, request: Request):
    return await _svc(request).create_class(body.name, body.year, body.students)


@router.get("/classes", dependencies=[teacher_only])
async def list_classes(request: Request):
    return await _svc(request).list_classes()


@router.get("/classes/{class_id}/report", dependencies=[teacher_only])
async def class_report(class_id: str, request: Request):
    from fastapi.responses import PlainTextResponse

    from ..classroom.reports import build_class_report, report_to_markdown

    svc = _svc(request)
    cls = await svc.get_class(class_id)
    if not cls:
        raise HTTPException(404, "turma não encontrada")
    sessions = await svc.list_sessions()
    report = await build_class_report(
        request.app.state.storage,
        cls,
        sessions,
        date_from=request.query_params.get("from", ""),
        date_to=request.query_params.get("to", ""),
    )
    if request.query_params.get("format") == "md":
        return PlainTextResponse(report_to_markdown(report), media_type="text/markdown; charset=utf-8")
    return report


@router.put("/classes/{class_id}/students", dependencies=[teacher_only])
async def update_students(class_id: str, body: ClassRequest, request: Request):
    cls = await _svc(request).update_class_students(class_id, body.students)
    if not cls:
        raise HTTPException(404, "turma não encontrada")
    return cls


# ---- sessões ----


@router.post("/sessions", dependencies=[teacher_only])
async def create_session(body: SessionRequest, request: Request):
    svc = _svc(request)
    session = await svc.create_session(body.class_id, body.activity_slug, body.activity_title)
    if not session:
        raise HTTPException(404, "turma não encontrada")
    return svc.project_session(session, role="teacher")


@router.get("/sessions", dependencies=[teacher_only])
async def list_sessions(request: Request):
    svc = _svc(request)
    return [
        svc.project_session(session, role="teacher")
        for session in await svc.list_sessions()
    ]


@router.get("/sessions/{session_id}", dependencies=[teacher_only])
async def get_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")
    return svc.project_session(session, role="teacher")


@router.post("/sessions/{session_id}/close", dependencies=[teacher_only])
async def close_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await _domain(svc.close_session(session_id))
    return svc.project_session(session, role="teacher")


@router.get("/join/{join_code}")
async def join_by_code(join_code: str, request: Request):
    svc = _svc(request)
    session = await svc.find_by_code(join_code)
    if not session:
        raise HTTPException(404, "não há nenhuma aula com esse código")
    return svc.project_session(session, role="student")


@router.get("/sessions/{session_id}/me")
async def whoami(session_id: str, request: Request):
    """Retoma de sessão do aluno: valida o token guardado no dispositivo e
    devolve a identidade + estado público da sessão (sem tokens de terceiros)."""
    svc = _svc(request)
    token = request.query_params.get("student_token", "")
    student_id = await svc.student_for_token(session_id, token, require_live=False)
    if not student_id:
        raise HTTPException(401, "token inválido")
    session = await svc.get_session(session_id)
    entry = session["roster"][student_id]
    return {
        "student_id": student_id,
        "display_name": entry["display_name"],
        "session": svc.project_session(session, role="student"),
    }


@router.post("/sessions/{session_id}/claim")
async def claim(session_id: str, body: ClaimRequest, request: Request):
    result = await _domain(
        _svc(request).claim_identity(session_id, body.student_id)
    )
    if not result:
        raise HTTPException(409, "esse nome já foi escolhido (pede ao professor para libertar)")
    return result


@router.post("/sessions/{session_id}/release/{student_id}", dependencies=[teacher_only])
async def release(session_id: str, student_id: str, request: Request):
    await _domain(_svc(request).release_identity(session_id, student_id))
    return {"ok": True}


# ---- eventos ----


@router.get("/session-event-types")
async def session_event_types():
    """Declaração pública e estática do vocabulário da Sessão de aula."""
    return {"version": 1, "types": SESSION_EVENT_TYPES.declaration()}


@router.post("/sessions/{session_id}/events")
async def post_events(session_id: str, body: EventsRequest, request: Request):
    svc = _svc(request)
    student_id = await svc.student_for_token(session_id, body.student_token)
    if not student_id:
        raise HTTPException(401, "token inválido")
    accepted = await _domain(svc.ingest_events(session_id, student_id, body.events))
    feedback = request.app.state.feedback
    for record in accepted:
        if record["type"] == "feedback_request":
            await feedback.request(session_id, student_id, record.get("unit_id"), record.get("payload", {}))
    return {"accepted": [r["event_id"] for r in accepted]}


@router.post("/sessions/{session_id}/message", dependencies=[teacher_only])
async def teacher_message(session_id: str, body: TeacherMessageRequest, request: Request):
    return await _domain(
        _svc(request).send_teacher_message(
            session_id,
            body.text,
            student_id=body.student_id,
        )
    )


@router.post("/sessions/{session_id}/control", dependencies=[teacher_only])
async def session_control(session_id: str, body: ControlRequest, request: Request):
    """Controlo de sala: chamar a atenção para uma parte (highlight, para todos
    ou para um aluno) e congelar/descongelar os ecrãs para olharem para o quadro."""
    return await _domain(
        _svc(request).control_session(
            session_id,
            body.action,
            student_id=body.student_id,
            unit_id=body.unit_id,
            unit_label=body.unit_label or "",
        )
    )


@router.post("/sessions/{session_id}/pit")
async def pit(session_id: str, body: PitRequest, request: Request):
    svc = _svc(request)
    student_id = await svc.student_for_token(session_id, body.student_token)
    if not student_id:
        raise HTTPException(401, "token inválido")
    item = await _domain(
        svc.upsert_pit_item(
            session_id, student_id, body.text, body.status, body.item_id
        )
    )
    if not item:
        raise HTTPException(400, "item PIT inválido")
    return item


@router.get("/sessions/{session_id}/stream")
async def stream_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")

    role = request.query_params.get("role", "")
    student_id = None
    token = ""
    if role == "teacher":
        require_teacher(request)
    elif role == "student":
        token = request.query_params.get("student_token", "")
        # permitir ligação numa sessão já fechada (para ver o histórico próprio)
        student_id = await svc.student_for_token(session_id, token, require_live=False)
        if not student_id:
            raise HTTPException(401, "token inválido")
    else:
        raise HTTPException(400, "role tem de ser teacher ou student")

    visible_types = {
        event_type.name for event_type in SESSION_EVENT_TYPES.visible_to(role)
    }
    last_id = request.headers.get("last-event-id") or request.query_params.get("after", "0")
    try:
        after_seq = int(last_id)
    except ValueError:
        after_seq = 0

    log = svc.events_log(session_id)

    def visible(record: dict) -> bool:
        if record.get("type") not in visible_types:
            return False
        if role == "teacher":
            return True
        target = record.get("student_id")
        return target is None or target == student_id

    async def gen():
        async for record in log.subscribe(after_seq):
            if role == "student":
                # revalidar a cada entrega: se o professor libertou a
                # identidade, o stream antigo morre em vez de vazar eventos
                current = await svc.student_for_token(session_id, token, require_live=False)
                if current != student_id:
                    break
            if not visible(record):
                continue
            yield (
                f"id: {record['seq']}\n"
                f"event: {record['type']}\n"
                f"data: {json.dumps(record, ensure_ascii=False)}\n\n"
            )
            if record.get("type") == "session_closed":
                break

    return StreamingResponse(gen(), media_type="text/event-stream")
