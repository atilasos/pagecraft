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
from .errors import (
    SessionClosedError,
    SessionNotFoundError,
    StudentNotInRosterError,
)
from .event_types import SESSION_EVENT_TYPES


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

    async def _load_session_unlocked(self, session_id: str) -> dict | None:
        session = await self.storage.read_json(self._session_path(session_id))
        if not session:
            return None
        events = await self.events_log(session_id).replay()
        changed = False

        closed = next(
            (event for event in reversed(events) if event.get("type") == "session_closed"),
            None,
        )
        expected_status = "closed" if closed else "live"
        expected_closed_at = closed.get("ts") if closed else None
        if (
            session.get("status") != expected_status
            or session.get("closed_at") != expected_closed_at
        ):
            session["status"] = expected_status
            session["closed_at"] = expected_closed_at
            changed = True

        pit_items: dict[str, dict] = {}
        last_identity_event: dict[str, str] = {}
        for event in events:
            event_type = event.get("type")
            student_id = event.get("student_id")
            if student_id and event_type in ("joined", "identity_released"):
                last_identity_event[str(student_id)] = str(event_type)
            if event_type != "pit_updated":
                continue
            item = dict(event.get("payload") or {})
            item_id = item.get("id")
            if not item_id:
                continue
            item["student_id"] = str(student_id or item.get("student_id") or "")
            pit_items[str(item_id)] = item
        expected_pit_items = list(pit_items.values())
        if session.get("pit_items") != expected_pit_items:
            session["pit_items"] = expected_pit_items
            changed = True

        for student_id, last_event in last_identity_event.items():
            if last_event != "identity_released":
                continue
            entry = session.get("roster", {}).get(student_id)
            if entry and (entry.get("token") is not None or entry.get("claimed_at") is not None):
                entry["token"] = None
                entry["claimed_at"] = None
                changed = True

        if changed:
            await self.storage.write_json(self._session_path(session_id), session)
        return session

    async def _require_writable_unlocked(
        self, session_id: str, student_id: str | None = None
    ) -> dict:
        session = await self._load_session_unlocked(session_id)
        if not session:
            raise SessionNotFoundError("sessão não encontrada")
        if session.get("status") != "live":
            raise SessionClosedError("a sessão já não está ativa")
        if student_id is not None and student_id not in session.get("roster", {}):
            raise StudentNotInRosterError("esse aluno não pertence à sessão")
        return session

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
        async with self._session_locks[session_id]:
            return await self._load_session_unlocked(session_id)

    def project_session(self, session: dict, *, role: str) -> dict:
        """Produz a forma transportável da sessão sem expor tokens."""
        if role == "student":
            return {
                "id": session["id"],
                "class_name": session["class_name"],
                "activity_slug": session["activity_slug"],
                "activity_title": session["activity_title"],
                "status": session["status"],
                "roster": [
                    {
                        "student_id": student_id,
                        "display_name": entry["display_name"],
                        "taken": bool(entry.get("token")),
                    }
                    for student_id, entry in session["roster"].items()
                ],
            }
        if role == "teacher":
            projection = {key: value for key, value in session.items() if key != "roster"}
            projection["roster"] = {
                student_id: {
                    key: value for key, value in entry.items() if key != "token"
                }
                | {"taken": bool(entry.get("token"))}
                for student_id, entry in session["roster"].items()
            }
            return projection
        raise ValueError(f"papel desconhecido: {role}")

    async def find_by_code(self, join_code: str) -> dict | None:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return None
        for path in sessions_dir.glob("*/session.json"):
            data = await self.get_session(path.parent.name)
            if data and data.get("join_code") == join_code.upper() and data.get("status") == "live":
                return data
        return None

    async def list_sessions(self) -> list[dict]:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return []
        out = []
        for path in sorted(sessions_dir.glob("*/session.json")):
            data = await self.get_session(path.parent.name)
            if data:
                out.append(data)
        out.sort(key=lambda s: s.get("started_at", ""), reverse=True)
        return out

    async def close_session(self, session_id: str) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            record = await self._append_event_unlocked(
                session_id, "session_closed", {}, author="session"
            )
            session["status"] = "closed"
            session["closed_at"] = record["ts"]
            await self.storage.write_json(self._session_path(session_id), session)
        return session

    # ---- identidade do aluno ----

    async def claim_identity(self, session_id: str, student_id: str) -> dict | None:
        """Aluno escolhe quem é. Devolve token; None se já reclamado/inválido."""
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            entry = session["roster"][student_id]
            if entry.get("token"):
                return None
            token = uuid.uuid4().hex
            claimed_at = utcnow()
            await self._append_event_unlocked(
                session_id,
                "joined",
                {"display_name": entry["display_name"]},
                author="session",
                student_id=student_id,
            )
            entry["token"] = token
            entry["claimed_at"] = claimed_at
            await self.storage.write_json(self._session_path(session_id), session)
        return {"student_token": token, "student_id": student_id, "display_name": entry["display_name"]}

    async def release_identity(self, session_id: str, student_id: str) -> bool:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            entry = session["roster"][student_id]
            await self._append_event_unlocked(
                session_id,
                "identity_released",
                {},
                author="teacher",
                student_id=student_id,
            )
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
        async with self._session_locks[session_id]:
            session = await self._load_session_unlocked(session_id)
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
        async with self._session_locks[session_id]:
            await self._require_writable_unlocked(session_id, student_id)
            seen = await self._seen(session_id)
            accepted = []
            log = self.events_log(session_id)
            activity_types = {
                entry.name for entry in SESSION_EVENT_TYPES.by_author("activity")
            }
            for ev in events[:20]:
                event_id = str(ev.get("event_id") or uuid.uuid4().hex)
                ev_type = str(ev.get("type", ""))
                if event_id in seen or ev_type not in activity_types:
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

    async def send_teacher_message(
        self, session_id: str, text: str, *, student_id: str | None = None
    ) -> dict:
        return await self.emit_event(
            session_id,
            "teacher_message",
            {"text": text},
            author="teacher",
            student_id=student_id,
        )

    async def control_session(
        self,
        session_id: str,
        action: str,
        *,
        student_id: str | None = None,
        unit_id: str | None = None,
        unit_label: str = "",
    ) -> dict:
        if action == "highlight":
            return await self.emit_event(
                session_id,
                "teacher_highlight",
                {"unit_id": unit_id, "unit_label": unit_label},
                author="teacher",
                student_id=student_id,
            )
        type_ = {"freeze": "freeze_screens", "unfreeze": "unfreeze_screens"}[action]
        return await self.emit_event(
            session_id,
            type_,
            {},
            author="teacher",
        )

    async def emit_event(
        self,
        session_id: str,
        type_: str,
        payload: dict,
        *,
        author: str,
        student_id: str | None = None,
    ) -> dict:
        async with self._session_locks[session_id]:
            await self._require_writable_unlocked(session_id, student_id)
            return await self._append_event_unlocked(
                session_id,
                type_,
                payload,
                author=author,
                student_id=student_id,
            )

    async def _append_event_unlocked(
        self,
        session_id: str,
        type_: str,
        payload: dict,
        *,
        author: str,
        student_id: str | None = None,
    ) -> dict:
        event_type = SESSION_EVENT_TYPES.get(type_)
        if event_type is None:
            raise ValueError(f"tipo de Acontecimento de sessão não declarado: {type_}")
        if author not in event_type.authors:
            raise ValueError(f"{author} não pode emitir o Acontecimento de sessão {type_}")
        return await self.events_log(session_id).append(
            {"type": type_, "student_id": student_id, "payload": payload}
        )

    # ---- PIT-lite ----

    async def upsert_pit_item(
        self, session_id: str, student_id: str, text: str, status: str, item_id: str | None = None
    ) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
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
            await self._append_event_unlocked(
                session_id,
                "pit_updated",
                dict(item),
                author="student",
                student_id=student_id,
            )
            await self.storage.write_json(self._session_path(session_id), session)
        return item
