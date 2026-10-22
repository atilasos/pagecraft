import asyncio
import json
from datetime import datetime, timedelta

import httpx
import pytest

from server import app as app_module
from server.access import STUDENT_COOKIE_NAME


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as http:
            panel = await http.get("/teacher/")
            assert panel.status_code == 200
            setattr(http, "app", app)
            yield http


async def _session(client, students=("Ana",)):
    cls = (
        await client.post(
            "/api/classes",
            json={"name": "3.º A", "year": 3, "students": list(students)},
        )
    ).json()
    return (
        await client.post(
            "/api/sessions",
            json={
                "class_id": cls["id"],
                "activity_slug": "fracoes",
                "activity_title": "Frações",
            },
        )
    ).json()


def _sse_frames(body):
    frames = []
    for block in body.strip().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            key, _, value = line.partition(": ")
            fields[key] = value
        if "data" in fields:
            fields["data"] = json.loads(fields["data"])
        frames.append(fields)
    return frames


def _student_cookie(response):
    credential = response.cookies.get(STUDENT_COOKIE_NAME)
    assert credential
    return {"cookie": f"{STUDENT_COOKIE_NAME}={credential}"}


async def test_teacher_stream_starts_with_current_snapshot_without_replaying_log(client):
    session = await _session(client)
    student_id = next(iter(session["roster"]))
    await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": student_id},
    )
    await client.app.state.classroom.emit_event(
        session["id"],
        "attempt",
        {"correct": True},
        author="activity",
        student_id=student_id,
    )
    await client.post(
        f"/api/sessions/{session['id']}/control",
        json={"action": "freeze"},
    )
    await client.post(f"/api/sessions/{session['id']}/close")

    response = await client.get(
        f"/api/sessions/{session['id']}/stream",
    )

    assert response.status_code == 200
    frames = _sse_frames(response.text)
    assert [frame["event"] for frame in frames] == ["session_state_snapshot"]
    snapshot = frames[0]["data"]
    assert snapshot["session"] == {
        "status": "closed",
        "closed": True,
        "frozen": True,
    }
    assert snapshot["students"][student_id]["numbers"]["correct_attempts"] == 1
    assert snapshot["students"][student_id]["pit_items"] == []
    assert snapshot["numbers"]["correct_attempts"] == 1
    assert "token" not in response.text.lower()


async def test_student_snapshot_contains_only_own_state_and_no_class_totals(client):
    session = await _session(client, students=("Ana", "Bia"))
    ana_id, bia_id = session["roster"]
    student_headers = _student_cookie(
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    )
    await client.app.state.classroom.emit_event(
        session["id"],
        "attempt",
        {"correct": True},
        author="activity",
        student_id=bia_id,
    )
    await client.post(f"/api/sessions/{session['id']}/close")

    response = await client.get(
        f"/api/sessions/{session['id']}/stream",
        headers=student_headers,
    )

    frames = _sse_frames(response.text)
    assert [frame["event"] for frame in frames] == [
        "session_state_snapshot"
    ]
    snapshot = frames[0]["data"]
    assert set(snapshot["students"]) == {ana_id}
    assert snapshot["students"][ana_id]["numbers"]["correct_attempts"] == 0
    assert "numbers" not in snapshot
    assert bia_id not in response.text
    assert "token" not in response.text.lower()


async def test_board_stream_contains_only_shared_state_and_global_events(client):
    session = await _session(client, students=("Ana", "Bia"))
    ana_id = next(iter(session["roster"]))
    await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": ana_id},
    )

    async def produce():
        await asyncio.sleep(0.01)
        await client.app.state.classroom.emit_event(
            session["id"],
            "attempt",
            {"correct": False, "detail": "resposta privada"},
            author="activity",
            student_id=ana_id,
        )
        await client.post(
            f"/api/sessions/{session['id']}/control",
            json={
                "action": "highlight",
                "unit_id": "privada",
                "student_id": ana_id,
            },
        )
        await client.post(
            f"/api/sessions/{session['id']}/control",
            json={"action": "highlight", "unit_id": "global"},
        )
        await client.post(
            f"/api/sessions/{session['id']}/control",
            json={"action": "freeze"},
        )
        await client.post(
            f"/api/sessions/{session['id']}/control",
            json={"action": "unfreeze"},
        )
        await client.post(f"/api/sessions/{session['id']}/close")

    transport = httpx.ASGITransport(
        app=client.app,
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://board.test",
    ) as board:
        challenge = (await board.post("/api/board/pairings")).json()
        await client.post(
            "/api/board/pairings/confirm",
            json={"code": challenge["code"]},
        )
        completed = await board.post(
            "/api/board/pairings/complete",
            json={"pairing_id": challenge["pairing_id"]},
        )
        assert completed.status_code == 200

        producer = asyncio.create_task(produce())
        response = await board.get(
            f"/api/board/sessions/{session['id']}/stream",
        )
        await producer

    assert response.status_code == 200
    frames = _sse_frames(response.text)
    assert [frame["event"] for frame in frames] == [
        "session_state_snapshot",
        "teacher_highlight",
        "freeze_screens",
        "session_state_changed",
        "unfreeze_screens",
        "session_state_changed",
        "session_closed",
        "session_state_changed",
    ]
    assert frames[0]["data"] == {
        "session": {"status": "live", "closed": False, "frozen": False},
        "event_types": [
            {"name": "session_resumed", "bridge_name": None},
            {"name": "group_codes_updated", "bridge_name": None},
            {"name": "teacher_highlight", "bridge_name": "highlight"},
            {"name": "freeze_screens", "bridge_name": None},
            {"name": "unfreeze_screens", "bridge_name": None},
            {"name": "session_closed", "bridge_name": None},
        ],
    }
    assert frames[1]["data"]["payload"]["unit_id"] == "global"
    assert frames[-1]["data"] == {
        "session": {"status": "closed", "closed": True, "frozen": False}
    }
    assert "student_id" not in response.text
    assert ana_id not in response.text
    assert "resposta privada" not in response.text
    assert "privada" not in response.text
    assert "token" not in response.text.lower()


