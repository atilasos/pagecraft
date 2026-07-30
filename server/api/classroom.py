"""Endpoints de turmas, sessões de aula, eventos e PIT."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from ..access import Role, RoutePolicy, access_policy
from ..classroom.errors import (
    ClassroomError,
    InvalidPitItemError,
    InvalidSessionEventError,
    SessionClosedError,
    SessionNotFoundError,
    StudentNotInRosterError,
)
from ..classroom.event_types import SESSION_EVENT_TYPES
from ..classroom.live_state import (
    changed_session_frame,
    changed_student_frames,
    session_state_snapshot,
)

router = APIRouter(prefix="/api", tags=["classroom"])


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


class ReleaseRequest(BaseModel):
    reset_progress: bool = False


class EventsRequest(BaseModel):
    student_token: str
    events: list[dict] = Field(max_length=20)


class CreatePitItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_token: str
    text: str = Field(min_length=1, max_length=280)


class AdvancePitItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_token: str


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


@router.post("/classes")
@access_policy(RoutePolicy.TEACHER)
async def create_class(body: ClassRequest, request: Request):
    return await _svc(request).create_class(body.name, body.year, body.students)


@router.get("/classes")
@access_policy(RoutePolicy.TEACHER)
async def list_classes(request: Request):
    return await _svc(request).list_classes()


@router.get("/classes/{class_id}/report")
@access_policy(RoutePolicy.TEACHER)
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


@router.put("/classes/{class_id}/students")
@access_policy(RoutePolicy.TEACHER)
async def update_students(class_id: str, body: ClassRequest, request: Request):
    cls = await _svc(request).update_class_students(class_id, body.students)
    if not cls:
        raise HTTPException(404, "turma não encontrada")
    return cls


# ---- sessões ----


@router.post("/sessions")
@access_policy(RoutePolicy.TEACHER)
async def create_session(body: SessionRequest, request: Request):
    svc = _svc(request)
    session = await svc.create_session(body.class_id, body.activity_slug, body.activity_title)
    if not session:
        raise HTTPException(404, "turma não encontrada")
    return svc.project_session(session, role="teacher")


@router.get("/sessions")
@access_policy(RoutePolicy.TEACHER)
async def list_sessions(request: Request):
    svc = _svc(request)
    return [
        svc.project_session(session, role="teacher")
        for session in await svc.list_sessions()
    ]


@router.get("/sessions/{session_id}")
@access_policy(RoutePolicy.TEACHER)
async def get_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")
    return svc.project_session(session, role="teacher")


@router.post("/sessions/{session_id}/close")
@access_policy(RoutePolicy.TEACHER)
async def close_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await _domain(svc.close_session(session_id))
    return svc.project_session(session, role="teacher")


@router.get("/join/{join_code}")
@access_policy(RoutePolicy.PUBLIC)
async def join_by_code(join_code: str, request: Request):
    svc = _svc(request)
    session = await svc.find_by_code(join_code)
    if not session:
        raise HTTPException(404, "não há nenhuma aula com esse código")
    return svc.project_session(session, role="student")


@router.get("/sessions/{session_id}/me")
@access_policy(RoutePolicy.STUDENT)
async def whoami(session_id: str, request: Request):
    """Retoma de sessão do aluno: valida o token guardado no dispositivo e
    devolve a identidade + estado público da sessão (sem tokens de terceiros)."""
    svc = _svc(request)
    student_id = request.state.access.student_id
    session = await svc.get_session(session_id)
    entry = session["roster"][student_id]
    return {
        "student_id": student_id,
        "display_name": entry["display_name"],
        "session": svc.project_session(session, role="student"),
    }


@router.post("/sessions/{session_id}/claim")
@access_policy(RoutePolicy.PUBLIC)
async def claim(session_id: str, body: ClaimRequest, request: Request):
    result = await _domain(
        _svc(request).claim_identity(session_id, body.student_id)
    )
    if not result:
        raise HTTPException(409, "esse nome já foi escolhido (pede ao professor para libertar)")
    return result


@router.post("/sessions/{session_id}/release/{student_id}")
@access_policy(RoutePolicy.TEACHER)
async def release(
    session_id: str,
    student_id: str,
    request: Request,
    body: ReleaseRequest | None = None,
):
    await _domain(
        _svc(request).release_identity(
            session_id,
            student_id,
            reset_progress=body.reset_progress if body else False,
        )
    )
    return {"ok": True}


# ---- eventos ----


@router.get("/session-event-types")
@access_policy(RoutePolicy.TEACHER)
async def session_event_types():
    """Declaração estática do vocabulário da Sessão de aula para o Professor."""
    return {"version": 1, "types": SESSION_EVENT_TYPES.declaration()}


@router.post("/sessions/{session_id}/events")
@access_policy(RoutePolicy.STUDENT)
async def post_events(session_id: str, body: EventsRequest, request: Request):
    svc = _svc(request)
    student_id = request.state.access.student_id
    accepted = await _domain(svc.ingest_events(session_id, student_id, body.events))
    return {"accepted": [r["event_id"] for r in accepted]}


@router.post("/sessions/{session_id}/message")
@access_policy(RoutePolicy.TEACHER)
async def teacher_message(session_id: str, body: TeacherMessageRequest, request: Request):
    return await _domain(
        _svc(request).send_teacher_message(
            session_id,
            body.text,
            student_id=body.student_id,
        )
    )


@router.post("/sessions/{session_id}/control")
@access_policy(RoutePolicy.TEACHER)
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
@access_policy(RoutePolicy.STUDENT)
async def create_pit_item(
    session_id: str, body: CreatePitItemRequest, request: Request
):
    svc = _svc(request)
    student_id = request.state.access.student_id
    return await _domain(
        svc.create_pit_item(session_id, student_id, body.text)
    )


@router.post("/sessions/{session_id}/pit/{item_id}/advance")
@access_policy(RoutePolicy.STUDENT)
async def advance_pit_item(
    session_id: str,
    item_id: str,
    body: AdvancePitItemRequest,
    request: Request,
):
    svc = _svc(request)
    student_id = request.state.access.student_id
    return await _domain(
        svc.advance_pit_item(session_id, student_id, item_id)
    )


@router.get("/sessions/{session_id}/students/{student_id}/history")
@access_policy(RoutePolicy.TEACHER, RoutePolicy.STUDENT)
async def student_history(
    session_id: str,
    student_id: str,
    request: Request,
):
    """Devolve o registo completo da criança, projetado para o papel."""
    svc = _svc(request)
    session = await svc.get_session(session_id)
    if not session or student_id not in session.get("roster", {}):
        raise HTTPException(404, "criança ou sessão não encontrada")

    access = request.state.access
    role = access.role.value
    if access.role is Role.STUDENT:
        if access.student_id != student_id:
            raise HTTPException(403, "uma criança só pode consultar o seu histórico")

    visible_types = {
        event_type.name for event_type in SESSION_EVENT_TYPES.visible_to(role)
    }
    events = [
        record
        for record in await svc.events_log(session_id).replay()
        if record.get("student_id") == student_id
        and record.get("type") in visible_types
    ]
    return {"student_id": student_id, "events": events}


@router.get("/sessions/{session_id}/stream")
@access_policy(RoutePolicy.TEACHER, RoutePolicy.STUDENT)
async def stream_session(session_id: str, request: Request):
    svc = _svc(request)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")

    access = request.state.access
    requested_role = request.query_params.get("role", "")
    student_id = None
    token = ""
    if access.role is Role.TEACHER:
        if requested_role not in {"teacher", "projection"}:
            raise HTTPException(400, "role tem de ser teacher ou projection")
        role = requested_role
    elif access.role is Role.STUDENT:
        if requested_role not in {"", "student"}:
            raise HTTPException(403, "este Papel não pode usar esta vista")
        role = "student"
        student_id = access.student_id
        token = access.student_token
    else:
        raise AssertionError("o middleware de Acesso deixou passar um pedido sem Papel")

    visible_types = {
        event_type.name
        for event_type in SESSION_EVENT_TYPES.visible_to(role)
        if event_type.in_timeline
    }
    log = svc.events_log(session_id)
    events = await log.replay()
    frontier = max((int(record.get("seq", 0)) for record in events), default=0)

    def visible(record: dict) -> bool:
        if record.get("type") not in visible_types:
            return False
        if role == "teacher":
            return True
        target = record.get("student_id")
        if role == "projection":
            return target is None
        return target is None or target == student_id

    async def gen():
        state = session_state_snapshot(
            events,
            session,
            now=svc.now(),
            role=role,
            student_id=student_id,
        )
        yield (
            f"id: {frontier}\n"
            "event: session_state_snapshot\n"
            f"data: {json.dumps(state, ensure_ascii=False)}\n\n"
        )
        if state["session"]["closed"]:
            return

        raw_records = log.subscribe(frontier)
        ticks = svc.live_ticks.subscribe(session_id)
        record_task = asyncio.create_task(anext(raw_records))
        tick_task = asyncio.create_task(anext(ticks))
        try:
            while True:
                done, _ = await asyncio.wait(
                    {record_task, tick_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if record_task in done:
                    try:
                        record = record_task.result()
                    except StopAsyncIteration:
                        return
                    if role == "student":
                        # Se a identidade foi libertada, o stream antigo morre.
                        current = await svc.student_for_token(
                            session_id, token, require_live=False
                        )
                        if current != student_id:
                            return
                    events.append(record)
                    if visible(record):
                        visible_record = (
                            {
                                key: value
                                for key, value in record.items()
                                if key != "student_id"
                            }
                            if role == "projection"
                            else record
                        )
                        yield (
                            f"id: {record['seq']}\n"
                            f"event: {record['type']}\n"
                            f"data: {json.dumps(visible_record, ensure_ascii=False)}\n\n"
                        )
                    current_state = session_state_snapshot(
                        events,
                        session,
                        now=svc.now(),
                        role=role,
                        student_id=student_id,
                    )
                    session_delta = changed_session_frame(state, current_state)
                    if session_delta is not None:
                        yield (
                            "event: session_state_changed\n"
                            f"data: {json.dumps(session_delta, ensure_ascii=False)}\n\n"
                        )
                    for delta in changed_student_frames(state, current_state):
                        yield (
                            "event: student_state_changed\n"
                            f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"
                        )
                    state = current_state
                    if record.get("type") == "session_closed":
                        return
                    record_task = asyncio.create_task(anext(raw_records))

                if tick_task in done:
                    try:
                        tick_now = tick_task.result()
                    except StopAsyncIteration:
                        return
                    current_state = session_state_snapshot(
                        events,
                        session,
                        now=tick_now,
                        role=role,
                        student_id=student_id,
                    )
                    for delta in changed_student_frames(state, current_state):
                        yield (
                            "event: student_state_changed\n"
                            f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"
                        )
                    state = current_state
                    tick_task = asyncio.create_task(anext(ticks))
        finally:
            ticks.close()
            for task in (record_task, tick_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(record_task, tick_task, return_exceptions=True)
            await raw_records.aclose()

    return StreamingResponse(gen(), media_type="text/event-stream")
