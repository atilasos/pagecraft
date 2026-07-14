import asyncio
import json

import httpx
import pytest

from server import app as app_module


class InstantFeedbackProvider:
    name = "fake"

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=20, workdir=None):
        return {"feedback": "Boa! Já viste que a metade de 8 é 4."}


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        app.state.feedback.provider = InstantFeedbackProvider()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"x-teacher-token": app.state.teacher_token},
        ) as c:
            c.app = app
            yield c


async def test_full_classroom_flow(client):
    # professor cria turma e sessão
    resp = await client.post(
        "/api/classes", json={"name": "2.º B", "year": 2, "students": ["Rita", "Tomás"]}
    )
    assert resp.status_code == 200
    cls = resp.json()

    resp = await client.post(
        "/api/sessions",
        json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "Dobros"},
    )
    session = resp.json()
    assert session["join_code"]

    # aluno entra por código (sem tokens expostos)
    resp = await client.get(f"/api/join/{session['join_code']}")
    public = resp.json()
    assert "roster" in public
    assert all("token" not in s for s in public["roster"])

    # reclama identidade; segunda vez conflito
    student = public["roster"][0]
    resp = await client.post(
        f"/api/sessions/{session['id']}/claim", json={"student_id": student["student_id"]}
    )
    assert resp.status_code == 200
    claim = resp.json()
    resp = await client.post(
        f"/api/sessions/{session['id']}/claim", json={"student_id": student["student_id"]}
    )
    assert resp.status_code == 409

    # eventos: attempt + feedback_request (dispara IA fake)
    events = [
        {"event_id": "a1", "type": "attempt", "unit_id": "u1", "payload": {"correct": False}},
        {
            "event_id": "a2",
            "type": "feedback_request",
            "unit_id": "u1",
            "payload": {"question": "metade de 8?", "answer": "6", "expected": "4"},
        },
    ]
    resp = await client.post(
        f"/api/sessions/{session['id']}/events",
        json={"student_token": claim["student_token"], "events": events},
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] == ["a1", "a2"]

    # token errado → 401
    resp = await client.post(
        f"/api/sessions/{session['id']}/events",
        json={"student_token": "invalido", "events": events},
    )
    assert resp.status_code == 401

    # o feedback IA chega ao log de eventos da sessão
    storage = client.app.state.storage
    path = storage.path("sessions", session["id"], "events.jsonl")

    async def wait_feedback():
        while True:
            for r in await storage.read_jsonl(path):
                if r["type"] == "ai_feedback":
                    return r
            await asyncio.sleep(0.02)

    record = await asyncio.wait_for(wait_feedback(), timeout=5)
    assert "metade" in record["payload"]["text"]

    # PIT do aluno
    resp = await client.post(
        f"/api/sessions/{session['id']}/pit",
        json={"student_token": claim["student_token"], "text": "Acabar os dobros", "status": "doing"},
    )
    assert resp.status_code == 200

    # fechar sessão
    resp = await client.post(f"/api/sessions/{session['id']}/close")
    assert resp.json()["status"] == "closed"


