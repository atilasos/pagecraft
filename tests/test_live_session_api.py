import asyncio
import json

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
