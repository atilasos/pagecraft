import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

from server import app as app_module
from server.access import BOARD_COOKIE_NAME, TEACHER_COOKIE_NAME, Role
from starlette.requests import Request


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


async def test_pairing_a_browser_previously_used_by_the_teacher_keeps_board_access(
    board_http,
):
    _, teacher, _, _ = board_http
    await _pair(teacher, teacher)

    waiting = await teacher.get("/api/board/session")

    assert waiting.status_code == 204
    # O painel do professor continua a funcionar noutra aba do mesmo browser.
    assert (await teacher.get("/api/meta")).status_code == 200
    await teacher.delete("/api/board/pairing")
    # A sessão de professor não substitui uma credencial de quadro revogada.
    assert (await teacher.get("/api/board/session")).status_code == 401
    assert (
        await teacher.get("/api/board/sessions/unknown/stream")
    ).status_code == 401
    assert (await teacher.get("/api/meta")).status_code == 200


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
        "join_code": session["join_code"],
        "status": "live",
        "started_at": "2026-07-30T09:00:00+00:00",
    }
    assert teacher_action.status_code == 403
    assert student_action.status_code == 403
    assert closed.status_code == 204


@pytest.mark.parametrize("teacher_cookie", [False, True])
async def test_board_stream_derives_its_collective_view_from_the_cookie(
    board_http,
    teacher_cookie,
):
    app, teacher, board, _ = board_http
    await _pair(teacher, board)
    if teacher_cookie:
        board.headers.pop("cf-connecting-ip")
        board.cookies.set(
            TEACHER_COOKIE_NAME, teacher.cookies.get(TEACHER_COOKIE_NAME)
        )
    assert (await board.get("/api/board/session")).status_code == 204
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
        board.get(f"/api/board/sessions/{session['id']}/stream")
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
    # Let the collective event reach the consumer before closing access.
    await asyncio.sleep(.05)
    await teacher.post(f"/api/sessions/{session['id']}/close")
    response = await asyncio.wait_for(stream, timeout=2)

    assert response.status_code == 200
    assert "event: session_state_snapshot" in response.text
    assert '"name": "teacher_highlight"' in response.text
    assert '"bridge_name": "highlight"' in response.text
    assert '"students"' not in response.text
    assert '"unit_id": "global"' in response.text
    assert "privada" not in response.text
    assert student_id not in response.text
    if teacher_cookie:
        # A rota do professor mantém a sua vista no mesmo browser.
        teacher_view = await board.get(f"/api/sessions/{session['id']}/stream")
        assert teacher_view.status_code == 200
        assert student_id in teacher_view.text


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
        board.get(f"/api/board/sessions/{session['id']}/stream")
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


async def test_board_stream_revalidates_if_revoked_after_request_access(
    board_http,
    monkeypatch,
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

    request_access_resolved = asyncio.Event()
    let_request_continue = asyncio.Event()
    original_resolve = app.state.board_pairings.resolve
    calls = 0

    async def pause_after_first_resolution(credential):
        nonlocal calls
        calls += 1
        resolved = await original_resolve(credential)
        if calls == 2:
            request_access_resolved.set()
            await let_request_continue.wait()
        return resolved

    monkeypatch.setattr(
        app.state.board_pairings,
        "resolve",
        pause_after_first_resolution,
    )
    stream = asyncio.create_task(
        board.get(f"/api/board/sessions/{session['id']}/stream")
    )
    await asyncio.wait_for(request_access_resolved.wait(), timeout=1)
    revoked = await teacher.delete("/api/board/pairing")
    let_request_continue.set()
    response = await asyncio.wait_for(stream, timeout=1)

    assert revoked.status_code == 204
    assert response.status_code == 200
    assert "event: session_state_snapshot" not in response.text


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


async def _board_lesson(teacher):
    classroom = (await teacher.post('/api/classes', json={
        'name': 'Quadro descartável', 'year': 2, 'students': ['Ana', 'Bruno', 'Carla'],
    })).json()
    session = (await teacher.post('/api/sessions', json={
        'class_id': classroom['id'], 'activity_slug': 'fracoes-2-minecraft',
        'activity_title': 'Sessão A',
    })).json()
    return classroom, session


async def _next_board_lesson(teacher, classroom, clock):
    clock['now'] += timedelta(minutes=1)
    response = await teacher.post('/api/sessions', json={
        'class_id': classroom['id'], 'activity_slug': 'fracoes-2-minecraft',
        'activity_title': 'Sessão B',
    })
    assert response.status_code == 200
    return response.json()


async def _wait_for_board_stream(app, session_id):
    for _ in range(200):
        if session_id in app.state.classroom.live_session_ids():
            return
        await asyncio.sleep(.001)
    pytest.fail('O stream não subscreveu o relógio da sessão')


async def test_old_board_stream_rejected_like_content_while_students_keep_access(board_http):
    app, teacher, board, clock = board_http
    await _pair(teacher, board)
    classroom, session = await _board_lesson(teacher)
    path = f"/api/sessions/{session['id']}"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='https://studio.example') as student:
        assert (await student.post(path + '/claim', json={
            'student_id': next(iter(session['roster'])),
        })).status_code == 200
        # Generate a real eight-character code before B becomes current.
        ids = list(session['roster'])
        group = (await teacher.post(path + '/groups/claim', json={
            'participant_ids': ids[1:], 'mode': 'pair',
        })).json()['work_group']
        code_response = await teacher.post(path + f"/groups/{group['id']}/access-code")
        assert code_response.status_code == 200, code_response.text
        code = code_response.json()['code']
        await teacher.post(path + '/group-codes', json={'visible': True})
        current = await _next_board_lesson(teacher, classroom, clock)
        assert (await board.get('/api/board/session')).json()['id'] == current['id']
        assert (await board.get(f"/api/board/sessions/{session['id']}/content")).status_code == 404
        request = asyncio.create_task(board.get(f"/api/board/sessions/{session['id']}/stream"))
        # Closing A bounds the reproduction even on the unfixed server.
        await asyncio.sleep(.05)
        assert (await student.get(path + '/me')).status_code == 200
        assert (await teacher.get(path)).json()['status'] == 'live'
        await teacher.post(path + '/close')
        response = await asyncio.wait_for(request, 1)
        assert response.status_code == 404, response.text
        assert 'session_state_snapshot' not in response.text
        assert code not in response.text
        assert 'Ana' not in response.text
        # Teacher and student SSE remain usable for A after B starts.
        for client in (teacher, student):
            own = await client.get(path + '/stream')
            assert own.status_code == 200
            assert 'event: session_state_snapshot' in own.text