async def test_student_stream_filters_events(client):
    resp = await client.post("/api/classes", json={"name": "1.º C", "year": 1, "students": ["Zé", "Mia"]})
    cls = resp.json()
    resp = await client.post(
        "/api/sessions", json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "Sílabas"}
    )
    session = resp.json()
    public = (await client.get(f"/api/join/{session['join_code']}")).json()
    s1, s2 = public["roster"][0], public["roster"][1]
    c1 = (await client.post(f"/api/sessions/{session['id']}/claim", json={"student_id": s1["student_id"]})).json()
    c2 = (await client.post(f"/api/sessions/{session['id']}/claim", json={"student_id": s2["student_id"]})).json()

    # mensagem dirigida só ao aluno 2
    await client.post(
        f"/api/sessions/{session['id']}/message",
        json={"text": "Boa, Mia!", "student_id": s2["student_id"]},
    )
    await client.post(f"/api/sessions/{session['id']}/close")

    async def collect(token):
        types = []
        async with client.stream(
            "GET",
            f"/api/sessions/{session['id']}/stream",
            params={"role": "student", "student_token": token},
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    types.append(json.loads(line[6:])["type"])
                if types and types[-1] == "session_closed":
                    break
        return types

    types1 = await asyncio.wait_for(collect(c1["student_token"]), timeout=5)
    types2 = await asyncio.wait_for(collect(c2["student_token"]), timeout=5)
    assert "teacher_message" not in types1  # dirigida à Mia, o Zé não vê
    assert "teacher_message" in types2
    # eventos de outros alunos (joined) nunca chegam a alunos
    assert "joined" not in types1 and "joined" not in types2


async def test_teacher_routes_require_token(client):
    # cliente "aluno": sem header de professor
    naked = {"x-teacher-token": ""}
    for method, url in [
        ("GET", "/api/sessions"),
        ("GET", "/api/classes"),
        ("GET", "/api/jobs"),
    ]:
        resp = await client.request(method, url, headers=naked)
        assert resp.status_code == 401, url
    resp = await client.post(
        "/api/classes", json={"name": "X", "year": 1, "students": []}, headers=naked
    )
    assert resp.status_code == 401


async def test_sessions_never_expose_student_tokens(client):
    cls = (await client.post("/api/classes", json={"name": "4.º D", "year": 4, "students": ["Nuno"]})).json()
    session = (
        await client.post(
            "/api/sessions", json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "T"}
        )
    ).json()
    await client.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": next(iter(session["roster"]))},
    )
    for url in (f"/api/sessions/{session['id']}", "/api/sessions"):
        body = (await client.get(url)).text
        assert '"token"' not in body, url


async def test_stream_rejects_missing_role(client):
    cls = (await client.post("/api/classes", json={"name": "X", "year": 1, "students": ["A"]})).json()
    session = (
        await client.post(
            "/api/sessions", json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "T"}
        )
    ).json()
    resp = await client.get(f"/api/sessions/{session['id']}/stream", headers={"x-teacher-token": ""})
    assert resp.status_code == 400
    resp = await client.get(
        f"/api/sessions/{session['id']}/stream", params={"role": "teacher"}, headers={"x-teacher-token": ""}
    )
    assert resp.status_code == 401


async def test_activities_get_restrictive_csp(client):
    resp = await client.get("/activities/")
    csp = resp.headers.get("content-security-policy", "")
    assert "connect-src 'none'" in csp


