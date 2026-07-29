"""Redução pura do registo de uma Sessão de aula para o seu estado vivo."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime

from .event_types import SESSION_EVENT_TYPES


def _blank_numbers(evidence_types: tuple[str, ...]) -> dict:
    return {
        "evidence": {event_type: 0 for event_type in evidence_types},
        "correct_attempts": 0,
        "pit_total": 0,
        "pit_done": 0,
    }


def reduce_session(
    events: Iterable[Mapping],
    *,
    now: datetime,
) -> dict:
    """Produz sempre o mesmo estado para a mesma sequência e o mesmo instante."""
    evidence_types = tuple(
        event_type.name for event_type in SESSION_EVENT_TYPES.evidence()
    )
    students: dict[str, dict] = {}
    participants: set[str] = set()

    for event in events:
        student_id = event.get("student_id")
        if not student_id:
            continue
        student = students.setdefault(
            str(student_id),
            {"numbers": _blank_numbers(evidence_types)},
        )
        event_type = event.get("type")
        if event_type == "joined":
            participants.add(str(student_id))
        if event_type not in student["numbers"]["evidence"]:
            continue
        student["numbers"]["evidence"][event_type] += 1
        if event_type == "attempt" and (event.get("payload") or {}).get("correct"):
            student["numbers"]["correct_attempts"] += 1

    numbers = _blank_numbers(evidence_types)
    numbers["participants"] = len(participants)
    for student in students.values():
        for event_type, count in student["numbers"]["evidence"].items():
            numbers["evidence"][event_type] += count
        numbers["correct_attempts"] += student["numbers"]["correct_attempts"]

    return {"students": students, "numbers": numbers}
