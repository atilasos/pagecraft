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


def _blank_student(
    evidence_types: tuple[str, ...],
    *,
    anchor: datetime | None = None,
    display_name: str | None = None,
) -> dict:
    student = {
        "numbers": _blank_numbers(evidence_types),
        "participated": False,
        "_last_presence": anchor,
        "_last_work": anchor,
        "_help_since": None,
        "_consecutive_failures": 0,
        "_failures_since": None,
        "_pit_items": {},
    }
    if display_name is not None:
        student["display_name"] = display_name
    return student


def reduce_session(
    events: Iterable[Mapping],
    *,
    now: datetime | str,
    roster: Mapping[str, object] | Iterable[str] = (),
    started_at: datetime | str | None = None,
) -> dict:
    """Produz sempre o mesmo estado para a mesma sequência e o mesmo instante."""
    events = list(events)
    now_instant = _instant(now)
    if now_instant is None:
        raise ValueError("now tem de ser um instante válido")
    start_instant = _instant(started_at)
    evidence_types = tuple(
        event_type.name for event_type in SESSION_EVENT_TYPES.evidence()
    )
    students: dict[str, dict] = {}
    roster_entries = roster.items() if isinstance(roster, Mapping) else (
        (student_id, None) for student_id in roster
    )
    for student_id, entry in roster_entries:
        display_name = None
        if isinstance(entry, Mapping):
            display_name = entry.get("display_name")
        elif isinstance(entry, str):
            display_name = entry
        students[str(student_id)] = _blank_student(
            evidence_types,
            anchor=start_instant,
            display_name=str(display_name) if display_name is not None else None,
        )
    groups = {}
    group_ids = {str(event["work_group_id"]) for event in events if event.get("work_group_id")}
    # Reduce the joint production once; its counts never become individual results.
    for group_id in sorted(group_ids):
        records = [event for event in events if event.get("work_group_id") == group_id]
        joined = next((event for event in records if event.get("type") == "work_group_joined"), None)
        if joined is None:
            continue
        description = joined["payload"]
        projected = [
            {key: value for key, value in event.items() if key not in {"work_group_id", "participant_ids"}}
            | {"student_id": group_id, "type": "joined" if event.get("type") == "work_group_joined" else "identity_released" if event.get("type") == "work_group_released" else event.get("type")}
            for event in records
        ]
        group = reduce_session(projected, now=now, roster={group_id: {"display_name": description["display_name"]}}, started_at=started_at)["students"][group_id]
        group.update({"id": group_id, "participant_ids": joined["participant_ids"], "members": description["members"], "level": description["level"], "active": not any(e.get("type") == "work_group_released" for e in records)})
        for event in records:
            if event.get("type") == "level_changed" and (event.get("payload") or {}).get("level") in {"support", "intermediate", "challenge"}:
                group["level"] = event["payload"]["level"]
        groups[group_id] = group

    participants: set[str] = set()

    for event in events:
        if event.get("type") == "work_group_joined":
            for sid in event.get("participant_ids", []):
                if sid in students:
                    students[sid]["participated"] = True
                    participants.add(sid)
        student_id = event.get("student_id")
        if not student_id:
            continue
        student = students.setdefault(
            str(student_id),
            _blank_student(evidence_types, anchor=start_instant),
        )
        event_type = event.get("type")
        declaration = SESSION_EVENT_TYPES.get(str(event_type))
        instant = _instant(event.get("ts"))
        if (
            event_type == "identity_released"
            and (event.get("payload") or {}).get("reset_progress") is True
        ):
            student["numbers"] = _blank_numbers(evidence_types)
            student["_last_work"] = instant
            student["_help_since"] = None
            student["_consecutive_failures"] = 0
            student["_failures_since"] = None
            student["_pit_items"].clear()
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
            student["participated"] = True
            display_name = (event.get("payload") or {}).get("display_name")
            if display_name and "display_name" not in student:
                student["display_name"] = str(display_name)
            if student["_last_work"] is None:
                student["_last_work"] = instant
        elif event_type in _WORK_EVENT_TYPES and instant is not None:
            student["_last_work"] = instant
            student["_help_since"] = None
        elif event_type == "ai_feedback":
            student["_help_since"] = None
        if event_type == "attempt":
            correct = (event.get("payload") or {}).get("correct")
            if correct is True:
                student["_consecutive_failures"] = 0
                student["_failures_since"] = None
            elif correct is False:
                if student["_consecutive_failures"] == 0:
                    student["_failures_since"] = instant
                student["_consecutive_failures"] += 1
        elif event_type == "pit_updated":
            payload = event.get("payload") or {}
            item_id = payload.get("id")
            status = payload.get("status")
            if item_id and status:
                item = dict(payload)
                item.pop("previous_status", None)
                item["id"] = str(item_id)
                item["student_id"] = str(
                    student_id or item.get("student_id") or ""
                )
                item["status"] = str(status)
                student["_pit_items"][str(item_id)] = item
        if event_type not in student["numbers"]["evidence"]:
            continue
        student["numbers"]["evidence"][event_type] += 1
        if event_type == "attempt" and (event.get("payload") or {}).get("correct"):
            student["numbers"]["correct_attempts"] += 1

    numbers = _blank_numbers(evidence_types)
    numbers["participants"] = len(participants)
    for student in students.values():
        pit_items = list(student.pop("_pit_items").values())
        student["pit_items"] = pit_items
        student["numbers"]["pit_total"] = len(pit_items)
        student["numbers"]["pit_done"] = sum(
            item["status"] in {"done", "to_share"} for item in pit_items
        )
        for event_type, count in student["numbers"]["evidence"].items():
            numbers["evidence"][event_type] += count
        numbers["correct_attempts"] += student["numbers"]["correct_attempts"]
        numbers["pit_total"] += student["numbers"]["pit_total"]
        numbers["pit_done"] += student["numbers"]["pit_done"]
        presence_wait = _elapsed_seconds(now_instant, student.pop("_last_presence"))
        work_wait = _elapsed_seconds(now_instant, student.pop("_last_work"))
        help_since = student.pop("_help_since")
        explicit_help = help_since is not None
        help_wait = _elapsed_seconds(now_instant, help_since)
        consecutive_failures = student.pop("_consecutive_failures")
        failures_wait = _elapsed_seconds(
            now_instant, student.pop("_failures_since")
        )
        if presence_wait >= 90:
            band, reason = "Sem sinal", "Sem presença"
            wait_seconds = presence_wait
        elif explicit_help:
            band, reason = "Precisa de ti", "Pediu ajuda"
            wait_seconds = max(help_wait, work_wait if work_wait >= 180 else 0)
        elif work_wait >= 180:
            band, reason = "Precisa de ti", "Parado"
            wait_seconds = work_wait
        elif consecutive_failures >= 3:
            band, reason = "A tropeçar", "Três falhas consecutivas"
            wait_seconds = failures_wait
        else:
            band, reason = "A fluir", "A trabalhar"
            wait_seconds = work_wait
        student["triage"] = {
            "band": band,
            "reason": reason,
            "wait_seconds": wait_seconds,
            "explicit_help": explicit_help,
        }

    for group in groups.values():
        for event_type, count in group["numbers"]["evidence"].items():
            numbers["evidence"][event_type] += count
        numbers["correct_attempts"] += group["numbers"]["correct_attempts"]
        for sid in group["participant_ids"]:
            if sid in students:
                students[sid].setdefault("shared_work", []).append({"work_group_id": group["id"], "display_name": group["display_name"]})
                if group["active"]:
                    students[sid]["triage"] = group["triage"]
    result = {"students": students, "numbers": numbers}
    if groups:
        result["groups"] = groups
    return result
