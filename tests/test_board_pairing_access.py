from datetime import datetime, timezone

import httpx
import pytest

from server import app as app_module
from server.access import BOARD_COOKIE_NAME


@pytest.fixture
async def board_http(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    clock = {"now": datetime(2026, 7, 30, 9, 0, tzinfo=timezone.utc)}
    app = app_module.create_app(classroom_clock=lambda: clock["now"].isoformat())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("127.0.0.1", 41000),
        )
        async with httpx.AsyncClient(
            transport=transport,
            base_url="https://studio.example",
        ) as teacher:
            await teacher.get("/teacher/")
            tunnel_headers = {"cf-connecting-ip": "203.0.113.17"}
            async with httpx.AsyncClient(
                transport=transport,
                base_url="https://studio.example",
                headers=tunnel_headers,
            ) as board:
                yield app, teacher, board, clock


async def test_board_pairs_with_a_short_confirmation_and_an_opaque_handle(
    board_http,
):
    _, teacher, board, _ = board_http

    challenge = (await board.post("/api/board/pairings")).json()
    pending = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["pairing_id"]},
    )
    confirmation = await teacher.post(
        "/api/board/pairings/confirm",
        json={"code": challenge["code"]},
    )
    code_is_not_a_credential = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["code"]},
    )
    completed = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["pairing_id"]},
    )
    consumed = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["pairing_id"]},
    )

    assert len(challenge["code"]) == 6
    assert challenge["pairing_id"] != challenge["code"]
    assert challenge["expires_at"] == "2026-07-30T09:05:00+00:00"
    assert pending.status_code == 202
    assert pending.json() == {"status": "pending"}
    assert confirmation.status_code == 200
    assert confirmation.json() == {"status": "confirmed"}
    assert code_is_not_a_credential.status_code == 404
    assert completed.status_code == 200
    assert completed.json() == {
        "status": "paired",
        "expires_at": "2026-08-27T09:00:00+00:00",
    }
    cookie = completed.headers["set-cookie"]
    assert cookie.startswith(f"{BOARD_COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Secure" in cookie
    assert "Max-Age=2419200" in cookie
    assert consumed.status_code == 404


async def _pair(teacher, board):
    challenge = (await board.post("/api/board/pairings")).json()
    assert (
        await teacher.post(
            "/api/board/pairings/confirm",
            json={"code": challenge["code"]},
        )
    ).status_code == 200
    completed = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["pairing_id"]},
    )
    assert completed.status_code == 200


async def test_board_sees_only_the_live_collective_session_and_cannot_act(
    board_http,
):
    _, teacher, board, _ = board_http
    await _pair(teacher, board)

    no_session = await board.get("/api/board/session")
    created_class = (
        await teacher.post(
            "/api/classes",
            json={"name": "2.º A", "year": 2, "students": ["Lia"]},
        )
    ).json()
    session = (
        await teacher.post(
            "/api/sessions",
            json={
                "class_id": created_class["id"],
                "activity_slug": "demo",
                "activity_title": "Dobros",
            },
        )
    ).json()

    live = await board.get("/api/board/session")
    teacher_action = await board.get("/api/meta")
    student_action = await board.post(
        f"/api/sessions/{session['id']}/events",
        json={"events": []},
    )
    await teacher.post(f"/api/sessions/{session['id']}/close")
    closed = await board.get("/api/board/session")

    assert no_session.status_code == 204
    assert live.status_code == 200
    assert live.json() == {
        "id": session["id"],
        "class_name": "2.º A",
        "activity_slug": "demo",
        "activity_title": "Dobros",
        "status": "live",
        "started_at": "2026-07-30T09:00:00+00:00",
    }
    assert teacher_action.status_code == 403
    assert student_action.status_code == 403
    assert closed.status_code == 204
