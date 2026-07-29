"""Frames transitórios do estado vivo de uma Sessão de aula.

Estes frames são projeções do registo e nunca são Acontecimentos persistidos.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime

from .session_state import reduce_session


def _session_projection(events: Iterable[Mapping], session: Mapping) -> dict:
    frozen = False
    status = str(session.get("status") or "live")
    for record in events:
        event_type = record.get("type")
        if event_type == "freeze_screens":
            frozen = True
        elif event_type == "unfreeze_screens":
            frozen = False
        elif event_type == "session_closed":
            status = "closed"
    return {
        "status": status,
        "closed": status == "closed",
        "frozen": frozen,
    }


def session_state_snapshot(
    events: list[Mapping],
    session: Mapping,
    *,
    now: datetime | str,
    role: str,
    student_id: str | None = None,
) -> dict:
    """Projeta o estado autorizado no instante pedido."""
    state = reduce_session(
        events,
        now=now,
        roster=session.get("roster", {}),
        started_at=session.get("started_at"),
    )
    students = state["students"]
    if role == "student":
        if student_id is None:
            raise ValueError("o instantâneo de aluno requer uma identidade")
        students = (
            {student_id: students[student_id]}
            if student_id in students
            else {}
        )
    elif role != "teacher":
        raise ValueError(f"papel desconhecido: {role}")

    snapshot = {
        "session": _session_projection(events, session),
        "students": students,
    }
    if role == "teacher":
        snapshot["numbers"] = state["numbers"]
    return snapshot


def changed_student_frames(previous: Mapping, current: Mapping) -> list[dict]:
    """Compara duas projeções autorizadas sem expor alunos fora delas."""
    before = previous.get("students", {})
    after = current.get("students", {})
    return [
        {"student_id": student_id, "student": student}
        for student_id, student in after.items()
        if before.get(student_id) != student
    ]


def changed_session_frame(
    previous: Mapping, current: Mapping
) -> dict | None:
    """Produz o delta global quando o controlo ou ciclo de vida mudou."""
    session = current.get("session", {})
    if previous.get("session") == session:
        return None
    return {"session": session}
