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
    assert first["students"]["ana"]["participated"] is True
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


def test_presence_without_work_does_not_imply_difficulty():
    events = [
        event("joined", 0),
        event("heartbeat", 3),
    ]

    state = reduce_session(
        events,
        now=datetime(2026, 7, 29, 10, 3, tzinfo=timezone.utc),
    )

    assert state["students"]["ana"]["triage"] == {
        "band": "A fluir",
        "reason": "Sem atividade recente no PageCraft",
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


def test_plan_replays_the_complete_sequence_and_the_final_step_back():
    transitions = [
        (None, "planned"),
        ("planned", "doing"),
        ("doing", "done"),
        ("done", "to_share"),
        ("to_share", "done"),
    ]
    events = [
        event(
            "pit_updated",
            minute,
            payload={
                "id": "p1",
                "student_id": "ana",
                "text": "Preparar a leitura",
                "previous_status": previous_status,
                "status": status,
                "updated_at": f"2026-07-29T10:{minute:02d}:00+00:00",
            },
        )
        for minute, (previous_status, status) in enumerate(transitions)
    ]

    state = reduce_session(events, now=NOW)

    assert state["students"]["ana"]["pit_items"] == [
        {
            "id": "p1",
            "student_id": "ana",
            "text": "Preparar a leitura",
            "status": "done",
            "updated_at": "2026-07-29T10:04:00+00:00",
        }
    ]
    assert state["students"]["ana"]["numbers"]["pit_total"] == 1
    assert state["students"]["ana"]["numbers"]["pit_done"] == 1


def test_roster_student_without_events_uses_session_start_as_time_anchor():
    state = reduce_session(
        [],
        roster={"beatriz": {"display_name": "Beatriz"}},
        started_at="2026-07-29T10:00:00+00:00",
        now=datetime(2026, 7, 29, 10, 1, 30, tzinfo=timezone.utc),
    )

    assert state["students"]["beatriz"]["display_name"] == "Beatriz"
    assert state["students"]["beatriz"]["participated"] is False
    assert state["students"]["beatriz"]["triage"]["band"] == "Sem sinal"
    assert state["students"]["beatriz"]["triage"]["wait_seconds"] == 90
    assert state["students"]["beatriz"]["numbers"]["evidence"]["attempt"] == 0


def test_each_declared_kind_of_work_resets_the_stopped_clock():
    work_events = {
        "attempt": {"correct": True},
        "discovery": {},
        "unit_started": {},
        "pit_updated": {"id": "p1", "status": "planned"},
        "feedback_request": {},
    }

    for event_type, payload in work_events.items():
        state = reduce_session(
            [
                event("joined", 0),
                event(event_type, 3, payload=payload),
                event("heartbeat", 5),
            ],
            now=NOW,
        )

        assert state["students"]["ana"]["triage"]["band"] == "A fluir"


def test_assessment_result_counts_as_work():
    state = reduce_session(
        [
            event("joined", 0),
            event("assessment_result", 3),
            event("heartbeat", 3),
        ],
        now=datetime(2026, 7, 29, 10, 3, tzinfo=timezone.utc),
    )

    student = state["students"]["ana"]
    assert student["numbers"]["evidence"]["assessment_result"] == 1
    assert student["triage"]["band"] == "A fluir"
    assert student["triage"]["reason"] == "A trabalhar"


def test_explicit_help_does_not_restart_an_older_wait_in_the_same_band():
    state = reduce_session(
        [
            event("joined", 0),
            event("help_needed", 3),
            event("heartbeat", 4),
        ],
        now=datetime(2026, 7, 29, 10, 4, tzinfo=timezone.utc),
    )

    triage = state["students"]["ana"]["triage"]
    assert triage["band"] == "Precisa de ti"
    assert triage["explicit_help"] is True
    assert triage["wait_seconds"] == 60


def test_releasing_an_identity_keeps_progress_by_default():
    events = [
        event("joined", 0),
        event("attempt", 1, payload={"correct": True}),
        event("discovery", 2),
        event("pit_updated", 2, payload={"id": "p1", "status": "done"}),
        event("identity_released", 3),
        event("joined", 4),
        event("attempt", 4, payload={"correct": False}),
    ]

    student = reduce_session(events, now=NOW)["students"]["ana"]

    assert student["numbers"]["evidence"]["attempt"] == 2
    assert student["numbers"]["evidence"]["discovery"] == 1
    assert student["numbers"]["correct_attempts"] == 1
    assert student["numbers"]["pit_total"] == 1
    assert student["numbers"]["pit_done"] == 1


def test_explicit_reset_is_a_frontier_for_all_numbers_and_plan_items():
    events = [
        event("joined", 0),
        event("attempt", 1, payload={"correct": True}),
        event("discovery", 2),
        event("pit_updated", 2, payload={"id": "old", "status": "done"}),
        event("identity_released", 3, payload={"reset_progress": True}),
        event("joined", 4),
        event("attempt", 4, payload={"correct": False}),
        event("pit_updated", 4, payload={"id": "new", "status": "planned"}),
    ]

    state = reduce_session(events, now=NOW)
    student = state["students"]["ana"]

    assert student["numbers"]["evidence"]["attempt"] == 1
    assert student["numbers"]["evidence"]["discovery"] == 0
    assert student["numbers"]["evidence"]["pit_updated"] == 1
    assert student["numbers"]["correct_attempts"] == 0
    assert student["numbers"]["pit_total"] == 1
    assert student["numbers"]["pit_done"] == 0
    assert state["numbers"] == {
        **student["numbers"],
        "participants": 1,
    }
    assert len(events) == 8


def test_canva_reading_and_discussion_are_declared_work_even_without_presence():
    for location in ['canva', 'reading', 'discussion']:
        records = [event('joined', 0), event('work_location', 1, payload={'location': location})]
        student = reduce_session(records, now=NOW)['students']['ana']
        assert student['triage']['band'] == 'A fluir'
        assert student['triage']['reason'].startswith('Trabalho declarado: ')
        assert student['work_location'] == location
        records.append(event('help_needed', 2))
        assert reduce_session(records, now=NOW)['students']['ana']['triage']['explicit_help']


def test_a_hint_or_revision_does_not_resolve_an_explicit_help_request():
    records = [event('joined', 0), event('help_needed', 1),
               event('ai_feedback', 2), event('assessment_result', 3), event('heartbeat', 5)]
    assert reduce_session(records, now=NOW)['students']['ana']['triage']['explicit_help']
    records.append(event('help_resolved', 5, payload={'note': 'Já conseguimos continuar'}))
    assert not reduce_session(records, now=NOW)['students']['ana']['triage']['explicit_help']


def test_any_named_external_application_is_declared_work():
    student=reduce_session([event('joined',0),event('work_location',1,payload={'location':'external','label':'Scratch'})],now=NOW)['students']['ana']
    assert student['triage']['reason']=='Trabalho declarado: Scratch'
    assert student['work_location']=='external'