async def test_child_history_is_complete_for_teacher_and_role_authorized_for_student(client):
    session = await _session(client, students=("Ana", "Bia"))
    ana_id, bia_id = session["roster"]
    ana_cookie = _student_cookie(
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    )
    bia_cookie = _student_cookie(
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": bia_id},
        )
    )
    await client.app.state.classroom.emit_event(
        session["id"],
        "heartbeat",
        {},
        author="activity",
        student_id=ana_id,
    )
    await client.app.state.classroom.emit_event(
        session["id"],
        "attempt",
        {"correct": True},
        author="activity",
        student_id=ana_id,
    )
    await client.post(
        f"/api/sessions/{session['id']}/message",
        json={"text": "Só para a Ana", "student_id": ana_id},
    )
    await client.post(
        f"/api/sessions/{session['id']}/message",
        json={"text": "Só para a Bia", "student_id": bia_id},
    )

    teacher = await client.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history",
    )
    student = await client.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history",
        headers=ana_cookie,
    )
    forbidden = await client.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history",
        headers=bia_cookie,
    )

    assert teacher.status_code == 200
    assert [record["type"] for record in teacher.json()["events"]] == [
        "joined",
        "heartbeat",
        "attempt",
        "teacher_message",
    ]
    assert student.status_code == 200
    assert [record["type"] for record in student.json()["events"]] == [
        "attempt",
        "teacher_message",
    ]
    assert forbidden.status_code == 403
    assert "Bia" not in teacher.text
    assert "token" not in teacher.text.lower()
    assert "token" not in student.text.lower()


async def test_live_stream_keeps_raw_timeline_and_emits_only_changed_children(client):
    session = await _session(client, students=("Ana", "Bia"))
    ana_id, bia_id = session["roster"]
    await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": ana_id},
    )
    await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": bia_id},
    )

    async def produce():
        await asyncio.sleep(0.01)
        await client.app.state.classroom.emit_event(
            session["id"],
            "attempt",
            {"correct": True},
            author="activity",
            student_id=ana_id,
        )
        await client.app.state.classroom.emit_event(
            session["id"],
            "heartbeat",
            {},
            author="activity",
            student_id=bia_id,
        )
        await client.post(
            f"/api/sessions/{session['id']}/message",
            json={"text": "Continua", "student_id": ana_id},
        )
        await client.post(f"/api/sessions/{session['id']}/close")

    producer = asyncio.create_task(produce())
    response = await client.get(
        f"/api/sessions/{session['id']}/stream",
    )
    await producer

    frames = _sse_frames(response.text)
    events = [frame["event"] for frame in frames]
    assert events == [
        "session_state_snapshot",
        "attempt",
        "student_state_changed",
        "teacher_message",
        "session_closed",
        "session_state_changed",
    ]
    delta = next(
        frame["data"]
        for frame in frames
        if frame["event"] == "student_state_changed"
    )
    assert delta["student_id"] == ana_id
    assert delta["student"]["numbers"]["correct_attempts"] == 1
    assert bia_id not in json.dumps(delta)
    assert "heartbeat" not in events
    session_delta = frames[-1]["data"]
    assert session_delta == {
        "session": {"status": "closed", "closed": True, "frozen": False}
    }


