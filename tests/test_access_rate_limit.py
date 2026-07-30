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
    assert responses[20].json() == {
        "detail": "muitas tentativas — espera um bocadinho"
    }


async def test_claim_has_its_own_twenty_request_budget_per_ip(
    rate_limit_app,
):
    app, _, session = rate_limit_app
    student_id = next(iter(session["roster"]))
    async with tunnel_client(app, "203.0.113.17") as student:
        joins = [
            await student.get(f"/api/join/{session['join_code']}")
            for _ in range(20)
        ]
        claims = [
            await student.post(
                f"/api/sessions/{session['id']}/claim",
                json={"student_id": student_id},
            )
            for _ in range(21)
        ]

    assert [response.status_code for response in joins] == [200] * 20
    assert claims[0].status_code == 200
    assert [response.status_code for response in claims[1:20]] == [409] * 19
    assert claims[20].status_code == 429
    assert claims[20].json() == {
        "detail": "muitas tentativas — espera um bocadinho"
    }


async def test_tunnel_uses_cloudflare_ip_and_keeps_ips_independent(
    rate_limit_app,
):
    app, _, session = rate_limit_app
    path = f"/api/join/{session['join_code']}"
    async with (
        tunnel_client(app, "203.0.113.17") as first_student,
        tunnel_client(app, "198.51.100.31") as second_student,
    ):
        first_twenty = [await first_student.get(path) for _ in range(20)]
        independent = await second_student.get(path)
        limited = await first_student.get(path)

    assert [response.status_code for response in first_twenty] == [200] * 20
    assert independent.status_code == 200
    assert limited.status_code == 429


async def test_lan_uses_socket_ip_and_ignores_proxy_headers(
    rate_limit_app,
):
    app, _, session = rate_limit_app
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=False,
        client=("10.0.0.9", 41000),
    )
    path = f"/api/join/{session['join_code']}"
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://studio.lan",
    ) as student:
        first_twenty = [
            await student.get(
                path,
                headers={"cf-connecting-ip": "203.0.113.17"},
            )
            for _ in range(20)
        ]
        forged_new_ip = await student.get(
            path,
            headers={"cf-connecting-ip": "198.51.100.31"},
        )

    assert [response.status_code for response in first_twenty] == [200] * 20
    assert forged_new_ip.status_code == 429


async def test_join_budget_recovers_after_the_sliding_minute(
    rate_limit_app,
):
    app, clock, session = rate_limit_app
    path = f"/api/join/{session['join_code']}"
    async with tunnel_client(app, "203.0.113.17") as student:
        first_twenty = [await student.get(path) for _ in range(20)]
        clock["now"] = 59.0
        still_limited = await student.get(path)
        clock["now"] = 60.0
        recovered = await student.get(path)

    assert [response.status_code for response in first_twenty] == [200] * 20
    assert still_limited.status_code == 429
    assert recovered.status_code == 200
