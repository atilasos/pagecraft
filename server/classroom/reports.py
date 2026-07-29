"""Relatórios agregados por turma, para a avaliação cooperada (conselho).

Agrega os eventos de todas as sessões de uma turma num intervalo de datas:
por aluno (participação, tentativas, descobertas, pedidos de ajuda, PIT,
partilhas) e por sessão. Sem juízos automáticos: o relatório é matéria-prima
para o conselho de cooperação, não uma classificação.
"""

from __future__ import annotations

from ..storage import Storage
from .event_types import SESSION_EVENT_TYPES


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
        participants: set[str] = set()
        row = {
            "session_id": session["id"],
            "activity_title": session.get("activity_title", ""),
            "started_at": started,
            "status": session.get("status", ""),
            "participants": 0,
            "attempts": 0,
            "discoveries": 0,
            "help_needed": 0,
        }
        for ev in events:
            sid = ev.get("student_id")
            ev_type = ev.get("type", "")
            st = students.get(sid) if sid else None
            if st is not None and ev_type == "joined":
                participants.add(sid)
            if st is None:
                continue
            if ev_type not in evidence_types:
                continue
            st[ev_type] += 1
            if ev_type == "attempt":
                row["attempts"] += 1
                if (ev.get("payload") or {}).get("correct"):
                    st["correct"] += 1
            elif ev_type == "discovery":
                row["discoveries"] += 1
            elif ev_type == "help_needed":
                row["help_needed"] += 1

        for sid in participants:
            students[sid]["sessions"] += 1
        row["participants"] = len(participants)
        session_rows.append(row)

        for item in session.get("pit_items", []):
            st = students.get(item.get("student_id"))
            if st is None:
                continue
            st["pit_total"] += 1
            if item.get("status") in ("done", "to_share"):
                st["pit_done"] += 1

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