async def test_controlled_ticks_publish_stopped_and_no_signal_without_new_work(client):
    session = await _session(client)
    student_id = next(iter(session["roster"]))
    student_headers = _student_cookie(
        await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": student_id},
        )
    )
    svc = client.app.state.classroom
    records = await svc.events_log(session["id"]).replay()
    joined_at = datetime.fromisoformat(records[-1]["ts"])
    clock = {"now": joined_at.isoformat()}
    svc._clock = lambda: clock["now"]

    teacher_stream = asyncio.create_task(
        client.get(
            f"/api/sessions/{session['id']}/stream",
        )
    )
    student_stream = asyncio.create_task(
        client.get(
            f"/api/sessions/{session['id']}/stream",
            headers=student_headers,
        )
    )
    await asyncio.sleep(0.01)
    assert svc.live_session_ids() == (session["id"],)

    recent_presence = joined_at + timedelta(seconds=179)
    await svc.events_log(session["id"]).append(
        {
            "type": "heartbeat",
            "student_id": student_id,
            "payload": {},
            "ts": recent_presence.isoformat(),
        }
    )
    await asyncio.sleep(0.01)
    stopped_at = joined_at + timedelta(seconds=180)
    clock["now"] = stopped_at.isoformat()
    svc.tick_session(session["id"], now=clock["now"])
    await asyncio.sleep(0.01)
    no_signal_at = joined_at + timedelta(seconds=270)
    clock["now"] = no_signal_at.isoformat()
    svc.tick_session(session["id"], now=clock["now"])
    await asyncio.sleep(0.01)
    await client.post(f"/api/sessions/{session['id']}/close")
    responses = await asyncio.gather(teacher_stream, student_stream)

    for response in responses:
        frames = _sse_frames(response.text)
        deltas = [
            frame["data"]["student"]["triage"]
            for frame in frames
            if frame["event"] == "student_state_changed"
        ]
        assert [(delta["band"], delta["reason"]) for delta in deltas] == [
        ("A fluir", "Sem atividade recente no PageCraft"),
        ("Sem sinal", "Sem presença"),
        ]
        assert "heartbeat" not in [frame["event"] for frame in frames]
    assert svc.live_session_ids() == ()


async def test_recorded_close_terminates_stream_when_session_write_fails_and_reconciles(
    client, monkeypatch
):
    session = await _session(client)
    svc = client.app.state.classroom
    stream = asyncio.create_task(
        client.get(
            f"/api/sessions/{session['id']}/stream",
        )
    )
    await asyncio.sleep(0.01)
    assert svc.live_session_ids() == (session["id"],)

    original_write = svc.storage.write_json

    async def fail_session_write(path, data):
        if path == svc._session_path(session["id"]):
            raise OSError("falha depois do registo")
        return await original_write(path, data)

    monkeypatch.setattr(svc.storage, "write_json", fail_session_write)
    close = await client.post(f"/api/sessions/{session['id']}/close")
    response = await stream

    assert close.status_code == 500
    assert [frame["event"] for frame in _sse_frames(response.text)][-2:] == [
        "session_closed",
        "session_state_changed",
    ]
    assert svc.live_session_ids() == ()

    monkeypatch.setattr(svc.storage, "write_json", original_write)
    reconciled = await svc.get_session(session["id"])
    assert reconciled["status"] == "closed"


async def test_individual_identity_version_survives_reload_but_changes_after_release(client):
    session = await _session(client)
    path = f"/api/sessions/{session['id']}"
    student_id = next(iter(session['roster']))
    claim = await client.post(path + '/claim', json={'student_id': student_id})
    first = claim.json()
    assert first['identity_version']
    original_cookie = _student_cookie(claim)
    me = await client.get(path + '/me', headers=original_cookie)
    assert me.json()['identity_version'] == first['identity_version']
    assert 'student_credential' not in first
    assert 'token' not in me.json()
    await client.post(path + '/release/' + student_id)
    assert (await client.get(path + '/me', headers=original_cookie)).status_code == 401
    newer = await client.post(path + '/claim', json={'student_id': student_id})
    assert newer.json()['identity_version'] != first['identity_version']


async def test_outbox_replay_requires_the_original_individual_identity(client):
    session = await _session(client, students=('Ana', 'Bruno'))
    path = f"/api/sessions/{session['id']}"
    ana, bruno = session['roster']
    first = await client.post(path + '/claim', json={'student_id': ana})
    body = {'events': [{'event_id': 'pending-ana', 'type': 'attempt', 'payload': {'correct': True}}],
            'expected_identity': {'student_id': ana, 'version': first.json()['identity_version']}}
    original_cookie = _student_cookie(first)
    other = await client.post(path + '/claim', json={'student_id': bruno})
    wrong_child = await client.post(path + '/events', json=body, headers=_student_cookie(other))
    assert wrong_child.status_code == 409
    assert wrong_child.json()['detail']['code'] == 'identity_changed'
    await client.post(path + '/release/' + ana)
    renewed = await client.post(path + '/claim', json={'student_id': ana})
    wrong_version = await client.post(path + '/events', json=body, headers=_student_cookie(renewed))
    assert wrong_version.status_code == 409
    assert wrong_version.json()['detail']['code'] == 'identity_changed'
    assert (await client.post(path + '/events', json=body, headers=original_cookie)).status_code == 401
    for sid in (ana, bruno):
        history = (await client.get(path + f'/students/{sid}/history')).json()['events']
        assert not any(event.get('event_id') == 'pending-ana' for event in history)