@pytest.mark.parametrize('wake', ['event', 'private_event', 'group_code', 'heartbeat'])
async def test_open_board_stream_stops_after_switch_without_old_frames(board_http, wake):
    app, teacher, board, clock = board_http
    await _pair(teacher, board)
    classroom, session = await _board_lesson(teacher)
    path = f"/api/sessions/{session['id']}"
    if wake == 'group_code':
        group = (await teacher.post(path + '/groups/claim', json={
            'participant_ids': list(session['roster'])[:2], 'mode': 'pair',
        })).json()['work_group']
    stream = asyncio.create_task(board.get(f"/api/board/sessions/{session['id']}/stream"))
    try:
        await _wait_for_board_stream(app, session['id'])
        await _next_board_lesson(teacher, classroom, clock)
        new_code = None
        if wake in {'event', 'private_event'}:
            control = {'action': 'highlight', 'unit_id': 'ANTIGA-NAO-PROJETAR'}
            if wake == 'private_event':
                control['student_id'] = next(iter(session['roster']))
            assert (await teacher.post(path + '/control', json=control)).status_code == 200
        elif wake == 'group_code':
            generated = await teacher.post(path + f"/groups/{group['id']}/access-code")
            assert generated.status_code == 200
            new_code = generated.json()['code']
        else:
            # Same publisher used by the periodic heartbeat; no record in A.
            app.state.classroom.live_ticks.publish(session['id'])
        response = await asyncio.wait_for(asyncio.shield(stream), .5)
        assert response.status_code == 200
        assert response.text.count('event: session_state_snapshot') == 1
        assert 'ANTIGA-NAO-PROJETAR' not in response.text
        if new_code:
            assert new_code not in response.text
        assert response.text.count('\nevent: ') == 1
        assert 'session_state_changed' not in response.text
        assert 'student_state_changed' not in response.text
        assert 'work_group_state_changed' not in response.text
        assert session['id'] not in app.state.classroom.live_session_ids()
    finally:
        stream.cancel()
        await asyncio.gather(stream, return_exceptions=True)


async def test_board_stream_rechecks_selection_before_snapshot(board_http, monkeypatch):
    app, teacher, board, clock = board_http
    await _pair(teacher, board)
    classroom, session = await _board_lesson(teacher)
    checked = asyncio.Event()
    proceed = asyncio.Event()
    resolve = app.state.board_pairings.resolve
    calls = 0

    async def pause_after_handler_check(credential):
        nonlocal calls
        calls += 1
        valid = await resolve(credential)
        if calls == 2:
            checked.set()
            await proceed.wait()
        return valid

    monkeypatch.setattr(app.state.board_pairings, 'resolve', pause_after_handler_check)
    stream = asyncio.create_task(board.get(f"/api/board/sessions/{session['id']}/stream"))
    try:
        await asyncio.wait_for(checked.wait(), 1)
        await _next_board_lesson(teacher, classroom, clock)
        proceed.set()
        response = await asyncio.wait_for(asyncio.shield(stream), .5)
        assert response.status_code in (200, 401)
        assert 'session_state_snapshot' not in response.text
        assert session['id'] not in app.state.classroom.live_session_ids()
    finally:
        proceed.set()
        stream.cancel()
        await asyncio.gather(stream, return_exceptions=True)


async def test_board_stream_rechecks_between_frames_of_one_record(board_http):
    from server.api.classroom import stream_session

    app, teacher, board, clock = board_http
    await _pair(teacher, board)
    classroom, session = await _board_lesson(teacher)
    # Drive the actual response iterator so consumer backpressure is controlled.
    # HTTP role resolution and rejection are covered by the tests above.
    request = Request({'type': 'http', 'app': app})
    request.state.access = SimpleNamespace(
        role=Role.BOARD, board_credential=board.cookies.get(BOARD_COOKIE_NAME),
    )
    response = await stream_session(session['id'], request)
    frames = response.body_iterator
    try:
        assert 'event: session_state_snapshot' in await anext(frames)
        await teacher.post(f"/api/sessions/{session['id']}/control", json={'action': 'freeze'})
        assert 'event: freeze_screens' in await asyncio.wait_for(anext(frames), 1)
        await _next_board_lesson(teacher, classroom, clock)
        # The same record also produces a session delta. It must not escape.
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(anext(frames), 1)
        assert session['id'] not in app.state.classroom.live_session_ids()
    finally:
        await frames.aclose()
