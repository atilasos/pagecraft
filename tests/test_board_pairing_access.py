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
