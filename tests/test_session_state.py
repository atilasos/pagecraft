from datetime import datetime, timezone

from server.classroom.session_state import reduce_session


NOW = datetime(2026, 7, 29, 10, 5, tzinfo=timezone.utc)


def event(type_, minute, *, student_id="ana", payload=None):
    return {
        "type": type_,
        "student_id": student_id,
        "ts": f"2026-07-29T10:{minute:02d}:00+00:00",
        "payload": payload or {},
    }


def test_reduction_is_deterministic_and_counts_declared_evidence():
    events = [
        event("joined", 0),
        event("attempt", 1, payload={"correct": True}),
        event("discovery", 2),
        event("teacher_message", 3),
    ]

    first = reduce_session(events, now=NOW)
    second = reduce_session(events, now=NOW)

    assert first == second
    assert first["students"]["ana"]["numbers"]["evidence"]["attempt"] == 1
    assert first["students"]["ana"]["numbers"]["evidence"]["discovery"] == 1
    assert "teacher_message" not in first["students"]["ana"]["numbers"]["evidence"]
    assert first["numbers"]["evidence"]["attempt"] == 1
    assert first["numbers"]["correct_attempts"] == 1


def test_no_presence_for_ninety_seconds_has_highest_precedence():
    events = [
        event("joined", 0),
        event("attempt", 0, payload={"correct": False}),
        event("attempt", 0, payload={"correct": False}),
        event("attempt", 0, payload={"correct": False}),
        event("help_needed", 0),
    ]

    state = reduce_session(
        events,
        now=datetime(2026, 7, 29, 10, 1, 30, tzinfo=timezone.utc),
    )
    triage = state["students"]["ana"]["triage"]

    assert triage == {
        "band": "Sem sinal",
        "reason": "Sem presença",
        "wait_seconds": 90,
        "explicit_help": True,
    }


def test_presence_does_not_count_as_work_and_stopped_starts_at_three_minutes():
    events = [
        event("joined", 0),
        event("heartbeat", 3),
    ]

    state = reduce_session(
        events,
        now=datetime(2026, 7, 29, 10, 3, tzinfo=timezone.utc),
    )

    assert state["students"]["ana"]["triage"] == {
        "band": "Precisa de ti",
        "reason": "Parado",
        "wait_seconds": 180,
        "explicit_help": False,
    }
