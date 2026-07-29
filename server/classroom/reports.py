"""Relatórios agregados por turma, para a avaliação cooperada (conselho).

Agrega os eventos de todas as sessões de uma turma num intervalo de datas:
por aluno (participação, tentativas, descobertas, pedidos de ajuda, PIT,
partilhas) e por sessão. Sem juízos automáticos: o relatório é matéria-prima
para o conselho de cooperação, não uma classificação.
"""

from __future__ import annotations

from ..storage import Storage
from .event_types import SESSION_EVENT_TYPES
from .session_state import reduce_session


def _blank_student(name: str, evidence_types: tuple[str, ...]) -> dict:
    row = {"display_name": name, "sessions": 0, "correct": 0, "pit_total": 0, "pit_done": 0}
    for event_type in evidence_types:
        row[event_type] = 0
    return row


async def build_class_report(
    storage: Storage,
    class_data: dict,
    sessions: list[dict],
    date_from: str = "",
    date_to: str = "",
) -> dict:
    """Relatório agregado. `date_from`/`date_to` são prefixos ISO (ex.: 2026-07)."""
    evidence_types = tuple(
        event_type.name for event_type in SESSION_EVENT_TYPES.evidence()
    )
    students: dict[str, dict] = {
        s["id"]: _blank_student(s["display_name"], evidence_types)
        for s in class_data["students"]
    }
    session_rows: list[dict] = []

    for session in sessions:
        if session.get("class_id") != class_data["id"]:
            continue
        started = session.get("started_at") or ""
        if date_from and started[: len(date_from)] < date_from:
            continue
        if date_to and started[: len(date_to)] > date_to:
            continue

        events = await storage.read_jsonl(
            storage.path("sessions", session["id"], "events.jsonl")
        )
        reduction_now = (
            session.get("closed_at")
            or (events[-1].get("ts") if events else None)
            or started
            or "1970-01-01T00:00:00+00:00"
        )
        state = reduce_session(
            events,
            now=reduction_now,
            roster=session.get("roster", {}),
            started_at=started or None,
        )
        numbers = state["numbers"]
        row = {
            "session_id": session["id"],
            "activity_title": session.get("activity_title", ""),
            "started_at": started,
            "status": session.get("status", ""),
            "participants": numbers["participants"],
            "attempts": numbers["evidence"]["attempt"],
            "discoveries": numbers["evidence"]["discovery"],
            "help_needed": numbers["evidence"]["help_needed"],
        }
        for student_id, student_state in state["students"].items():
            st = students.get(student_id)
            if st is None:
                continue
            student_numbers = student_state["numbers"]
            if student_state["participated"]:
                st["sessions"] += 1
            for event_type, count in student_numbers["evidence"].items():
                st[event_type] += count
            st["correct"] += student_numbers["correct_attempts"]
            st["pit_total"] += student_numbers["pit_total"]
            st["pit_done"] += student_numbers["pit_done"]
        session_rows.append(row)

    session_rows.sort(key=lambda r: r["started_at"])
    return {
        "class_id": class_data["id"],
        "class_name": class_data["name"],
        "year": class_data.get("year"),
        "date_from": date_from,
        "date_to": date_to,
        "sessions": session_rows,
        "students": sorted(students.values(), key=lambda s: s["display_name"]),
    }


def report_to_markdown(report: dict) -> str:
    """Versão em Markdown para levar ao conselho de cooperação."""
    period = ""
    if report["date_from"] or report["date_to"]:
        period = f" · período {report['date_from'] or '…'} a {report['date_to'] or '…'}"
    lines = [
        f"# Registo de trabalho — {report['class_name']}{period}",
        "",
        "Matéria-prima para a avaliação cooperada: o que cada um fez, pediu e partilhou.",
        "",
        "## Por aluno",
        "",
        "| Aluno | Aulas | Tentativas | Certas | Descobertas | Pediu ajuda | Feedback pedido | Partilhas | PIT feito |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in report["students"]:
        lines.append(
            f"| {s['display_name']} | {s['sessions']} | {s['attempt']} | {s['correct']} "
            f"| {s['discovery']} | {s['help_needed']} | {s['feedback_request']} "
            f"| {s['share_requested']} | {s['pit_done']}/{s['pit_total']} |"
        )
    lines += ["", "## Por sessão", ""]
    if not report["sessions"]:
        lines.append("_Sem sessões no período._")
    else:
        lines += [
            "| Data | Atividade | Presentes | Tentativas | Descobertas | Pedidos de ajuda |",
            "|---|---|---|---|---|---|",
        ]
        for r in report["sessions"]:
            day = (r["started_at"] or "")[:10]
            lines.append(
                f"| {day} | {r['activity_title']} | {r['participants']} | {r['attempts']} "
                f"| {r['discoveries']} | {r['help_needed']} |"
            )
    lines.append("")
    return "\n".join(lines)
