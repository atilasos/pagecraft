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
            yield http


async def _session(client):
    cls = (
        await client.post(
            "/api/classes",
            json={"name": "3.º A", "year": 3, "students": ["Ana"]},
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


async def test_http_maps_closed_session_commands_to_conflict(client):
    session = await _session(client)
    await client.post(f"/api/sessions/{session['id']}/close")

    message = await client.post(
        f"/api/sessions/{session['id']}/message",
        json={"text": "Mensagem tardia"},
    )
    control = await client.post(
        f"/api/sessions/{session['id']}/control",
        json={"action": "freeze"},
    )

    assert message.status_code == 409
    assert control.status_code == 409


async def test_http_maps_a_recipient_outside_the_roster_to_not_found(client):
    session = await _session(client)

    message = await client.post(
        f"/api/sessions/{session['id']}/message",
        json={"text": "Olá", "student_id": "intruso"},
    )
    control = await client.post(
        f"/api/sessions/{session['id']}/control",
        json={"action": "highlight", "student_id": "intruso"},
    )

    assert message.status_code == 404
    assert control.status_code == 404
