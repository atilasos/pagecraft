"""Redução pura do registo de uma Sessão de aula para o seu estado vivo."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone

from .event_types import SESSION_EVENT_TYPES

_PRESENCE_AUTHORS = frozenset({"activity", "student"})
_WORK_EVENT_TYPES = frozenset(
    {"attempt", "discovery", "unit_started", "pit_updated", "feedback_request"}
)


def _instant(value: object) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _elapsed_seconds(now: datetime, since: datetime | None) -> int:
    if since is None:
        return 0
    return max(0, int((now - since).total_seconds()))


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
    now_instant = _instant(now)
    if now_instant is None:
        raise ValueError("now tem de ser um instante válido")
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
            {
                "numbers": _blank_numbers(evidence_types),
                "_last_presence": None,
                "_last_work": None,
                "_help_since": None,
            },
        )
        event_type = event.get("type")
        declaration = SESSION_EVENT_TYPES.get(str(event_type))
        instant = _instant(event.get("ts"))
        if instant is not None and (
            event_type == "joined"
            or (
                declaration is not None
                and bool(declaration.authors & _PRESENCE_AUTHORS)
            )
        ):
            student["_last_presence"] = instant
        if event_type == "help_needed":
            student["_help_since"] = instant
        if event_type == "joined":
            participants.add(str(student_id))
            if student["_last_work"] is None:
                student["_last_work"] = instant
        elif event_type in _WORK_EVENT_TYPES and instant is not None:
            student["_last_work"] = instant
            student["_help_since"] = None
        elif event_type == "ai_feedback":
            student["_help_since"] = None
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
        presence_wait = _elapsed_seconds(now_instant, student.pop("_last_presence"))
        work_wait = _elapsed_seconds(now_instant, student.pop("_last_work"))
        help_since = student.pop("_help_since")
        explicit_help = help_since is not None
        help_wait = _elapsed_seconds(now_instant, help_since)
        if presence_wait >= 90:
            band, reason = "Sem sinal", "Sem presença"
            wait_seconds = presence_wait
        elif explicit_help:
            band, reason = "Precisa de ti", "Pediu ajuda"
            wait_seconds = max(help_wait, work_wait if work_wait >= 180 else 0)
        elif work_wait >= 180:
            band, reason = "Precisa de ti", "Parado"
            wait_seconds = work_wait
        else:
            band, reason = "A fluir", "A trabalhar"
            wait_seconds = work_wait
        student["triage"] = {
            "band": band,
            "reason": reason,
            "wait_seconds": wait_seconds,
            "explicit_help": explicit_help,
        }

    return {"students": students, "numbers": numbers}
