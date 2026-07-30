import httpx
import pytest

from server import app as app_module


@pytest.fixture
async def rate_limit_app(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    clock = {"now": 0.0}
    app = app_module.create_app(rate_limit_clock=lambda: clock["now"])
    async with app.router.lifespan_context(app):
        teacher_transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("127.0.0.1", 41000),
        )
        async with httpx.AsyncClient(
            transport=teacher_transport,
            base_url="http://studio.example",
        ) as teacher:
            await teacher.get("/teacher/")
            classroom = (
                await teacher.post(
                    "/api/classes",
                    json={
                        "name": "3.º A",
                        "year": 3,
                        "students": ["Ana"],
                    },
                )
            ).json()
            session = (
                await teacher.post(
                    "/api/sessions",
                    json={
                        "class_id": classroom["id"],
                        "activity_slug": "demo",
                        "activity_title": "Dobros",
                    },
                )
            ).json()
        yield app, clock, session


def tunnel_client(app, ip):
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=False,
        client=("127.0.0.1", 41000),
    )
    return httpx.AsyncClient(
        transport=transport,
        base_url="https://studio.example",
        headers={"cf-connecting-ip": ip},
    )


async def test_twenty_first_join_in_the_same_minute_and_ip_is_limited(
    rate_limit_app,
):
    app, _, session = rate_limit_app
    async with tunnel_client(app, "203.0.113.17") as student:
        responses = [
            await student.get(f"/api/join/{session['join_code']}")
            for _ in range(21)
        ]

    assert [response.status_code for response in responses[:20]] == [200] * 20
    assert responses[20].status_code == 429
