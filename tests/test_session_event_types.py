import pytest

from server.classroom.event_types import (
    SESSION_EVENT_TYPES,
    SessionEventRegistry,
    SessionEventType,
)


def _names(entries):
    return {entry.name for entry in entries}


def test_registry_can_be_queried_without_knowing_its_representation():
    assert {
        "activity_loaded",
        "attempt",
        "discovery",
        "heartbeat",
    } <= _names(SESSION_EVENT_TYPES.by_author("activity"))
    assert "pit_updated" in _names(SESSION_EVENT_TYPES.by_author("student"))

    assert _names(SESSION_EVENT_TYPES.visible_to("student")) == {
        "ai_feedback",
        "freeze_screens",
        "pit_updated",
        "session_closed",
        "teacher_highlight",
        "teacher_message",
        "unfreeze_screens",
    }
    assert "feedback_error" in _names(SESSION_EVENT_TYPES.visible_to("teacher"))

    assert {
        "attempt",
        "discovery",
        "feedback_request",
        "help_needed",
        "pit_updated",
    } <= _names(SESSION_EVENT_TYPES.evidence())
    assert "heartbeat" not in _names(SESSION_EVENT_TYPES.timeline())


def test_internal_and_bridge_names_remain_distinct():
    highlight = SESSION_EVENT_TYPES.get("teacher_highlight")

    assert highlight is not None
    assert highlight.name == "teacher_highlight"
    assert highlight.bridge_name == "highlight"


def _entry(**changes):
    fields = {
        "name": "example",
        "authors": frozenset({"activity"}),
        "student_visible": False,
        "is_evidence": True,
        "in_timeline": True,
        "bridge_name": None,
        "payload_fields": {"answer": "Resposta observável da criança."},
    }
    fields.update(changes)
    return SessionEventType(**fields)


@pytest.mark.parametrize(
    "changes",
    (
        {"name": ""},
        {"authors": frozenset()},
        {"payload_fields": {"answer": ""}},
        {"authors": frozenset({"teacher"}), "is_evidence": True},
        {"student_visible": False, "bridge_name": "example"},
    ),
)
def test_incomplete_or_contradictory_entries_are_rejected(changes):
    with pytest.raises(ValueError):
        _entry(**changes)


def test_registry_rejects_ambiguous_names():
    first = _entry()
    second = _entry()

    with pytest.raises(ValueError):
        SessionEventRegistry((first, second))
