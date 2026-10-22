"""Ciclo de vida reconstruído do registo, incluindo novas janelas de aula."""
from typing import Iterable, Mapping


def session_lifecycle(events: Iterable[Mapping], session: Mapping) -> dict:
    state = {
        "status": "live", "closed_at": None,
        "active_since": session.get("active_since", session.get("started_at")),
        "frozen": False,
    }
    for record in events:
        kind = record.get("type")
        if kind == "session_closed":
            state.update(status="closed", closed_at=record.get("ts"))
        elif kind == "session_resumed":
            state.update(status="live", closed_at=None, frozen=False,
                         active_since=record.get("ts"))
        elif kind == "freeze_screens":
            state["frozen"] = True
        elif kind == "unfreeze_screens":
            state["frozen"] = False
    return state
