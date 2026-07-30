import asyncio
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


async def test_board_stream_derives_its_collective_view_from_the_cookie(
    board_http,
):
    app, teacher, board, _ = board_http
    await _pair(teacher, board)
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
    student_id = next(iter(session["roster"]))

    stream = asyncio.create_task(
        board.get(f"/api/sessions/{session['id']}/stream")
    )
    for _ in range(200):
        if session["id"] in app.state.classroom.live_session_ids():
            break
        await asyncio.sleep(0.001)
    assert session["id"] in app.state.classroom.live_session_ids()

    await teacher.post(
        f"/api/sessions/{session['id']}/control",
        json={
            "action": "highlight",
            "unit_id": "privada",
            "student_id": student_id,
        },
    )
    await teacher.post(
        f"/api/sessions/{session['id']}/control",
        json={"action": "highlight", "unit_id": "global"},
    )
    await teacher.post(f"/api/sessions/{session['id']}/close")
    response = await asyncio.wait_for(stream, timeout=2)

    assert response.status_code == 200
    assert "event: session_state_snapshot" in response.text
    assert '"students"' not in response.text
    assert '"unit_id": "global"' in response.text
    assert "privada" not in response.text
    assert student_id not in response.text


async def test_unpairing_immediately_closes_an_open_board_stream(board_http):
    app, teacher, board, _ = board_http
    await _pair(teacher, board)
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

    stream = asyncio.create_task(
        board.get(f"/api/sessions/{session['id']}/stream")
    )
    for _ in range(200):
        if session["id"] in app.state.classroom.live_session_ids():
            break
        await asyncio.sleep(0.001)
    assert session["id"] in app.state.classroom.live_session_ids()

    state_before = await teacher.get("/api/board/pairing")
    revoked = await teacher.delete("/api/board/pairing")
    response = await asyncio.wait_for(stream, timeout=1)
    state_after = await teacher.get("/api/board/pairing")
    old_cookie = await board.get("/api/board/session")

    assert state_before.json() == {
        "paired": True,
        "expires_at": "2026-08-27T09:00:00+00:00",
    }
    assert revoked.status_code == 204
    assert response.status_code == 200
    assert "event: session_state_snapshot" in response.text
    assert state_after.json() == {"paired": False, "expires_at": None}
    assert old_cookie.status_code == 401


async def test_board_credential_survives_restart_then_expires_server_side(
    tmp_path,
    monkeypatch,
):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(data_dir))
    clock = {"now": datetime(2026, 7, 30, 9, 0, tzinfo=timezone.utc)}

    app = app_module.create_app(classroom_clock=lambda: clock["now"].isoformat())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("127.0.0.1", 41000),
        )
        async with (
            httpx.AsyncClient(
                transport=transport,
                base_url="http://studio.test",
            ) as teacher,
            httpx.AsyncClient(
                transport=transport,
                base_url="http://board.test",
            ) as board,
        ):
            await teacher.get("/teacher/")
            await _pair(teacher, board)
            board_credential = board.cookies.get(BOARD_COOKIE_NAME)
            assert board_credential
            created_class = (
                await teacher.post(
                    "/api/classes",
                    json={
                        "name": "2.º A",
                        "year": 2,
                        "students": ["Lia"],
                    },
                )
            ).json()
            await teacher.post(
                "/api/sessions",
                json={
                    "class_id": created_class["id"],
                    "activity_slug": "demo",
                    "activity_title": "Dobros",
                },
            )

    persisted = (data_dir / "board-pairing.json").read_text("utf-8")
    assert board_credential not in persisted
    assert '"credential_digest"' in persisted

    restarted = app_module.create_app(
        classroom_clock=lambda: clock["now"].isoformat()
    )
    async with restarted.router.lifespan_context(restarted):
        transport = httpx.ASGITransport(
            app=restarted,
            raise_app_exceptions=False,
            client=("10.0.0.20", 41000),
        )
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://board.test",
            headers={
                "cookie": f"{BOARD_COOKIE_NAME}={board_credential}",
            },
        ) as board:
            restored = await board.get("/api/board/session")
            clock["now"] = datetime(
                2026,
                8,
                27,
                9,
                0,
                tzinfo=timezone.utc,
            )
            expired = await board.get("/api/board/session")

    assert restored.status_code == 200
    assert restored.json()["activity_slug"] == "demo"
    assert expired.status_code == 401


async def test_board_cookie_omits_secure_on_the_http_lan_fallback(board_http):
    app, teacher, _, _ = board_http
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=False,
        client=("10.0.0.20", 41000),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://board.local",
    ) as board:
        challenge = (await board.post("/api/board/pairings")).json()
        await teacher.post(
            "/api/board/pairings/confirm",
            json={"code": challenge["code"]},
        )
        completed = await board.post(
            "/api/board/pairings/complete",
            json={"pairing_id": challenge["pairing_id"]},
        )

    assert completed.status_code == 200
    assert "Secure" not in completed.headers["set-cookie"]


async def test_short_pairing_challenge_expires_after_five_minutes(board_http):
    _, teacher, board, clock = board_http
    challenge = (await board.post("/api/board/pairings")).json()
    clock["now"] = datetime(
        2026,
        7,
        30,
        9,
        5,
        tzinfo=timezone.utc,
    )

    confirmation = await teacher.post(
        "/api/board/pairings/confirm",
        json={"code": challenge["code"]},
    )
    completion = await board.post(
        "/api/board/pairings/complete",
        json={"pairing_id": challenge["pairing_id"]},
    )

    assert confirmation.status_code == 404
    assert completion.status_code == 404
