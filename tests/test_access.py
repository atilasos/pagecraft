import httpx
import pytest
from fastapi import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from server import app as app_module
from server.access import STUDENT_COOKIE_NAME, RoutePolicy, access_policy


def test_app_refuses_to_start_with_a_route_without_an_access_policy():
    def add_unprotected_route(app):
        @app.get("/api/forgotten")
        async def forgotten_route():
            return {"should": "never be public by accident"}

    with pytest.raises(
        RuntimeError,
        match=r"GET /api/forgotten.*forgotten_route",
    ):
        app_module.create_app(route_extensions=[add_unprotected_route])


@pytest.fixture
async def app_client(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            setattr(client, "app", app)
            yield client


async def test_only_the_declared_public_surface_answers_without_a_role(app_client):
    for path in (
        "/api/health",
        "/student/",
        "/activities/not-published/",
        "/outputs/not-generated.html",
    ):
        response = await app_client.get(path)
        assert response.status_code != 401, path
        assert response.status_code != 403, path

    for path in (
        "/api/activities",
        "/api/meta",
        "/api/session-event-types",
        "/docs",
        "/openapi.json",
        "/redoc",
    ):
        response = await app_client.get(path)
        assert response.status_code == 401, path


async def test_opening_teacher_panel_on_loopback_issues_httponly_cookie(
    app_client,
):
    panel = await app_client.get("/teacher/")

    assert panel.status_code == 200
    assert "PageCraft Studio" in panel.text
    cookie = panel.headers["set-cookie"]
    assert cookie.startswith("pagecraft_teacher_session=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/" in cookie

    response = await app_client.get("/api/meta")

    assert response.status_code == 200


async def test_non_loopback_channel_without_cookie_cannot_bootstrap_or_act_as_teacher(
    app_client,
):
    transport = httpx.ASGITransport(
        app=app_client.app,
        raise_app_exceptions=False,
        client=("127.0.0.1", 41000),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://studio.example",
        headers={"cf-connecting-ip": "203.0.113.17"},
    ) as tunnel_client:
        bootstrap = await tunnel_client.get("/api/teacher-bootstrap")
        teacher_shell = await tunnel_client.get("/teacher/")
        protected = await tunnel_client.get("/api/meta")

    assert bootstrap.status_code == 401
    assert teacher_shell.status_code == 401
    assert protected.status_code == 401


async def test_public_static_mount_cannot_traverse_into_the_teacher_panel(
    app_client,
):
    transport = httpx.ASGITransport(
        app=app_client.app,
        raise_app_exceptions=False,
        client=("127.0.0.1", 41000),
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://studio.example",
        headers={"cf-connecting-ip": "203.0.113.17"},
    ) as tunnel_client:
        response = await tunnel_client.get(
            "/student/%2e%2e/teacher/index.html"
        )

    assert response.status_code != 200
    assert "O ficheiro do professor" not in response.text


async def test_teacher_cookie_authenticates_sse_without_a_credential_in_the_url(
    app_client,
):
    await app_client.get("/teacher/")
    created_class = (
        await app_client.post(
            "/api/classes",
            json={"name": "2.º A", "year": 2, "students": ["Lia"]},
        )
    ).json()
    session = (
        await app_client.post(
            "/api/sessions",
            json={
                "class_id": created_class["id"],
                "activity_slug": "demo",
                "activity_title": "Dobros",
            },
        )
    ).json()
    await app_client.post(f"/api/sessions/{session['id']}/close")

    response = await app_client.get(
        f"/api/sessions/{session['id']}/stream",
    )

    assert response.status_code == 200
    assert "event: session_state_snapshot" in response.text
    assert "teacher_token" not in str(response.request.url)


async def test_legacy_teacher_token_transports_no_longer_authenticate(app_client):
    token = app_client.app.state.teacher_token

    header_response = await app_client.get(
        "/api/meta",
        headers={"x-teacher-token": token},
    )
    query_response = await app_client.get(
        "/api/meta",
        params={"teacher_token": token},
    )
    delivery_response = await app_client.get("/api/teacher-token")

    assert header_response.status_code == 401
    assert query_response.status_code == 401
    assert delivery_response.status_code == 404


async def test_access_resolves_the_role_and_trust_channel_once_per_request(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))

    def add_access_probe(app):
        @app.get("/api/access-probe")
        @access_policy(RoutePolicy.TEACHER)
        async def access_probe(request: Request):
            access = request.state.access
            return {
                "role": access.role,
                "channel": access.channel,
                "client_ip": access.client_ip,
            }

    app = app_module.create_app(route_extensions=[add_access_probe])
    async with app.router.lifespan_context(app):
        loopback_transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("127.0.0.1", 41000),
        )
        async with httpx.AsyncClient(
            transport=loopback_transport,
            base_url="http://studio.example",
        ) as loopback_client:
            panel = await loopback_client.get("/teacher/")
            teacher_cookies = httpx.Cookies(loopback_client.cookies)
        assert panel.status_code == 200

        tunnel_transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("127.0.0.1", 41000),
        )
        async with httpx.AsyncClient(
            transport=tunnel_transport,
            base_url="http://studio.example",
            cookies=teacher_cookies,
        ) as tunnel_client:
            tunnel_response = await tunnel_client.get(
                "/api/access-probe",
                headers={"cf-connecting-ip": "203.0.113.17"},
            )
        lan_transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
            client=("10.0.0.9", 41000),
        )
        async with httpx.AsyncClient(
            transport=lan_transport,
            base_url="http://studio.example",
            cookies=teacher_cookies,
        ) as lan_client:
            lan_response = await lan_client.get(
                "/api/access-probe",
                headers={"cf-connecting-ip": "198.51.100.31"},
            )

    assert tunnel_response.status_code == 200
    assert tunnel_response.json() == {
        "role": "teacher",
        "channel": "cloudflare_tunnel",
        "client_ip": "203.0.113.17",
    }
    assert lan_response.status_code == 200
    assert lan_response.json() == {
        "role": "teacher",
        "channel": "lan",
        "client_ip": "10.0.0.9",
    }


async def test_a_teacher_is_forbidden_from_a_student_route(app_client):
    panel = await app_client.get("/teacher/")
    assert panel.status_code == 200
    created_class = (
        await app_client.post(
            "/api/classes",
            json={"name": "2.º A", "year": 2, "students": ["Lia"]},
        )
    ).json()
    session = (
        await app_client.post(
            "/api/sessions",
            json={
                "class_id": created_class["id"],
                "activity_slug": "demo",
                "activity_title": "Dobros",
            },
        )
    ).json()
    student_id = next(iter(session["roster"]))
    claim = await app_client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": student_id},
    )
    student_cookie = claim.cookies.get(STUDENT_COOKIE_NAME)

    student_response = await app_client.get(
        f"/api/sessions/{session['id']}/me",
        headers={"cookie": f"{STUDENT_COOKIE_NAME}={student_cookie}"},
    )
    response = await app_client.get(
        f"/api/sessions/{session['id']}/me",
    )

    assert student_response.status_code == 200
    assert response.status_code == 403


async def test_runtime_denies_a_route_that_escaped_startup_validation(app_client):
    async def forgotten_route(_request):
        return JSONResponse({"should": "not run"})

    app_client.app.router.routes.insert(
        0,
        Route("/api/runtime-forgotten", forgotten_route),
    )

    response = await app_client.get("/api/runtime-forgotten")

    assert response.status_code == 403
