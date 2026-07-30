"""Boundary HTTP do Emparelhamento e da vista coletiva do Quadro."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from ..access import (
    RoutePolicy,
    access_policy,
    issue_board_cookie,
)


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
    classroom = request.app.state.classroom
    session = next(
        (
            candidate
            for candidate in await classroom.list_sessions()
            if candidate.get("status") == "live"
        ),
        None,
    )
    if session is None:
        return Response(status_code=204)
    return classroom.project_session(session, role="board")