async def test_student_resume_via_me(client):
    cls = (await client.post("/api/classes", json={"name": "1.º D", "year": 1, "students": ["Maria"]})).json()
    session = (
        await client.post(
            "/api/sessions", json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "T"}
        )
    ).json()
    student_id = next(iter(session["roster"]))
    claim = (
        await client.post(f"/api/sessions/{session['id']}/claim", json={"student_id": student_id})
    ).json()

    # retoma válida: devolve identidade + sessão pública sem tokens
    resp = await client.get(
        f"/api/sessions/{session['id']}/me", params={"student_token": claim["student_token"]}
    )
    assert resp.status_code == 200
    me = resp.json()
    assert me["display_name"] == "Maria"
    assert '"token"' not in resp.text
    assert me["session"]["status"] == "live"

    # token errado → 401
    resp = await client.get(f"/api/sessions/{session['id']}/me", params={"student_token": "x"})
    assert resp.status_code == 401

    # depois de fechada, a retoma reporta o estado (o cliente limpa e volta ao código)
    await client.post(f"/api/sessions/{session['id']}/close")
    resp = await client.get(
        f"/api/sessions/{session['id']}/me", params={"student_token": claim["student_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["session"]["status"] == "closed"


async def test_class_report_endpoint(client):
    cls = (await client.post("/api/classes", json={"name": "4.º E", "year": 4, "students": ["Pedro"]})).json()
    resp = await client.get(f"/api/classes/{cls['id']}/report")
    assert resp.status_code == 200
    report = resp.json()
    assert report["class_name"] == "4.º E"
    assert report["students"][0]["display_name"] == "Pedro"
    md = await client.get(f"/api/classes/{cls['id']}/report", params={"format": "md"})
    assert md.status_code == 200
    assert "Registo de trabalho" in md.text
    # exige token de professor
    resp = await client.get(f"/api/classes/{cls['id']}/report", headers={"x-teacher-token": ""})
    assert resp.status_code == 401


async def test_session_control_events(client):
    cls = (await client.post("/api/classes", json={"name": "3.º C", "year": 3, "students": ["Inês", "Duarte"]})).json()
    session = (
        await client.post(
            "/api/sessions", json={"class_id": cls["id"], "activity_slug": "demo", "activity_title": "T"}
        )
    ).json()
    public = (await client.get(f"/api/join/{session['join_code']}")).json()
    s1, s2 = public["roster"]
    c1 = (await client.post(f"/api/sessions/{session['id']}/claim", json={"student_id": s1["student_id"]})).json()
    c2 = (await client.post(f"/api/sessions/{session['id']}/claim", json={"student_id": s2["student_id"]})).json()

    # highlight dirigido só ao aluno 2; freeze para todos
    resp = await client.post(
        f"/api/sessions/{session['id']}/control",
        json={"action": "highlight", "unit_id": "u2", "unit_label": "Missão de leitura", "student_id": s2["student_id"]},
    )
    assert resp.status_code == 200
    assert (await client.post(f"/api/sessions/{session['id']}/control", json={"action": "freeze"})).status_code == 200
    assert (await client.post(f"/api/sessions/{session['id']}/control", json={"action": "unfreeze"})).status_code == 200
    # sem token de professor → 401; ação inválida → 422
    resp = await client.post(
        f"/api/sessions/{session['id']}/control", json={"action": "freeze"}, headers={"x-teacher-token": ""}
    )
    assert resp.status_code == 401
    resp = await client.post(f"/api/sessions/{session['id']}/control", json={"action": "explodir"})
    assert resp.status_code == 422

    await client.post(f"/api/sessions/{session['id']}/close")

    async def collect(token):
        types = []
        async with client.stream(
            "GET",
            f"/api/sessions/{session['id']}/stream",
            params={"role": "student", "student_token": token},
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    types.append(json.loads(line[6:])["type"])
                if types and types[-1] == "session_closed":
                    break
        return types

    types1 = await asyncio.wait_for(collect(c1["student_token"]), timeout=5)
    types2 = await asyncio.wait_for(collect(c2["student_token"]), timeout=5)
    assert "freeze_screens" in types1 and "unfreeze_screens" in types1
    assert "teacher_highlight" not in types1  # era dirigido ao aluno 2
    assert "teacher_highlight" in types2


async def test_activities_catalog_and_units(client):
    data = (await client.get("/api/activities")).json()
    assert "items" in data and "subjects" in data and "years" in data
    if data["items"]:
        item = data["items"][0]
        assert {"slug", "title", "subject", "year", "tags"} <= set(item)
        units = (await client.get(f"/api/activities/{item['slug']}/units")).json()
        assert units["units"], "atividade publicada deve ter unidades do docspec"
        assert units["units"][0]["id"] == "u1"
    resp = await client.get("/api/activities/nao-existe/units")
    assert resp.status_code == 404
    # path traversal rejeitado
    for bad in ("..", "%2e%2e", "a..b", "UPPER", "a/b"):
        resp = await client.get(f"/api/activities/{bad}/units")
        assert resp.status_code == 404, bad


async def test_health_and_meta(client):
    health = (await client.get("/api/health")).json()
    assert health["status"] == "ok"
    meta = (await client.get("/api/meta")).json()
    assert meta["years"] == [1, 2, 3, 4]
    assert "Matemática" in meta["subjects"]
