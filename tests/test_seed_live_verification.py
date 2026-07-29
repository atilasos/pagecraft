from datetime import datetime

from scripts.seed_live_verification import build_fixture, seed
from server.classroom.session_state import reduce_session


def test_seed_covers_all_triage_bands_and_orders_needs_by_wait(tmp_path):
    now = datetime.fromisoformat("2026-07-29T12:00:00+00:00")
    classroom, session, events, manifest = build_fixture(now)

    state = reduce_session(
        events,
        now=now,
        roster=session["roster"],
        started_at=session["started_at"],
    )
    students = state["students"]

    by_band = {}
    for student in students.values():
        by_band.setdefault(student["triage"]["band"], []).append(student)
    needs = sorted(
        by_band["Precisa de ti"],
        key=lambda student: -student["triage"]["wait_seconds"],
    )

    assert set(by_band) == {"Sem sinal", "Precisa de ti", "A tropeçar", "A fluir"}
    assert [student["display_name"] for student in needs] == ["Beatriz", "Carlos"]
    assert needs[0]["triage"]["explicit_help"] is True
    assert needs[1]["triage"]["explicit_help"] is False
    assert manifest["expected"]["Precisa de ti"] == ["Beatriz", "Carlos"]
    assert len(classroom["students"]) == 6


def test_seed_writes_a_server_ready_fixture(tmp_path):
    now = datetime.fromisoformat("2026-07-29T12:00:00+00:00")

    manifest = seed(tmp_path, now)

    assert (tmp_path / "classes" / "verify25.json").is_file()
    assert (tmp_path / "sessions" / "verify25" / "session.json").is_file()
    assert (tmp_path / "sessions" / "verify25" / "events.jsonl").is_file()
    assert manifest["join_code"] == "PC2525"
