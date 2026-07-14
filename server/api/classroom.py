"""Endpoints de turmas, sessões de aula, eventos e PIT."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..security import require_teacher

router = APIRouter(prefix="/api", tags=["classroom"])
teacher_only = Depends(require_teacher)

STUDENT_VISIBLE_TYPES = {"ai_feedback", "teacher_message", "session_closed", "pit_updated"}


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


def _svc(request: Request):
    return request.app.state.classroom


def _public_session(session: dict) -> dict:
    """Versão sem tokens, segura para o browser do aluno."""
    return {
        "id": session["id"],
        "class_name": session["class_name"],
        "activity_slug": session["activity_slug"],
        "activity_title": session["activity_title"],
        "status": session["status"],
        "roster": [
            {"student_id": sid, "display_name": e["display_name"], "taken": bool(e["token"])}
            for sid, e in session["roster"].items()
        ],
    }


def _teacher_session(session: dict) -> dict:
    """Para o professor: tudo menos os tokens dos alunos (nunca saem do servidor)."""
    out = dict(session)
    out["roster"] = {
        sid: {k: v for k, v in entry.items() if k != "token"} | {"taken": bool(entry.get("token"))}
        for sid, entry in session["roster"].items()
    }
    return out


# ---- turmas ----


@router.post("/classes", dependencies=[teacher_only])
async def create_class(body: ClassRequest, request: Request):
    return await _svc(request).create_class(body.name, body.year, body.students)


@router.get("/classes", dependencies=[teacher_only])
async def list_classes(request: Request):
    return await _svc(request).list_classes()


@router.put("/classes/{class_id}/students", dependencies=[teacher_only])
async def update_students(class_id: str, body: ClassRequest, request: Request):
    cls = await _svc(request).update_class_students(class_id, body.students)
    if not cls:
        raise HTTPException(404, "turma não encontrada")
    return cls


# ---- sessões ----


@router.post("/sessions", dependencies=[teacher_only])
async def create_session(body: SessionRequest, request: Request):
    session = await _svc(request).create_session(body.class_id, body.activity_slug, body.activity_title)
    if not session:
        raise HTTPException(404, "turma não encontrada")
    return _teacher_session(session)


@router.get("/sessions", dependencies=[teacher_only])
async def list_sessions(request: Request):
    return [_teacher_session(s) for s in await _svc(request).list_sessions()]


@router.get("/sessions/{session_id}", dependencies=[teacher_only])
async def get_session(session_id: str, request: Request):
    session = await _svc(request).get_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")
    return _teacher_session(session)


@router.post("/sessions/{session_id}/close", dependencies=[teacher_only])
async def close_session(session_id: str, request: Request):
    session = await _svc(request).close_session(session_id)
    if not session:
        raise HTTPException(404, "sessão não encontrada")
    return _teacher_session(session)


@router.get("/join/{join_code}")
async def join_by_code(join_code: str, request: Request):
    session = await _svc(request).find_by_code(join_code)
    if not session:
        raise HTTPException(404, "não há nenhuma aula com esse código")
    return _public_session(session)


@router.post("/sessions/{session_id}/claim")
async def claim(session_id: str, body: ClaimRequest, request: Request):
    result = await _svc(request).claim_identity(session_id, body.student_id)
    if not result:
        raise HTTPException(409, "esse nome já foi escolhido (pede ao professor para libertar)")
    return result


@router.post("/sessions/{session_id}/release/{student_id}", dependencies=[teacher_only])
async def release(session_id: str, student_id: str, request: Request):
    ok = await _svc(request).release_identity(session_id, student_id)
    if not ok:
        raise HTTPException(404, "aluno não encontrado")
    return {"ok": True}


# ---- eventos ----


@router.post("/sessions/{session_id}/events")
async def post_events(session_id: str, body: EventsRequest, request: Request):
    svc = _svc(request)
    student_id = await svc.student_for_token(session_id, body.student_token)
    if not student_id:
        raise HTTPException(401, "token inválido")
    accepted = await svc.ingest_events(session_id, student_id, body.events)
    feedback = request.app.state.feedback
    for record in accepted:
        if record["type"] == "feedback_request":
            await feedback.request(session_id, student_id, record.get("unit_id"), record.get("payload", {}))
    return {"accepted": [r["event_id"] for r in accepted]}


@router.post("/sessions/{session_id}/message", dependencies=[teacher_only])
async def teacher_message(session_id: str, body: TeacherMessageRequest, request: Request):
    record = await _svc(request).emit_teacher_event(
        session_id, "teacher_message", {"text": body.text}, student_id=body.student_id
    )
    return record


@router.post("/sessions/{session_id}/pit")
async def pit(session_id: str, body: PitRequest, request: Request):
    svc = _svc(request)
    student_id = await svc.student_for_token(session_id, body.student_token)
    if not student_id:
        raise HTTPException(401, "token inválido")
    item = await svc.upsert_pit_item(session_id, student_id, body.text, body.status, body.item_id)
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

    last_id = request.headers.get("last-event-id") or request.query_params.get("after", "0")
    try:
        after_seq = int(last_id)
    except ValueError:
        after_seq = 0

    log = svc.events_log(session_id)

    def visible(record: dict) -> bool:
        if role == "teacher":
            return True
        if record.get("type") not in STUDENT_VISIBLE_TYPES:
            return False
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
