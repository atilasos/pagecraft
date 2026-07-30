import asyncio
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest

from server import app as app_module
from server.access import STUDENT_COOKIE_NAME


class MutableClock:
    def __init__(self, instant: datetime):
        self.instant = instant

    def __call__(self):
        return self.instant.isoformat()


@pytest.fixture
async def classroom_http(tmp_path, monkeypatch):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    clock = MutableClock(datetime(2026, 7, 30, 8, 30, tzinfo=timezone.utc))
    app = app_module.create_app(
        classroom_clock=clock,
        school_timezone=ZoneInfo("Europe/Lisbon"),
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with (
            httpx.AsyncClient(transport=transport, base_url="http://test") as teacher,
            httpx.AsyncClient(transport=transport, base_url="http://test") as student,
        ):
            assert (await teacher.get("/teacher/")).status_code == 200
            yield app, teacher, student, clock


async def create_session(teacher, students=("Ana",)):
    classroom = (
        await teacher.post(
            "/api/classes",
            json={"name": "3.º A", "year": 3, "students": list(students)},
        )
    ).json()
    return (
        await teacher.post(
            "/api/sessions",
            json={
                "class_id": classroom["id"],
                "activity_slug": "fracoes",
                "activity_title": "Frações",
            },
        )
    ).json()


async def test_claim_issues_httponly_cookie_and_me_accepts_only_that_cookie(
    classroom_http,
):
    app, teacher, student, _ = classroom_http
    session = await create_session(teacher)
    student_id = next(iter(session["roster"]))

    claim = await student.post(
        f"/api/sessions/{session['id']}/claim",
        json={"student_id": student_id},
    )

    assert claim.status_code == 200
    assert claim.json() == {"student_id": student_id, "display_name": "Ana"}
    assert "student_token" not in claim.text
    set_cookie = claim.headers["set-cookie"]
    assert set_cookie.startswith(f"{STUDENT_COOKIE_NAME}=")
    assert "HttpOnly" in set_cookie
    assert "SameSite=strict" in set_cookie
    assert "expires=Thu, 30 Jul 2026 23:00:00 GMT" in set_cookie
    assert "Max-Age=52200" in set_cookie

    resumed = await student.get(f"/api/sessions/{session['id']}/me")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as legacy_client:
        legacy = await legacy_client.get(
            f"/api/sessions/{session['id']}/me",
            params={"student_token": student.cookies.get(STUDENT_COOKIE_NAME)},
        )

    assert resumed.status_code == 200
    assert resumed.json()["display_name"] == "Ana"
    assert legacy.status_code == 401


async def test_default_school_timezone_keeps_dst_transitions(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("PAGECRAFT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("TZ", "Europe/Lisbon")
    clock = MutableClock(
        datetime(2026, 3, 28, 23, 30, tzinfo=timezone.utc)
    )
    app = app_module.create_app(classroom_clock=clock)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with (
            httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as teacher,
            httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as student,
        ):
            assert (await teacher.get("/teacher/")).status_code == 200
            session = await create_session(teacher)
            student_id = next(iter(session["roster"]))
            claim = await student.post(
                f"/api/sessions/{session['id']}/claim",
                json={"student_id": student_id},
            )

    set_cookie = claim.headers["set-cookie"]
    assert "expires=Sun, 29 Mar 2026 00:00:00 GMT" in set_cookie
    assert "Max-Age=1800" in set_cookie


async def test_cookie_authenticates_events_and_pit_without_a_secret_body(
    classroom_http,
):
    app, teacher, student, _ = classroom_http
    session = await create_session(teacher, students=("Ana",))
    ana_id = next(iter(session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    events = await student.post(
        f"/api/sessions/{session['id']}/events",
        json={
            "events": [
                {
                    "event_id": "tentativa-ana",
                    "type": "attempt",
                    "payload": {"correct": True},
                }
            ]
        },
    )
    pit = await student.post(
        f"/api/sessions/{session['id']}/pit",
        json={"text": "Explicar as frações"},
    )
    assert events.status_code == 200
    assert pit.status_code == 200

    advanced = await student.post(
        f"/api/sessions/{session['id']}/pit/{pit.json()['id']}/advance",
        json={},
    )

    assert advanced.status_code == 200


async def test_student_http_contract_has_no_legacy_token_field(classroom_http):
    _, teacher, student, _ = classroom_http
    session = await create_session(teacher, students=("Ana",))
    ana_id = next(iter(session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    legacy_body = await student.post(
        f"/api/sessions/{session['id']}/events",
        json={"student_token": "segredo", "events": []},
    )
    openapi = await teacher.get("/openapi.json")

    assert legacy_body.status_code == 422
    assert "student_token" not in json.dumps(openapi.json())


async def test_own_history_survives_close_until_local_midnight(classroom_http):
    _, teacher, student, clock = classroom_http
    session = await create_session(teacher, students=("Ana", "Bia"))
    ana_id, bia_id = session["roster"]
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    assert (
        await student.get(
            f"/api/sessions/{session['id']}/students/{ana_id}/history"
        )
    ).status_code == 200
    assert (
        await student.get(
            f"/api/sessions/{session['id']}/students/{bia_id}/history"
        )
    ).status_code == 403
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/events",
            json={
                "events": [
                    {
                        "event_id": "descoberta-ana",
                        "type": "discovery",
                        "payload": {"message": "Descobri uma equivalência."},
                    }
                ]
            },
        )
    ).status_code == 200
    assert (
        await teacher.post(f"/api/sessions/{session['id']}/close")
    ).status_code == 200

    clock.instant = datetime(2026, 7, 30, 22, 59, tzinfo=timezone.utc)
    history = await student.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history"
    )
    resumed = await student.get(f"/api/sessions/{session['id']}/me")
    assert history.status_code == 200
    assert [event["type"] for event in history.json()["events"]] == [
        "discovery"
    ]
    assert resumed.status_code == 200
    assert resumed.json()["session"]["status"] == "closed"

    clock.instant = datetime(2026, 7, 30, 23, 0, tzinfo=timezone.utc)
    expired = await student.get(
        f"/api/sessions/{session['id']}/students/{ana_id}/history"
    )
    assert expired.status_code == 401


async def test_student_cookie_is_forbidden_on_another_session(classroom_http):
    _, teacher, student, _ = classroom_http
    own_session = await create_session(teacher, students=("Ana",))
    other_session = await create_session(teacher, students=("Carla",))
    ana_id = next(iter(own_session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{own_session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    crossed = await student.get(f"/api/sessions/{other_session['id']}/me")

    assert crossed.status_code == 403


async def test_release_revokes_the_old_cookie_and_live_stream(classroom_http):
    app, teacher, student, _ = classroom_http
    session = await create_session(teacher, students=("Ana",))
    ana_id = next(iter(session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    old_stream = asyncio.create_task(
        student.get(f"/api/sessions/{session['id']}/stream")
    )
    await asyncio.sleep(0.01)
    released = await teacher.post(
        f"/api/sessions/{session['id']}/release/{ana_id}"
    )
    stream_response = await asyncio.wait_for(old_stream, timeout=2)

    assert released.status_code == 200
    assert stream_response.status_code == 200
    assert (
        await student.get(f"/api/sessions/{session['id']}/me")
    ).status_code == 401

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as replacement:
        reclaimed = await replacement.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
        assert reclaimed.status_code == 200
        assert (
            await replacement.get(f"/api/sessions/{session['id']}/me")
        ).status_code == 200


async def test_stream_revalidates_after_replay_before_its_first_snapshot(
    classroom_http,
    monkeypatch,
):
    app, teacher, student, _ = classroom_http
    session = await create_session(teacher, students=("Ana",))
    ana_id = next(iter(session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    log = app.state.classroom.events_log(session["id"])
    original_replay = log.replay
    handler_reached_replay = asyncio.Event()
    continue_replay = asyncio.Event()
    replay_calls = 0

    async def coordinate_release_after_access(after_seq=0):
        nonlocal replay_calls
        replay_calls += 1
        if replay_calls == 3:
            handler_reached_replay.set()
            await continue_replay.wait()
        return await original_replay(after_seq)

    monkeypatch.setattr(log, "replay", coordinate_release_after_access)
    stream = asyncio.create_task(
        student.get(f"/api/sessions/{session['id']}/stream")
    )
    await asyncio.wait_for(handler_reached_replay.wait(), timeout=1)
    released = await teacher.post(
        f"/api/sessions/{session['id']}/release/{ana_id}"
    )
    continue_replay.set()
    response = await asyncio.wait_for(stream, timeout=1)

    assert released.status_code == 200
    assert response.status_code == 401


async def test_open_stream_expires_on_the_first_tick_of_the_next_day(
    classroom_http,
):
    app, teacher, student, clock = classroom_http
    session = await create_session(teacher, students=("Ana",))
    ana_id = next(iter(session["roster"]))
    assert (
        await student.post(
            f"/api/sessions/{session['id']}/claim",
            json={"student_id": ana_id},
        )
    ).status_code == 200

    stream = asyncio.create_task(
        student.get(f"/api/sessions/{session['id']}/stream")
    )
    await asyncio.sleep(0.01)
    clock.instant = datetime(2026, 7, 30, 23, 0, tzinfo=timezone.utc)
    app.state.classroom.tick_session(
        session["id"],
        now=clock.instant.isoformat(),
    )
    response = await asyncio.wait_for(stream, timeout=1)

    assert response.status_code == 200
