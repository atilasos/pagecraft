"""Turmas, sessões de aula, identidades de alunos e eventos de progresso.

Sem dados sensíveis: alunos são apenas nome próprio/pseudónimo escolhido
pelo professor. A "autenticação" do aluno é um token opaco por sessão,
criado quando o aluno reclama a sua identidade no arranque da aula.
"""

from __future__ import annotations

import asyncio
import secrets
import uuid
from collections import defaultdict

from ..config import Config
from ..events import EventHub, utcnow
from ..storage import Storage

STUDENT_EVENT_TYPES = {
    "joined",
    "activity_loaded",
    "heartbeat",
    "unit_started",
    "attempt",
    "discovery",
    "assessment_result",
    "feedback_request",
    "help_needed",
    "share_requested",
}


def _join_code() -> str:
    # sem 0/O/1/I para ditar em voz alta sem ambiguidade
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(6))


class ClassroomService:
    def __init__(self, config: Config, storage: Storage, hub: EventHub):
        self.config = config
        self.storage = storage
        self.hub = hub
        self._seen_event_ids: dict[str, set[str]] = {}
        # lock por sessão: torna atómicas as transações read-modify-write
        # (claim/release/PIT/close); um só processo, chega um asyncio.Lock
        self._session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    # ---- turmas ----

    def _class_path(self, class_id: str):
        return self.storage.path("classes", f"{class_id}.json")

    async def create_class(self, name: str, year: int, students: list[str]) -> dict:
        cls = {
            "id": uuid.uuid4().hex[:10],
            "name": name,
            "year": year,
            "students": [
                {"id": uuid.uuid4().hex[:8], "display_name": s.strip()}
                for s in students
                if s.strip()
            ],
            "created_at": utcnow(),
        }
        await self.storage.write_json(self._class_path(cls["id"]), cls)
        return cls

    async def get_class(self, class_id: str) -> dict | None:
        return await self.storage.read_json(self._class_path(class_id))

    async def list_classes(self) -> list[dict]:
        classes_dir = self.storage.root / "classes"
        if not classes_dir.is_dir():
            return []
        out = []
        for path in sorted(classes_dir.glob("*.json")):
            data = await self.storage.read_json(path)
            if data:
                out.append(data)
        return out

    async def update_class_students(self, class_id: str, students: list[str]) -> dict | None:
        cls = await self.get_class(class_id)
        if not cls:
            return None
        existing = {s["display_name"]: s for s in cls["students"]}
        cls["students"] = [
            existing.get(name.strip()) or {"id": uuid.uuid4().hex[:8], "display_name": name.strip()}
            for name in students
            if name.strip()
        ]
        await self.storage.write_json(self._class_path(class_id), cls)
        return cls

    # ---- sessões ----

    def _session_path(self, session_id: str):
        return self.storage.path("sessions", session_id, "session.json")

    def events_log(self, session_id: str):
        return self.hub.log_for("sessions", session_id, "events.jsonl")

    async def create_session(self, class_id: str, activity_slug: str, activity_title: str) -> dict | None:
        cls = await self.get_class(class_id)
        if not cls:
            return None
        session = {
            "id": uuid.uuid4().hex[:10],
            "class_id": class_id,
            "class_name": cls["name"],
            "activity_slug": activity_slug,
            "activity_title": activity_title,
            "status": "live",
            "join_code": _join_code(),
            "started_at": utcnow(),
            "closed_at": None,
            "roster": {
                s["id"]: {"display_name": s["display_name"], "token": None, "claimed_at": None}
                for s in cls["students"]
            },
            "pit_items": [],
        }
        await self.storage.write_json(self._session_path(session["id"]), session)
        return session

    async def get_session(self, session_id: str) -> dict | None:
        return await self.storage.read_json(self._session_path(session_id))

    async def find_by_code(self, join_code: str) -> dict | None:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return None
        for path in sessions_dir.glob("*/session.json"):
            data = await self.storage.read_json(path)
            if data and data.get("join_code") == join_code.upper() and data.get("status") == "live":
                return data
        return None

    async def list_sessions(self) -> list[dict]:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return []
        out = []
        for path in sorted(sessions_dir.glob("*/session.json")):
            data = await self.storage.read_json(path)
            if data:
                out.append(data)
        out.sort(key=lambda s: s.get("started_at", ""), reverse=True)
        return out

    async def close_session(self, session_id: str) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self.get_session(session_id)
            if not session:
                return None
            session["status"] = "closed"
            session["closed_at"] = utcnow()
            await self.storage.write_json(self._session_path(session_id), session)
        await self.events_log(session_id).append({"type": "session_closed", "student_id": None, "payload": {}})
        return session

    # ---- identidade do aluno ----

    async def claim_identity(self, session_id: str, student_id: str) -> dict | None:
        """Aluno escolhe quem é. Devolve token; None se já reclamado/inválido."""
        async with self._session_locks[session_id]:
            session = await self.get_session(session_id)
            if not session or session["status"] != "live":
                return None
            entry = session["roster"].get(student_id)
            if entry is None or entry.get("token"):
                return None
            token = uuid.uuid4().hex
            entry["token"] = token
            entry["claimed_at"] = utcnow()
            await self.storage.write_json(self._session_path(session_id), session)
        await self.events_log(session_id).append(
            {"type": "joined", "student_id": student_id, "payload": {"display_name": entry["display_name"]}}
        )
        return {"student_token": token, "student_id": student_id, "display_name": entry["display_name"]}

    async def release_identity(self, session_id: str, student_id: str) -> bool:
        async with self._session_locks[session_id]:
            session = await self.get_session(session_id)
            if not session:
                return False
            entry = session["roster"].get(student_id)
            if not entry:
                return False
            entry["token"] = None
            entry["claimed_at"] = None
            await self.storage.write_json(self._session_path(session_id), session)
            return True

    async def student_for_token(
        self, session_id: str, token: str, *, require_live: bool = True
    ) -> str | None:
        """Valida o token do aluno. Por omissão exige sessão viva — tokens
        deixam de servir para mutações depois do fecho ou do release."""
        if not token:
            return None
        session = await self.get_session(session_id)
        if not session:
            return None
        if require_live and session.get("status") != "live":
            return None
        for student_id, entry in session["roster"].items():
            if entry.get("token") == token:
                return student_id
        return None

    # ---- eventos ----

    async def _seen(self, session_id: str) -> set[str]:
        if session_id not in self._seen_event_ids:
            records = await self.storage.read_jsonl(
                self.storage.path("sessions", session_id, "events.jsonl")
            )
            self._seen_event_ids[session_id] = {
                r["event_id"] for r in records if r.get("event_id")
            }
        return self._seen_event_ids[session_id]

    async def ingest_events(self, session_id: str, student_id: str, events: list[dict]) -> list[dict]:
        """Aceita lote de eventos do aluno (at-least-once, dedup por event_id)."""
        seen = await self._seen(session_id)
        accepted = []
        log = self.events_log(session_id)
        for ev in events[:20]:
            event_id = str(ev.get("event_id") or uuid.uuid4().hex)
            ev_type = str(ev.get("type", ""))
            if event_id in seen or ev_type not in STUDENT_EVENT_TYPES:
                continue
            seen.add(event_id)
            record = await log.append(
                {
                    "event_id": event_id,
                    "type": ev_type,
                    "student_id": student_id,
                    "unit_id": ev.get("unit_id"),
                    "payload": ev.get("payload") or {},
                }
            )
            accepted.append(record)
        return accepted

    async def emit_teacher_event(self, session_id: str, type_: str, payload: dict, student_id: str | None = None) -> dict:
        return await self.events_log(session_id).append(
            {"type": type_, "student_id": student_id, "payload": payload}
        )

    # ---- PIT-lite ----

    async def upsert_pit_item(
        self, session_id: str, student_id: str, text: str, status: str, item_id: str | None = None
    ) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self.get_session(session_id)
            if not session:
                return None
            if status not in ("planned", "doing", "done", "to_share"):
                return None
            item = None
            if item_id:
                item = next(
                    (i for i in session["pit_items"] if i["id"] == item_id and i["student_id"] == student_id),
                    None,
                )
            if item is None:
                item = {"id": uuid.uuid4().hex[:8], "student_id": student_id}
                session["pit_items"].append(item)
            item.update({"text": text.strip()[:280], "status": status, "updated_at": utcnow()})
            await self.storage.write_json(self._session_path(session_id), session)
        await self.events_log(session_id).append(
            {"type": "pit_updated", "student_id": student_id, "payload": dict(item)}
        )
        return item
