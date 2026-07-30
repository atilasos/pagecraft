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
