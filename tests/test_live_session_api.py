import asyncio
import json
from datetime import datetime, timedelta

import httpx
import pytest

from server import app as app_module


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"x-teacher-token": app.state.teacher_token},
        ) as http:
            http.app = app
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
        params={"role": "teacher"},
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
    claim = (
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).json()
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
        params={
            "role": "student",
            "student_token": claim["student_token"],
        },
        headers={"x-teacher-token": ""},
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


async def test_child_history_is_complete_for_teacher_and_role_authorized_for_student(client):
    session = await _session(client, students=("Ana", "Bia"))
    ana_id, bia_id = session["roster"]
    ana_claim = (
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).json()
    bia_claim = (
        await client.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": bia_id},
        )
    ).json()
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
        params={"role": "teacher"},
    )
    student = await client.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history",
        params={
            "role": "student",
            "student_token": ana_claim["student_token"],
        },
        headers={"x-teacher-token": ""},
    )
    forbidden = await client.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history",
        params={
            "role": "student",
            "student_token": bia_claim["student_token"],
        },
        headers={"x-teacher-token": ""},
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
        params={"role": "teacher"},
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
    claim = (
        await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": student_id},
        )
    ).json()
    svc = client.app.state.classroom
    records = await svc.events_log(session["id"]).replay()
    joined_at = datetime.fromisoformat(records[-1]["ts"])
    clock = {"now": joined_at.isoformat()}
    svc._clock = lambda: clock["now"]

    teacher_stream = asyncio.create_task(
        client.get(
            f"/api/sessions/{session['id']}/stream",
            params={"role": "teacher"},
        )
    )
    student_stream = asyncio.create_task(
        client.get(
            f"/api/sessions/{session['id']}/stream",
            params={
                "role": "student",
                "student_token": claim["student_token"],
            },
            headers={"x-teacher-token": ""},
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
        ("Precisa de ti", "Parado"),
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
            params={"role": "teacher"},
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
