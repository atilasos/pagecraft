"""Boundary HTTP do Emparelhamento e da vista coletiva do Quadro."""

from __future__ import annotations



from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from ..access import (
    RoutePolicy,
    access_policy,
    issue_board_cookie,
)
from ..classroom.activity_content import session_activity_path
from .classroom import stream_session, _domain, _current_board_session, current_board_view
from .learning import ACTIVITY_CONTENT_HEADERS


router = APIRouter(prefix="/api/board", tags=["board"])


class CompletePairingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pairing_id: str = Field(min_length=1, max_length=128)


class ConfirmPairingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=6, max_length=6)


@router.post("/pairings", status_code=201)
@access_policy(RoutePolicy.PUBLIC)
async def create_pairing(request: Request):
    return await request.app.state.board_pairings.create_challenge()


@router.post("/pairings/complete")
@access_policy(RoutePolicy.PUBLIC)
async def complete_pairing(
    body: CompletePairingRequest,
    request: Request,
    response: Response,
):
    try:
        completed = await request.app.state.board_pairings.complete(
            body.pairing_id
        )
    except KeyError as error:
        raise HTTPException(404, "desafio de emparelhamento inválido") from error
    if completed is None:
        response.status_code = 202
        return {"status": "pending"}

    issue_board_cookie(
        response,
        completed["credential"],
        completed["issued_at"],
        completed["expires_at"],
        secure=request.url.scheme == "https",
    )
    return {
        "status": "paired",
        "expires_at": completed["expires_at"].isoformat(),
    }


@router.post("/pairings/confirm")
@access_policy(RoutePolicy.TEACHER)
async def confirm_pairing(body: ConfirmPairingRequest, request: Request):
    confirmed = await request.app.state.board_pairings.confirm(body.code)
    if not confirmed:
        raise HTTPException(404, "código de emparelhamento inválido")
    return {"status": "confirmed"}


@router.get("/pairing")
@access_policy(RoutePolicy.TEACHER)
async def pairing_state(request: Request):
    return await request.app.state.board_pairings.state()


@router.delete("/pairing", status_code=204)
@access_policy(RoutePolicy.TEACHER)
async def revoke_pairing(request: Request):
    await request.app.state.board_pairings.revoke()


@router.get("/session")
@access_policy(RoutePolicy.BOARD)
async def current_session(request: Request):
    view = await current_board_view(request)
    if view is None:
        return Response(status_code=204)
    return view


@router.get("/lesson-content")
@access_policy(RoutePolicy.BOARD)
async def board_lesson_content(request: Request, atividade: str = ''):
    """O quadro só demonstra a atividade de roteiro que o professor escolheu."""
    focus = await current_board_view(request)
    # Um pedido para uma escolha anterior não recebe a atual com o título errado;
    # o Quadro volta a consultar a escolha e carrega a nova.
    if focus is None or focus.get('kind') != 'lesson' or atividade.upper() != focus['activity_code']:
        raise HTTPException(404, 'Nenhuma atividade de roteiro está no quadro.')
    learning = request.app.state.learning
    path = learning.content_path(await learning.activity(focus['activity_code']))
    return FileResponse(path, headers=ACTIVITY_CONTENT_HEADERS)


@router.get("/sessions/{session_id}/stream")
@access_policy(RoutePolicy.BOARD)
async def stream_board_session(session_id: str, request: Request):
    return await stream_session(session_id, request)


@router.get("/sessions/{session_id}/content")
@access_policy(RoutePolicy.BOARD)
async def board_activity_content(session_id: str, request: Request):
    """The paired board may demonstrate only the activity of its current class."""
    session = await _current_board_session(session_id, request)
    if session is None:
        raise HTTPException(404, 'A sessão já não está no quadro.')
    path = await _domain(session_activity_path(request.app, session['activity_slug']))
    return FileResponse(path, headers=ACTIVITY_CONTENT_HEADERS)
