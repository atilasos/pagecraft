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
