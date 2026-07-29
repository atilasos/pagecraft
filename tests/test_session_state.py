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


def test_explicit_help_is_visible_without_a_numeric_priority():
    state = reduce_session(
        [event("joined", 0), event("help_needed", 1)],
        now=datetime(2026, 7, 29, 10, 2, tzinfo=timezone.utc),
    )

    assert state["students"]["ana"]["triage"] == {
        "band": "Precisa de ti",
        "reason": "Pediu ajuda",
        "wait_seconds": 60,
        "explicit_help": True,
    }
    assert "score" not in state["students"]["ana"]
    assert "priority" not in state["students"]["ana"]["triage"]


def test_three_consecutive_failures_stumble_until_a_correct_attempt():
    failures = [
        event("joined", 0),
        event("attempt", 0, payload={"correct": False}),
        event("attempt", 1, payload={"correct": False}),
        event("attempt", 2, payload={"correct": False}),
    ]

    stumbling = reduce_session(
        failures,
        now=datetime(2026, 7, 29, 10, 2, tzinfo=timezone.utc),
    )
    recovered = reduce_session(
        [*failures, event("attempt", 3, payload={"correct": True})],
        now=datetime(2026, 7, 29, 10, 3, tzinfo=timezone.utc),
    )

    assert stumbling["students"]["ana"]["triage"] == {
        "band": "A tropeçar",
        "reason": "Três falhas consecutivas",
        "wait_seconds": 120,
        "explicit_help": False,
    }
    assert recovered["students"]["ana"]["triage"]["band"] == "A fluir"


def test_plan_numbers_come_from_the_latest_state_of_each_item():
    events = [
        event("joined", 0),
        event(
            "pit_updated",
            1,
            payload={"id": "p1", "status": "planned"},
        ),
        event(
            "pit_updated",
            2,
            payload={"id": "p1", "status": "done"},
        ),
        event(
            "pit_updated",
            3,
            payload={"id": "p2", "status": "to_share"},
        ),
    ]

    state = reduce_session(events, now=NOW)

    assert state["students"]["ana"]["numbers"]["pit_total"] == 2
    assert state["students"]["ana"]["numbers"]["pit_done"] == 2
    assert state["numbers"]["pit_total"] == 2
    assert state["numbers"]["pit_done"] == 2


def test_roster_student_without_events_uses_session_start_as_time_anchor():
    state = reduce_session(
        [],
        roster={"beatriz": {"display_name": "Beatriz"}},
        started_at="2026-07-29T10:00:00+00:00",
        now=datetime(2026, 7, 29, 10, 1, 30, tzinfo=timezone.utc),
    )

    assert state["students"]["beatriz"]["display_name"] == "Beatriz"
    assert state["students"]["beatriz"]["triage"]["band"] == "Sem sinal"
    assert state["students"]["beatriz"]["triage"]["wait_seconds"] == 90
    assert state["students"]["beatriz"]["numbers"]["evidence"]["attempt"] == 0
